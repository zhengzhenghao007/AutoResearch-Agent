"""Summarize published average precision, treating each generator as one unit."""
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "published_table4.csv"
GENERATORS = ("MSE", "OS", "Pika", "ST2V", "T2VZ", "VC2")
PAPER = "https://openaccess.thecvf.com/content/ICCV2025/papers/Zheng_D3_Training-Free_AI-Generated_Video_Detection_Using_Second-Order_Features_ICCV_2025_paper.pdf"


def summarize(scores):
    worst = min(scores, key=scores.get)
    avg = mean(scores.values())
    omitted = {
        g: round(mean(v for name, v in scores.items() if name != g), 4)
        for g in scores
    }
    return {
        "n_generators": len(scores), "macro_ap": round(avg, 4),
        "worst_generator": worst, "worst_ap": scores[worst],
        "mean_minus_worst_pp": round(avg - scores[worst], 4),
        "leave_one_generator_out_macro_ap": omitted,
    }


def main():
    with INPUT.open(encoding="ascii", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [r["method"] for r in rows] == ["FID", "NPR", "AIGVDet", "Demamba", "Our D3"]
    methods = {}
    for row in rows:
        scores = {g: float(row[g]) for g in GENERATORS}
        assert all(0 <= score <= 100 for score in scores.values())
        full = summarize(scores)
        reported = float(row["reported_mAP"])
        assert abs(reported - full["macro_ap"]) <= 0.011
        methods[row["method"]] = {
            "published_ap": scores, "published_map": reported, "all_six": full,
            "excluding_pika": summarize({g: v for g, v in scores.items() if g != "Pika"}),
        }
    result = {
        "source": PAPER, "table": 4, "dataset": "VidProM", "unit": "AP percentage points",
        "source_pdf_sha256": "eae035922f465a8245969a95a7e8d9e06f11ed022b06bb2c11ce4f6a5d265981",
        "input_csv_sha256": hashlib.sha256(INPUT.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "methods": methods,
    }
    (ROOT / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for method, metrics in methods.items():
        primary = metrics["excluding_pika"]
        print(method, primary["macro_ap"], primary["worst_generator"], primary["worst_ap"],
              primary["mean_minus_worst_pp"])


if __name__ == "__main__":
    main()
