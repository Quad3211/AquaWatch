# Evaluating Time-Series Anomaly Detection for Water Leak/Burst Detection (AquaWatch Jamaica)

Scope: a concrete evaluation protocol for a prototype that currently reports point-wise precision/recall per hourly reading on one chronological split (10 days train / 4 days test), comparing Isolation Forest (flow + pressure) with a flow-only threshold rule.

Note on sourcing: sources marked "(fetched)" were read in this session. Sources marked "(not fetched; standard reference)" are well-known papers/docs cited from prior knowledge, with stable URLs; the report writer should spot-check them before quoting specific numbers. Some BattLeDIM primary documents (journal PDF, rules PDF) blocked automated reading (HTTP 403 / compressed PDF), so the exact cost constants are listed as gaps.

## 1. Event-level vs point-wise metrics: which suit leak detection?

### Takeaway
Point-wise F1 per hourly reading is the wrong unit for leaks, because a leak is a contiguous event and what matters is whether and how fast it is caught. Point-adjust (PA) F1, the usual fix in ML papers, is badly inflated: random scores reach about 0.9 F1. AquaWatch should report event-level recall and precision (one leak = one event, front-biased), a false-alarm rate per unit time, and, as a threshold-free secondary metric, VUS-PR or affiliation F1. It should never report PA-F1 alone.

### Cited Findings
- **Point adjustment (PA)**: if any single point inside a ground-truth anomaly segment is flagged, the entire segment is counted as detected. F1_PA is F1 on these adjusted labels. — [Kim et al., AAAI 2022 (ar5iv, fetched)](https://ar5iv.arxiv.org/html/2109.05257)
- With PA, **uniform random anomaly scores** U(0,1) score F1_PA of 0.969 (SWaT), 0.965 (WADI), 0.931 (MSL), 0.961 (SMAP) and 0.804 (SMD). Plain F1 for the same random scores is only 0.216, 0.109, 0.190, 0.227 and 0.080. — [Kim et al. 2022 (fetched)](https://ar5iv.arxiv.org/html/2109.05257)
- Kim et al. also show that an **untrained** LSTM encoder-decoder, and even "input norm as score" (‖w_t‖₂), match published SOTA methods without PA. For example, the untrained model gets F1 = 0.789 on SWaT. — [Kim et al. 2022 (fetched)](https://ar5iv.arxiv.org/html/2109.05257); [AAAI version](https://ojs.aaai.org/index.php/AAAI/article/view/20680)
- **PA%K**: apply PA to segment S_m only if the fraction of S_m's points with score > δ exceeds K%. K = 0 gives F1_PA and K = 100 gives plain F1. To remove the dependence on K, report the **area under F1_PA%K over K ∈ [0,100]**. — [Kim et al. 2022 (fetched)](https://ar5iv.arxiv.org/html/2109.05257)
- **Kim et al.'s recommended protocol**:
  1. Report plain F1 without PA.
  2. Compare against untrained/trivial baselines and report the relative improvement.
  3. Report F1_PA%K or its AUC.
  4. Consider threshold-independent AUROC/AUPR, because "existing methods often pick thresholds using the test set".

  — [Kim et al. 2022 (fetched)](https://ar5iv.arxiv.org/html/2109.05257)
- **Range-based precision/recall (Tatbul et al., NeurIPS 2018)**:
  - Recall_T(R,P) = (1/N_r) Σ_i [ α·ExistenceReward(R_i,P) + (1−α)·OverlapReward(R_i,P) ].
  - ExistenceReward = 1 if R_i overlaps any predicted range, else 0.
  - OverlapReward = CardinalityFactor · Σ_j ω(R_i, R_i∩P_j, δ).
  - Precision_T(R,P) = (1/N_p) Σ_i CardinalityFactor · Σ_j ω(P_i, P_i∩R_j, δ). Precision has no existence term.
  - CardinalityFactor = 1 if the range overlaps at most one range on the other side, else γ = typically 1/x, where x is the number of overlapping ranges.
  - ω is the δ-weighted fraction of the range covered.
  - Positional bias δ:
    - flat: δ = 1
    - **front: δ = L − i + 1 (rewards catching the start, i.e. early detection)**
    - back: δ = i
    - middle

  — [Tatbul et al. 2018 (ar5iv, fetched)](https://ar5iv.labs.arxiv.org/html/1803.03639); [NeurIPS proceedings](https://proceedings.neurips.cc/paper/2018/hash/8f468c873a32bb0619eaeb2050ba45d1-Abstract.html)
- Tatbul et al. motivate the range metrics by noting that point-based P/R misrepresent detectors on range anomalies, since one predicted range can be partly TP and partly FP. They say NAB's scoring follows the same early-detection idea. — [Tatbul et al. 2018 (fetched)](https://ar5iv.labs.arxiv.org/html/1803.03639)
- **Affiliation metrics (Huet, Navarro & Rossi, KDD 2022)**: a parameter-free extension of precision/recall that evaluates each ground-truth event locally, by the distance from predictions to events. The authors show that existing range-based metrics **can be gamed by adversarial predictions** and compare against random-baseline predictions. The Python package `affiliation-metrics-py` provides Affi_Precision, Affi_Recall and Affi_F1. — [arXiv 2206.13167](https://arxiv.org/abs/2206.13167); [paper PDF](https://nonsns.github.io/paper/rossi22kdd.pdf); [code](https://github.com/ahstat/affiliation-metrics-py)
- **VUS-ROC / VUS-PR (Paparrizos et al., PVLDB 2022)**: range-AUC curves "buffer" each labelled anomaly by a margin ℓ. VUS is the volume under the surface of the PR (or ROC) curve over thresholds × buffer lengths ℓ ∈ [0, L]. It is **independent of threshold and of buffer length**. If the right buffer length is known, range-AUC is preferred; if it is uncertain, VUS is more robust. Computing it costs O(N·L). — [TSB-UAD docs on VUS](https://tsb-uad.readthedocs.io/en/latest/evaluation/VUS.html); [PVLDB paper](https://www.vldb.org/pvldb/vol15/p2774-paparrizos.pdf)
- The extended VUS journal version reports that **the choice of evaluation measure can significantly bias experimental outcomes**. — [arXiv 2502.13318](https://arxiv.org/abs/2502.13318)
- Implementations: the reference repo [TheDatumOrg/VUS](https://github-redirect.dependabot.com/TheDatumOrg/VUS) (also evaluated on TSB-UAD), and `aeon.benchmarking.metrics.anomaly_detection.range_pr_vus_score` (default max buffer 500; defaults differ from the reference repo, so do not compare numbers across tools). — [aeon docs](https://www.aeon-toolkit.org/en/stable/api_reference/auto_generated/aeon.benchmarking.metrics.anomaly_detection.range_pr_vus_score.html)
- **NAB (Numenta Anomaly Benchmark)** formalises rewards for real-time detectors with a scoring algorithm for streaming data. The ideal detector catches anomalies as early as possible with no false alarms. (I could not fetch the window and sigmoid details in this session.) — [Lavin & Ahmad 2015, arXiv 1510.03336 (abstract fetched)](https://arxiv.org/abs/1510.03336)

### Inferences
- **Recommended headline metrics for AquaWatch** (event = one labelled leak/burst interval):
  1. **Event recall** = detected leaks / total leaks. A leak is "detected" if ≥1 alarm falls in [leak_start, leak_start + T_max]. This equals Tatbul recall with α = 1, using the existence reward only.
  2. **Alarm precision** = alarms matched to a real leak / total alarms. Collapse consecutive flagged hours into one alarm episode, and count repeat alarms on an already-detected leak as neither TP nor FP (see BattLeDIM below).
  3. **False alarms per DMA per week**.
  4. **Detection delay** (see §2).

  Secondary metrics:
  - Tatbul range P/R with front bias and α ≈ 0.5.
  - Affiliation F1.
  - VUS-PR, a threshold-free ranking metric useful for comparing Isolation Forest scores with the rule's margin scores.
  - Plain point-wise F1, kept only for continuity.
  - If PA is shown at all, show it only next to PA%K AUC, plus a **random-score baseline** row, so readers see how much inflation the metric allows.
- Front-biased metrics suit leaks because water loss accumulates with time. Late detection is worth less, which NAB and BattLeDIM also encode.
- Python options:
  - `affiliation-metrics-py`
  - the `VUS` package (`pip install vus`, from TheDatumOrg)
  - `aeon` for range P/R and VUS
  - TSB-UAD for benchmarking
  - the `prts` package (Tatbul range P/R)

  The `prts` package is from my own knowledge and not verified this session; check its maintenance status.

### Gaps
- Exact NAB window sizing and scaled-sigmoid formula were not fetched. The full paper is at arxiv.org/pdf/1510.03336. Some critiques of NAB (e.g. Singh & Olinsky 2017; Wu & Keogh 2021) exist, but I did not verify them here.
- I found no leak-specific study comparing VUS and affiliation metrics; their suitability for leaks is my inference.

## 2. Leak-specific metrics (latency, leak size, false alarms, BattLeDIM, localisation)

### Takeaway
Water-sector evaluation centres on how big a leak is caught (sensitivity, or minimum detectable leak), how fast (detection time), how often the system is wrong (false alarms), and, if localising, how far the alarm is from the true location. BattLeDIM folds these into an economic score that rewards water saved by early, correctly located detection and penalises false alarms. Random daily alarms score negative under the official rules.

### Cited Findings
- **BattLeDIM 2020 (L-Town)** scoring principles:
  - The utility "calculates a reward (or cost)" per submitted detection.
  - A detection is correct only if it falls within a time window after leak start (example Tmax: within a week) and within a pipe-length radius of the leak (e.g. Xmax = 300 m).
  - Earlier and closer detections score higher.
  - Detections **before leak start or after the maximum delay get no reward**.
  - **False detections are penalised**, because they cost the utility lost person-hours.

  — [BattLeDIM site / Zenodo summary via search](https://battledim.ucy.ac.cy/?p=270); [Vrachimis et al. 2022, JWRPM (TU Delft record)](https://research.tudelft.nl/en/publications/battle-of-the-leakage-detection-and-isolation-methods/)
- Official BattLeDIM scorer details, from a GitHub issue that compared the EPyT-Flow Python scorer against the organisers' MATLAB `Scoring_Algorithm.m` / `scoring_function.m`:
  - An alarm counts as TP only if a leak is **active** at alarm time and the pipe distance is ≤ 300 m (`abs(x) <= xmax`).
  - Alarms are processed in **time order**.
  - An alarm whose matched leaks were **all already detected is a repeat: neither TP nor FP, and it scores 0**.
  - **Water saved = sum(leak.timeSeries(td:end))/12**: the leak flow (m³/h at 5-min resolution) is summed from detection time td to the leak's end and converted to m³.
  - Distance adds half the lengths of both the leak pipe and the detected pipe, and never routes through pumps or PRVs.

  — [EPyT-Flow issue #34 (fetched)](https://github.com/WaterFutures/EPyT-Flow/issues/34); [fix PR #35](https://github.com/WaterFutures/EPyT-Flow/pull/35); [KIOS-Research/BattLeDIM repo (fetched)](https://github.com/KIOS-Research/BattLeDIM)
- Reference values under the official rules (2018 data, 20 seeds), useful as sanity baselines:

  | Alarm set | TP | Economic score |
  |---|---|---|
  | Perfect | 14 | about €179k |
  | Random alarms, 1/week | about 4.5 | about €33k |
  | Random alarms, 1/day | about 10.1 | about **−€34k** |

  — [EPyT-Flow issue #34 (fetched)](https://github.com/WaterFutures/EPyT-Flow/issues/34)
- BattLeDIM results:
  - The published leaderboard lists a perfect score of €523,154.
  - The 1st-place team (Tongji) scored €264,873 with 56.52% TPR and 3 FP. Another listing shows "Under Pressure" at 65.22% TPR, 4 FP, €260,562.
  - The leaderboard was revised to include IRI in 3rd place (€210,772).

  — [BattLeDIM results page (fetched)](https://battledim.ucy.ac.cy/?p=270); [Zenodo/TU Delft via search](https://research.tudelft.nl/en/publications/battle-of-the-leakage-detection-and-isolation-methods/)
- An entrant paper notes the economic score can favour a model with *lower* TPR. The highest-TPR model scored 326,521 but had **138 false positives**, showing the TPR/false-alarm trade-off is real. — [Liquor-HGNN, LWDA 2023](https://ceur-ws.org/Vol-3630/LWDA2023-paper40.pdf)
- The BattLeDIM paper has sections on "Alternative evaluation criteria" and "Evaluation parameter sensitivity analysis", which shows the organisers tested how rankings change with Tmax/Xmax. — [Vrachimis et al. 2022 PDF (headings only readable)](https://zenodo.org/record/6641304/files/battledim2020.pdf)
- Generic leak-detection-system evaluation criteria:
  - **Sensitivity** (smallest leak detected and the time taken; detection time shrinks as leak size grows)
  - **Reliability** (false alarms versus real leaks)
  - **Response time** (time from leak to alarm)
  - leak size estimation, leak location and robustness

  Filtering reduces false alarms but delays detection. — [Pipeline LDS & data fusion survey, arXiv 1902.03927](https://arxiv.org/pdf/1902.03927); [PHMSA leak detection report 2003](https://www.phmsa.dot.gov/sites/phmsa.dot.gov/files/docs/technical-resources/pipeline/hazardous-liquid-integrity-management/64381/leakdetectionreportfinalapr03.pdf)
- Most WDN leak-detection techniques monitor DMA inlet flows. False-alarm reduction is treated as a primary design goal, for example through a validation step. — [Boracchi et al. 2021, WDN monitoring (search snippet)](https://boracchi.faculty.polimi.it/docs/2021_WDN_Monitoring_NCA.pdf)
- A review benchmarking leak detection and localisation methods on BattLeDIM 2020 (Romero-Ben et al.) is a good WDN-specific reference. — [IRI-UPC document](https://www.iri.upc.edu/download/scidoc/2726)

### Inferences
- **Concrete leak metrics for AquaWatch**:
  - **Time to detection** TTD = t_first_alarm − t_leak_start, in hours. Report the median and IQR over detected leaks, plus a count of missed leaks.
  - **Detected-volume metric**: water lost before detection, Σ_{t_start}^{t_detect} q_leak(t), in m³. Its complement, BattLeDIM-style "volume saved", is Σ_{t_detect}^{t_end} q_leak(t).
  - **Sensitivity curve**: inject synthetic leaks of increasing size (e.g. 1%, 2%, 5% and 10% of mean DMA flow, or fixed L/s values) at random times, including night and day. Plot detection probability and TTD against leak size. The **minimum detectable leak** is the smallest size detected in ≥90% of injections within T_max.
  - **False alarms per DMA per week (or month)**, reported on leak-free periods.
  - A simplified economic score:

    Σ_TP (C_water·V_saved − C_crew) − Σ_FP C_crew

    Use local NWC tariff and crew-cost assumptions, stated explicitly.
- Localisation error (pipe distance in m) applies only if AquaWatch localises below DMA level. With 1 flow and 1 pressure sensor, report detection only, and say so.
- With a tiny dataset, **synthetic leak injection** (or using L-Town/BattLeDIM data) is the only way to obtain enough events. Report results on real labels and synthetic injections separately.

### Gaps
- The official BattLeDIM constants (water price €/m³, crew cost per alarm, exact Tmax in hours, and the exact form of the time and distance decay) were not readable. The journal PDF returned 403, and the PDFs could not be parsed. They are in `KIOS-Research/BattLeDIM/Scoring Algorithm/*.m`.
- I found no authoritative industry benchmark for an "acceptable false alarms per DMA per month". A utility engineer should set it.
- The DMA minimum-detectable-leak article (thewaternetwork.com) returned 404.

## 3. Validation design (walk-forward CV, leakage, history length, threshold selection, unsupervised setting)

### Takeaway
Replace the single 10/4-day split with **expanding-window walk-forward evaluation**. In every fold, choose features, the contamination value and the alarm threshold using only past data, with an inner validation block for the threshold. Training "normal" data must be defined without test-period labels, using robust statistics on past data. Fourteen days cannot capture weekly or seasonal patterns. Several weeks of data at minimum, ideally covering wet and dry seasons, is needed before accuracy claims mean anything.

### Cited Findings
- Kim et al. explicitly criticise the common practice of **picking thresholds using the test set** and recommend threshold-independent metrics or proper threshold protocols. — [Kim et al. 2022 (fetched)](https://ar5iv.arxiv.org/html/2109.05257)
- scikit-learn `TimeSeriesSplit` gives expanding-window splits in which each training set precedes its test set. Its `gap` parameter excludes samples between train and test, and `max_train_size` gives a rolling window. — [scikit-learn TimeSeriesSplit docs (not fetched; standard reference)](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
- Isolation Forest's `contamination` parameter sets the score threshold from the expected outlier fraction in the training set. Tuning it to the test set is test-set threshold selection. — [scikit-learn IsolationForest docs (not fetched; standard reference)](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)
- Many public TSAD benchmarks are flawed: they contain trivially solvable anomalies, unrealistic anomaly density, mislabelled ground truth, and run-to-failure bias. This argues for checking that a simple "one-liner" baseline does not already solve the data. — [Wu & Keogh 2021, arXiv 2009.13807 (not fetched; standard reference)](https://arxiv.org/abs/2009.13807)

### Inferences
- **Proposed protocol**:
  1. Order the data by time.
  2. For each fold k: train on [t0, t_k), use [t_k, t_k + v) as validation to set the threshold for a **target false-alarm rate** (e.g. ≤1 alarm per DMA per week), skip a gap of ≥24 h, and test on [t_k + v + gap, t_k + v + gap + h).
  3. Roll forward and aggregate event metrics over all test windows.
  4. Use weekly folds where data allows.
- **Leakage checks**:
  - Fit scalers and rolling statistics only on training data. Rolling or lag features must be causal (no centred windows).
  - Do not drop "anomalous" training rows using ground-truth labels. Instead, either keep all rows (Isolation Forest tolerates some contamination), or filter with a label-free robust rule: drop rows with |x − median| / (1.4826·MAD) > 3–3.5 within the same hour-of-week.
  - Fix the contamination value a priori or choose it on the validation block, and report sensitivity to it.
- **History length**: urban demand has daily and weekly cycles, so each hour-of-week bin needs at least 3–4 training weeks for stable statistics. Annual and seasonal effects (Jamaican wet and dry seasons, holidays) need ≥1 year before claiming seasonal robustness. Until then, state that the results only cover the observed season. This is a domain-logic inference; I found no single authoritative number.
- **Unsupervised operation**: treat the trailing N weeks as "mostly normal" and score new data against an hour-of-week robust baseline (median/MAD), refitting periodically. Monitor drift, such as the MNF trend.
- **Hyperparameter search**, if any, must happen inside each fold (nested). Report the number of configurations tried.

### Gaps
- I found no peer-reviewed source giving a minimum history length for DMA leak detectors. BattLeDIM provided a full year (2018) for calibration and a year (2019) for evaluation, but I did not verify this from the primary document this session.

## 4. Fair baselines and ablations

### Takeaway
Comparing Isolation Forest on flow + pressure with a rule that only sees flow mixes the model effect with the feature effect. Every detector should be compared with simple, strong, domain-standard baselines that use the **same inputs**, and with trivial baselines (random, untrained, input-magnitude). Ablations should separate the contribution of features from that of the model.

### Cited Findings
- An untrained model, or "input magnitude as score", already matched published deep TSAD methods. Kim et al. therefore recommend always reporting relative improvement over such baselines. — [Kim et al. 2022 (fetched)](https://ar5iv.arxiv.org/html/2109.05257)
- Affiliation metrics are explicitly benchmarked against **random predictions** to show what chance level looks like for a given metric and dataset. — [Huet et al. 2022](https://arxiv.org/abs/2206.13167)
- Under BattLeDIM's official scoring, random alarms at 1 per week still earn about €33k and about 4.5 TP. A detector must clearly beat this chance level. — [EPyT-Flow issue #34](https://github.com/WaterFutures/EPyT-Flow/issues/34)
- Most WDN methods monitor DMA inlet flows. Night-flow-based methods are the established practice. — [Boracchi et al. 2021 snippet](https://boracchi.faculty.polimi.it/docs/2021_WDN_Monitoring_NCA.pdf); [pipeline LDS survey](https://arxiv.org/pdf/1902.03927)

### Inferences
- **Baseline ladder that every model should beat** (each run through the same walk-forward protocol and threshold rule):
  1. Random alarms at a matched alarm rate, which sets chance level.
  2. Static flow threshold.
  3. **Minimum Night Flow (MNF)** rule: daily MNF (e.g. 02:00–04:00) above a rolling median + k·MAD of the prior 14–28 nights.
  4. **Seasonal-naive residual**: r_t = q_t − q_{t−168h} (or the median of the same hour-of-week over the past 4 weeks), alarming on |r_t| / MAD > k.
  5. **CUSUM** on standardised residuals: S_t = max(0, S_{t−1} + z_t − κ), alarm when S_t > h. This is good for slow leaks.
  6. **Flow + pressure rule**: alarm when the flow residual is high AND the pressure residual is low. This makes the rule–IF comparison fair.
  7. Isolation Forest on flow only.
  8. Isolation Forest on flow + pressure.
- **Ablations**: IF with and without pressure, with and without hour-of-week features, with and without label-based training filtering, and across contamination ∈ {0.005, 0.01, 0.02, 0.05}. Report each as event recall, false alarms per week and median TTD.
- Python options: `statsmodels` (seasonal decomposition, STL), `ruptures` (change points), `river` (streaming detectors), `pyod` (IF and other detectors), and a hand-rolled CUSUM (about 10 lines). These are from my own knowledge and were not fetched.

### Gaps
- I did not retrieve a peer-reviewed head-to-head showing MNF or CUSUM performance on DMA data. The baseline choices are domain-standard inference.

## 5. Uncertainty and significance with few events

### Takeaway
With a handful of leak events, any recall figure has very wide uncertainty: 3 of 4 detected gives a 95% CI of roughly 19% to 99%. Report counts (k/n) with exact binomial (Clopper-Pearson) or Wilson intervals for event recall. Use a **block bootstrap over time** (resampling days or weeks, never individual hours) for precision, false-alarm rate and score differences. Use paired comparisons on the same events to compare models.

### Cited Findings
- Kim et al. average over 5 random seeds for stochastic baselines, which shows that variance across seeds must be reported. — [Kim et al. 2022 (fetched)](https://ar5iv.arxiv.org/html/2109.05257)
- BattLeDIM reference results were averaged over 20 random seeds for random-alarm baselines. — [EPyT-Flow issue #34](https://github.com/WaterFutures/EPyT-Flow/issues/34)
- `scipy.stats.bootstrap` provides percentile/BCa bootstrap CIs, and `scipy.stats.binomtest(...).proportion_ci(method='exact'|'wilson')` provides exact and Wilson binomial intervals. `statsmodels.stats.proportion.proportion_confint` provides the same intervals. — [SciPy bootstrap docs (not fetched; standard reference)](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html); [SciPy binomtest docs (not fetched)](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html)

### Inferences
- **Reporting rules**:
  - Always state n_events and the hours of leak-free test data.
  - Give event recall as "k/n (95% CI a–b)".
  - Express false alarms as a Poisson rate with an exact CI (e.g. 2 alarms in 4 weeks).
  - Use a moving- or circular-block bootstrap with block length ≥24 h (better, 1 week) to keep autocorrelation. `arch.bootstrap.MovingBlockBootstrap` / `CircularBlockBootstrap` implement this (from my knowledge, not fetched).
  - For IF vs rule on the same leaks, use McNemar's exact test on the detected/missed pairs, or a paired bootstrap of ΔTTD.
  - Avoid claiming "better" when the CIs overlap heavily.
- Repeat synthetic leak injection over many random start times and sizes to get enough events (hundreds) for stable estimates. Label these results "simulated".

### Gaps
- I found no water-sector paper on statistical significance for leak detectors with small event counts. The methods above are general statistical practice.

## 6. Alert explainability and alarm fatigue (operator usefulness, human-in-the-loop)

### Takeaway
For utilities, the binding constraint is false alarms. Each one costs crew time, and BattLeDIM explicitly prices them, so evaluation should be framed as "detections at an operator-acceptable alarm budget". Each alert should come with an explanation operators can verify (which signal deviated, by how much versus the hour-of-week baseline, the MNF trend). Field-crew outcomes (leak found / not found / other cause) should be logged as labels to recalibrate thresholds and to measure real-world precision.

### Cited Findings
- BattLeDIM penalises false detections because they cause financial loss through lost person-hours. Repeat alarms on an already-detected leak are given zero value. — [BattLeDIM summary](https://battledim.ucy.ac.cy/?p=270); [EPyT-Flow issue #34](https://github.com/WaterFutures/EPyT-Flow/issues/34)
- A BattLeDIM entry with the highest TPR had 138 false positives. Its economic ranking shows that maximising recall without controlling false alarms is not what a utility values. — [LWDA 2023](https://ceur-ws.org/Vol-3630/LWDA2023-paper40.pdf)
- Leak detection systems trade sensitivity against false alarms, and filtering to reduce false alarms delays detection. — [arXiv 1902.03927](https://arxiv.org/pdf/1902.03927)
- WDN monitoring research adds explicit validation steps to suppress false alarms before alerting operators. — [Boracchi et al. 2021 snippet](https://boracchi.faculty.polimi.it/docs/2021_WDN_Monitoring_NCA.pdf)
- There is work on assessing predictive systems by their **alarm burden**, in a clinical setting. — [arXiv 2102.05691, "Novel Techniques to Assess Predictive Systems and Reduce Their Alarm Burden" (search result only)](https://arxiv.org/pdf/2102.05691)

### Inferences
- Report a curve of **event recall vs false alarms per DMA per week**, a FROC-style operating curve, and mark the operating point chosen on validation data.
- Alert payload:
  - observed vs expected flow (hour-of-week median ± MAD)
  - pressure deviation
  - duration so far
  - estimated excess volume
  - top contributing features (for IF, per-feature deviation z-scores or SHAP via `shap.TreeExplainer`, which supports IsolationForest; from my knowledge, not verified)
- Human-in-the-loop: keep an alert log with operator/crew disposition codes (confirmed leak, burst, meter fault, legitimate demand such as a fire or filling, no cause found). Compute **field-verified precision** monthly and feed confirmed events back as labelled evaluation data, not as training-filter labels.

### Gaps
- I found no water-utility-specific study quantifying acceptable alarm rates or operator trust in ML leak alerts in this session.

## 7. Reporting standards (model cards, datasheets)

### Takeaway
Publish a model card with intended use (DMA-level leak screening, not localisation), evaluation data and protocol, metrics with CIs, disaggregated performance (night/day, leak size bins, DMA), limitations and the alarm budget. Pair it with a datasheet describing the sensor data's provenance, sampling, gaps, labelling process and known biases.

### Cited Findings
- **Model Cards for Model Reporting** (Mitchell et al., FAT* 2019) propose short documents that accompany trained models. Their sections are model details, intended use, factors, metrics, evaluation data, training data, quantitative analyses (disaggregated by relevant factors), ethical considerations, and caveats and recommendations. — [arXiv 1810.03993 (not fetched; standard reference)](https://arxiv.org/abs/1810.03993)
- **Datasheets for Datasets** (Gebru et al., CACM 2021) propose documenting a dataset's motivation, composition, collection process, preprocessing/labelling, uses, distribution and maintenance. — [arXiv 1803.09010 (not fetched; standard reference)](https://arxiv.org/abs/1803.09010)
- The VUS authors show that metric choice can change conclusions, which supports reporting several metrics and stating the protocol explicitly. — [arXiv 2502.13318](https://arxiv.org/abs/2502.13318)

### Inferences
- AquaWatch model card "Factors" should include time of day (night vs peak), leak size bin, leak type (burst vs background), DMA, season and sensor-gap periods.
- "Metrics" should list:
  - event recall with CI
  - false alarms per DMA per week with CI
  - median TTD
  - minimum detectable leak
  - VUS-PR
  - the simplified economic score
  - point-wise F1 for continuity only
- The datasheet must state whether labels are real (field-confirmed) or synthetic, how leak start and end times were determined, and that the dataset covers only 14 days and one season.
- Version the evaluation code and fix random seeds, so a reviewer can reproduce every number.

### Gaps
- I did not verify the exact current section lists of the model card and datasheet papers in this session. Spot-check them before quoting.
