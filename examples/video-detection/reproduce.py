"""Rebuild the video-detection study from its frozen public observations."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from services.academic_humanizer import humanize


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def main():
    subprocess.run([sys.executable, str(HERE / "experiment/analyze.py")], check=True)
    methods = load("experiment/results.json")["methods"]
    papers = load("literature/papers.json")
    sources = {p["id"]: p for p in papers}
    if len(sources) != len(papers) or len(papers) < 20:
        raise ValueError("Expected at least 20 distinct literature records")
    for paper in papers:
        if not all(paper.get(k) for k in ("authors", "title", "year", "url")):
            raise ValueError(paper["id"])
    receipt = load("workflow/run.json")
    quantitative = load("experiment/results.json")
    pdf_hashes = {source["sha256"] for source in receipt["sources"]}
    if quantitative["source_pdf_sha256"] not in pdf_hashes:
        raise ValueError("Table 4 source does not match an ingested PDF")
    gaps = []
    sections = []
    count = 0

    def add(title, *paragraphs):
        nonlocal count
        sections.append("## " + title)
        for paragraph in paragraphs:
            sections.append(humanize(paragraph))
            count += 1

    d = methods["Our D3"]["excluding_pika"]
    winner = max(methods, key=lambda m: methods[m]["excluding_pika"]["worst_ap"])
    floor = methods[winner]["excluding_pika"]["worst_ap"]
    def cite(key):
        p = sources["arxiv-" + key]
        return f"[{p['authors'][0]} et al. ({p['year']})]({p['url']})"

    add("Abstract", f"Can a detector selected by average precision also protect against its weakest generator? We reanalysed five detectors on six named video generators from Table 4 of Zheng et al. After excluding Pika, which supplied training positives for supervised baselines, D3 averaged {d['macro_ap']:.3f}% AP but reached only {d['worst_ap']:.2f}% on Text2Video-Zero. {winner} had the highest observed minimum ({floor:.2f}%). The choice of selection criterion changes the preferred detector on this benchmark. Deployment error rates remain unknown.")
    add("Introduction", "A platform choosing a detector may care about performance on a difficult new generator even when that generator contributes few clips. A single average can conceal this failure. We ask whether the same method leads under two explicit criteria, equal weight per generator and performance on the weakest observed generator.")
    add("Related Work", f"{cite('2404.15955')} examine transfer from synthetic images to video. {cite('2405.19707')} introduce DeMamba and GenVideo. {cite('2501.11340')} broaden benchmark coverage with GenVidBench, while {cite('2503.06624')} study commercial-grade generators. These studies motivate an evaluation that keeps generator identity visible. We use one shared table for numerical comparisons because scores across separately constructed datasets need not have comparable class prevalence or negative examples.")
    # Keep measures from different studies attached to their own protocols.
    coverage = {item["arxiv_id"]: item for item in load("literature/fulltext-coverage.json")}
    d3_source = next(source for source in receipt["sources"]
                     if source["sha256"] == quantitative["source_pdf_sha256"])
    coverage["2508.00701"] = {**d3_source, "url": quantitative["source"]}
    for item in load("literature/evidence.json"):
        paper = sources[item["id"]]
        page = item["page"]
        if not 1 <= page <= coverage[paper["arxiv_id"]]["total_pages"]:
            raise ValueError(f"Invalid evidence page for {item['id']}")
        if item["url"] != f"{coverage[paper['arxiv_id']]['url']}#page={page}":
            raise ValueError(f"Evidence link disagrees with its reference: {item['id']}")
        sections.append(humanize(item["note"] + " " + item["limitation"]) +
                        f" [{paper['authors'][0]}, {item['locator']}, p. {page}]({item['url']})")
        count += 1
    add("Methodology", "We selected Zheng et al.'s VidProM table because it documents a difficult generator. This purposive choice tests whether a mean can conceal an observed failure. It cannot estimate how often failures occur in the wider literature. Our exploratory hypothesis was that the detector with the highest mean would differ from the detector with the highest minimum AP. We retained every detector and generator in the source table.")
    add("Experiments", "For each row we verified the mean over all six printed cells against the published mAP within 0.011 percentage points. For the primary comparison we excluded Pika from every row, computed the unweighted mean and minimum over the remaining five cells, and repeated the mean after omitting each generator in turn. This experiment uses published AP aggregates. It requires no trained weights, random seed, or clip-level inference.")
    add("Results", f"D3 had the highest five-generator mean ({d['macro_ap']:.3f}%), followed by FID ({methods['FID']['excluding_pika']['macro_ap']:.3f}%). D3 also had the lowest individual-generator score among the five detectors. The difference between its mean and its weakest generator was {d['mean_minus_worst_pp']:.3f} percentage points. {winner} led under the minimum criterion. Including Pika changes the mean leader to FID.")
    table = ["| Detector | Five-generator mean AP (%) | Lowest AP (%) | Weakest generator |", "|---|---:|---:|---|"]
    for method, result in methods.items():
        m = result["excluding_pika"]
        table.append(f"| {method} | {m['macro_ap']:.3f} | {m['worst_ap']:.2f} | {m['worst_generator']} |")
    sections.append("\n".join(table))
    add("Discussion", "The ranking change illustrates a practical decision problem. A detector selected for average performance offers no guarantee on an individual generator. Encoding, prompt mix and real-video selection may vary alongside generator identity. Published cells cannot separate these effects. AP is threshold independent and sensitive to prevalence. Calibration, false-positive rates and uncertainty for individual clips require labels and scores that the table does not supply.")
    add("Conclusion", "On this fixed benchmark, detector selection depended on how the generator results were aggregated. Reporting the weakest named generator alongside the mean makes one consequential failure visible. A prospective test on later generators with locked thresholds and independent real video remains open.")
    add("References", "The conference paper supplies all numerical observations. The literature inventory below includes retrieval candidates as well as works cited in the text. Inclusion in the inventory alone provides no support for a numerical claim.")
    sections.append("[Zheng et al. (2025). D3: Training-Free AI-Generated Video Detection Using Second-Order Features. ICCV, Table 4.](https://openaccess.thecvf.com/content/ICCV2025/html/Zheng_D3_Training-Free_AI-Generated_Video_Detection_Using_Second-Order_Features_ICCV_2025_paper.html)")
    sections.extend(f"- {', '.join(p['authors'])} ({p['year']}). [{p['title']}]({p['url']})." for p in papers)
    (HERE / "paper.md").write_text("# Reliability and Generalization of AI-Generated Video Detection\n\n" + "\n\n".join(sections) + "\n", encoding="utf-8")
    for title, body in [
        ("1. Generator-sensitive detector selection (selected)", "Compare the highest mean with the highest minimum on a published matrix. The contribution is a reusable decision audit. This is a low-cost secondary analysis, feasible with identified observations. The selected table deliberately includes a failure case."),
        ("2. Matched encoding and motion", "Re-encode matched source clips at controlled quality levels and measure within-clip score changes. This could separate encoding shortcuts from motion cues. Medium cost: it requires licensed clips, detector weights and matched transformations. The causal effect is untested."),
        ("3. Prospective temporal transfer", "Freeze thresholds before collecting newer generator families and independent real sources. Evaluate false positives and calibration by source, with uncertainty clustered by prompt or source video. This design addresses deployment decisions but requires new labels and score-level access. It is the most expensive option and remains untested.")]:
        gaps.append("## " + title + "\n\n" + humanize(body))
    (HERE / "research-gaps.md").write_text("# Research direction selection\n\n" + "\n\n".join(gaps) + "\n", encoding="utf-8")
    print(f"Rendered {count + len(gaps)} checked prose blocks and {len(papers)} literature records.")


if __name__ == "__main__":
    main()
