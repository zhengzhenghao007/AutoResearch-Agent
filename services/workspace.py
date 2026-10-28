"""Offline numeric material rendering and append-only workspace records."""
import html
import io
import math
import re
from threading import RLock

from schemas.workspace import WorkspaceItem, WorkspaceItemRequest, WorkspacePreview

_LOCK = RLock()
_RENDER_LOCK = RLock()


def _request(item):
    return WorkspaceItemRequest.model_validate({key: getattr(item, key) for key in WorkspaceItemRequest.model_fields})


def _dataset(run, request):
    if request.dataset_id is None:
        return None
    dataset = next((d for d in run.experiments if d.id == request.dataset_id), None)
    if dataset is None:
        raise ValueError('Unknown workspace dataset')
    names = {c.name for c in dataset.data.columns}
    if not set(request.columns) <= names or (request.x_column and request.x_column not in names):
        raise ValueError('Unknown workspace column')
    return dataset


def validate_workspace(run):
    ids = set()
    for item in run.workspace_items:
        request = _request(item)
        dataset = _dataset(run, request)
        if item.id in ids or item.dataset_sha256 != (dataset.sha256 if dataset else None):
            raise ValueError('Workspace item ID or dataset hash binding mismatch')
        ids.add(item.id)


def validate_append_only(previous, current):
    if current.workspace_items[:len(previous.workspace_items)] != previous.workspace_items:
        raise ValueError('Workspace records are append-only; create a new record for corrections')


def _escape(value):
    text = html.escape(str(value), quote=True)
    return re.sub(r'([\\`*_{}\[\]()#+.!|>~\-])', r'\\\1', text).replace('\r', ' ').replace('\n', ' ')


def preview_workspace(run, request):
    request = WorkspaceItemRequest.model_validate(request)
    from services.research_validation import validate_run
    validate_run(run)
    dataset = _dataset(run, request)
    result = WorkspacePreview(item=request, dataset_sha256=dataset.sha256 if dataset else None,
        headers=[], rows=[], svg=None, markdown='', warnings=[])
    if request.kind == 'note':
        result.markdown = _escape(request.text)
        return result
    columns = list(dict.fromkeys(([request.x_column] if request.x_column else []) + request.columns))
    units = {c.name: c.unit for c in dataset.data.columns}
    result.headers = ['sample_id'] + [f'{c} ({units[c] or "unit unspecified"})' for c in columns]
    # JSON numbers beyond JavaScript's exact integer range silently change in browser CSV exports.
    def cell(value):
        return str(value) if isinstance(value, int) and abs(value) > 9007199254740991 else value
    result.rows = [[row.sample_id, *[cell(row.values[c]) for c in columns]] for row in dataset.data.rows]
    result.markdown = '| ' + ' | '.join(_escape(h) for h in result.headers) + ' |\n'
    result.markdown += '| ' + ' | '.join('---' for _ in result.headers) + ' |\n'
    result.markdown += '\n'.join('| ' + ' | '.join('—' if v is None else _escape(v) for v in row) + ' |' for row in result.rows)
    missing = sum(any(row.values[c] is None for c in columns) for row in dataset.data.rows)
    if missing:
        result.warnings.append(f'{missing} rows contain missing selected values; no imputation. Missing plot values are excluded; lines retain gaps.')
    if request.kind == 'figure':
        if (request.chart_type == 'line' and request.x_column and
                any(row.values[request.x_column] is None for row in dataset.data.rows)):
            result.warnings.append('Missing X has no known position: showing points only, without connecting lines.')
        result.svg = _figure(dataset, request, units)
    return result


def _figure(dataset, request, units):
    # Matplotlib global rcParams and font caches require serialization across API threads.
    with _RENDER_LOCK:
        import matplotlib
        matplotlib.use('Agg')
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        y_name = request.columns[0]
        rows = list(dataset.data.rows)
        if request.x_column:
            rows.sort(key=lambda r: (r.values[request.x_column] is None,
                                    r.values[request.x_column] or 0, r.sample_id))
        for row in rows:
            for name in [y_name] + ([request.x_column] if request.x_column else []):
                value = row.values[name]
                if value is not None:
                    try:
                        valid = math.isfinite(float(value)) and abs(float(value)) <= 1e150
                    except (OverflowError, ValueError):
                        valid = False
                    if not valid:
                        raise ValueError('Values exceed supported plotting range (absolute maximum 1e150)')
        with matplotlib.rc_context({'svg.hashsalt':'research-workspace-v1', 'svg.fonttype':'none',
                                    'text.usetex':False, 'text.parse_math':False, 'font.family':'DejaVu Sans'}):
            figure = Figure(figsize=(8, 4.5), dpi=100, layout='constrained')
            FigureCanvasAgg(figure)
            axis = figure.subplots()
            xs = [row.values[request.x_column] if request.x_column else i for i,row in enumerate(rows)]
            ys = [row.values[y_name] for row in rows]
            valid = [(x,y) for x,y in zip(xs,ys) if x is not None and y is not None]
            if request.chart_type == 'bar':
                axis.bar([x for x,y in valid], [y for x,y in valid])
                low, high = axis.get_ylim()
                axis.set_ylim(min(0,low),max(0,high))
                if not request.x_column:
                    step = max(1, math.ceil(len(rows)/20))
                    axis.set_xticks(list(range(0,len(rows),step)), [r.sample_id[:50] for r in rows[::step]], rotation=45, ha='right')
            elif request.chart_type == 'scatter':
                axis.scatter([x for x,y in valid],[y for x,y in valid])
            else:
                # Unknown X has no sortable location: render points only rather than imply continuity.
                has_unknown_x = any(x is None for x in xs)
                axis.plot([float('nan') if x is None else x for x in xs],
                          [float('nan') if y is None else y for y in ys],
                          marker='o', linestyle='None' if has_unknown_x else '-')
            axis.set_title(request.title, wrap=True)
            axis.set_xlabel(f'{request.x_column} ({units[request.x_column] or "unit unspecified"})' if request.x_column else 'Sample ID')
            axis.set_ylabel(f'{y_name} ({units[y_name] or "unit unspecified"})')
            output = io.StringIO()
            figure.savefig(output, format='svg', metadata={'Date':None, 'Creator':'Research workspace'})
            figure.clear()
            return output.getvalue()


def save_workspace_item(store, run_id, request):
    request = WorkspaceItemRequest.model_validate(request)
    with store.transaction() if hasattr(store, 'transaction') else _LOCK:
        run = store.load(run_id)
        if len(run.workspace_items) >= 100:
            raise ValueError('Workspace item limit reached (100)')
        preview = preview_workspace(run, request)
        run.workspace_items.append(WorkspaceItem(**request.model_dump(), dataset_sha256=preview.dataset_sha256))
        store.save(run)
        return run


def get_workspace_item(store, run_id, item_id):
    run = store.load(run_id)
    item = next((item for item in run.workspace_items if item.id == item_id), None)
    if item is None:
        raise FileNotFoundError('Workspace item not found')
    return preview_workspace(run, _request(item))
