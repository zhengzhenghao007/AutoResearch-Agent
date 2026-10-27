# Methods side by side; no ranking inferred

[paper_report; method] Conformal Prediction with Missing Values, p.1: Conformal Prediction with Missing Values
Margaux Zaffran 1 2 3 Aymeric Dieuleveut3 Julie Josse 2 Yaniv Romano4
Abstract
Conformal prediction is a theoretically grounded
framework for constructing predictive intervals. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:1]
[paper_report; method] Conformal Prediction with Missing Values, p.1: This motivates our novel generalized conformal-
ized quantile regression framework, missing data
augmentation, which yields prediction intervals
that are valid conditionally to the patterns of miss-
ing values, despite their exponential number. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:3]
[paper_report; method] Conformal Prediction with Missing Values, p.1: We
then show that a universally consistent quantile
regression algorithm trained on the imputed data
is Bayes optimal for the pinball risk, thus achiev-
ing valid coverage conditionally to any given data
point. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:4]
[paper_report; method] Conformal Prediction with Missing Values, p.1: Using synthetic and
data from critical care, we corroborate our theory
and report improved performance of our methods. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:5]
[paper_report; method] Conformal Prediction with Missing Values, p.1: CP provides controlled predictive regions for any
underlying predictive algorithm (e.g., neural networks and
random forests), in finite samples with no assumption on
the data distribution except for the exchangeability of the
train and test data. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:8]
[paper_report; method] Conformal Prediction with Missing Values, p.3: As most predictive algorithms
can not directly handle missing values, we impute the
incomplete data using an imputation functionΦ which maps
observed values to themselves and missing values to a func-
tion of the observed values. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:17]
[paper_report; method] Conformal Prediction with Missing Values, p.3: In practice, Φ is obtained as the result
of an algorithm I trained on
\u0008\u0000
X (k), M(k)\u0001\u0009n+1
k=1. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:18]
[paper_report; method] Conformal Prediction with Missing Values, p.3: The imputation
function Φ is the output of an algorithm I treating its input
data points symmetrically: I((X (σ(k)), M(σ(k)))n+1
k=1 )
(d)
=
I((X (k), M(k))n+1
k=1 ) conditionally on (X (k), M(k))n+1
k=1
and for any permutation σ on J1, n+ 1K. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:19]
[paper_report; method] Conformal Prediction with Missing Values, p.4: In a medical application con-
text, it is very common to have missing data completely at
3Note that our proposed framework is not based on CQR, this is
only one instance of it. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:22]
[paper_report; method] Conformal Prediction with Missing Values, p.5: Algorithm 1 CP-MDA-Exact (with CQR)
Input: Imputation algorithm I, quantile regression al-
gorithm QR, significance level α, training set\u0008\u0000
x(k), m(k), y(k)\u0001\u0009n
k=1, test point
\u0000
x(test), m(test)\u0001
Output: Prediction interval bCα
\u0000
x(test), m(test)\u0001
1: Randomly split {1, . [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:24]
[paper_report; method] Conformal Prediction with Missing Values, p.5: Algorithms 1 and 2 are written using CQR as the base
conformal procedure, but they work with any conformal
method as we describe in Appendix E.1. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:25]
[paper_report; method] Conformal Prediction with Missing Values, p.5: Algorithm 1 – CP-MDA-Exact. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:26]
[paper_report; method] Conformal Prediction with Missing Values, p.5: Then Algorithm 1 performs as impute-
then-predict+conformalization: impute the calibration set
(l. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:27]
[paper_report; method] Conformal Prediction with Missing Values, p.5: Note that
Algorithm 1 is described for one test point for simplicity but
extends easily to many test points. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:28]
[paper_report; method] Conformal Prediction with Missing Values, p.6: Conformal Prediction with Missing Values
Algorithm 2 CP-MDA-Nested (with CQR)
Input: Same as Algorithm 1
Output: Same as Algorithm 1
1: Compute lines 1 to 4 of Algorithm 1
// Generate an augmented calibration set:
2: for k ∈ Cal do Additional nested masking
3: em(k) = max(m(test), m(k))
4: end for Augmented calibration set generated. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:29]
[paper_report; method] Conformal Prediction with Missing Values, p.6: Algorithm 2 – CP-MDA-Nested. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:31]
[paper_report; method] Conformal Prediction with Missing Values, p.7: If X admits a density on Rd, then, for almost
all imputation function Φ ∈ FI
∞, (i) g∗
ℓβ ,Φ ◦ Φ is ℓβ-Bayes-
optimal (ii) any universally consistent algorithm for QR
trained on the data imputed by Φ is ℓβ-Bayes-consistent
(i.e., asymptotically in the training set size). [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:34]
[paper_report; method] Conformal Prediction with Missing Values, p.7: The prediction algorithm is a Neural Network
(NN), fitted to minimize the pinball loss (Sesia & Romano,
2021, see Appendix G.1 for details). [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:37]
[paper_report; method] Conformal Prediction with Missing Values, p.11: Algorithmic
Learning in a Random World. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:49]
[paper_report; method] Conformal Prediction with Missing Values, p.12: (2021)) within the MDA framework is of interest. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:54]
[paper_report; method] Conformal Prediction with Missing Values, p.12: Finally, while our approach is to be agnostic to the imputation chosen (similarly to CP being agnostic to the underlying
model), an interesting research path is to study the impact of the imputation on QR with finite samples. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:55]
[paper_report; method] Conformal Prediction with Missing Values, p.12: Description of the algorithm
Similarly, Algorithm 1 can be written to include any underlying predictive algorithm (regression or classification) and any
score function. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:56]
[paper_report; method] Conformal Prediction with Missing Values, p.14: Conformal Prediction with Missing Values
Algorithm 3 SCP on impute-then-predict
Input: Imputation algorithm I, predictive algorithm A, conformity score function s, significance level α, training set\u0008\u0000
X (1), M(1), Y(1)\u0001
, · · ·,
\u0000
X (n), M(n), Y(n)\u0001\u0009
. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:58]
[paper_report; method] Conformal Prediction with Missing Values, p.14: 2: Fit the imputation function: Φ(·) ← I
\u0000\u0008\u0000
X (k), M(k)\u0001
, k∈ Tr
\u0009\u0001
3: Impute the data set:
n
X (k)
imp
on
k=1
:=
\u0008
Φ
\u0000
X (k), M(k)\u0001\u0009n
k=1
4: Fit algorithm A: ˆg(·) ← A
\u0010n\u0010
X (k)
imp , Y(k)
\u0011
, k∈ Tr
o\u0011
5: for k ∈ Cal do
6: Set S(k) = s
\u0010
Y (k), ˆg
\u0010
X (k)
imp
\u0011\u0011
, the conformity scores
7: end for
8: Set SCal = {S(k), k∈ Cal}
9: Compute bQ1−αSCP (SCal), the 1 − αSCP-th empirical quantile of SCal, with 1 − αSCP := (1 − α) (1 + 1/#Cal). [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:59]
[paper_report; method] Conformal Prediction with Missing Values, p.14: For a given set of points {X (k), M(k), Y(k)}k∈T the imputation
function Φ is the output of an algorithm I that treats the data points in T symmetrically: I({X (k), M(k), Y(k)}k∈T )
(d)
=
I({X (σ(k)), M(σ(k)), Y(σ(k))})k∈T conditionally to {X (k), M(k), Y(k)}k∈T and for any permutation σ on J1, #T K. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:60]
[paper_report; method] Conformal Prediction with Missing Values, p.14: Full CP: if A5 is satisfied for T = J1, n+ 1K (i.e., the imputation algorithm treats all points symmetrically), then
impute-then-predict+Full CP is marginally valid. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:61]
[paper_report; method] Conformal Prediction with Missing Values, p.14: Jackknife+ if A5 is satisfied for T = J1, n+ 1K (i.e., the imputation algorithm treats all points symmetrically), then
impute-then-predict+Jackknife+ is marginally valid (of level 1 − 2α). [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:62]
[paper_report; method] Conformal Prediction with Missing Values, p.14: Φ is the output of an imputing algorithm I trained on
n\u0000
X (k), M(k), Y(k)\u0001
k∈T
o
. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:63]
[paper_report; method] Conformal Prediction with Missing Values, p.17: Finite sample algorithms
E.1. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:64]
[paper_report; method] Conformal Prediction with Missing Values, p.17: General statement of Algorithm 1
We provide in Algorithm 4 a general statement of CP-MDA-Exact handling any learning algorithm (both regression and
classification) and any score function. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:65]
[paper_report; method] Conformal Prediction with Missing Values, p.17: Algorithm 4 CP-MDA-Exact
Input: Imputation algorithm I, predictive algorithm A, conformity score function sg paramatrized by a model g, signifi-
cance level α, training set
\u0008\u0000
X (k), M(k), Y(k)\u0001\u0009n
k=1, test point
\u0000
X (test), M(test)\u0001
. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:66]
[paper_report; method] Conformal Prediction with Missing Values, p.17: 2: Fit the imputation function: Φ(·) ← I
\u0000\u0008\u0000
X (k), M(k)\u0001
, k∈ Tr
\u0009\u0001
3: Impute the training set:
n
X (k)
imp
o
k∈Tr
:=
\u0008
Φ
\u0000
X (k), M(k)\u0001\u0009
k∈Tr
4: Fit algorithm A: ˆg(·) ← A
\u0010n\u0010
X (k)
imp , Y(k)
\u0011
, k∈ Tr
o\u0011
// Generate an augmented calibration set:
5: Cal(test) =
\u0008
k ∈ Cal such that M(k) ⊂ M(test)\u0009
6: for k ∈ Cal(test) do
7: fM (k) = M (test) Additional masking
8: end for
Augmented calibration set generated. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:67]
[paper_report; method] Conformal Prediction with Missing Values, p.18: Since the algorithm I treats the calibration and test data points symmetrically (A5 with T =
Cal S Test), A5 also holds for any T ′ ⊂ T . [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:68]
[paper_report; method] Conformal Prediction with Missing Values, p.19: Conformal Prediction with Missing Values
Indeed, first mention that the output of Algorithm 1 can be written in the following ways:
• bCα(X (test), m(test)) =
h
ˆq α
2 ◦ Φ(X (test), m(test)) − bQ1− ˜α (S) ; ˆq1− α
2 ◦ Φ(X (test), m(test)) + bQ1− ˜α (S)
i
• bCα(X (test), m(test)) =
h
bQ ˜α
\u0000
ˆq α
2 ◦ Φ(X (test), m(test)) − SCal(test)
\u0001
; bQ1− ˜α
\u0000
ˆq1− α
2 ◦ Φ(X (test), m(test)) + SCal(test)
\u0001i
• bCα(X (test), m(test)) =
h
bQ ˜α
\u0010
Z m(test)
α
2
\u0011
; bQ1− ˜α
\u0010
Z m(test)
1− α
2
\u0011i
. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:69]
[paper_report; method] Conformal Prediction with Missing Values, p.19: On the other hand, the output predictive interval of Algorithm 2 is then written as:
• bCα
\u0000
X (test), m(test)\u0001
= [ bQ ˜α
\u0000
Z α
2
\u0001
; bQ1− ˜α
\u0000
Z1− α
2
\u0001
]. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:70]
[paper_report; method] Conformal Prediction with Missing Values, p.19: The result of Algorithm 1 implies that for any mask m ∈ M, we have :
P
\u0010
Y (test) ∈ bCα
\u0010
X (test), m
\u0011
|M (test) = m
\u0011
≥ 1 − α,
i.e. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:71]
[paper_report; method] Conformal Prediction with Missing Values, p.19: (11)
This inequality shows the conservativeness of the quantiles of the bags resulting from larger missing patterns ˜m than m
when the construction of the output of Algorithm 2. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:72]
[paper_report; method] Conformal Prediction with Missing Values, p.21: Conformal Prediction with Missing Values
Then the resulting algorithm is mask-conditionally-valid. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:73]
[paper_report; method] Conformal Prediction with Missing Values, p.22: Thus, a universally consistent algorithm learning gΦ chained
with Φ will lead to a Bayes consistent function. [evidence=e:80d2a6482a415d424e8cc77f4bcac0da0a4e45413cf77c2d60f00e858e0d5a15:74]
[paper_report; method] Probabilistically robust conformal prediction, p.1: Abstract
Conformal prediction (CP) is a framework to quan-
tify uncertainty of machine learning classifiers in-
cluding deep neural networks. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:1]
[paper_report; method] Probabilistically robust conformal prediction, p.1: We propose a novel adaptive PRCP
(aPRCP) algorithm to achieve probabilistically ro-
bust coverage. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:3]
[paper_report; method] Probabilistically robust conformal prediction, p.1: We
provide theoretical analysis to show that aPRCP
algorithm achieves robust coverage. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:4]
[paper_report; method] Probabilistically robust conformal prediction, p.1: Our experi-
ments on CIFAR-10, CIFAR-100, and ImageNet
datasets using deep neural networks demonstrate
that aPRCP achieves better trade-offs than state-of-
the-art CP and adversarially robust CP algorithms. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:5]
[paper_report; method] Probabilistically robust conformal prediction, p.1: Conformal prediction (CP) [V ovk et al., 1999,
2005, Shafer and V ovk, 2008] is a framework for UQ that
provides formal guarantees for a user-specified coverage:
ground-truth output is contained in the prediction set with a
high probability 1 − α (e.g., 90%). [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:6]
[paper_report; method] Probabilistically robust conformal prediction, p.2: The goal is to improve the robustness of the CP framework
to handle perturbations ϵ bounded by r for every input X ∈ X. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:8]
[paper_report; method] Probabilistically robust conformal prediction, p.2: The key contribution of this paper is the
development, theoretical analysis, and empirical evaluation
of the aPRCP algorithm. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:10]
[paper_report; method] Probabilistically robust conformal prediction, p.2: • Development of the adaptive PRCP algorithm based
on the principle of "quantile-of-quantile" design. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:11]
[paper_report; method] Probabilistically robust conformal prediction, p.2: • Theory to show that aPRCP algorithm achieves proba-
bilistically robust coverage for adversarial examples. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:12]
[paper_report; method] Probabilistically robust conformal prediction, p.2: CP is a framework that allows
us to compute UQ for any given predictor through a confor-
malization step. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:15]
[paper_report; method] Probabilistically robust conformal prediction, p.3: (a) (b) (c) (d)
Figure 2: Results on CIFAR100 dataset using a ResNet model to illustrate the trade-offs between nominal performance
(evaluation on clean data) and robust performance (evaluation on adversarial examples) for Vanilla CP, RSCP, and variants
of the aPRCP algorithm. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:16]
[paper_report; method] Probabilistically robust conformal prediction, p.3: The high-level goal of this paper is
to study methods to improve the robustness of the standard
CP framework to adversarial/noisy examples of the form
eX = X + ϵ, where ϵ is the additive perturbation from
Er = {ϵ ∈ Rd : ∥ϵ∥p ≤ r}. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:18]
[paper_report; method] Probabilistically robust conformal prediction, p.3: Specifically, we propose a
novel adaptive probabilistically robust conformal prediction
(aPRCP) algorithm which accounts for (1 − ˜α) (see ˜α for
robust quantile in (8)) fraction of perturbations in Er for
each data (X, Y). [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:19]
[paper_report; method] Probabilistically robust conformal prediction, p.3: 3 ROBUST CONFORMAL PREDICTION
This section describes our proposed adaptive probabilisti-
cally robust conformal prediction (aPRCP) algorithm. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:21]
[paper_report; method] Probabilistically robust conformal prediction, p.3: Next, we
motivate the significance of aPRCP algorithm and study the
theoretical connection between aPRCP and adversarially
robust CP setting [Gendler et al., 2022] in terms of proba-
bilistically robust coverage and prediction set size. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:22]
[paper_report; method] Probabilistically robust conformal prediction, p.4: (4)
The strategy of RSCP algorithm [Gendler et al., 2022] for
the ARCP setting is to directly add an inflated quantity Mr
to the quantile determined from the clean data (X, Y),
τ AR(α) :=Q(α) +Mr, (5)
and construct a prediction set with CAR(X) = {y ∈ Y:
S(X + ϵ, y) ≤ τ AR(α)}. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:23]
[paper_report; method] Probabilistically robust conformal prediction, p.5: Algorithm 1 adaptive PRCP (aPRCP)
1: Input: target probability α ∈ (0, 1); the hyper-
parameter s; set ˜α = 1− 1−α
1−α+s; split data into disjoint
training set Dtr and calibration set Dcal with |Dcal| = n. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:24]
[paper_report; method] Probabilistically robust conformal prediction, p.5: Otherwise, we have to design a score
function that satisfies the desired condition, similar to how
the randomly smoothed score function was designed by
RSCP algorithm to work for the ARCP setting [Gendler
et al., 2022]. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:25]
[paper_report; method] Probabilistically robust conformal prediction, p.5: Therefore, we would like to
address the following question: Can we design an adaptive
algorithm to fit the underlying distribution without any prior
knowledge or special design of the score function? [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:26]
[paper_report; method] Probabilistically robust conformal prediction, p.5: 3.2 ADAPTIVE PRCP ALGORITHM
This section presents our adaptive algorithm for achieving
probabilistically robust coverage (aPRCP). [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:27]
[paper_report; method] Probabilistically robust conformal prediction, p.5: We summarize
it in Algorithm 1 and elaborate it below. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:28]
[paper_report; method] Probabilistically robust conformal prediction, p.5: We denote
the empirical robust quantile (in Line 5 of Algorithm 1) by
bQrob. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:29]
[paper_report; method] Probabilistically robust conformal prediction, p.5: In
practice, the empirical threshold bτ aPR = bQrob
(⌈(n+1)(1−α+s)⌉)
is selected from empirical robust quantiles { bQrob
i }n
i=1 (in
Line 6 of Algorithm 1). [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:30]
[paper_report; method] Probabilistically robust conformal prediction, p.5: Our aPRCP algorithm is adaptive
since it finds α∗
aPR that is adaptive to the underlying dis-
tribution of (X, Y) as long as α and s are fixed apriori. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:31]
[paper_report; method] Probabilistically robust conformal prediction, p.5: The following formal result guarantees the probabilistically
robust coverage for the aPRCP algorithm. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:32]
[paper_report; method] Probabilistically robust conformal prediction, p.5: 3.3 CONNECTION BETWEEN ARCP AND PRCP
Although ARCP algorithm can achieve adversarially robust
coverage, we can still connect ARCP and PRCP in the sense
of probabilistically robust coverage and understand their
performance in terms of efficiency. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:33]
[paper_report; method] Probabilistically robust conformal prediction, p.5: Recall that efficiency
of conformal prediction algorithms refers to the measured
size of prediction sets for testing samples when some de-
sired coverage is achieved. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:34]
[paper_report; method] Probabilistically robust conformal prediction, p.6: When all three algorithms achieve (1 − α)-probabilistically
robust coverage, smaller thresholds yield better efficiency,
i.e., iPRCP and aPRCP. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:35]
[paper_report; method] Probabilistically robust conformal prediction, p.6: 3.4 APPROXIMATION ERROR OF EMPIRICAL
QUANTILES
In the above sections, we presented algorithms and their
analysis directly in the population sense, including the true
quantile Q(α) and Qrob(X; α). [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:36]
[paper_report; method] Probabilistically robust conformal prediction, p.6: 4 EXPERIMENTS AND RESULTS
In this section, we present the empirical evaluation of our
proposed aPRCP algorithm along different dimensions. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:37]
[paper_report; method] Probabilistically robust conformal prediction, p.6: We consider two relevant state-
of-the-art CP algorithms as our baselines. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:42]
[paper_report; method] Probabilistically robust conformal prediction, p.6: We consider different configurations of our proposed
adaptive probabilistically robust CP ( aPRCP) algorithm. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:43]
[paper_report; method] Probabilistically robust conformal prediction, p.6: aPRCP(worst-adv) refers to the configuration where the
evaluation of aPRCP is performed over adversarial ex-
amples generated using an adversarial attack algorithm. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:44]
[paper_report; method] Probabilistically robust conformal prediction, p.6: Adversarial Attack Algorithms. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:45]
[paper_report; method] Probabilistically robust conformal prediction, p.6: For RSCP and aPRCP(worst-adv), we employ
an adapted PGD algorithm for smoothed classifiers as pro-
posed in Salman et al. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:46]
[paper_report; method] Probabilistically robust conformal prediction, p.6: We provide additional results
using different adversarial algorithms in the Appendix. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:47]
[paper_report; method] Probabilistically robust conformal prediction, p.7: (b) Worst-case evaluation: We employ adversarial attack
algorithms as mentioned above to create one worst-case
adversarial example ( ˜X) for each clean testing input ( X). [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:51]
[paper_report; method] Probabilistically robust conformal prediction, p.7: 1)
Vanilla CP algorithm fails in achieving the target prob-
abilistic robust coverage. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:53]
[paper_report; method] Probabilistically robust conformal prediction, p.7: 2) RSCP algorithm achieves the
desired probabilistic coverage, but has an empirical cover-
age significantly larger then 90%. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:54]
[paper_report; method] Probabilistically robust conformal prediction, p.8: CP is a general framework for un-
certainty quantification that provides marginal coverage
guarantees without any assumptions on the underlying data
distribution [Shafer and V ovk, 2008]. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:58]
[paper_report; method] Probabilistically robust conformal prediction, p.8: Prior work has also considered
instantiations of the CP framework to handle the differences
between training and test distributions that is caused by
long-term distribution shift [Gibbs and Candes, 2021], co-
variate shift[Tibshirani et al., 2019], and label-distribution
shift [Podkopaev and Ramdas, 2021]. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:59]
[paper_report; method] Probabilistically robust conformal prediction, p.8: We study the general setting of probabilistically robust CP
and develop probably correct algorithms to achieve im-
proved trade-offs for nominal and robust performance over
vanilla CP and RSCP. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:62]
[paper_report; method] Probabilistically robust conformal prediction, p.8: We developed the adap-
tive PRCP (aPRCP) algorithm based on the principle of
quantile-of-quantile design and theoretically analyzed its
effectiveness to achieve improved trade-offs between perfor-
mance on clean data and robustness to adversarial examples. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:64]
[paper_report; method] Probabilistically robust conformal prediction, p.9: Human-
centered tools for coping with imperfect algorithms dur-
ing medical decision-making. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:67]
[paper_report; method] Probabilistically robust conformal prediction, p.9: Improving uncertainty quantification
of deep classifiers via neighborhood conformal predic-
tion: Novel algorithm and theoretical analysis. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:68]
[paper_report; method] Probabilistically robust conformal prediction, p.10: A unifying framework for combining complemen-
tary strengths of humans and ml toward better predic-
tive decision-making. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:70]
[paper_report; method] Probabilistically robust conformal prediction, p.10: Algorithmic learning in a random world. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:71]
[paper_report; method] Probabilistically robust conformal prediction, p.10: Machine-learning applications of algorithmic ran-
domness. [evidence=e:9f37139214aa91dc67b1cc622cfa53331a1edd04d379cf73aba7944b0546e533:72]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.1: Unlike probabilistic models that rely on asymp-
totic assumptions or priors, conformal methods provide a
distribution-free framework with guaranteed coverage. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:3]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.2: As shown in the figure, our method
(EPICSCORE) successfully expands the predictive regions
where data is scarce, providing a more reliable uncertainty
quantification. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:8]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.2: Our method explicitly accounts for epistemic
uncertainty, resulting in appropriately widened predictive
intervals that better reflect total uncertainty when extrapo-
lating beyond the training distribution. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:9]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.2: 1.1 NOVELTY
We introduce EPICSCORE (Epistemic Conformal Score),
a novel nonconformity score that explicitly integrates epis-
temic uncertainty into the conformal prediction framework. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:11]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.2: By incorpo-
rating these probabilistic models, our method dynamically
adjusts predictive regions to account for both aleatoric and
epistemic uncertainty. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:12]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.2: 1.2 RELATION TO OTHER WORK
Several recent frameworks have attempted to model epis-
temic uncertainty in machine learning predictions (see, e.g.,
He et al. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:13]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.2: 14] is particularly
relevant to our approach. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:15]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.3: However, our approach is more flexible, as it
accommodates any nonconformity score and, unlike this
method, ensures asymptotic conditional coverage. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:17]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.4: be applied to other frameworks, such as Bayesian Addi-
tive Regression Trees [Chipman et al., 2012]. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:18]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.4: 2.2 OUR APPROACH - EPICSCORE
We assume that a nonconformity score s(x, y) is already
defined based on the training set. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:19]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.5: EPICSCORE is summarized in Algorithm 1 and illustrated
in Figure 3. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:24]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.5: A discussion of the computational complex-
ity introduced by incorporating Bayesian models into our
framework is presented in Appendix D.6. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:25]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.5: Algorithm 1: EPICSCORE
Input: Data D = {(Xi, Yi)}n
i=1, conformal score
s(X, Y), nominal level α, test point Xn+1
Step I: Fit conformal scores
1: Split data D into a training set Dtrain and a calibration
set Dcal. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:26]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.7: As shown by Lei and Wasserman [2014], exact
conditional coverage is unattainable in general conformal
frameworks. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:28]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.7: 4 EXPERIMENTS
In this section, we evaluate our framework against state-of-
the-art baselines, applying EPICSCORE to two initial con-
formal scores: (i) quantile-based and (ii) regression-based. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:30]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.11: A unified
framework for constructing, tuning and assessing photo-
metric redshift density estimates in a selection bias setting. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:48]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.11: Localized conformal prediction: A gen-
eralized inference framework for conformal prediction. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:49]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.12: Optimisation of large wave farms us-
ing a multi-strategy evolutionary framework. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:52]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.13: Algorithmic learning in a random world , volume 29. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:53]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.14: In this setting, we use a K-nearest neighbors (KNN) algorithm with k = 10 as the regression base model g(x). [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:54]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.16: Overall, these results reinforce the flexibility of our method across regions with varying levels of epistemic uncertainty,
showcasing its advantage over the standard APS by explicitly incorporating epistemic uncertainty into the cutoff derivation. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:61]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.20: D EPICSCORE COMPUTATIONAL AND METHODOLOGICAL DETAILS
This section outlines the specifications of each predictive model used in our framework, discusses the scalability of each
approach, and details the trade-offs associated with prior choices. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:70]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.22: In general, our framework produces narrower intervals in most datasets. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:78]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.25: Figure 8: Variation of the Average Interval Score Loss(AISL) as a function of the β hyperparameter in the BART model
used within the EPICSCORE framework. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:94]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.26: To quantify this cost within our framework, we evaluate the run-
time of EPICSCORE across increasing sample sizes using the three Bayesian predictive models discussed previously:
MDN, BART, and Variational GP. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:95]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.27: Following the same simulation setup described in Section D.5, we
compare our approach to a standard method for conformal prediction with a density-based score, namely HPD-split [Izbicki
et al., 2022]. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:101]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.27: The experiment is designed to reflect regions with both high epistemic and aleatoric uncertainty, allowing us to
highlight the advantages of our method in capturing complex uncertainty structures. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:102]
[paper_report; method] Epistemic Uncertainty in Conformal Scores: A Unified Approach, p.27: Compared to the HPD-based region, our method exhibits significantly better adaptiveness and uncertainty quantification,
particularly in data-sparse regions of the input space. [evidence=e:c1de719f04cef9e2edf5ed75d9cc61341db27deb97812678deaf985d36f3f91e:103]
