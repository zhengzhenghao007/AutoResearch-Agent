# Extractive review draft

> Automatically assembled quotations. Not human approved. Not a publishable synthesis.

Attribution and CC BY 4.0 license: see ../sources.json and ../README.md.

## Background

We study conformal prediction with missing val-
ues in the covariates – a setting that brings new
challenges to uncertainty quantification.

Source: Conformal Prediction with Missing Values; PDF page(s): 1

high-stakes decision-making problems such as autonomous
driving, medical or civic applications, and more.

Source: Conformal Prediction with Missing Values; PDF page(s): 1

Missing values create
additional challenges to the task of supervised learning, as
traditional machine learning algorithms can not handle in-
complete data (Josse et al., 2019; Le Morvan et al., 2020b;a;
2021; Ayme et al., 2022; Van Ness et al., 2022).

Source: Conformal Prediction with Missing Values; PDF page(s): 1

However, this line of work focuses on point predic-
tion with missing values that aim to predict the most likely
outcome.

Source: Conformal Prediction with Missing Values; PDF page(s): 1

Settings are given in Section 7, in a nutshell: data follows a Gaussian linear model where missing
values are independent of everything else and of proportion 20%; the dimension of the problem is 3 in Figure 1a while in 1b it is 10.

Source: Conformal Prediction with Missing Values; PDF page(s): 2

Challenge: NAs induce heteroskedasticity
To better understand the interplay between missing values
and conditional coverage with respect to the mask, we con-
sider an illustrative example of a Gaussian linear model.

Source: Conformal Prediction with Missing Values; PDF page(s): 4

Consider the problem of predicting a disease among a popu-
lation.

Source: Conformal Prediction with Missing Values; PDF page(s): 5

The challenge in proving MCV of CP-MDA-Nested is that
the augmented calibration and test points are not exchange-
able conditional on the mask and thus may result in under-
coverage.

Source: Conformal Prediction with Missing Values; PDF page(s): 6

This brings challenges on how to provide uncertainty esti-
mators that are valid conditionally on the missing patterns,
which are addressed by this work.

Source: Conformal Prediction with Missing Values; PDF page(s): 9

This paper studies the problem
of probabilistically robust conformal prediction
(PRCP) which ensures robustness to most pertur-
bations around clean input examples.

Source: Probabilistically robust conformal prediction; PDF page(s): 1

The main research question of
this paper is: how can we develop probably correct CP al-
gorithms for ensuring robustness to most perturbations for
(pre-trained) deep classifiers?

Source: Probabilistically robust conformal prediction; PDF page(s): 1

To address this challenge,
we develop the adaptive PRCP algorithm (aPRCP) which
is based on the principle of " quantile-of-quantile" design:
consists of two parallel quantiles as illustrated in Figure 1:
one defined in the perturbed noise space (see (8)), the other
one in the data space (9).

Source: Probabilistically robust conformal prediction; PDF page(s): 2

2 BACKGROUND AND PROBLEM SETUP
We consider the problem of uncertainty quantification (UQ)
of pre-trained deep models for classification tasks in the
presence of adversarial perturbations.

Source: Probabilistically robust conformal prediction; PDF page(s): 2

Problem Definition.

Source: Probabilistically robust conformal prediction; PDF page(s): 3

Figure 1 conceptually illustrates the PRCP problem setting.

Source: Probabilistically robust conformal prediction; PDF page(s): 3

While using adversarial training seems intu-
itive to mitigate this problem, it was shown that vanilla
CP cannot achieve the target coverage on adversarial data
[Gendler et al., 2022].

Source: Probabilistically robust conformal prediction; PDF page(s): 8

Prediction and outlier
detection in classification problems.

Source: Probabilistically robust conformal prediction; PDF page(s): 9

Designed for compat-
ibility with any Bayesian model, but equipped
with distribution-free guarantees, EPICSCORE
provides a general-purpose framework for uncer-
tainty quantification in prediction problems.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 1

For instance, in regression
problems, a standard choice is s(x, y) = |y − g(x)|, where
g(x) is a point prediction for Y , typically an estimate of
the regression function E[Y |x] [Lei et al., 2018].

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 1

A key challenge in this area has been
enhancing the quality of predictive regions, particularly by
achieving conditional coverage, which ensures validity con-
ditional on specific feature values.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 2

These three models were chosen
for their complementary strengths: BART offers flexibility
and interpretability, naturally handling categorical features;
GPs provide expressive nonparametric inference with scal-
able tractability via variational approximations; and MDNs
with Monte Carlo dropout are highly scalable, making them
well-suited for large-scale or high-dimensional problems.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 4

Recent methods aim to improve local cover-
age [Boström and Johansson, 2020, Foygel Barber et al.,
2021, Cabezas et al., 2025] and could be combined with
EPICSCORE to improve local calibration.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 7

This
flexibility extends EPICSCORE’s applicability across re-
gression, classification, and structured prediction problems.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 9

Con-
formal prediction: a unified review of theory and new
challenges.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 10

In Recent advances
in optimization and modeling of contemporary problems,
pages 255–278.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 10

Simulator-based inference with
waldo: Confidence regions by leveraging prediction algo-
rithms and posterior estimators for inverse problems.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 12

Concrete problems for autonomous vehicle safety:
Advantages of bayesian deep learning.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 12

SSC metric
The SSC metric aims to evaluate the calibration of prediction sets by stratifying them into G bins {Bj}G
j=1 based on their
cardinality.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 15

This highlights a key trade-off: while BART is effective for small to
medium-scale problems, neural network–based models like MDNs are better suited for larger datasets, where the iterative
nature of MCMC-based methods such as BART becomes increasingly expensive.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 26

## Reported methods

Conformal Prediction with Missing Values
Margaux Zaffran 1 2 3 Aymeric Dieuleveut3 Julie Josse 2 Yaniv Romano4
Abstract
Conformal prediction is a theoretically grounded
framework for constructing predictive intervals.

Source: Conformal Prediction with Missing Values; PDF page(s): 1

This motivates our novel generalized conformal-
ized quantile regression framework, missing data
augmentation, which yields prediction intervals
that are valid conditionally to the patterns of miss-
ing values, despite their exponential number.

Source: Conformal Prediction with Missing Values; PDF page(s): 1

We
then show that a universally consistent quantile
regression algorithm trained on the imputed data
is Bayes optimal for the pinball risk, thus achiev-
ing valid coverage conditionally to any given data
point.

Source: Conformal Prediction with Missing Values; PDF page(s): 1

Using synthetic and
data from critical care, we corroborate our theory
and report improved performance of our methods.

Source: Conformal Prediction with Missing Values; PDF page(s): 1

Introduction
By leveraging increasingly large data sets, statistical algo-
rithms and machine learning methods can be used to support
1Electricit´e de France R&D, Palaiseau, France 2PreMeDICaL
project team, INRIA Sophia-Antipolis, Montpellier, France
3CMAP, ´Ecole polytechnique, Institut Polytechnique de Paris,
Palaiseau, France 4Departments of Electrical Engineering and
of Computer Science, Technion - Israel Institute of Technol-
ogy, Haifa, Israel.

Source: Conformal Prediction with Missing Values; PDF page(s): 1

CP provides controlled predictive regions for any
underlying predictive algorithm (e.g., neural networks and
random forests), in finite samples with no assumption on
the data distribution except for the exchangeability of the
train and test data.

Source: Conformal Prediction with Missing Values; PDF page(s): 1

(2020b; 2021) showed that such impute-then-predict
strategies are Bayes consistent, under the assumption that
a universally consistent learner is applied on an imputed
data set.

Source: Conformal Prediction with Missing Values; PDF page(s): 1

Lastly, we support our proposal using both (semi)-synthetic
experiments and real medical data (Section 7).

Source: Conformal Prediction with Missing Values; PDF page(s): 2

The code to
reproduce our experiments is available on GitHub.

Source: Conformal Prediction with Missing Values; PDF page(s): 2

Consider a data set
with n exchangeable realizations of the random variable
(X, M, Y) ∈ Rd ×{0, 1}d ×R:
\u0008\u0000
X (k), M(k), Y(k)\u0001	n
k=1,
where X represents the features, M the missing pattern, or
mask, and Y an outcome to predict.

Source: Conformal Prediction with Missing Values; PDF page(s): 3

As most predictive algorithms
can not directly handle missing values, we impute the
incomplete data using an imputation functionΦ which maps
observed values to themselves and missing values to a func-
tion of the observed values.

Source: Conformal Prediction with Missing Values; PDF page(s): 3

In practice, Φ is obtained as the result
of an algorithm I trained on
\u0008\u0000
X (k), M(k)\u0001	n+1
k=1.

Source: Conformal Prediction with Missing Values; PDF page(s): 3

The imputation
function Φ is the output of an algorithm I treating its input
data points symmetrically: I((X (σ(k)), M(σ(k)))n+1
k=1 )
(d)
=
I((X (k), M(k))n+1
k=1 ) conditionally on (X (k), M(k))n+1
k=1
and for any permutation σ on J1, n+ 1K.

Source: Conformal Prediction with Missing Values; PDF page(s): 3

assumption, the
imputed data set is only exchangeable but not i.i.d.

Source: Conformal Prediction with Missing Values; PDF page(s): 4

In a medical application con-
text, it is very common to have missing data completely at
3Note that our proposed framework is not based on CQR, this is
only one instance of it.

Source: Conformal Prediction with Missing Values; PDF page(s): 4

Algorithm 1 CP-MDA-Exact (with CQR)
Input: Imputation algorithm I, quantile regression al-
gorithm QR, significance level α, training set\u0008\u0000
x(k), m(k), y(k)\u0001	n
k=1, test point
\u0000
x(test), m(test)\u0001
Output: Prediction interval bCα
\u0000
x(test), m(test)\u0001
1: Randomly split {1, .

Source: Conformal Prediction with Missing Values; PDF page(s): 5

Algorithms 1 and 2 are written using CQR as the base
conformal procedure, but they work with any conformal
method as we describe in Appendix E.1.

Source: Conformal Prediction with Missing Values; PDF page(s): 5

Algorithm 1 – CP-MDA-Exact.

Source: Conformal Prediction with Missing Values; PDF page(s): 5

Then Algorithm 1 performs as impute-
then-predict+conformalization: impute the calibration set
(l.

Source: Conformal Prediction with Missing Values; PDF page(s): 5

Note that
Algorithm 1 is described for one test point for simplicity but
extends easily to many test points.

Source: Conformal Prediction with Missing Values; PDF page(s): 5

Conformal Prediction with Missing Values
Algorithm 2 CP-MDA-Nested (with CQR)
Input: Same as Algorithm 1
Output: Same as Algorithm 1
1: Compute lines 1 to 4 of Algorithm 1
// Generate an augmented calibration set:
2: for k ∈ Cal do Additional nested masking
3: em(k) = max(m(test), m(k))
4: end for Augmented calibration set generated.

Source: Conformal Prediction with Missing Values; PDF page(s): 6

Algorithm 2 – CP-MDA-Nested.

Source: Conformal Prediction with Missing Values; PDF page(s): 6

We conjecture that
CP-MDA-Nested attains MCV (without any modification),
as also supported by experiments.

Source: Conformal Prediction with Missing Values; PDF page(s): 6

If X admits a density on Rd, then, for almost
all imputation function Φ ∈ FI
∞, (i) g∗
ℓβ ,Φ ◦ Φ is ℓβ-Bayes-
optimal (ii) any universally consistent algorithm for QR
trained on the data imputed by Φ is ℓβ-Bayes-consistent
(i.e., asymptotically in the training set size).

Source: Conformal Prediction with Missing Values; PDF page(s): 7

For any missing mechanism, for almost all
imputation function Φ ∈ FI
∞, if FY |(Xobs(M),M ) is continu-
ous, a universally consistent quantile regressor trained on
the imputed data set yields asymptotic conditional coverage.

Source: Conformal Prediction with Missing Values; PDF page(s): 7

In all experiments, the data are imputed using it-
erative regression (iterative ridge implemented in
Scikit-learn, Pedregosa et al.

Source: Conformal Prediction with Missing Values; PDF page(s): 7

The prediction algorithm is a Neural Network
(NN), fitted to minimize the pinball loss (Sesia & Romano,
2021, see Appendix G.1 for details).

Source: Conformal Prediction with Missing Values; PDF page(s): 7

Synthetic and semi-synthetic experiments.

Source: Conformal Prediction with Missing Values; PDF page(s): 7

All
experiments are repeated 100 times with different splits.

Source: Conformal Prediction with Missing Values; PDF page(s): 7

Synthetic experiments: Gaussian linear data
Data generation.

Source: Conformal Prediction with Missing Values; PDF page(s): 7

Similar experiments with 40% of missing values are avail-
0.50
0.75
1.00
Average coverage
CQR CQR-MDA-Exact CQR-MDA-Nested
Marg.0NA1NA2NA3NA4NA5NA6NA7NA8NA9NA
5
10
15Average length
Oracle length
Marg.0NA1NA2NA3NA4NA5NA6NA7NA8NA9NA
Marg.0NA1NA2NA3NA4NA5NA6NA7NA8NA9NA
1
Figure 3.

Source: Conformal Prediction with Missing Values; PDF page(s): 8

Semi-synthetic experiments
We consider 6 benchmark real data sets for regression:
meps_19, meps_20, meps_21 (MEPS), bio, bike
and concrete (Dua & Graff, 2017), where we introduce
missing values in their quantitative features, each of them
having a probability 0.2 of being missing (i.e.

Source: Conformal Prediction with Missing Values; PDF page(s): 8

it is a MCAR
mechanism), as in the synthetic experiments.

Source: Conformal Prediction with Missing Values; PDF page(s): 8

Each of the panels in Figure 4 summarizes the
results for one data set, with the average coverage shown in
the x-axis and the average length in the y-axis.

Source: Conformal Prediction with Missing Values; PDF page(s): 8

We observe that:
• CQR is marginally valid (orange ♦, Proposition 3.3), but
not MCV as the lowest mask coverage (orange ▼) is far
below 90% (bio, concrete, and bike data sets);
• CQR-MDA-Exact is marginally valid (purple ♦, The-
orem 5.4).

Source: Conformal Prediction with Missing Values; PDF page(s): 8

Validity and efficiency with missing values for 4 data sets (panels) withd features, including l quantitative ones in which missing
values are introduced with probability 0.2.

Source: Conformal Prediction with Missing Values; PDF page(s): 9

Algorithmic
Learning in a Random World.

Source: Conformal Prediction with Missing Values; PDF page(s): 11

Finally, Appendix G contains all the details for the experimental study and additional results completing Section 7.

Source: Conformal Prediction with Missing Values; PDF page(s): 12

Appendix G.4 describes the real data sets used for the semi-synthetic experiments, and presents the remaining
results.

Source: Conformal Prediction with Missing Values; PDF page(s): 12

Appendix G.5 presents the real medical data set (TraumaBase ®), the pipeline and settings used and the results
obtained by QR on this data set.

Source: Conformal Prediction with Missing Values; PDF page(s): 12

On the numerical side, preliminary experiments show
promising results, indicating CP-MDA’s robustness, but a detailed numerical study is needed.

Source: Conformal Prediction with Missing Values; PDF page(s): 12

(2021)) within the MDA framework is of interest.

Source: Conformal Prediction with Missing Values; PDF page(s): 12

Finally, while our approach is to be agnostic to the imputation chosen (similarly to CP being agnostic to the underlying
model), an interesting research path is to study the impact of the imputation on QR with finite samples.

Source: Conformal Prediction with Missing Values; PDF page(s): 12

Description of the algorithm
Similarly, Algorithm 1 can be written to include any underlying predictive algorithm (regression or classification) and any
score function.

Source: Conformal Prediction with Missing Values; PDF page(s): 12

Conformal Prediction with Missing Values
0 1 2 3 4 5
x
−4
−2
0
2
4
y
1
▶ Create a proper training set, a calibration set, and keep
your test set, by randomly splitting your data set.

Source: Conformal Prediction with Missing Values; PDF page(s): 13

Conformal Prediction with Missing Values
Algorithm 3 SCP on impute-then-predict
Input: Imputation algorithm I, predictive algorithm A, conformity score function s, significance level α, training set\u0008\u0000
X (1), M(1), Y(1)\u0001
, · · ·,
\u0000
X (n), M(n), Y(n)\u0001	
.

Source: Conformal Prediction with Missing Values; PDF page(s): 14

2: Fit the imputation function: Φ(·) ← I
\u0000\u0008\u0000
X (k), M(k)\u0001
, k∈ Tr
	\u0001
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
X (k), M(k)\u0001	n
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
9: Compute bQ1−αSCP (SCal), the 1 − αSCP-th empirical quantile of SCal, with 1 − αSCP := (1 − α) (1 + 1/#Cal).

Source: Conformal Prediction with Missing Values; PDF page(s): 14

For a given set of points {X (k), M(k), Y(k)}k∈T the imputation
function Φ is the output of an algorithm I that treats the data points in T symmetrically: I({X (k), M(k), Y(k)}k∈T )
(d)
=
I({X (σ(k)), M(σ(k)), Y(σ(k))})k∈T conditionally to {X (k), M(k), Y(k)}k∈T and for any permutation σ on J1, #T K.

Source: Conformal Prediction with Missing Values; PDF page(s): 14

Full CP: if A5 is satisfied for T = J1, n+ 1K (i.e., the imputation algorithm treats all points symmetrically), then
impute-then-predict+Full CP is marginally valid.

Source: Conformal Prediction with Missing Values; PDF page(s): 14

Jackknife+ if A5 is satisfied for T = J1, n+ 1K (i.e., the imputation algorithm treats all points symmetrically), then
impute-then-predict+Jackknife+ is marginally valid (of level 1 − 2α).

Source: Conformal Prediction with Missing Values; PDF page(s): 14

Φ is the output of an imputing algorithm I trained on
n\u0000
X (k), M(k), Y(k)\u0001
k∈T
o
.

Source: Conformal Prediction with Missing Values; PDF page(s): 14

Finite sample algorithms
E.1.

Source: Conformal Prediction with Missing Values; PDF page(s): 17

General statement of Algorithm 1
We provide in Algorithm 4 a general statement of CP-MDA-Exact handling any learning algorithm (both regression and
classification) and any score function.

Source: Conformal Prediction with Missing Values; PDF page(s): 17

Algorithm 4 CP-MDA-Exact
Input: Imputation algorithm I, predictive algorithm A, conformity score function sg paramatrized by a model g, signifi-
cance level α, training set
\u0008\u0000
X (k), M(k), Y(k)\u0001	n
k=1, test point
\u0000
X (test), M(test)\u0001
.

Source: Conformal Prediction with Missing Values; PDF page(s): 17

2: Fit the imputation function: Φ(·) ← I
\u0000\u0008\u0000
X (k), M(k)\u0001
, k∈ Tr
	\u0001
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
X (k), M(k)\u0001	
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
k ∈ Cal such that M(k) ⊂ M(test)	
6: for k ∈ Cal(test) do
7: fM (k) = M (test) Additional masking
8: end for
Augmented calibration set generated.

Source: Conformal Prediction with Missing Values; PDF page(s): 17

Since the algorithm I treats the calibration and test data points symmetrically (A5 with T =
Cal S Test), A5 also holds for any T ′ ⊂ T .

Source: Conformal Prediction with Missing Values; PDF page(s): 18

Conformal Prediction with Missing Values
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
.

Source: Conformal Prediction with Missing Values; PDF page(s): 19

On the other hand, the output predictive interval of Algorithm 2 is then written as:
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
].

Source: Conformal Prediction with Missing Values; PDF page(s): 19

The result of Algorithm 1 implies that for any mask m ∈ M, we have :
P
\u0010
Y (test) ∈ bCα
\u0010
X (test), m
\u0011
|M (test) = m
\u0011
≥ 1 − α,
i.e.

Source: Conformal Prediction with Missing Values; PDF page(s): 19

(11)
This inequality shows the conservativeness of the quantiles of the bags resulting from larger missing patterns ˜m than m
when the construction of the output of Algorithm 2.

Source: Conformal Prediction with Missing Values; PDF page(s): 19

Conformal Prediction with Missing Values
Then the resulting algorithm is mask-conditionally-valid.

Source: Conformal Prediction with Missing Values; PDF page(s): 21

Thus, a universally consistent algorithm learning gΦ chained
with Φ will lead to a Bayes consistent function.

Source: Conformal Prediction with Missing Values; PDF page(s): 22

Corollary 6.2 states that “For any missing mechanism, for almost all imputation function Φ ∈ FI
∞,
if FY |(Xobs(M),M ) is continuous, a universally consistent quantile regressor trained on the imputed data set yields asymptotic
conditional coverage.”.

Source: Conformal Prediction with Missing Values; PDF page(s): 23

Remark that Proposition 6.1 states that for any missing mechanism, for almost all imputation function Φ ∈ FI
∞
a universally consistent quantile regressor trained on the imputed data set achieves the Bayes risk asymptotically.

Source: Conformal Prediction with Missing Values; PDF page(s): 23

Experimental study
G.1.

Source: Conformal Prediction with Missing Values; PDF page(s): 23

The architecture and optimization of the Quantile Neural Network used in the experiments is
taken from Sesia & Romano (2021) (their code is freely available).

Source: Conformal Prediction with Missing Values; PDF page(s): 23

Higher proportion of missing values
We present synthetic experiments where the proportion of MCAR missing values is of 40% (instead of 20% in Figure 3).

Source: Conformal Prediction with Missing Values; PDF page(s): 25

The experiment is repeated 100 times.

Source: Conformal Prediction with Missing Values; PDF page(s): 25

Interestingly, although expected, these experiments lead CP-MDA-Exact to frequently output infinite intervals.

Source: Conformal Prediction with Missing Values; PDF page(s): 25

Semi-synthetic experiments
In the semi-synthetic experiments, two settings are examined: one where the training size is small in comparison to the
number of parameters of the Neural Network – “Medium” –, and one where the training size is even smaller so that some
masks have a really low (or null) frequency of appearance in the training set – “Small”.

Source: Conformal Prediction with Missing Values; PDF page(s): 26

Semi-synthetic settings: training and calibration sizes for each of the 6 data sets depending on the setting.

Source: Conformal Prediction with Missing Values; PDF page(s): 26

For the results on the two other
meps data sets (meps_20 and meps_21) see Figure 14, which repeats the visualisation of meps_19 to ease comparison.

Source: Conformal Prediction with Missing Values; PDF page(s): 26

Real data
Data set description.

Source: Conformal Prediction with Missing Values; PDF page(s): 27

For
each individual in the data set, we make only one prediction, this way avoiding too many repetitions of the same test point
when computing the average.

Source: Conformal Prediction with Missing Values; PDF page(s): 27

We split the data set into 5 folds, and predict on each fold by training the procedure on the 4
others, with 15390 observations for training, and 7694 for calibration.

Source: Conformal Prediction with Missing Values; PDF page(s): 27

Abstract
Conformal prediction (CP) is a framework to quan-
tify uncertainty of machine learning classifiers in-
cluding deep neural networks.

Source: Probabilistically robust conformal prediction; PDF page(s): 1

We propose a novel adaptive PRCP
(aPRCP) algorithm to achieve probabilistically ro-
bust coverage.

Source: Probabilistically robust conformal prediction; PDF page(s): 1

We
provide theoretical analysis to show that aPRCP
algorithm achieves robust coverage.

Source: Probabilistically robust conformal prediction; PDF page(s): 1

Our experi-
ments on CIFAR-10, CIFAR-100, and ImageNet
datasets using deep neural networks demonstrate
that aPRCP achieves better trade-offs than state-of-
the-art CP and adversarially robust CP algorithms.

Source: Probabilistically robust conformal prediction; PDF page(s): 1

Conformal prediction (CP) [V ovk et al., 1999,
2005, Shafer and V ovk, 2008] is a framework for UQ that
provides formal guarantees for a user-specified coverage:
ground-truth output is contained in the prediction set with a
high probability 1 − α (e.g., 90%).

Source: Probabilistically robust conformal prediction; PDF page(s): 1

The goal is to improve the robustness of the CP framework
to handle perturbations ϵ bounded by r for every input X ∈ X.

Source: Probabilistically robust conformal prediction; PDF page(s): 2

The key contribution of this paper is the
development, theoretical analysis, and empirical evaluation
of the aPRCP algorithm.

Source: Probabilistically robust conformal prediction; PDF page(s): 2

• Development of the adaptive PRCP algorithm based
on the principle of "quantile-of-quantile" design.

Source: Probabilistically robust conformal prediction; PDF page(s): 2

• Theory to show that aPRCP algorithm achieves proba-
bilistically robust coverage for adversarial examples.

Source: Probabilistically robust conformal prediction; PDF page(s): 2

• Experimental evaluation of aPRCP method on clas-
sification benchmarks using deep models to demon-
strate its efficacy over prior CP methods on CIFAR-10,
CIFAR-100, and ImageNet.

Source: Probabilistically robust conformal prediction; PDF page(s): 2

CP is a framework that allows
us to compute UQ for any given predictor through a confor-
malization step.

Source: Probabilistically robust conformal prediction; PDF page(s): 2

(a) (b) (c) (d)
Figure 2: Results on CIFAR100 dataset using a ResNet model to illustrate the trade-offs between nominal performance
(evaluation on clean data) and robust performance (evaluation on adversarial examples) for Vanilla CP, RSCP, and variants
of the aPRCP algorithm.

Source: Probabilistically robust conformal prediction; PDF page(s): 3

The high-level goal of this paper is
to study methods to improve the robustness of the standard
CP framework to adversarial/noisy examples of the form
eX = X + ϵ, where ϵ is the additive perturbation from
Er = {ϵ ∈ Rd : ∥ϵ∥p ≤ r}.

Source: Probabilistically robust conformal prediction; PDF page(s): 3

Specifically, we propose a
novel adaptive probabilistically robust conformal prediction
(aPRCP) algorithm which accounts for (1 − ˜α) (see ˜α for
robust quantile in (8)) fraction of perturbations in Er for
each data (X, Y).

Source: Probabilistically robust conformal prediction; PDF page(s): 3

3 ROBUST CONFORMAL PREDICTION
This section describes our proposed adaptive probabilisti-
cally robust conformal prediction (aPRCP) algorithm.

Source: Probabilistically robust conformal prediction; PDF page(s): 3

Next, we
motivate the significance of aPRCP algorithm and study the
theoretical connection between aPRCP and adversarially
robust CP setting [Gendler et al., 2022] in terms of proba-
bilistically robust coverage and prediction set size.

Source: Probabilistically robust conformal prediction; PDF page(s): 3

(4)
The strategy of RSCP algorithm [Gendler et al., 2022] for
the ARCP setting is to directly add an inflated quantity Mr
to the quantile determined from the clean data (X, Y),
τ AR(α) :=Q(α) +Mr, (5)
and construct a prediction set with CAR(X) = {y ∈ Y:
S(X + ϵ, y) ≤ τ AR(α)}.

Source: Probabilistically robust conformal prediction; PDF page(s): 4

Algorithm 1 adaptive PRCP (aPRCP)
1: Input: target probability α ∈ (0, 1); the hyper-
parameter s; set ˜α = 1− 1−α
1−α+s; split data into disjoint
training set Dtr and calibration set Dcal with |Dcal| = n.

Source: Probabilistically robust conformal prediction; PDF page(s): 5

Otherwise, we have to design a score
function that satisfies the desired condition, similar to how
the randomly smoothed score function was designed by
RSCP algorithm to work for the ARCP setting [Gendler
et al., 2022].

Source: Probabilistically robust conformal prediction; PDF page(s): 5

Therefore, we would like to
address the following question: Can we design an adaptive
algorithm to fit the underlying distribution without any prior
knowledge or special design of the score function?

Source: Probabilistically robust conformal prediction; PDF page(s): 5

3.2 ADAPTIVE PRCP ALGORITHM
This section presents our adaptive algorithm for achieving
probabilistically robust coverage (aPRCP).

Source: Probabilistically robust conformal prediction; PDF page(s): 5

We summarize
it in Algorithm 1 and elaborate it below.

Source: Probabilistically robust conformal prediction; PDF page(s): 5

We denote
the empirical robust quantile (in Line 5 of Algorithm 1) by
bQrob.

Source: Probabilistically robust conformal prediction; PDF page(s): 5

In
practice, the empirical threshold bτ aPR = bQrob
(⌈(n+1)(1−α+s)⌉)
is selected from empirical robust quantiles { bQrob
i }n
i=1 (in
Line 6 of Algorithm 1).

Source: Probabilistically robust conformal prediction; PDF page(s): 5

Our aPRCP algorithm is adaptive
since it finds α∗
aPR that is adaptive to the underlying dis-
tribution of (X, Y) as long as α and s are fixed apriori.

Source: Probabilistically robust conformal prediction; PDF page(s): 5

The following formal result guarantees the probabilistically
robust coverage for the aPRCP algorithm.

Source: Probabilistically robust conformal prediction; PDF page(s): 5

3.3 CONNECTION BETWEEN ARCP AND PRCP
Although ARCP algorithm can achieve adversarially robust
coverage, we can still connect ARCP and PRCP in the sense
of probabilistically robust coverage and understand their
performance in terms of efficiency.

Source: Probabilistically robust conformal prediction; PDF page(s): 5

Recall that efficiency
of conformal prediction algorithms refers to the measured
size of prediction sets for testing samples when some de-
sired coverage is achieved.

Source: Probabilistically robust conformal prediction; PDF page(s): 5

When all three algorithms achieve (1 − α)-probabilistically
robust coverage, smaller thresholds yield better efficiency,
i.e., iPRCP and aPRCP.

Source: Probabilistically robust conformal prediction; PDF page(s): 6

3.4 APPROXIMATION ERROR OF EMPIRICAL
QUANTILES
In the above sections, we presented algorithms and their
analysis directly in the population sense, including the true
quantile Q(α) and Qrob(X; α).

Source: Probabilistically robust conformal prediction; PDF page(s): 6

4 EXPERIMENTS AND RESULTS
In this section, we present the empirical evaluation of our
proposed aPRCP algorithm along different dimensions.

Source: Probabilistically robust conformal prediction; PDF page(s): 6

4.1 EXPERIMENTAL SETUP
Classification Datasets.

Source: Probabilistically robust conformal prediction; PDF page(s): 6

We consider three benchmark
datasets for evaluation: CIFAR10 [Krizhevsky et al., 2009],
CIFAR100 [Krizhevsky et al., 2009], and ImageNet [Deng
et al., 2009] using the standard training and test split.

Source: Probabilistically robust conformal prediction; PDF page(s): 6

We consider ResNet-110
[He et al., 2016] as the main model architecture for CI-
FAR10 and CIFAR100 and ResNet-50 for ImageNet in our
experiments.

Source: Probabilistically robust conformal prediction; PDF page(s): 6

We consider two relevant state-
of-the-art CP algorithms as our baselines.

Source: Probabilistically robust conformal prediction; PDF page(s): 6

We consider different configurations of our proposed
adaptive probabilistically robust CP ( aPRCP) algorithm.

Source: Probabilistically robust conformal prediction; PDF page(s): 6

aPRCP(worst-adv) refers to the configuration where the
evaluation of aPRCP is performed over adversarial ex-
amples generated using an adversarial attack algorithm.

Source: Probabilistically robust conformal prediction; PDF page(s): 6

Adversarial Attack Algorithms.

Source: Probabilistically robust conformal prediction; PDF page(s): 6

For RSCP and aPRCP(worst-adv), we employ
an adapted PGD algorithm for smoothed classifiers as pro-
posed in Salman et al.

Source: Probabilistically robust conformal prediction; PDF page(s): 6

We provide additional results
using different adversarial algorithms in the Appendix.

Source: Probabilistically robust conformal prediction; PDF page(s): 6

We present all our experimental
results for desired coverage as (1 − α)=90%.

Source: Probabilistically robust conformal prediction; PDF page(s): 6

We report the
average metrics (coverage and prediction set size) over 50
different runs for all datasets.

Source: Probabilistically robust conformal prediction; PDF page(s): 6

Prediction Set Size = 1
ns
nsX
j=1
| ˜C(Xn+1 + ϵj)|, (11)
where ||ϵj||2 ≤ r = 0.125 for CIFAR dataset, and ||ϵj||2 ≤
r = 0.25 for the ImageNet dataset.

Source: Probabilistically robust conformal prediction; PDF page(s): 7

(b) Worst-case evaluation: We employ adversarial attack
algorithms as mentioned above to create one worst-case
adversarial example ( ˜X) for each clean testing input ( X).

Source: Probabilistically robust conformal prediction; PDF page(s): 7

Figure 3
shows the probabilistic robustness performance (in terms
of coverage and prediction set size) obtained by Vanilla
CP, RSCP, and aPRCP( ˜α = 0.1) for all three datasets using
standard training.

Source: Probabilistically robust conformal prediction; PDF page(s): 7

1)
Vanilla CP algorithm fails in achieving the target prob-
abilistic robust coverage.

Source: Probabilistically robust conformal prediction; PDF page(s): 7

2) RSCP algorithm achieves the
desired probabilistic coverage, but has an empirical cover-
age significantly larger then 90%.

Source: Probabilistically robust conformal prediction; PDF page(s): 7

Figure 4
shows the robust coverage and prediction set size obtained
by Vanilla CP , RSCP, and aPRCP(worst-adv) achieved
on the worst-case examples for three different datasets using
Gaussian augmented training.

Source: Probabilistically robust conformal prediction; PDF page(s): 7

For all
datasets, it achieves empirical coverage lower then 80%.

Source: Probabilistically robust conformal prediction; PDF page(s): 7

2) Similar to the probabilistic robustness results, RSCP
method achieves an empirical coverage larger then 95%
for all datasets, yielding significantly large prediction sets
for all datasets.

Source: Probabilistically robust conformal prediction; PDF page(s): 7

CP is a general framework for un-
certainty quantification that provides marginal coverage
guarantees without any assumptions on the underlying data
distribution [Shafer and V ovk, 2008].

Source: Probabilistically robust conformal prediction; PDF page(s): 8

Prior work has also considered
instantiations of the CP framework to handle the differences
between training and test distributions that is caused by
long-term distribution shift [Gibbs and Candes, 2021], co-
variate shift[Tibshirani et al., 2019], and label-distribution
shift [Podkopaev and Ramdas, 2021].

Source: Probabilistically robust conformal prediction; PDF page(s): 8

We study the general setting of probabilistically robust CP
and develop probably correct algorithms to achieve im-
proved trade-offs for nominal and robust performance over
vanilla CP and RSCP.

Source: Probabilistically robust conformal prediction; PDF page(s): 8

We developed the adap-
tive PRCP (aPRCP) algorithm based on the principle of
quantile-of-quantile design and theoretically analyzed its
effectiveness to achieve improved trade-offs between perfor-
mance on clean data and robustness to adversarial examples.

Source: Probabilistically robust conformal prediction; PDF page(s): 8

Our experiments on multiple image datasets using deep
classifiers demonstrated the effectiveness of aPRCP over
vanilla CP methods and adversarially robust CP methods.

Source: Probabilistically robust conformal prediction; PDF page(s): 8

Human-
centered tools for coping with imperfect algorithms dur-
ing medical decision-making.

Source: Probabilistically robust conformal prediction; PDF page(s): 9

Improving uncertainty quantification
of deep classifiers via neighborhood conformal predic-
tion: Novel algorithm and theoretical analysis.

Source: Probabilistically robust conformal prediction; PDF page(s): 9

A unifying framework for combining complemen-
tary strengths of humans and ml toward better predic-
tive decision-making.

Source: Probabilistically robust conformal prediction; PDF page(s): 10

Algorithmic learning in a random world.

Source: Probabilistically robust conformal prediction; PDF page(s): 10

Machine-learning applications of algorithmic ran-
domness.

Source: Probabilistically robust conformal prediction; PDF page(s): 10

Unlike probabilistic models that rely on asymp-
totic assumptions or priors, conformal methods provide a
distribution-free framework with guaranteed coverage.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 1

As shown in the figure, our method
(EPICSCORE) successfully expands the predictive regions
where data is scarce, providing a more reliable uncertainty
quantification.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 2

Our method explicitly accounts for epistemic
uncertainty, resulting in appropriately widened predictive
intervals that better reflect total uncertainty when extrapo-
lating beyond the training distribution.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 2

1.1 NOVELTY
We introduce EPICSCORE (Epistemic Conformal Score),
a novel nonconformity score that explicitly integrates epis-
temic uncertainty into the conformal prediction framework.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 2

By incorpo-
rating these probabilistic models, our method dynamically
adjusts predictive regions to account for both aleatoric and
epistemic uncertainty.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 2

1.2 RELATION TO OTHER WORK
Several recent frameworks have attempted to model epis-
temic uncertainty in machine learning predictions (see, e.g.,
He et al.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 2

14] is particularly
relevant to our approach.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 2

This uncertainty is estimated
via Monte Carlo Dropout, which we also employ in some
experiments.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 3

However, our approach is more flexible, as it
accommodates any nonconformity score and, unlike this
method, ensures asymptotic conditional coverage.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 3

be applied to other frameworks, such as Bayesian Addi-
tive Regression Trees [Chipman et al., 2012].

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 4

2.2 OUR APPROACH - EPICSCORE
We assume that a nonconformity score s(x, y) is already
defined based on the training set.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 4

In our experiments, we use Gaussian Processes (GP),
Bayesian Additive Regression Trees (BART), and approx-
imate Bayesian Mixture Density Networks (MDNs) with
Monte Carlo dropout.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 4

The first subset, Dcal,1 is
transformed into the dataset
D = {(X, S) : (X, Y) ∈ Dcal,1, S= s(X, Y)}.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 4

Using this transformed dataset, we compute the posterior
distribution f (θ|D), which reflects the updated epistemic
uncertainty about the data-generating process after observ-
ing this data.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 4

EPICSCORE is summarized in Algorithm 1 and illustrated
in Figure 3.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 5

A discussion of the computational complex-
ity introduced by incorporating Bayesian models into our
framework is presented in Appendix D.6.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 5

Algorithm 1: EPICSCORE
Input: Data D = {(Xi, Yi)}n
i=1, conformal score
s(X, Y), nominal level α, test point Xn+1
Step I: Fit conformal scores
1: Split data D into a training set Dtrain and a calibration
set Dcal.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 5

As shown by Lei and Wasserman [2014], exact
conditional coverage is unattainable in general conformal
frameworks.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 7

4 EXPERIMENTS
In this section, we evaluate our framework against state-of-
the-art baselines, applying EPICSCORE to two initial con-
formal scores: (i) quantile-based and (ii) regression-based.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 7

Our comparisons are conducted using 13 datasets commonly
employed for benchmarking in the conformal prediction lit-
erature: Airfoil [Dua et al., 2017], Bike [Mehra, 2023], Con-
crete [Yeh, 1998, Dua et al., 2017], Cycle [Tfekci and Kaya,
2014, Dua et al., 2017], HomesKaggle [2016], Electric [Dua
et al., 2017], Meps19 [Romano et al., 2019], Protein [Rana,
2013, Dua et al., 2017], Star [Achilles et al., 2008], Super-
Conductivity [Hamidieh, 2018], WEC [Neshat et al., 2020],
WineRed [Cortez et al., 2009], and WineWhite [Cortez et al.,
2009].

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 7

Additional details on these datasets are provided in
Table 5 of the Appendix.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 7

Table 1: Quantile regression AISL values for each method and dataset.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 8

EPICSCORE demonstrates strong performance across most datasets and consistently ranks among the top methods.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 8

Dataset EPIC-BART EPIC-GP EPIC-MDN CQR CQR-r UACQR-P UACQR-S
airfoil 19.361 (0.234) 19.704 (0.27) 18.799 (0.29) 20.521 (0.234) 20.535 (0.236) 23.021 (0.337) 20.188 (0.3)
bike×(101) 44.722 (0.297) 47.818 (0.320)43.858 (0.326)45.628 (0.256) 45.638 (0.258) 53.413 (0.376)43.815 (0.385)
concrete 42.765 (0.723) 45.276 (0.764) 44.442 (0.8) 46.882 (0.681) 46.896 (0.683) 52.789 (1.097) 47.324 (1.349)
cycle 34.435 (0.142) 35.054 (0.131) 34.077 (0.129)39.218 (0.134) 39.408 (0.136) 43.775 (0.181) 35.346 (0.197)
electric 0.099 (< 0.001) 0.096 (< 0.001) 0.082 (< 0.001)0.102 (0.001) 0.102 (0.001) 0.111 (0.001) 0.097 (< 0.001)
homes×(105) 7.739 (0.066) 8.098 (0.072) 7.225 (0.049) 8.360 (0.075) 8.433 (0.078) 11.427 (0.131) 8.544 (0.107)
meps19 65.085 (1.469) 64.907 (1.56) 64.3 (1.528) 64.239 (1.56) 64.239 (1.56) 71.015 (1.763)63.737 (1.461)
protein 17.687 (0.019) 18.096 (0.037) 17.417 (0.019) 17.7 (0.015) 17.7 (0.016) 18.149 (0.015) 17.691 (0.015)
star×(101) 98.466 (0.768) 98.033 (0.750) 98.725 (0.754) 97.770 (0.725) 97.791 (0.724)99.782 (0.647) 99.809 (0.968)
superconductivity 74.37 (0.222) 80.278 (0.266) 70.212 (0.196)75.496 (0.219) 75.508 (0.218) 87.929 (0.513) 73.971 (0.404)
WEC×(105) 2.925 (0.009) 2.665 (0.012) 2.374 (0.010) 3.138 (0.009) 3.142 (0.009) 3.517 (0.010) 3.046 (0.010)
winered 3.007 (0.058) 3.009 (0.059) 2.977 (0.05) 2.979 (0.069) 2.978 (0.069) 3.059 (0.069) 2.999 (0.063)
winewhite 3.334 (0.03) 3.327 (0.034) 3.219 (0.03) 3.316 (0.036) 3.315 (0.036) 3.378 (0.038) 3.2 (0.036)
Table 2: Regression AISL values for each method and dataset.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 8

Dataset EPIC-BART EPIC-GP EPIC-MDN Mondrian Reg-split Weighted
airfoil 19.747 (0.767) 20.287 (0.686) 19.823 (0.675) 21.532 (0.919) 21.201 (0.98) 20.276 (0.819)
bike×(101) 36.381 (0.463) 41.448 (0.575) 37.041 (0.452) 38.190 (0.403) 43.918 (0.567) 37.773 (0.468)
concrete 52.098 (2.237) 52.998 (2.359) 51.648 (2.185) 61.915 (2.815) 54.902 (2.634) 58.399 (3.165)
cycle 19.418 (0.211) 19.522 (0.221) 19.436 (0.213) 19.403 (0.226) 19.73 (0.208) 19.49 (0.207)
electric 0.048 (<0.001) 0.049 (<0.001) 0.048 (<0.001) 0.05 (<0.001) 0.05 (0.001) 0.048 (<0.001)
homes×(105) 5.921 (0.0716) 6.192 (0.0689) 5.546 (0.055) 5.710 (0.053) 7.569 (0.098) 5.860 (0.056)
meps19 86.039 (2.421) 87.086 (2.405) 75.061 (1.807) 79.192 (1.821) 109.83 (2.695) 92.433 (3.259)
protein 18.885 (0.054) 18.772 (0.065) 17.735 (0.055) 17.586 (0.051) 19.423 (0.055) 18.314 (0.065)
star×(101) 105.616 (1.255) 106.112 (0.998) 106.368 (1.173) 109.346 (1.119) 105.250 (1.038) 129.492 (1.657)
superconductivity 54.895 (0.364) 59.16 (0.449) 53.406 (0.365) 58.065 (0.313) 68.183 (0.418) 54.981 (0.345)
WEC×(105) 1.437 (0.010) 1.435 (0.011) 1.283 (0.009) 1.294 (0.009) 1.620 (0.009) 1.410 (0.009)
winered 3.152 (0.07) 3.171 (0.064) 3.101 (0.062) 3.262 (0.069) 3.214 (0.063) 3.415 (0.067)
winewhite 3.104 (0.027) 3.187 (0.029) 3.129 (0.029) 3.087 (0.023) 3.181 (0.028) 3.189 (0.033)
model in all conformal methods.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 8

Table 3: Average outlier-to-inlier interval length ratio across methods and datasets in the quantile regression setting.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 9

Dataset EPIC-BART EPIC-GP EPIC-MDN CQR CQR-r UACQR-P UACQR-S
airfoil 1.028 (0.034) 1.01 (0.018) 1.048 (0.04) 1.005 (0.013) 1.004 (0.012) 1.002 (0.01) 1.005 (0.016)
bike 0.991 (0.007) 1.01 (0.007) 0.989 (0.007) 0.985 (0.007) 0.985 (0.007) 0.99 (0.005) 0.981 (0.01)
concrete 0.983 (0.033) 0.995 (0.016) 1.043 (0.029) 0.998 (0.012) 0.998 (0.012) 0.998 (0.008) 0.998 (0.012)
cycle 0.953 (0.014) 0.966 (0.014) 0.949 (0.014) 0.997 (0.005) 0.997 (0.005) 1.0 (0.004) 0.998 (0.007)
electric 1.01 (0.004) 1.01 (0.004) 1.012 (0.008) 1.008 (0.004) 1.007 (0.003) 1.006 (0.003) 1.01 (0.005)
homes 1.116 (0.019) 1.101 (0.016) 1.173 (0.027) 1.088 (0.015) 1.081 (0.014) 1.039 (0.006) 1.094 (0.014)
meps19 1.052 (0.029) 1.042 (0.025) 1.044 (0.028) 1.04 (0.025) 1.04 (0.025) 1.021 (0.015) 1.045 (0.026)
protein 1.001 (0.002) 1.001 (0.003) 1.006 (0.002) 1.002 (0.001) 1.002 (0.001) 1.001 (0.001) 1.002 (0.001)
star 0.994 (0.006) 0.994 (0.003) 0.999 (0.007) 0.994 (0.003) 0.993 (0.003) 0.997 (0.003) 0.997 (0.003)
superconductivity 1.021 (0.007) 0.987 (0.006) 1.029 (0.008) 1.041 (0.007) 1.041 (0.007) 1.023 (0.004) 1.049 (0.008)
WEC 1.012 (0.006) 1.003 (0.008) 1.02 (0.01) 1.016 (0.003) 1.016 (0.003) 1.011 (0.002) 1.021 (0.004)
winered 1.008 (0.012) 1.007 (0.008) 1.072 (0.022) 0.993 (0.008) 0.992 (0.008) 0.996 (0.005) 0.992 (0.009)
winewhite 1.031 (0.007) 1.024 (0.006) 1.053 (0.014) 1.018 (0.007) 1.018 (0.007) 1.018 (0.006) 1.034 (0.01)
timate variance by fitting a Random Forest to (X, Y).

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 9

In the quantile regression setting, Table 1 highlights
EPICSCORE’s strong performance across all datasets, with
the MDN-MC Dropout variant ranking among the top in 12
out of 13 cases.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 9

Notably,EPICSCORE outperforms all com-
peting methods on 7 datasets, effectively balancing coverage
and interval sharpness.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 9

For the regression setting, Table 2 confirms EPICSCORE’s
strong performance across most datasets, with the MDN-
MC Dropout variant excelling in 12 out of 13 cases and the
BART version ranking among the top in 8.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 9

Code to implementEPICSCORE
and reproduce the experiments is available at https:
//github.com/Monoxido45/EPICSCORE.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 9

A unified
framework for constructing, tuning and assessing photo-
metric redshift density estimates in a selection bias setting.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 11

Localized conformal prediction: A gen-
eralized inference framework for conformal prediction.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 11

Optimisation of large wave farms us-
ing a multi-strategy evolutionary framework.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 12

Algorithmic learning in a random world , volume 29.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 13

In this setting, we use a K-nearest neighbors (KNN) algorithm with k = 10 as the regression base model g(x).

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 14

A.2 CLASSIFICATION
For the image classification example (introduced in Figure 2), we used the publicly available CIFAR-100 dataset [Krizhevsky
et al., 2009], which consists of 60, 000 color images of size 32 × 32 spanning 100 classes, with each class containing 600
images.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 14

The dataset was split into training, calibration, and test sets, allocating 10% for testing and 45% each for training
456

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 14

Overall, these results reinforce the flexibility of our method across regions with varying levels of epistemic uncertainty,
showcasing its advantage over the standard APS by explicitly incorporating epistemic uncertainty into the cutoff derivation.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 16

C ADDITIONAL RESULTS AND DETAILS FOR REAL DATA EXPERIMENTS
In this section, we provide an overview of the evaluation metrics, dataset summaries, and additional results for both quantile
and standard regression experiments.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 18

,(Xm, Ym), we evaluate performance
using the following metrics:
• Average Marginal Coverage (AMC):
AMC = 1
m
mX
i=1
I
\u0010
Yi ∈ ˆR(Xi)
\u0011
,
which is an estimate of the marginal coverage of R.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 18

C.2 ADDITIONAL RESULTS
Table 5 summarizes the dataset details.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 19

Table 5: Summary of the datasets used in this paper, including the number of samples (n), features (p), and access links.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 19

Dataset n p Source Dataset n p Source
Airfoil 1503 5 Airfoil (UCI) Protein 45730 8 Protein (UCI)
Bike 10885 12 Bike (Kaggle) Star 2161 48 Star (Harvard Dataverse)
Concrete 1030 8 Concrete (UCI) SuperConductivity 21263 81 Superconductivity (UCI)
Cycle 9568 4 Cycle (UCI) Wave Energy Converter 54000 49 WEC (UCI)
Homes 21613 17 Home (Kaggle) Winered 4898 11 Wine red (UCI)
Eletric 10000 12 Electric (UCI) WineWhite 1599 11 Wine white (UCI)
Meps19 15781 141 Meps19 (AHRQ site))
461

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 19

Table 6: Quantile regression Mean Average Coverage values across different methods and datasets.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 20

As expected for conformal methods,
all approaches achieve marginal coverage close to the nominal level of 0.9
Dataset EPIC-BART EPIC-GP EPIC-MDN CQR CQR-r UACQR-P UACQR-S
airfoil 0.9 (0.008) 0.9 (0.01) 0.896 (0.01) 0.901 (0.007) 0.901 (0.007) 0.907 (0.009) 0.9 (0.007)
bike 0.9 (0.003) 0.898 (0.003) 0.899 (0.003) 0.899 (0.002) 0.899 (0.002) 0.9 (0.002) 0.9 (0.002)
concrete 0.905 (0.008) 0.9 (0.009) 0.898 (0.01) 0.897 (0.007) 0.897 (0.007) 0.914 (0.012) 0.895 (0.007)
cycle 0.899 (0.003) 0.9 (0.003) 0.898 (0.004) 0.901 (0.003) 0.902 (0.003) 0.901 (0.002) 0.9 (0.002)
electric 0.9 (0.003) 0.901 (0.003) 0.902 (0.004) 0.901 (0.002) 0.901 (0.002) 0.901 (0.002) 0.901 (0.002)
homes 0.902 (0.003) 0.902 (0.003) 0.9 (0.003) 0.901 (0.002) 0.901 (0.002) 0.901 (0.002) 0.901 (0.002)
meps19 0.9 (0.003) 0.9 (0.003) 0.9 (0.003) 0.899 (0.002) 0.899 (0.002) 0.901 (0.002) 0.899 (0.002)
protein 0.897 (0.003) 0.897 (0.003) 0.897 (0.003) 0.9 (0.001) 0.9 (0.001) 0.901 (0.001) 0.9 (0.001)
star 0.902 (0.006) 0.902 (0.006) 0.903 (0.006) 0.902 (0.004) 0.901 (0.004) 0.93 (0.013) 0.902 (0.004)
superconductivity 0.898 (0.004) 0.898 (0.003) 0.898 (0.003) 0.9 (0.002) 0.9 (0.002) 0.9 (0.001) 0.9 (0.002)
WEC 0.897 (0.003) 0.899 (0.003) 0.897 (0.004) 0.9 (0.001) 0.9 (0.001) 0.899 (0.001) 0.9 (0.001)
winered 0.906 (0.008) 0.905 (0.008) 0.904 (0.007) 0.897 (0.006) 0.897 (0.006) 0.903 (0.009) 0.897 (0.006)
winewhite 0.901 (0.004) 0.9 (0.005) 0.9 (0.004) 0.898 (0.003) 0.898 (0.003) 0.908 (0.009) 0.898 (0.003)
Table 7: Quantile regression Interval Length values across different methods and datasets.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 20

Dataset EPIC-BART EPIC-GP EPIC-MDN CQR CQR-r UACQR-P UACQR-S
airfoil 16.521 (0.18) 16.395 (0.237) 16.02 (0.222) 17.087 (0.127) 17.09 (0.124) 18.838 (0.367) 16.656 (0.386)
bike×(101) 37.042 (0.190) 38.413 (0.229)36.250 (0.218)41.164 (0.150) 41.125 (0.153) 43.627 (0.591) 37.415 (0.386)
concrete 36.537 (0.375)38.328 (0.618) 37.614 (0.651) 39.477 (0.353) 39.486 (0.36) 44.425 (1.307) 39.853 (1.536)
cycle 30.975 (0.128)31.587 (0.132)30.714 (0.146)35.235 (0.095) 35.346 (0.093) 38.292 (0.195) 31.045 (0.207)
electric 0.088 (0.001) 0.084 (0.001) 0.072 (0.001) 0.09 (0.001) 0.09 (0.001) 0.097 (0.001) 0.084 (0.001)
homes×(105) 5.888 (0.028) 5.739 (0.028) 5.816 (0.040) 6.313 (0.024) 6.259 (0.024) 6.750 (0.0302) 5.312 (0.0309)
meps19 32.996 (0.314) 29.268 (0.262) 29.16 (0.266) 28.948 (0.249) 28.949 (0.249) 27.857 (0.314)32.763 (0.815)
protein 16.195 (0.039) 16.485 (0.052) 16.048 (0.034)16.378 (0.011) 16.378 (0.011) 16.797 (0.019) 16.356 (0.017)
star×(101) 81.851 (1.029) 81.760 (1.042) 82.050 (1.083) 81.359 (0.508) 81.396 (0.5117)82.521 (0.618) 83.253 (0.952)
superconductivity 66.906 (0.205) 70.631 (0.366)64.805 (0.197) 69.51 (0.144) 69.482 (0.145) 78.478 (0.7) 67.046 (0.492)
WEC×(105) 2.401 (0.0111) 2.076 (0.011) 1.890 (0.009) 2.708 (0.004) 2.709 (0.004) 2.843 (0.008) 2.547 (0.007)
winered 2.098 (0.034) 2.096 (0.035) 2.11 (0.031) 1.906 (0.011) 1.902 (0.01) 2.031 (0.025) 2.077 (0.042)
winewhite 2.31 (0.017) 2.212 (0.029) 2.253 (0.016) 2.12 (0.006) 2.121 (0.006) 2.124 (0.012) 2.222 (0.017)
C.3 BASE MODEL HYPERPARAMETERS
For the CatBoost quantile regression model [Dorogush et al., 2018], we set the number of iterations (trees) to 1,000 and the
learning rate to 0.001, enabling early stopping after 50 rounds of no improvement.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 20

D EPICSCORE COMPUTATIONAL AND METHODOLOGICAL DETAILS
This section outlines the specifications of each predictive model used in our framework, discusses the scalability of each
approach, and details the trade-offs associated with prior choices.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 20

Table 8: Quantile regression Pearson correlation values across different methods and datasets.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 21

Dataset EPIC-BART EPIC-GP EPIC-MDN CQR CQR-r UACQR-P UACQR-S
airfoil 0.06 (0.013) 0.18 (0.016) 0.071 (0.016)0.125 (0.017) 0.129 (0.017) 0.132 (0.033) 0.108 (0.02)
bike 0.171 (0.013) 0.138 (0.013) 0.213 (0.012) 0.062 (0.013) 0.069 (0.013)0.108 (0.016) 0.091 (0.012)
concrete 0.101 (0.021) 0.147 (0.02) 0.068 (0.013) 0.081 (0.017) 0.082 (0.017)0.121 (0.034) 0.088 (0.02)
cycle 0.046 (0.008) 0.045 (0.009)0.085 (0.01) 0.27 (0.011) 0.292 (0.011) 0.255 (0.011) 0.192 (0.012)
electric 0.023 (0.006) 0.044 (0.009)0.159 (0.008) 0.075 (0.006) 0.071 (0.006) 0.123 (0.01) 0.134 (0.008)
homes 0.122 (0.007) 0.143 (0.01) 0.048 (0.008)0.126 (0.008) 0.15 (0.007) 0.271 (0.008) 0.221 (0.007)
meps19 0.017 (0.004) 0.084 (0.01) 0.069 (0.009) 0.08 (0.006) 0.08 (0.006) 0.128 (0.006) 0.051 (0.006)
protein 0.031 (0.004) 0.15 (0.01) 0.073 (0.004) 0.094 (0.003) 0.094 (0.003) 0.116 (0.004) 0.094 (0.004)
star 0.07 (0.012) 0.042 (0.009)0.085 (0.012)0.046 (0.009) 0.047 (0.01) 0.048 (0.011) 0.041 (0.009)
superconductivity 0.167 (0.006) 0.217 (0.008)0.034 (0.007)0.069 (0.007) 0.073 (0.006) 0.137 (0.008) 0.088 (0.005)
WEC 0.122 (0.004) 0.119 (0.006)0.149 (0.005) 0.136 (0.005) 0.147 (0.005)0.13 (0.007) 0.132 (0.005)
winered 0.062 (0.013) 0.085 (0.016) 0.058 (0.011)0.113 (0.015) 0.114 (0.016) 0.097 (0.019)0.076 (0.016)
winewhite 0.068 (0.016) 0.13 (0.016) 0.072 (0.012)0.147 (0.011) 0.147 (0.011) 0.156 (0.014) 0.099 (0.011)
Table 9: Average coverage on outliers across methods and datasets in the quantile regression setting.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 21

EPICSCORE consistently delivers near-nominal
coverage across most datasets.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 21

Dataset EPIC-BART EPIC-GP EPIC-MDN CQR CQR-r UACQR-P UACQR-S
airfoil 0.894 (0.029) 0.875 (0.032) 0.902 (0.024) 0.877 (0.031) 0.876 (0.032) 0.875 (0.033) 0.872 (0.031)
bike 0.885 (0.009) 0.9 (0.011) 0.894 (0.011) 0.882 (0.01) 0.882 (0.01) 0.887 (0.009) 0.885 (0.009)
concrete 0.824 (0.039) 0.855 (0.034) 0.875 (0.038) 0.845 (0.035) 0.844 (0.036) 0.878 (0.032) 0.845 (0.034)
cycle 0.907 (0.009) 0.908 (0.01) 0.906 (0.011) 0.9 (0.009) 0.901 (0.009) 0.909 (0.01) 0.906 (0.009)
electric 0.887 (0.01) 0.887 (0.009) 0.895 (0.009) 0.888 (0.009) 0.888 (0.009) 0.889 (0.01) 0.889 (0.009)
homes 0.89 (0.007) 0.885 (0.007) 0.895 (0.008) 0.883 (0.007) 0.88 (0.007)0.864 (0.009) 0.872 (0.007)
meps19 0.904 (0.008) 0.903 (0.008) 0.899 (0.009) 0.897 (0.008) 0.897 (0.008) 0.9 (0.008) 0.897 (0.008)
protein 0.893 (0.005) 0.895 (0.005) 0.896 (0.005) 0.894 (0.004) 0.894 (0.004) 0.894 (0.005) 0.894 (0.004)
star 0.867 (0.016) 0.871 (0.017) 0.876 (0.016) 0.875 (0.018) 0.875 (0.018) 0.911 (0.021)0.87 (0.018)
superconductivity 0.863 (0.008) 0.872 (0.009) 0.879 (0.008)0.913 (0.006) 0.912 (0.006)0.932 (0.005)0.912 (0.006)
WEC 0.901 (0.006)0.864 (0.008) 0.86 (0.009) 0.927 (0.005) 0.926 (0.005) 0.917 (0.005) 0.921 (0.005)
winered 0.875 (0.029) 0.876 (0.03) 0.892 (0.026) 0.846 (0.032) 0.847 (0.032) 0.861 (0.033) 0.848 (0.032)
winewhite 0.86 (0.015) 0.854 (0.016) 0.868 (0.014) 0.847 (0.016) 0.847 (0.016) 0.865 (0.02) 0.861 (0.016)
D.1 SPLITTING STRATEGY
When splitting the calibration set Dcal for fitting the predictive model and deriving EPICSCORE’s adaptive cutoffs in
disjunct data subsets, we prioritize allocating the majority of data to model training, as cutoff derivation primarily involves
a simpler quantile computation.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 21

For larger datasets, this allocation is capped at 1000 samples to maintain computational efficiency.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 21

Table 10: Regression Mean Average Coverage values across different methods and datasets.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 22

Dataset EPIC-BART EPIC-GP EPIC-MDN Mondrian Reg-split Weighted
airfoil 0.897 (0.01) 0.9 (0.008) 0.897 (0.009) 0.906 (0.006) 0.897 (0.007) 0.9 (0.007)
bike 0.901 (0.003) 0.903 (0.003) 0.898 (0.003) 0.904 (0.002) 0.899 (0.002) 0.9 (0.002)
concrete 0.897 (0.009) 0.902 (0.011) 0.907 (0.009) 0.929 (0.006) 0.901 (0.008) 0.896 (0.008)
cycle 0.898 (0.004) 0.9 (0.004) 0.896 (0.004) 0.905 (0.003) 0.898 (0.003) 0.9 (0.002)
electric 0.899 (0.003) 0.9 (0.003) 0.896 (0.003) 0.905 (0.002) 0.899 (0.003) 0.901 (0.003)
homes 0.9 (0.003) 0.899 (0.003) 0.9 (0.004) 0.902 (0.002) 0.901 (0.002) 0.9 (0.002)
meps19 0.899 (0.003) 0.9 (0.003) 0.897 (0.003) 0.902 (0.006) 0.9 (0.002) 0.9 (0.002)
protein 0.9 (0.003) 0.901 (0.003) 0.899 (0.002) 0.9 (0.001) 0.9 (0.001) 0.899 (0.001)
star 0.903 (0.005) 0.9 (0.006) 0.906 (0.006) 0.913 (0.005) 0.903 (0.004) 0.9 (0.004)
superconductivity 0.901 (0.003) 0.901 (0.003) 0.9 (0.004) 0.901 (0.002) 0.899 (0.002) 0.899 (0.002)
WEC 0.901 (0.002) 0.898 (0.003) 0.899 (0.003) 0.9 (0.001) 0.899 (0.001) 0.9 (0.001)
winered 0.898 (0.009) 0.9 (0.008) 0.895 (0.008) 0.91 (0.005) 0.903 (0.006) 0.895 (0.005)
winewhite 0.902 (0.004) 0.904 (0.004) 0.901 (0.004) 0.911 (0.003) 0.9 (0.004) 0.899 (0.003)
Table 11: Regression Interval length values across different methods and datasets.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 22

In general, our framework produces narrower intervals in most datasets.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 22

Dataset EPIC-BART EPIC-GP EPIC-MDN Mondrian Reg-split Weighted
airfoil 15.099 (0.592) 15.223 (0.591) 15.089 (0.56) 16.671 (0.632) 15.325 (0.469) 15.693 (0.521)
bike ×(101) 24.910 (0.302) 26.616 (0.333) 25.665 (0.338) 27.263 (0.264) 27.634 (0.271) 25.865 (0.249)
concrete 39.025 (1.49) 39.44 (1.575) 40.475 (1.551) 51.284 (1.904) 39.943 (1.204) 43.053 (1.629)
cycle 14.911 (0.183) 14.851 (0.199) 14.712 (0.174) 15.015 (0.164) 14.855 (0.159) 14.833 (0.15)
electric 0.036 (<0.001) 0.037 (<0.001) 0.036 (<0.001) 0.038 (<0.001) 0.037 (<0.001) 0.037 (<0.001)
homes×(105) 3.848 (0.043) 3.758 (0.049) 4.040 (0.059) 4.235 (0.037) 4.014 (0.033) 3.984 (0.032)
meps19 25.013 (0.87) 26.605 (0.774) 32.093 (1.446) 38.904 (1.039) 28.899 (0.544) 29.555 (0.843)
protein 14.572 (0.106) 14.311 (0.12) 13.573 (0.103) 14.102 (0.038) 15.261 (0.037) 13.692 (0.037)
star ×(101) 85.3 (1.015) 85.148 (1.326) 86.499 (1.288) 90.539 (0.762) 85.230 (0.792) 104.202 (1.306)
superconductivity 39.13 (0.419) 39.283 (0.479) 39.547 (0.5) 42.204 (0.216) 46.14 (0.242) 40.115 (0.228)
WEC ×(105) 0.893 (0.011) 0.858(0.011) 0.900 (0.012) 0.903 (0.004) 0.925 (0.006) 0.879 (0.006)
winered 2.361 (0.065) 2.37 (0.067) 2.316 (0.054) 2.576 (0.04) 2.39 (0.037) 2.541 (0.051)
winewhite 2.337 (0.032) 2.4 (0.032) 2.356 (0.031) 2.445 (0.013) 2.361 (0.014) 2.387 (0.015)
prior over the network weights—one that does not favor any specific parameter configuration and assumes equal uncertainty
over weights.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 22

Batch size selection is dataset-dependent: 40 for small datasets (n < 10000), 125 for medium datasets ( n < 50000),
and 250 for large-scaled datasets, such as WEC.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 22

For the image experiment, we introduce an additional hidden layer with
32 neurons and maintain a dropout rate of 0.5, while adjusting the batch size to 135.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 22

To approximate the posterior, we employ a Natural Variational Distribution
[Salimbeni et al., 2018], using 15 inducing points for small datasets (n <10000) and 50 for medium and large-scale data.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 22

Table 12: Regression Pearson correlation values across different methods and datasets.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 23

Dataset EPIC-BART EPIC-GP EPIC-MDN Mondrian Weighted
airfoil 0.056 (0.013) 0.125 (0.018) 0.054 (0.012) 0.148 (0.017) 0.124 (0.016)
bike 0.164 (0.009) 0.172 (0.006) 0.054 (0.007) 0.028 (0.005) 0.043 (0.007)
concrete 0.064 (0.015) 0.116 (0.019) 0.054 (0.011) 0.191 (0.02) 0.211 (0.022)
cycle 0.022 (0.005) 0.075 (0.008) 0.023 (0.005) 0.043 (0.006) 0.025 (0.005)
electric 0.052 (0.007) 0.128 (0.009) 0.024 (0.005) 0.047 (0.007) 0.029 (0.006)
homes 0.135 (0.007) 0.19 (0.011) 0.019 (0.005) 0.016 (0.003) 0.038 (0.005)
meps19 0.17 (0.012) 0.183 (0.015) 0.034 (0.008) 0.022 (0.006) 0.053 (0.016)
protein 0.063 (0.003) 0.071 (0.005) 0.062 (0.003) 0.013 (0.003) 0.043 (0.005)
star 0.076 (0.012) 0.037 (0.01) 0.073 (0.01) 0.156 (0.012) 0.335 (0.016)
superconductivity 0.072 (0.006) 0.254 (0.005) 0.016 (0.004) 0.019 (0.004) 0.025 (0.006)
WEC 0.012 (0.002) 0.115 (0.004) 0.21 (0.007) 0.009 (0.002) 0.059 (0.007)
winered 0.05 (0.01) 0.119 (0.016) 0.042 (0.009) 0.153 (0.018) 0.221 (0.019)
winewhite 0.035 (0.007) 0.079 (0.011) 0.025 (0.005) 0.055 (0.009) 0.092 (0.011)
Training is performed by minimizing the negative variational ELBO, where the Natural Gradient Descent [Salimbeni et al.,
2018] updates the variational parameters, while the Adam optimizer [Kingma, 2014] refines the GP kernel and noise variance
hyperparameters.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 23

Following the
MDN predictive model, we reserve 30% of the training data exclusively for validation and adopt an adaptive batch size
of 40 for small datasets (n <10000), 125 for medium-sized datasets (n <50000), and 250 for large datasets.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 23

D.5 IMPACT OF PRIOR CHOICES
In this section, we illustrate the impact of prior choices in EPICSCORE through a simulated experiment comparing the
prediction intervals produced by EPICSCORE-BART under two prior configurations: diffuse and concentrated.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 23

Table 13: Average outlier-to-inlier interval length ratio across methods and datasets in the regression setting.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 24

Overall,EPICSCORE consistently yields higher
ratios across diverse datasets.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 24

Dataset EPIC-BART EPIC-GP EPIC-MDN Mondrian Weighted
airfoil 1.021 (0.039) 1.004 (0.014) 1.03 (0.035) 0.988 (0.023) 1.03 (0.045)
bike 0.971 (0.014) 0.98 (0.006) 0.963 (0.02) 1.029 (0.018) 0.976 (0.016)
concrete 1.05 (0.036) 1.03 (0.018) 1.11 (0.035) 0.99 (0.036) 1.137 (0.067)
cycle 0.967 (0.007) 0.992 (0.002) 0.973 (0.008) 1.005 (0.006) 0.988 (0.005)
electric 0.987 (0.008) 1.0 (0.003) 0.992 (0.01) 0.996 (0.005) 0.992 (0.008)
homes 1.124 (0.019) 1.138 (0.015) 1.268 (0.035) 1.234 (0.026) 1.203 (0.035)
meps19 1.047 (0.027) 1.057 (0.041) 1.097 (0.065) 1.099 (0.05) 1.074 (0.058)
protein 0.999 (0.002) 0.996 (0.003) 1.008 (0.004) 1.003 (0.004) 1.0 (0.005)
star 1.0 (0.007) 1.0 (0.001) 1.005 (0.007) 1.016 (0.011) 0.984 (0.025)
superconductivity 1.129 (0.014) 1.061 (0.009) 1.107 (0.016) 1.211 (0.014) 1.111 (0.017)
WEC 1.077 (0.007) 1.034 (0.005) 1.122 (0.015) 1.2 (0.014) 1.041 (0.007)
winered 1.055 (0.019) 1.031 (0.009) 1.143 (0.027) 1.052 (0.02) 1.095 (0.045)
winewhite 1.01 (0.007) 1.001 (0.001) 1.039 (0.012) 1.058 (0.013) 0.997 (0.011)
results in low aleatoric and epistemic uncertainty over the densely sampled interval [−1, 0] and high uncertainty—both
epistemic and aleatoric—over the sparse interval [0, 1].

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 24

The dataset is divided into training, calibration, and test sets, each containing 200 samples.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 24

Table 14: Average coverage on outliers across methods and datasets in the regression setting.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 25

EPICSCORE consistently delivers near-nominal coverage across most datasets.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 25

Dataset EPIC-BART EPIC-GP EPIC-MDN Mondrian Reg-split Weighted
airfoil 0.896 (0.027) 0.883 (0.028) 0.894 (0.027) 0.91 (0.025) 0.902 (0.023) 0.903 (0.021)
bike 0.895 (0.01) 0.901 (0.011) 0.897 (0.01) 0.909 (0.009) 0.903 (0.01) 0.895 (0.009)
concrete 0.895 (0.029) 0.902 (0.027) 0.893 (0.028) 0.904 (0.023) 0.873 (0.033) 0.876 (0.029)
cycle 0.89 (0.009) 0.901 (0.01) 0.892 (0.008) 0.914 (0.008) 0.901 (0.009) 0.898 (0.009)
electric 0.9 (0.008) 0.898 (0.01) 0.902 (0.008) 0.909 (0.008) 0.906 (0.009) 0.911 (0.009)
homes 0.869 (0.008) 0.873 (0.008) 0.896 (0.006) 0.894 (0.007) 0.847 (0.008) 0.878 (0.008)
meps19 0.899 (0.007) 0.9 (0.007) 0.899 (0.008) 0.901 (0.012) 0.894 (0.008) 0.898 (0.007)
protein 0.89 (0.005) 0.892 (0.005) 0.89 (0.005) 0.898 (0.004) 0.895 (0.004) 0.892 (0.004)
star 0.892 (0.019) 0.899 (0.019) 0.906 (0.018) 0.899 (0.015) 0.885 (0.02) 0.879 (0.018)
superconductivity 0.891 (0.007) 0.872 (0.008) 0.887 (0.008) 0.918 (0.005) 0.884 (0.007) 0.888 (0.006)
WEC 0.861 (0.006) 0.85 (0.007) 0.871 (0.006) 0.897 (0.005) 0.85 (0.006) 0.852 (0.006)
winered 0.87 (0.028) 0.841 (0.029) 0.881 (0.027) 0.858 (0.024) 0.843 (0.031) 0.846 (0.029)
winewhite 0.872 (0.015) 0.876 (0.014) 0.878 (0.016) 0.9 (0.011) 0.863 (0.015) 0.867 (0.016)
yields wider intervals—particularly in data-sparse regions—capturing heightened epistemic uncertainty.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 25

Figure 8: Variation of the Average Interval Score Loss(AISL) as a function of the β hyperparameter in the BART model
used within the EPICSCORE framework.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 25

To quantify this cost within our framework, we evaluate the run-
time of EPICSCORE across increasing sample sizes using the three Bayesian predictive models discussed previously:
MDN, BART, and Variational GP.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 26

BART, on the other hand, maintains low computational cost for small datasets but exhibits a
sharp increase in runtime as the sample size grows.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 26

This experiment was conducted using an AMD Ryzen 7 6000 series CPU.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 26

For the largest dataset, which includes over
100000 calibration observations, the runtime for each method remained small: BART completed in under 16 minutes,
MDN in under 2 minutes, and GP in under 4 minutes.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 26

D.7 APPLICATION TO DENSITY-BASED CONFORMITY SCORES
In this section, we use a simulated experiment to illustrate howEPICSCORE can enhance density-based conformal prediction
methods by explicitly incorporating epistemic uncertainty.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 27

Following the same simulation setup described in Section D.5, we
compare our approach to a standard method for conformal prediction with a density-based score, namely HPD-split [Izbicki
et al., 2022].

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 27

The experiment is designed to reflect regions with both high epistemic and aleatoric uncertainty, allowing us to
highlight the advantages of our method in capturing complex uncertainty structures.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 27

Compared to the HPD-based region, our method exhibits significantly better adaptiveness and uncertainty quantification,
particularly in data-sparse regions of the input space.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 27

## Reported findings

(2022) achieved an average relative prediction
error (∥ˆy − y∥2/∥y∥2) that is no lower than 0.23.

Source: Conformal Prediction with Missing Values; PDF page(s): 9

We provide results on additional deep neural
networks in the Appendix due to space constraints noting
that we find similar patterns.

Source: Probabilistically robust conformal prediction; PDF page(s): 6

This generalization is achieved by introducing a constant
inflation condition that adjusts the CP quantile to adver-
sarial perturbations.

Source: Probabilistically robust conformal prediction; PDF page(s): 8

Empirical results show EPICSCORE often
outperforms alternatives, producing prediction regions that
better reflect uncertainty while maintaining valid coverage.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 9

Method SSC 2 * SE
EPICSCORE-MDN 0.734 0.014
APS 0.553 0.036
These results show that EPICSCORE-MDN achieves an SSC much closer to the nominal level of 0.8 than APS, indicating
more consistent coverage across different set sizes.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 15

## User observations

No user experimental observations were supplied. Add real data before drafting user results.

## Limitations and future directions

The drawback of this “impute-then-predict” approach is
that single imputation can distort the joint and marginal
distribution of the data.

Source: Conformal Prediction with Missing Values; PDF page(s): 1

5 This limitation brings us to the second
algorithm we propose, CP-MDA-Nested.

Source: Conformal Prediction with Missing Values; PDF page(s): 6

6 SUMMARY AND FUTURE WORK
This paper studied the novel problem of probabilistic ro-
bustness for conformal prediction (PRCP) based uncertainty
quantification of deep classifiers.

Source: Probabilistically robust conformal prediction; PDF page(s): 8

Future work should study and analyze end-to-end PRCP
algorithms.

Source: Probabilistically robust conformal prediction; PDF page(s): 9

Although recent conformal scores have
been developed to address this limitation, they are
typically designed for specific tasks, such as regres-
sion or quantile regression.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 1

How-
ever, an equally important source of uncertainty isepistemic
uncertainty, which stems from limitations in training data
and the resulting lack of knowledge about the true data-
generating process [Hüllermeier and Waegeman, 2021].

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 1

illustrates this issue in a regression problem (see Appendix
A.1 for technical details): in the range x ∈ (7, 8), there
is essentially no training data, so we expect predictive re-
gions to widen, reflecting the increased uncertainty.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 2

To address this limitation, we propose a novel ap-
proach that augments any conformal score with a measure
of epistemic uncertainty.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 2

This limitation also appears in classification tasks, where
conventional conformal methods produce overconfident pre-
diction sets for test instances outside the training distribution.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 2

Although potentially
stronger than necessary, relaxing it would require a more
technical analysis, which we leave for future work.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 7

Looking ahead, we plan to extend EPICSCORE to settings
involving distribution shift, where accounting for epistemic
uncertainty is important due to increased data sparsity in cer-
tain regions.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 9

This limitation arises because these
regions have low spread estimates due to insufficient data, leading to underestimated cutoffs.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 14

In general, we expect outliers to have wider prediction sets, as they are located in sparser regions of the feature space.

Source: Epistemic Uncertainty in Conformal Scores: A Unified Approach; PDF page(s): 16
