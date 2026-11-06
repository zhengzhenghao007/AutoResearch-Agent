from uuid import uuid4
from pathlib import Path
import pytest
from schemas.research import ResearchRun
from schemas.review_protocol import ReviewProtocolRequest
from services.research_store import ResearchStore
from services.review_protocol import get_protocol,save_protocol
from services.sqlite_store import ConflictError
from services.literature_review import build_literature_packet,render_literature_packet


def test_protocol_history_conflicts_and_project_isolation(tmp_path):
 store=ResearchStore(tmp_path)
 first=ResearchRun(id=uuid4().hex,topic='research',plan=[])
 other=ResearchRun(id=uuid4().hex,topic='other',plan=[])
 store.save(first);store.save(other)
 assert get_protocol(store,first.id).revisions==[]
 original=save_protocol(store,first.id,ReviewProtocolRequest(expected_revision=0,question='Which methods?'))
 with pytest.raises(ConflictError):save_protocol(store,first.id,ReviewProtocolRequest(expected_revision=0,question='Stale edits'))
 second=save_protocol(store,first.id,ReviewProtocolRequest(expected_revision=1,question='Updated question'))
 assert get_protocol(ResearchStore(tmp_path),first.id).revisions==[original,second]
 assert get_protocol(store,other.id).revisions==[]
 assert store.load(first.id)==first


def test_protocol_is_included_in_report_hash_and_markdown(tmp_path):
 store=ResearchStore(tmp_path)
 run=ResearchRun.model_validate_json(Path('examples/conformal-prediction/outputs/run.json').read_text(encoding='utf-8'))
 store.save(run)
 before=build_literature_packet(store,run.id,[])
 request=ReviewProtocolRequest(expected_revision=0,question='Coverage with missing values',inclusion_criteria='Studies reporting coverage',exclusion_criteria='No full text',publication_range='Unrestricted',search_strategy='Search Crossref and OpenAlex; preserve failed queries')
 saved=save_protocol(store,run.id,request)
 after=build_literature_packet(store,run.id,[])
 assert before.input_sha256!=after.input_sha256
 assert after.protocol==saved
 assert not any(item.startswith('Review protocol requires') for item in after.missing_requirements)
 text=render_literature_packet(after)
 assert 'Unrestricted' in text and 'Revision 1' in text
 assert after.missing_requirements


def test_protocol_api_conflict_and_missing_project(tmp_path):
 from fastapi.testclient import TestClient
 from types import SimpleNamespace
 from backend.app.main import app
 from backend.app.api.research import get_workflow
 store=ResearchStore(tmp_path);run=ResearchRun(id=uuid4().hex,topic='topic',plan=[]);store.save(run)
 app.dependency_overrides[get_workflow]=lambda:SimpleNamespace(store=store)
 try:
  client=TestClient(app);url=f'/api/research/runs/{run.id}/review-protocol'
  assert client.get(url).json()['revisions']==[]
  assert client.post(url,json={'expected_revision':0,'question':'Question'}).status_code==200
  assert client.post(url,json={'expected_revision':0,'question':'Old page'}).status_code==409
  assert client.get(url).json()['revisions'][0]['question']=='Question'
  assert client.get('/api/research/runs/'+'0'*32+'/review-protocol').status_code==404
 finally:app.dependency_overrides.clear()
