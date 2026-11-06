from pathlib import Path
from schemas.research import ResearchRun
from services.research_store import ResearchStore
from services.literature_review import build_literature_packet,render_literature_packet


def test_packet_reuses_evidence_and_respects_selection(tmp_path):
 run=ResearchRun.model_validate_json(Path('examples/conformal-prediction/outputs/run.json').read_text(encoding='utf-8'))
 store=ResearchStore(tmp_path);store.save(run)
 selected=run.papers[0].document.source.id
 before=store.load(run.id)
 packet=build_literature_packet(store,run.id,[selected])
 blocks=[block for section in packet.sections for block in section.blocks]
 assert blocks
 assert all(block.paper.source.id==selected for block in blocks)
 assert any('No saved' in item for item in packet.missing_requirements)
 assert any('protocol' in item for item in packet.missing_requirements)
 text=render_literature_packet(packet)
 assert packet.input_sha256 in text
 assert 'Screening history' in text
 assert store.load(run.id)==before
 assert build_literature_packet(store,run.id,[]).input_sha256!=packet.input_sha256

def test_packet_api_binds_project_and_returns_download_material(tmp_path):
 from fastapi.testclient import TestClient
 from types import SimpleNamespace
 from backend.app.main import app
 from backend.app.api.research import get_workflow
 run=ResearchRun.model_validate_json(Path('examples/conformal-prediction/outputs/run.json').read_text(encoding='utf-8'))
 store=ResearchStore(tmp_path);store.save(run)
 app.dependency_overrides[get_workflow]=lambda:SimpleNamespace(store=store)
 try:
  client=TestClient(app)
  response=client.post(f'/api/research/runs/{run.id}/literature-packet',json={'source_ids':[]})
  assert response.status_code==200,response.text
  assert response.json()['report']['run_id']==run.id
  assert 'Requirements to resolve' in response.json()['markdown']
  assert client.post(f'/api/research/runs/{run.id}/literature-packet',json={'source_ids':['missing']}).status_code==400
 finally:app.dependency_overrides.clear()
