"""Versioned, explicitly registered offline research capabilities."""
from dataclasses import dataclass
from types import MappingProxyType

from schemas.research_tasks import TaskResult


@dataclass(frozen=True)
class ResearchSkill:
    id: str
    version: int
    handler: str
    description: str
    consumes_evidence: bool = False
    permissions: tuple[str, ...] = ('saved_sources.read',)


class SkillRegistry:
    def __init__(self, skills):
        entries = {}
        for skill in skills:
            key = (skill.id, skill.version)
            if key in entries:
                raise ValueError(f'Duplicate research skill: {key}')
            entries[key] = skill
        self.entries = MappingProxyType(entries)

    def resolve(self, skill_id, version):
        try:
            return self.entries[(skill_id, version)]
        except KeyError:
            raise ValueError(f'Unsupported research skill: {skill_id} v{version}') from None

    def execute(self, executor, run, task, step, deadline):
        skill = self.resolve(step.tool, step.skill_version)
        result = getattr(executor, skill.handler)(run, task, step, deadline)
        return TaskResult.model_validate(result)

    def catalog(self):
        return [dict(id=skill.id, version=skill.version, description=skill.description,
                     permissions=list(skill.permissions), consumes_evidence=skill.consumes_evidence,
                     output_schema=TaskResult.model_json_schema())
                for skill in self.entries.values()]


RESEARCH_SKILLS = SkillRegistry([
    ResearchSkill('lexical_retrieve', 1, '_retrieve',
                  'Find saved quotations using query term overlap.', True),
    ResearchSkill('inspect_sources', 1, '_inspect',
                  'Check quotation source, page and literal text bindings.'),
])
