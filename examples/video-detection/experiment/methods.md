# Generator sensitivity in published VidProM detection results

## Source and study design

We asked whether the detector with the highest equal-generator mean also gave the best result on its weakest observed generator. We selected the six-column VidProM table because it includes a documented D3 failure on Text2Video-Zero. This is an exploratory, deliberately failure-focused analysis. All five reported detectors and all six generator columns enter the source check. The primary comparison excludes Pika for every method because Zheng et al. used Pika positives and Youku-mPLUG negatives to train their supervised baselines. D3 uses a pretrained visual encoder and requires no detector training. Excluding Pika controls known generator-name overlap only. The published aggregates cannot establish prompt disjointness, clip deduplication, or absence of pretraining exposure. [ICCV paper, sections 4.1 and 4.3, Table 4](https://openaccess.thecvf.com/content/ICCV2025/papers/Zheng_D3_Training-Free_AI-Generated_Video_Detection_Using_Second-Order_Features_ICCV_2025_paper.pdf)

Each CSV cell maps to the identically labeled row and column in Table 4. The final column copies the printed mAP. MSE denotes ModelScope, OS OpenSora, ST2V StreamingT2V, T2VZ Text2Video-Zero, and VC2 VideoCrafter2. The conference PDF SHA-256 is recorded in results.json. We redistribute numeric observations with attribution. The paper and code stay at their original sources. The VidProM authors describe their dataset as CC BY-NC 4.0. No video or weights enter this analysis. [Dataset](https://vidprom.github.io/) · [Dataset paper](https://arxiv.org/abs/2403.06098) · [D3 authors' code](https://github.com/Zig-HS/D3) · [DeMamba authors' code](https://github.com/chenhaoxing/DeMamba)

## Measurements

For each detector, take the unweighted mean of the per-generator average precision values, identify the minimum, and subtract that minimum from the mean. The analysis uses percentages and differences in percentage points. Every comparison uses the same columns in one published table. AP depends on positive prevalence and the ranking of clips. The table supplies neither per-clip scores nor operating thresholds. Hence these results do not estimate calibration, false-positive rates, or per-video correctness. Generator labels may coincide with changes in encoding, motion, prompt mix, and prevalence. The effect of generator architecture cannot be isolated.

| Detector | Mean AP excluding Pika | Lowest AP | Generator | Mean minus lowest |
| --- | ---: | ---: | --- | ---: |
| FID | 86.266 | 68.51 | T2VZ | 17.756 |
| NPR | 85.298 | 70.79 | VC2 | 14.508 |
| AIGVDet | 59.310 | 52.15 | VC2 | 7.160 |
| Demamba | 78.196 | 58.73 | MSE | 19.466 |
| Our D3 | 86.328 | 45.11 | T2VZ | 41.218 |

D3 leads the observed five-generator macro average by 0.062 points over FID. NPR has the highest observed minimum. Including Pika changes the mean leader to FID (published 88.49 versus 88.46 for D3). For the five-generator D3 comparison, omitting one generator at a time yields four-generator means from 83.235 to 96.6325. Omitting Text2Video-Zero gives the upper endpoint. This deterministic composition sensitivity does not quantify clip sampling uncertainty. The fixed, purposefully selected generators lack an exchangeable sampling design that would justify a population confidence interval. Printed source cells have two-decimal precision. Extra digits report arithmetic on those cells.

## Reproduction

Run `python analyze.py` from this directory with Python 3.12 or compatible standard-library Python. It recreates results.json from published_table4.csv without network access. The script checks each recomputed six-generator mean against the reported mAP within 0.011 percentage points to allow rounding of input and output. The SHA-256 for the CSV is computed after normalizing CRLF to LF. There is no random seed, fitted parameter, or inference step. The execution log records the interpreter and the five result rows.
