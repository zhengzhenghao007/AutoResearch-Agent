import pytest
from schemas.research_tasks import TaskStep
from services.skill_registry import RESEARCH_SKILLS, SkillRegistry


def test_registry_rejects_duplicate_and_unknown_versions():
    skill = RESEARCH_SKILLS.resolve('lexical_retrieve', 1)
    with pytest.raises(ValueError, match='Duplicate'):
        SkillRegistry([skill, skill])
    with pytest.raises(ValueError, match='Unsupported'):
        RESEARCH_SKILLS.resolve('lexical_retrieve', 2)
    with pytest.raises(ValueError, match='Unsupported'):
        RESEARCH_SKILLS.resolve('__import__', 1)


def test_old_step_defaults_to_existing_handler_version():
    step = TaskStep(id='s', question_id='q', title='retrieve', tool='lexical_retrieve',
                    depends_on=[], input_sha256='a')
    assert step.skill_version == 1
    assert RESEARCH_SKILLS.resolve(step.tool, step.skill_version).consumes_evidence
    assert TaskStep.model_validate_json(step.model_dump_json()) == step


def test_catalog_is_read_only_and_declares_permissions():
    entries = RESEARCH_SKILLS.catalog()
    assert {entry['id'] for entry in entries} == {'lexical_retrieve', 'inspect_sources'}
    assert all(entry['permissions'] == ['saved_sources.read'] for entry in entries)
    entries[0]['permissions'].append('network')
    assert RESEARCH_SKILLS.catalog()[0]['permissions'] == ['saved_sources.read']
