"""Durable offline retrieval. Paper text is data; no model or arbitrary tools run."""
import hashlib
import json
import re
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4
from schemas.research_tasks import ResearchTask, ResearchTaskCreate, TaskBudget, TaskQuestion, TaskStep, TaskResult, TaskEvent

TERMINAL = {'completed','incomplete','cancelled','stale','failed','budget_exhausted'}
STOPWORDS = set('what which how does do is are the a an of for in on and or to with from evidence sources about'.split())

def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def source_hash(run):
    return _hash([p.model_dump(mode='json') for p in run.papers])

def _terms(text):
    return set(re.findall(r'\w+', text.lower())) - STOPWORDS

def _intent(question):
    terms = _terms(question)
    if terms & {'compare', 'comparison', 'versus', 'vs', 'differences'}:
        return 'comparison', ['method', 'result', 'limitation']
    if terms & {'assumption', 'assumptions', 'limit', 'limits', 'limitation', 'limitations'}:
        return 'limitations', ['limitation']
    if terms & {'evaluate', 'evaluation', 'experiment', 'experiments', 'performance', 'results'}:
        return 'evaluation', ['experiment', 'result', 'dataset']
    if terms & {'method', 'methods', 'algorithm', 'algorithms', 'approach'}:
        return 'method', ['method']
    return 'general', []


def _plan(request):
    if request.subquestions:
        questions = request.subquestions
    else:
        questions = [q.strip() for q in re.split(r'[?;\n]+', request.question) if q.strip()]
        if len(questions) == 1:
            intent, _ = _intent(request.question)
            facets = {'comparison': ['methods', 'results', 'limitations'],
                      'limitations': ['assumptions', 'limitations'],
                      'evaluation': ['experiments', 'results'],
                      'method': ['methods', 'evaluation']}.get(intent, [])
            if facets:
                topic = ' '.join(sorted(_terms(request.question) - {'compare', 'comparison', 'versus', 'vs', 'differences', 'what'}))
                questions = [f'{facet} for {topic}' for facet in facets]
    if not questions or any(not _terms(q) or len(q) > 2000 for q in questions):
        raise ValueError('Questions must contain usable topic terms and at most 2000 characters')
    normalized = [' '.join(q.split()) for q in questions]
    if len(set(q.casefold() for q in normalized)) != len(normalized):
        raise ValueError('Subquestions must be distinct')
    return normalized[:6]


class ResearchTaskExecutor:
    def __init__(self, store, *, clock=time.time, lease_seconds=30):
        self.store, self.clock, self.lease_seconds = store, clock, lease_seconds
        store.root.mkdir(parents=True, exist_ok=True)
        self.database = store.root / 'research_tasks.sqlite3'
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, data TEXT NOT NULL, owner TEXT, started REAL, lease REAL, reserved REAL)')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.database, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _now(self):
        return datetime.fromtimestamp(self.clock(), timezone.utc)

    def _event(self, task, kind, message):
        task.updated_at = self._now()
        task.events.append(TaskEvent(at=task.updated_at, type=kind, message=message))

    def _read(self, db, run_id, task_id):
        if not re.fullmatch('[a-f0-9]{32}', task_id):
            raise ValueError('Invalid research task ID')
        row = db.execute('SELECT * FROM tasks WHERE id=? AND run_id=?', (task_id, run_id)).fetchone()
        if row is None: raise FileNotFoundError('Research task not found')
        return ResearchTask.model_validate_json(row['data']), row

    def _save(self, db, task):
        db.execute('UPDATE tasks SET data=? WHERE id=?', (task.model_dump_json(), task.id))

    def create(self, run_id, request: ResearchTaskCreate):
        request = ResearchTaskCreate.model_validate(request)
        run = self.store.load(run_id)
        questions = _plan(request)
        binding = source_hash(run)
        subs, steps = [], []
        for i, question in enumerate(dict.fromkeys(questions)):
            qid = f'q{i+1}'
            intent, categories = _intent(question)
            requirements = ['Exact saved-source quotations', f'Heuristic intent: {intent}', 'Lexical relevance; human semantic review required']
            if categories: requirements.append('Preferred categories: ' + ', '.join(categories))
            subs.append(TaskQuestion(id=qid, question=question, requirements=requirements))
            previous = []
            for tool in ('lexical_retrieve', 'inspect_sources'):
                sid = f'{qid}-{tool}'
                steps.append(TaskStep(id=sid, question_id=qid, title=f'{tool.replace("_", " ")}: {question}', tool=tool, depends_on=previous, input_sha256=_hash([binding, question, tool])))
                previous = [sid]
        task = ResearchTask(id=uuid4().hex, run_id=run_id, question=request.question, source_sha256=binding,
                            created_at=self._now(), updated_at=self._now(), budget=request.budget, subquestions=subs, steps=steps)
        self._event(task, 'planned', 'Offline lexical retrieval plan; no semantic verification or model calls.')
        with self._db() as db:
            if db.execute('SELECT count(*) FROM tasks WHERE run_id=?', (run_id,)).fetchone()[0] >= 20:
                raise ValueError('Research task limit reached (20 per run)')
            db.execute('INSERT INTO tasks(id,run_id,data) VALUES(?,?,?)', (task.id, run_id, task.model_dump_json()))
        return task

    def _refresh_stale(self, db, task, run):
        if task.status != 'stale' and source_hash(run) != task.source_sha256:
            task.status, task.stop_reason = 'stale', 'Saved sources changed; create a new task.'
            self._event(task, 'stale', task.stop_reason)
            self._save(db, task)
            db.execute('UPDATE tasks SET owner=NULL WHERE id=?', (task.id,))
        return task

    def get(self, run_id, task_id):
        run = self.store.load(run_id)
        with self._db() as db:
            return self._refresh_stale(db, self._read(db, run_id, task_id)[0], run)

    def list(self, run_id):
        run = self.store.load(run_id)
        with self._db() as db:
            tasks = [ResearchTask.model_validate_json(r[0]) for r in db.execute('SELECT data FROM tasks WHERE run_id=? ORDER BY rowid DESC LIMIT 20', (run_id,))]
            return [self._refresh_stale(db, task, run) for task in tasks]

    def cancel(self, run_id, task_id):
        self.store.load(run_id)
        with self._db() as db:
            task, row = self._read(db, run_id, task_id)
            if task.status in TERMINAL - {'budget_exhausted'}: return task
            if row['owner']:
                task.usage.seconds += min(max(0, self.clock() - row['started']), row['reserved'])
                for step in task.steps:
                    if step.status == 'running': step.status = 'pending'
            task.status, task.stop_reason = 'cancelled', 'Cancelled by user'
            self._event(task, 'cancelled', task.stop_reason)
            self._save(db, task)
            db.execute('UPDATE tasks SET owner=NULL WHERE id=?', (task.id,))
            return task

    def increase_budget(self, run_id, task_id, budget):
        budget = TaskBudget.model_validate(budget)
        self.store.load(run_id)
        with self._db() as db:
            task, row = self._read(db, run_id, task_id)
            if any(v < getattr(task.budget, k) for k,v in budget.model_dump().items()):
                raise ValueError('Budgets can only increase')
            if budget == task.budget: return task
            task.budget = budget
            if task.status == 'budget_exhausted': task.status, task.stop_reason = 'paused', None
            self._event(task, 'budget_increased', 'Explicit budget increase; historical usage retained.')
            self._save(db, task)
            return task

    def _compute(self, run, task, step, deadline):
        if step.tool == 'inspect_sources':
            prior = next(s for s in task.steps if s.id == step.depends_on[0]).result
            valid, gaps = [], list(prior.gaps)
            for eid in prior.evidence_ids:
                if self.clock() >= deadline: raise TimeoutError()
                matches = [(p, e) for p in run.papers for e in p.evidence if e.id == eid]
                if len(matches) != 1:
                    gaps.append(f'Missing or ambiguous evidence binding: {eid}')
                    continue
                paper, evidence = matches[0]
                pages = [p for p in paper.document.pages if p.number == evidence.page]
                quote = ' '.join(evidence.quote.split())
                if (evidence.source_id != paper.document.source.id or len(pages) != 1
                        or quote not in ' '.join(pages[0].text.split())):
                    gaps.append(f'Invalid source/page/quote binding: {eid}')
                else: valid.append(eid)
            return TaskResult(evidence_ids=valid, gaps=gaps,
                              summary='Source IDs, page numbers and literal quotations checked. Lexical retrieval does not establish semantic support or scientific truth.')
        question = next(q.question for q in task.subquestions if q.id == step.question_id)
        terms, ranked = _terms(question), []
        _, preferred = _intent(question)
        for paper in run.papers:
            for evidence in paper.evidence:
                if self.clock() >= deadline: raise TimeoutError()
                score = len(terms & _terms(evidence.quote))
                if score:
                    categories = {c.category for c in paper.claims if evidence.id in c.evidence_ids}
                    rank = (bool(categories & set(preferred)), score)
                    ranked.append((rank, evidence.id))
        ranked.sort(key=lambda x: (-x[0][0], -x[0][1], x[1]))
        remaining = task.budget.max_evidence - task.usage.evidence
        ids = [eid for _,eid in ranked[:min(3, remaining)]]
        gaps = [] if ids else ['No lexically matching saved evidence; question remains unanswered.']
        if len(ids) < min(3, len(ranked)):
            gaps.append('Evidence budget truncated matching quotations; coverage is partial.')
        return TaskResult(evidence_ids=ids, gaps=gaps, summary=f'Lexical term-overlap retrieval selected {len(ids)} quotations; not semantic verification.')

    def next(self, run_id, task_id):
        run = self.store.load(run_id)
        with self._db() as db:
            task, row = self._read(db, run_id, task_id)
            self._refresh_stale(db, task, run)
            if task.status in TERMINAL: return task
            now = self.clock()
            if row['owner'] and row['lease'] > now: return task
            if row['owner']:
                # A lost worker is charged its full reservation, so crashes cannot reset budgets.
                task.usage.seconds += row['reserved']
                for step in task.steps:
                    if step.status == 'running': step.status = 'pending'
                self._event(task, 'lease_recovered', 'Interrupted read step reclaimed; reserved time charged.')
                db.execute('UPDATE tasks SET owner=NULL WHERE id=?', (task.id,))
            if source_hash(run) != task.source_sha256:
                task.status, task.stop_reason = 'stale', 'Saved sources changed; create a new task.'
                self._event(task, 'stale', task.stop_reason)
                self._save(db, task)
                return task
            completed = {s.id for s in task.steps if s.status == 'completed'}
            step = next(s for s in task.steps if s.status == 'pending' and set(s.depends_on) <= completed)
            if (task.usage.steps >= task.budget.max_steps or task.usage.seconds >= task.budget.max_seconds
                    or (step.tool == 'lexical_retrieve' and task.usage.evidence >= task.budget.max_evidence)):
                task.status, task.stop_reason = 'budget_exhausted', 'Execution budget exhausted; explicitly increase budget to continue.'
                self._event(task, 'budget_exhausted', task.stop_reason)
                self._save(db, task)
                return task
            owner = uuid4().hex
            reserved = min(self.lease_seconds, task.budget.max_seconds - task.usage.seconds)
            step.status, step.attempts = 'running', step.attempts + 1
            task.status = 'running'
            task.usage.steps += 1
            self._event(task, 'step_started', step.id)
            self._save(db, task)
            db.execute('UPDATE tasks SET owner=?,started=?,lease=?,reserved=? WHERE id=?', (owner, now, now+reserved, reserved, task.id))
        error = None
        try:
            result = self._compute(run, task, step, now + reserved)
        except Exception as exc:
            error = exc
        with self._db() as db:
            current, row = self._read(db, run_id, task_id)
            if row['owner'] != owner or current.status == 'cancelled': return current
            final_source_hash = source_hash(self.store.load(run_id))
            elapsed = max(0, self.clock() - now)
            current.usage.seconds += min(elapsed, reserved)
            target = next(s for s in current.steps if s.id == step.id)
            if final_source_hash != current.source_sha256:
                current.status, current.stop_reason = 'stale', 'Saved sources changed during step; result discarded.'
                target.status = 'pending'
            elif elapsed >= reserved or isinstance(error, TimeoutError):
                current.status, current.stop_reason = 'budget_exhausted', 'Step time reservation exhausted; result discarded.'
                target.status = 'pending'
            elif error:
                current.status, current.stop_reason = 'failed', 'Offline execution failed; result discarded.'
                target.status = 'failed'
            else:
                target.status, target.result = 'completed', result
                if target.tool == 'lexical_retrieve': current.usage.evidence += len(result.evidence_ids)
                done = all(s.status == 'completed' for s in current.steps)
                current.status = ('incomplete' if any(s.result.gaps for s in current.steps) else 'completed') if done else 'paused'
                current.stop_reason = 'Plan finished; human semantic review remains required.' if done else None
            self._event(current, current.status, current.stop_reason or f'Checkpoint saved: {step.id}')
            self._save(db, current)
            db.execute('UPDATE tasks SET owner=NULL WHERE id=?', (current.id,))
            return current
