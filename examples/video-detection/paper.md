# Reliability and Generalization of AI-Generated Video Detection

## Abstract

Can a detector selected by average precision also protect against its weakest generator? We reanalysed five detectors on six named video generators from Table 4 of Zheng et al. After excluding Pika, which supplied training positives for supervised baselines, D3 averaged 86.328% AP but reached only 45.11% on Text2Video-Zero. NPR had the highest observed minimum (70.79%). The choice of selection criterion changes the preferred detector on this benchmark. Deployment error rates remain unknown.

## Introduction

A platform choosing a detector may care about performance on a difficult new generator even when that generator contributes few clips. A single average can conceal this failure. We ask whether the same method leads under two explicit criteria, equal weight per generator and performance on the weakest observed generator.

## Related Work

[Danial Samadi Vahdati et al. (2024)](https://arxiv.org/abs/2404.15955) examine transfer from synthetic images to video. [Haoxing Chen et al. (2024)](https://arxiv.org/abs/2405.19707) introduce DeMamba and GenVideo. [Zhenliang Ni et al. (2025)](https://arxiv.org/abs/2501.11340) broaden benchmark coverage with GenVidBench, while [Xingming Liao et al. (2025)](https://arxiv.org/abs/2503.06624) study commercial-grade generators. These studies motivate an evaluation that keeps generator identity visible. We use one shared table for numerical comparisons because scores across separately constructed datasets need not have comparable class prevalence or negative examples.

In a four-generator leave-one-out experiment, mean MISLnet AUC was 0.990 on seen sources and 0.727 on the held-out source. These four generators share one experimental pipeline. The figures are not a population estimate. [Danial Samadi Vahdati, Tables 7–8, p. 8](https://arxiv.org/pdf/2404.15955#page=8)

For Sora, MISLnet AUC rose from 0.530 zero-shot to 0.982 after generator-specific fine-tuning on less than a minute of separate footage. Sora's test subset contained 38 clips. Adaptation assumes labeled access to the new generator. [Danial Samadi Vahdati, Tables 7 and 9, p. 8](https://arxiv.org/pdf/2404.15955#page=8)

AIGVDet achieved 82.3% accuracy and 0.921 AUC on Sora compared with 95.1% and 1.000 on its training-generator family, Moonvalley. Reported results concern this dataset and decision threshold. Training and preprocessing differ from MISLnet. [Jianfa Bai, Table III, p. 4](https://arxiv.org/pdf/2403.16638#page=4)

Both classes underwent H.264 recompression at CRFs 0, 18, 23 and 28. Across six text-to-video generator subsets, the authors report accuracy above 80% and AUC above 0.88. This stress test omits the Sora subset and other codecs. [Jianfa Bai, Figure 3 and section III.D, p. 4](https://arxiv.org/pdf/2403.16638#page=4)

VideoSwin-Tiny trained on Pika achieved 96.93% top-1 accuracy on Pika and 54.66% on SVD. Single-generator training and this specific generator pair define the comparison. [Zhenliang Ni, Table 3, p. 4](https://arxiv.org/pdf/2501.11340#page=4)

For the two source-pair groups, mean scores fell from 61.81 to 56.71 and from 67.79 to 61.27 when changing generation sources. Source and generator identities are separate experimental variables. [Zhenliang Ni, Table 4, p. 4](https://arxiv.org/pdf/2501.11340#page=4)

On Chameleon, the authors report DeMamba accuracy of 0.8069 and AUC of 0.9263. TALL obtained 0.7726 and 0.8507, respectively. These figures apply to the Chameleon evaluation. No operational false-alarm rate follows from AUC alone. [Xingming Liao, Table 3, p. 5](https://arxiv.org/pdf/2503.06624#page=5)

The backtracking experiment asks which authentic source footage corresponds to a synthetic query. Random temporal cropping tests retrieval under partial overlap. Backtracking measures source retrieval and differs from binary authenticity classification. [Xingming Liao, Section 4.3, p. 5](https://arxiv.org/pdf/2503.06624#page=5)

The D3 implementation samples eight frames per second from at most two seconds of video, extracts XCLIP-B/16 features and measures successive feature distances. Implementations using pixel differences or another encoder test a different detector. [Chende Zheng, Section 4.1, p. 4](https://openaccess.thecvf.com/content/ICCV2025/papers/Zheng_D3_Training-Free_AI-Generated_Video_Detection_Using_Second-Order_Features_ICCV_2025_paper.pdf#page=4)

Across ten GenVideo generator subsets, D3 achieved 98.46% mean average precision. The largest baseline mean in the table was 88.07% for FID. AP depends on class prevalence. This aggregate does not establish an operational threshold or a false-positive rate. [Chende Zheng, Table 1, p. 5](https://openaccess.thecvf.com/content/ICCV2025/papers/Zheng_D3_Training-Free_AI-Generated_Video_Detection_Using_Second-Order_Features_ICCV_2025_paper.pdf#page=5)

## Methodology

We selected Zheng et al.'s VidProM table because it documents a difficult generator. This purposive choice tests whether a mean can conceal an observed failure. It cannot estimate how often failures occur in the wider literature. Our exploratory hypothesis was that the detector with the highest mean would differ from the detector with the highest minimum AP. We retained every detector and generator in the source table.

## Experiments

For each row we verified the mean over all six printed cells against the published mAP within 0.011 percentage points. For the primary comparison we excluded Pika from every row, computed the unweighted mean and minimum over the remaining five cells, and repeated the mean after omitting each generator in turn. This experiment uses published AP aggregates. It requires no trained weights, random seed, or clip-level inference.

## Results

D3 had the highest five-generator mean (86.328%), followed by FID (86.266%). D3 also had the lowest individual-generator score among the five detectors. The difference between its mean and its weakest generator was 41.218 percentage points. NPR led under the minimum criterion. Including Pika changes the mean leader to FID.

| Detector | Five-generator mean AP (%) | Lowest AP (%) | Weakest generator |
|---|---:|---:|---|
| FID | 86.266 | 68.51 | T2VZ |
| NPR | 85.298 | 70.79 | VC2 |
| AIGVDet | 59.310 | 52.15 | VC2 |
| Demamba | 78.196 | 58.73 | MSE |
| Our D3 | 86.328 | 45.11 | T2VZ |

## Discussion

The ranking change illustrates a practical decision problem. A detector selected for average performance offers no guarantee on an individual generator. Encoding, prompt mix and real-video selection may vary alongside generator identity. Published cells cannot separate these effects. AP is threshold independent and sensitive to prevalence. Calibration, false-positive rates and uncertainty for individual clips require labels and scores that the table does not supply.

## Conclusion

On this fixed benchmark, detector selection depended on how the generator results were aggregated. Reporting the weakest named generator alongside the mean makes one consequential failure visible. A prospective test on later generators with locked thresholds and independent real video remains open.

## References

The conference paper supplies all numerical observations. The literature inventory below includes retrieval candidates as well as works cited in the text. Inclusion in the inventory alone provides no support for a numerical claim.

[Zheng et al. (2025). D3: Training-Free AI-Generated Video Detection Using Second-Order Features. ICCV, Table 4.](https://openaccess.thecvf.com/content/ICCV2025/html/Zheng_D3_Training-Free_AI-Generated_Video_Detection_Using_Second-Order_Features_ICCV_2025_paper.html)

- Danial Samadi Vahdati, Tai D. Nguyen, Aref Azizpour, Matthew C. Stamm (2024). [Beyond Deepfake Images: Detecting AI-Generated Videos](https://arxiv.org/abs/2404.15955).

- Haoxing Chen, Yan Hong, Zizheng Huang, Zhuoer Xu, Zhangxuan Gu, Yaohui Li, Jun Lan, Huijia Zhu, Jianfu Zhang, Weiqiang Wang, Huaxiong Li (2024). [DeMamba: AI-Generated Video Detection on Million-Scale GenVideo Benchmark](https://arxiv.org/abs/2405.19707).

- Jianfa Bai, Man Lin, Gang Cao (2024). [AI-Generated Video Detection via Spatio-Temporal Anomaly Learning](https://arxiv.org/abs/2403.16638).

- Zhenliang Ni, Qiangyu Yan, Mouxiao Huang, Tianning Yuan, Yehui Tang, Hailin Hu, Xinghao Chen, Yunhe Wang (2025). [GenVidBench: A 6-Million Benchmark for AI-Generated Video Detection](https://arxiv.org/abs/2501.11340).

- Xingming Liao, Meiyu Zeng, Canyu Chen, Nankai Lin, Zhuowei Wang, Aimin Yang (2025). [Chameleon: Benchmarking Detection and Backtracking on Commercial-Grade AI-Generated Videos](https://arxiv.org/abs/2503.06624).

- Joren Michels, Lode Jorissen, Nick Michiels (2026). [Dataset Biases and Shortcut Learning in Motion-Based AI-Generated Video Detection](https://arxiv.org/abs/2607.00948).

- Chende Zheng, Ruiqi suo, Chenhao Lin, Zhengyu Zhao, Le Yang, Shuai Liu, Minghui Yang, Cong Wang, Chao Shen (2025). [D3: Training-Free AI-Generated Video Detection Using Second-Order Features](https://arxiv.org/abs/2508.00701).

- Zhuo Wang, Xiliang Liu, Ligang Sun (2025). [RobustSora: De-Watermarked Benchmark for Robust AI-Generated Video Detection](https://arxiv.org/abs/2512.10248).

- Zhengcen Li, Chenyang Jiang, Hang Zhao, Shiyang Zhou, Yunyang Mo, Feng Gao, Fan Yang, Qiben Shan, Shaocong Wu, Jingyong Su (2026). [Preserving Forgery Artifacts: AI-Generated Video Detection at Native Scale](https://arxiv.org/abs/2604.04634).

- Lichuan Ji, Yingqi Lin, Zhenhua Huang, Yan Han, Xiaogang Xu, Jiafei Wu, Chong Wang, Zhe Liu (2024). [Distinguish Any Fake Videos: Unleashing the Power of Large-scale Data and Motion Features](https://arxiv.org/abs/2405.15343).

- Riccardo Corvi, Davide Cozzolino, Ekta Prashnani, Shalini De Mello, Koki Nagano, Luisa Verdoliva (2025). [Seeing What Matters: Generalizable AI-generated Video Detection with Forensic-Oriented Augmentation](https://arxiv.org/abs/2506.16802).

- Long Ma, Zihao Xue, Yan Wang, Zhiyuan Yan, Jin Xu, Xiaorui Jiang, Haiyang Yu, Yong Liao, Zhen Bi (2026). [Your One-Stop Solution for AI-Generated Video Detection](https://arxiv.org/abs/2601.11035).

- Peisong He, Leyao Zhu, Jiaxing Li, Shiqi Wang, Haoliang Li (2024). [Exposing AI-generated Videos: A Benchmark Dataset and a Local-and-Global Temporal Defect Based Detection Method](https://arxiv.org/abs/2405.04133).

- Haiquan Wen, Yiwei He, Zhenglin Huang, Tianxiao Li, Zihan Yu, Xingru Huang, Lu Qi, Baoyuan Wu, Xiangtai Li, Guangliang Cheng (2025). [BusterX: MLLM-Powered AI-Generated Video Forgery Detection and Explanation](https://arxiv.org/abs/2505.12620).

- Minsuk Jang, Yujin Yang, Hee-Seon Kim, Minseok Son, Younghun Kim, Changick Kim (2026). [Detecting AI-Generated Videos with Spiking Neural Networks](https://arxiv.org/abs/2605.05895).

- Yifeng Gao, Yifan Ding, Hongyu Su, Juncheng Li, Yunhan Zhao, Lin Luo, Zixing Chen, Li Wang, Xin Wang, Yixu Wang, Xingjun Ma, Yu-Gang Jiang (2025). [DAVID-XR1: Detecting AI-Generated Videos with Explainable Reasoning](https://arxiv.org/abs/2506.14827).

- Meng Du, Hongchang Chen, Ran Li, Junjie Zhang, Qi Ouyang, Shibo Zhang, Shuxin Liu (2026). [G2VD: Generalizable AI-Generated Video Detection via Counterfactual Intervention and Causal Disentanglement](https://arxiv.org/abs/2607.04607).

- Wei Shang, Zhiyuan Li, Shengfeng He (2026). [Temporal Slice Learning for AI-Generated Video Detection with 400$\times$ Fewer FLOPs](https://arxiv.org/abs/2610.35148).

- Dylan Xinming Hou, Juntian Zhang, Xu Gu, Yichen Wu, Nils Lukas, Gus Xia, Xiuying Chen, Yuhan Liu (2026). [Detecting AI-Generated Video: A Vision-Language Dual-View Survey](https://arxiv.org/abs/2607.10787).

- Ziyi Liu, Firas Gabetni, Awais Hussain Sani, Xi Wang, Soobash Daiboo, Gaetan Brison, Gianni Franchi, Vicky Kalogeiton (2025). [FakeParts: a New Family of AI-Generated DeepFakes](https://arxiv.org/abs/2508.21052).

- Yuting Xu, Jian Liang, Gengyun Jia, Ziming Yang, Yanhao Zhang, Ran He (2023). [TALL: Thumbnail Layout for Deepfake Video Detection](https://arxiv.org/abs/2307.07494).

- Shehzeen Hussain, Paarth Neekhara, Malhar Jere, Farinaz Koushanfar, Julian McAuley (2020). [Adversarial Deepfakes: Evaluating Vulnerability of Deepfake Detectors to Adversarial Examples](https://arxiv.org/abs/2002.12749).

- Shruti Agarwal, Tarek El-Gaaly, Hany Farid, Ser-Nam Lim (2020). [Detecting Deep-Fake Videos from Appearance and Behavior](https://arxiv.org/abs/2004.14491).
