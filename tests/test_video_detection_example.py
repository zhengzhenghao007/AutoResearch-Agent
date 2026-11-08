"""Check the frozen research case through its public replay command."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "examples" / "video-detection"


def test_public_case_reproduces_manuscript_and_observations(tmp_path):
    case = tmp_path / "examples" / CASE.name
    shutil.copytree(CASE, case)
    for artifact in ("paper.md", "research-gaps.md", "experiment/results.json"):
        (case / artifact).unlink()
    env = {**os.environ, "PYTHONPATH": str(ROOT),
           "AUTORESEARCH_HUMANIZER_POLICY_FILE": str(tmp_path / "policy.json")}
    subprocess.run([sys.executable, str(case / "reproduce.py")], check=True, env=env)
    for artifact in ("paper.md", "research-gaps.md", "experiment/results.json"):
        assert (case / artifact).read_text(encoding="utf-8") == (CASE / artifact).read_text(encoding="utf-8")
    receipt = json.loads((case / "workflow/run.json").read_text(encoding="utf-8"))
    assert len(receipt["steps"]) == 6
    assert all(s["status"] == "completed" for s in receipt["steps"])
    assert sum(receipt["humanizer"]["workflow_calls"].values()) > 0
    assert receipt["status"] == "incomplete"
    assert all(s["anchors"] for s in receipt["sources"])
    paper = (case / "paper.md").read_text(encoding="utf-8")
    assert "45.11%" in paper and "70.79%" in paper

def test_replay_rejects_misattributed_evidence(tmp_path):
    case = tmp_path / "examples" / CASE.name
    shutil.copytree(CASE, case)
    evidence_path = case / "literature/evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence[0]["url"] = evidence[-1]["url"]
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    replay = subprocess.run([sys.executable, str(case / "reproduce.py")],
                            env={**os.environ, "PYTHONPATH": str(ROOT)}, capture_output=True)
    assert replay.returncode != 0
    assert b"Evidence link disagrees" in replay.stderr
