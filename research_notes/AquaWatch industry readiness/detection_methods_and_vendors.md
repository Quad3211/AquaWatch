# Leak and Burst Detection in Water Distribution Networks: Methods and Commercial Comparators

Scope note: this covers detection (did something happen, and when), localisation (which zone or pipe segment), and pinpointing (the exact spot to dig). AquaWatch's current method, an Isolation Forest on two hourly deviation features compared against a "flow > 25% above zone/hour mean" rule, is a zone-level detection method. It does not localise or pinpoint. Research budget limits: several primary full texts (the BattLeDIM 2022 overview paper, the UCL/Yorkshire Water Isolation Forest paper, Wu & Liu 2017) could not be retrieved. Those gaps are listed explicitly below. Items marked "unverified background" come from prior knowledge and were not confirmed with a source in this session.

## 1. Minimum Night Flow (MNF) analysis and DMA inflow monitoring

### Takeaway
MNF analysis of District Metered Area (DMA) inflow is the industry baseline for leak detection. It measures inflow in a low-demand window (typically somewhere in 01:00–05:00), compares it with a baseline or with expected legitimate night use, and flags step increases. Thresholds are mostly utility-configured rather than standardised. MNF is a detection and zone-localisation method, not a pinpointing method.

### Cited Findings
- MNF is usually taken between 01:00 and 05:00. A DMA whose MNF stays at or below about 50% of average daily flow is treated as unlikely to hold major leakage — [Bentley blog: MNFs and DMAs, new concepts](https://blog.bentley.com/software/mnfs-and-dmas-new-concepts)
- Studies use different night windows: 03:00–04:00 in one paper ([engrXiv preprint](https://engrxiv.org/preprint/download/3794/6712/5423)) and 02:00–04:00 in a Spanish study ([RiuNet UPV](https://riunet.upv.es/server/api/core/bitstreams/5fa6ee31-7dc9-4f67-af82-62623c7e2f9e/content)). The window is a configuration choice.
- An automated DMA leak detection system uses three severity tiers, from a notice of a possible minor fault up to an alert needing immediate action. Its thresholds can be set automatically or overridden manually — [engrXiv preprint](https://engrxiv.org/preprint/download/3794/6712/5423)
- A sudden rise in minimum consumption above a threshold is treated as a sign of new leakage. One documented real case saw MNF rise from 76.5 L/s to 85.2 L/s (about +11%), which indicated a new leak — [US patent 10401250](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10401250); [US patent 11326977](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11326977)
- Leakage varies over time, so one MDPI study used only 30–35 continuous days per DMA when estimating MNF — [Water 16(24):3642](https://www.mdpi.com/2073-4441/16/24/3642)
- Commercial practice combines MNF with a zone mass balance and the Infrastructure Leakage Index (ILI). Autodesk Info360 Insight computes ILI daily as current daily real losses divided by unavoidable daily real losses. Its option to estimate the minimum-usage period, night usage and the pressure–leakage (orifice) exponent requires billing sensors in the mass balance — [Autodesk Info360 Insight help: ILI](https://help.autodesk.com/cloudhelp/ENU/INF360I-UserGuide/files/GUID-9EAF65E8-2C26-45AC-863B-9A160EA21EEA.htm)
- Xylem's virtual-DMA white paper describes MNF tracking as alerting operators to leaks or bursts through a rise or spike in flow. It uses water balance to tell a leak apart from an improperly closed boundary valve — [Xylem white paper: virtual DMAs](https://www.xylem.com/en-ca/resources/white-papers/optimizing-leak-detection-using-virtual-district-metering-areas-dmas/)

### Inferences
- AquaWatch's "flow > 25% above zone/hour mean" rule is a crude all-hours version of this. The MNF example above (+11% leak signal) suggests a 25% all-hours threshold would miss many real leaks, because daytime demand variance swamps leak flow. An MNF-specific feature, such as the 02:00–04:00 mean inflow compared with a rolling 30-day median plus k·MAD, is the most credible and cheapest single upgrade.
- Night flow should be split into legitimate night use (estimated from household or meter counts) and leakage. Without that split, MNF supports trend and step detection only, not leak volume.
- An MNF "step change" (a new persistent level) differs from a burst (a large, short, sudden change). Industry tools treat them as different event types.

### Gaps
- I found no standardised MNF alarm threshold such as an IWA-prescribed percentage. Thresholds appear to be utility-specific.
- Unverified background: IWA/UK practice expresses night leakage in litres per property per hour and applies FAVAD (N1 exponent) pressure correction. No source was retrieved this session.
- No quantitative sensitivity figure (smallest detectable leak as a percentage of DMA inflow) was found for MNF alone.

## 2. Statistical and time-series methods compared with Isolation Forest

### Takeaway
The dominant data-driven paradigm in the literature is "prediction–classification": forecast expected flow or pressure, then apply a statistical test (CUSUM, EWMA, Western Electric/SPC rules, or a threshold on residuals) to the residual. Isolation Forest is used in recent work, mostly on DMA flow validated against repair logs. It is one unsupervised option among several, with no evidence that it beats forecast-residual plus CUSUM approaches. Published detection rates are modest, for example 44% of bursts at a 5% false-alarm rate in a Dutch real-world study.

### Cited Findings
- Wu & Liu (2017), "A review of data-driven approaches for burst detection in water distribution systems", *Urban Water Journal* 14(9):972–983, treats burst detection as anomaly detection on SCADA hydraulic data. It groups methods into three categories, with prediction–classification the most popular. It notes that balanced training sets are hard to obtain because bursts are rare — [aggregator summary](https://www.bohrium.com/paper-details/a-review-of-data-driven-approaches-for-burst-detection-in-water-distribution-systems/811065243181514755-3159); [Water 15(9):1662 citing it](https://www.mdpi.com/2073-4441/15/9/1662/html)
- A 2024 follow-up review by Wu, Liu & Kapelan focuses on the data limitations of data-driven methods, such as scarce labels and sensor issues, rather than on algorithm choice — [cited via Water 15(9):1662 / search summary](https://www.mdpi.com/2073-4441/15/9/1662/html)
- Bakker et al. (Netherlands) compared a heuristic that checks measured demand against adaptive forecasts with a CUSUM baseline on real data. The heuristic detected 44.4% of reported bursts at a 5.0% false-alarm rate, and produced fewer false alarms than CUSUM at the same detection rate — [Detecting pipe bursts using Heuristic and CUSUM methods](https://pure.korea.ac.kr/en/publications/detecting-pipe-bursts-using-heuristic-and-cusum-methods/); [Arizona record](https://experts.arizona.edu/en/publications/detecting-pipe-bursts-using-heuristic-and-cusum-methods/)
- A Lund University study compared univariate SPC (Western Electric rules, CUSUM, EWMA) with multivariate SPC (Hotelling T², MCUSUM, MEWMA) on net demand, pipe flows and nodal pressures. It tested the univariate methods on real data and all six on synthetic data — [Lund: Burst detection and location in water distribution networks](https://www.lunduniversity.lu.se/lup/publication/64b16f6c-20e6-4c71-ad67-ae464f7118eb)
- A 2024 arXiv preprint on real-time burst localisation with change-point detection found CUSUM gave better overall localisation than Shewhart charts on simulated pressure data — [arXiv 2407.09074](https://arxiv.org/html/2407.09074v1)
- CUSUM and Shewhart charts are the oldest online event-detection approaches in water systems (water-quality context) — [Sandia/OSTI literature review](https://www.osti.gov/servlets/purl/1707844)
- Isolation Forest literature:
  - A UCL study on more than 2,500 Yorkshire Water DMAs (up to about 2,000 households each, flow at each inlet and outlet) uses Isolation Forest to flag anomalies, checked against a mains repair log — [McMillan et al., UCL](https://discovery.ucl.ac.uk/id/eprint/10174209/1/McMillan_Machine-Learning-Based%20Health%20Monitoring%20and%20Leakage%20Management%20of%20Water%20Distribution%20Systems_VoR.pdf)
  - Joseph et al. (2025, *Water* 17(14):2164) compared one-class classifiers (Isolation Forest, OC-SVM, Elliptic Envelope) on DMA flow and found Isolation Forest outliers correlated with known repairs. The study removed industrial consumption and smoothed filter-backwash spikes before detection — [MDPI Water 17(14):2164](https://mdpi.com/2073-4441/17/14/2164); [VU repository PDF](https://vuir.vu.edu.au/49536/1/water-17-02164.pdf)
  - An Emilia-Romagna (Italy) study combined SCADA and smart-meter data to improve DMA anomaly detection — [Univ. Bologna](https://cris.unibo.it/bitstream/11585/1020130/1/Combining%20SCADA%20and%20smart%20meter%20data%20to%20improve%20anomaly%20detection.pdf)
  - A 2023 *Water Supply* paper applied Isolation Forest to spatiotemporal features from multiple sensors — [DOAJ record](https://doaj.org/article/2059879f0cf04b0bbec1ded3e13d01ab)
  - A Chinese patent feeds pressure-disturbance matrices into an Isolation Forest to output burst results — [US 11236867](https://patentimages.storage.googleapis.com/69/6c/5f/1114ffa7e64dff/US11236867.pdf)
  - A 2024 *Water* paper compared logic-based and ML-based leak and burst detection — [MDPI Water 16(14):1935](https://mdpi.com/2073-4441/16/14/1935)

### Inferences
- AquaWatch already uses deviation-from-profile features, which are residuals from a naive "zone × hour mean" forecast, so it is already doing a weak form of prediction–classification. The largest accuracy gains will most likely come from a better forecast (day-of-week, holidays, rolling baseline, gradient boosting or SARIMA/Prophet on recent data) and a sequential test such as CUSUM or EWMA. That catches small persistent leaks that a pointwise Isolation Forest on single hours treats as normal.
- Isolation Forest is pointwise and memoryless. It flags rare individual points, whereas leaks are persistent level shifts. Feeding it rolling-window features (24 h mean residual, night-flow residual, slope) or switching to CUSUM on residuals better matches the physics.
- All the Isolation Forest studies validate against repair logs, which suggests the credible evaluation for AquaWatch is detection rate versus false-alarm rate (and time-to-detect) on labelled or synthetically injected leaks, not anomaly counts.
- LSTM and other deep forecasters appear in the literature, but given label scarcity (Wu & Liu) and a small team, gradient boosting or SARIMA residuals with CUSUM is the more defensible step.

### Gaps
- I could not retrieve full text of the UCL/Yorkshire or Joseph et al. papers, so no precision/recall figures for Isolation Forest are available here.
- I found no head-to-head published benchmark of Isolation Forest against CUSUM, LSTM or Prophet on the same leak dataset.
- No quantitative comparison of SARIMA, Prophet, GBM and LSTM forecasting residuals was retrieved for leak detection specifically.

## 3. Model-based methods and BattLeDIM 2020

### Takeaway
BattLeDIM 2020 (L-Town benchmark, 5-minute SCADA data for 2019) showed that no single method dominates. The winners combined data-driven detection with hydraulic-model-based localisation, and the organisers concluded that leak detection and isolation methods still need development. Model-based localisation means calibrating an EPANET model and searching for leak location and size (emitters) that minimise pressure residuals. It needs a good network model, which AquaWatch does not have.

### Cited Findings
- The competition compared methods for detecting and locating leaks using SCADA flow and pressure from a virtual network. Teams used time-series analysis, statistical methods, ML, mathematical programming, meta-heuristics and engineering judgement. Entries were scored on economic criteria. The authors conclude that "the competition results highlight the need for further development of methods for leakage detection and isolation" (Vrachimis et al. 2022, *JWRPM*, doi:10.1061/(ASCE)WR.1943-5452.0001601) — [Zenodo record](https://zenodo.org/record/6641304); [ASCE](https://ascelibrary.com/doi/10.1061/(ASCE)WR.1943-5452.0001601); [TU Delft record](https://research.tudelft.nl/en/publications/battle-of-the-leakage-detection-and-isolation-methods/)
- Evaluation data run from 2019-01-01 00:00 to 2019-12-31 23:55 at 5-minute steps. Pressure sensors were placed to maximise collective sensitivity to leaks. A detection counted when it fell within a time window of leak start (e.g. Tmax = 1 week) and within a pipe-distance radius (e.g. Xmax = 300 m) — [NSF PAR paper citing BattLeDIM](https://par.nsf.gov/servlets/purl/10343901); [Problem description and rules](https://battledim.ucy.ac.cy/wp-content/uploads/2020/01/BattLeDIM_Problem_Description_and_Rules-v1.3.pdf)
- Awards: shared first place to Tongji and "Under Pressure", shared third to IRI and Leakbusters, and honourable mentions to Tsinghua and UNIFE. Solutions within 5% of the top normalised score were treated as tied. IRI's score was €210,772 after re-evaluation — [BattLeDIM site](https://battledim.ucy.ac.cy/?p=49)
- TU Delft lists a BattLeDIM first-place award for Steffelbauer, Deuerlein, Gilbert, Piller and Abraham, which is likely the "Under Pressure" team (team name not confirmed by the source) — [TU Delft prize record](https://research.tudelft.nl/en/prizes/first-place-award-for-outstanding-achievements-in-the-battle-of-t/)
- The IRI (UPC Barcelona) entry combined a model-based approach with a data-driven approach — [IRI paper](https://www.iri.upc.edu/download/scidoc/2503) (search snippet; full text failed to load)
- The KU (Korea) entry was two-phase: Western Electric rules on flow and pressure for detection, then localisation with a calibrated hydraulic model using emitters — [KU-hydrosystem report, Zenodo](https://zenodo.org/records/3922019/files/KU-hydrosystem%20ver2.pdf?download=1)
- DHI China combined data mining for detection with genetic-algorithm-optimised hydraulic simulation for isolation — [DHI China paper, Zenodo](https://zenodo.org/records/3911523/files/Leakage%20Detection%20and%20Isolation%20in%20Water%20Distribution%20Network%20Based%20on%20Data%20Mining%20and%20Genetic%20Optimized%20Hydraulic%20Simulation_DHI%20China_LIU_ZHANG_ZHANG.pdf)
- UNIFE submission — [UNIFE.pdf, Zenodo](https://zenodo.org/records/3900989/files/UNIFE.pdf)
- The dataset is openly available — [Zenodo dataset 4017658](https://zenodo.org/record/4017658)
- Recent follow-on work uses BattLeDIM for model-based localisation with few pressure sensors ([arXiv 2406.19900](https://arxiv.org/pdf/2406.19900)), dual unscented Kalman filters ([arXiv 2412.11687](https://arxiv.org/pdf/2412.11687)), and a multivariate statistical framework for detection, classification and pre-localisation ([arXiv 2512.15685](https://arxiv.org/pdf/2512.15685))

### Inferences
- The common pattern among strong BattLeDIM entries is "statistical or data-driven detection, then model-based localisation". AquaWatch could credibly copy the detection half (SPC rules or CUSUM on flow and pressure residuals). It should describe localisation as zone-level only until a calibrated network model exists.
- The BattLeDIM dataset (with ground-truth leak list) is an openly available labelled benchmark. AquaWatch could test its Isolation Forest against CUSUM on it, after resampling 5-min to hourly, to report real detection rate, false alarms and time-to-detect.

### Gaps
- I could not retrieve the full JWRPM overview paper (Zenodo PDF stream aborted, TU Delft PDF 403). Per-team true/false-positive counts, scores other than IRI's, and Tongji's method are therefore missing.
- Unverified background: L-Town has roughly 782 junctions and about 42.6 km of mains, 33 pressure sensors, 3 flow sensors and 82 AMR demand meters in area C. The 2019 evaluation year contained 23 leaks (mix of abrupt and incipient). Verify against the problem description PDF before citing.

## 4. Pressure transients, high-rate pressure, acoustic, satellite and GPR

### Takeaway
These are mostly hardware-based localisation and pinpointing technologies that sit downstream of SCADA analytics in the leak-management workflow. Analytics (MNF, residual tests) detects and assigns a zone. Acoustic loggers or correlators, satellite SAR surveys or transient monitoring narrow the location. Ground microphones, correlators or GPR pinpoint the dig site. High-rate (hundreds of Hz) pressure transient monitoring is the exception: it can detect and locate bursts in near real time via wave arrival times, but needs dedicated sensors.

### Cited Findings
- Misiunas et al. (2005) used a modified CUSUM on high-rate pressure to find burst-induced wave arrival times and magnitudes at two or more points, locating the burst, and validated it on a real network — [Lund record](https://lup.lub.lu.se/record/641581)
- Visenti/MIT WaterWiSe with PUB Singapore began in 2009 and scaled from 8 nodes in one zone to tens of nodes across several zones (>80 km²). It was linked to PUB SCADA and is reported to have detected several bursts via transient sensors plus many pressure abnormalities from planned and unplanned operations. No detection-rate statistics were published — [Allen et al. 2013, MIT](https://dspace.mit.edu/bitstream/1721.1/92758/1/Allen%20et%20al%20-%20SNPD2013.pdf); [CORE PDF](https://core.ac.uk/download/78057859.pdf); [Whittle, wavelet-based burst detection, MIT](https://dspace.mit.edu/bitstream/handle/1721.1/89664/Whittle_Wavelet-based%20burst.pdf?sequence=1)
- At Tuas Power, Singapore, Xylem installed high-rate wireless pressure monitors at four sites. Transient magnitudes fell from 60 PSI to 10 PSI after operational changes (vendor-reported) — [Xylem case study](https://www.xylem.com/en-gy/resources/case-studies/tuas-power-singapore-identifying-and-eliminating-harmful-transients-improving-system-reliability-and-prolonging-the-effective-life-of-infrastructure-assets/)
- Acoustic noise loggers: Gutermann ZONESCAN 820 uses correlation between loggers to reject ambient noise and spectrum analysis to reject electrical and mechanical pipe noise. ZONESCAN Hydro uses a hydrophone for plastic pipes, with automatic daily correlation (manufacturer claims) — [Gutermann logger](https://www.environmental-expert.com/products/leak-detection-noise-radio-logger-208939); [ZONESCAN Hydro launch](https://www.environmental-expert.com/news/gutermann-launches-zonescan-hydro-high-sensitivity-hydrophone-logger-for-plastic-pipe-networks-at-7t-1186861)
- Aquarius Spectrum offers a fixed permanent acoustic system and a smartphone-based mobile system (iQuarius) with correlation done in the cloud — [water-technology.net](https://www.water-technology.net/?p=13337); [company listing](https://www.environmental-expert.com/companies/aquarius-spectrum-ltd-98821)
- Satellite SAR (ASTERRA, formerly Utilis): the Affinity Water/SUEZ programme screened 9,045 km of network in five areas, produced 763 prioritised areas of interest, and identified 902 leaks, 59% of them non-surfacing. Crews walked less than 4% of the network (vendor/partner reported). That is roughly 10 km screened per leak found (derived arithmetic, not a source figure) — [SUEZ Affinity case study](https://www.suez.com/en/uk/case-studies/satellite-leak-detection-delivers-results-affinity-water); [SUEZ PDF](https://www.suez.com/-/media/suez-global/files/uk-files/case-studies/affinity-water-satellite-case-study.pdf)
- New Braunfels Utilities (Texas) found 229 leaks (128 customer-side, 101 utility-side) across four ASTERRA surveys — [WWD case study](https://www.wwdmag.com/channel/casestudies/using-satellite-radar-imaging-detect-pipeline-leaks-texas-new-braunfels)
- ASTERRA has also been presented in the Caribbean context (Caribbean Regional Water Loss Conference 2023, Trinidad & Tobago MPU) — [MPU CRWLC 2023 talk](https://www.mpu.gov.tt/crwlc2023/files/talks/Using%20Satellite%20RADAR%20Imagery%20to%20Detect%20Leaks%20from%20Potable%20Water%20Pipes%20-%20United%20States%20-%20John%20Stevens.pdf)

### Inferences
- AquaWatch should place itself as the detection and zone-prioritisation layer that tells crews which zone to survey acoustically, matching how TaKaDu, Info360 and ASTERRA outputs feed field teams. It should not claim pinpointing.
- Hourly data cannot detect transients, which last seconds. "Burst detection" claims should be limited to large, sustained flow increases.
- The Caribbean water-loss conference presence of satellite SAR suggests regional utilities already know these hardware and survey options. An analytics prototype adds value by being cheap and using existing meter data.

### Gaps
- I found no source for ground-penetrating radar accuracy in water leak pinpointing.
- No independent comparison of noise loggers, correlators, hydrophones and satellite (cost per leak, hit rate) was retrieved. A DTIC technology comparison report surfaced but was not opened ([DTIC AD1039195](https://apps.dtic.mil/sti/pdfs/AD1039195.pdf)).
- Typical acoustic correlator location accuracy (often cited as about ±1 m on metallic pipe, worse on plastic) was not verified this session.

## 5. Which features matter

### Takeaway
The literature and vendor practice centre on DMA inflow, especially night flow; residuals against a calendar-aware expected profile; the flow–pressure relationship (leak flow rises with pressure, so pressure drop with flow rise is a burst signature); and multi-sensor spatial correlation. Data hygiene features also matter, such as removing industrial users and filter-backwash spikes. Evidence on weather and temperature features and on intermittent supply was not found in this session.

### Cited Findings
- Night window flow (01:00–05:00) and MNF relative to average daily flow are core features — [Bentley blog](https://blog.bentley.com/software/mnfs-and-dmas-new-concepts)
- Pressure dependence of leakage is modelled explicitly: Info360 estimates an orifice (pressure–leakage) exponent from zonal usage, and ILI checks zonal pressure sensors for anomalies — [Autodesk ILI help](https://help.autodesk.com/cloudhelp/ENU/INF360I-UserGuide/files/GUID-9EAF65E8-2C26-45AC-863B-9A160EA21EEA.htm)
- Multi-sensor features: multivariate SPC on net demand, pipe flows and nodal pressures ([Lund](https://www.lunduniversity.lu.se/lup/publication/64b16f6c-20e6-4c71-ad67-ae464f7118eb)); clustering on multiple DMA pressure sensors ([Wu & Liu CCWI 2017](https://orda.shef.ac.uk/articles/journal_contribution/CCWI2017_F7_Clustering-based_Burst_Detection_Using_Multiple_Pressure_Sensors_in_District_Metering_Areas_/5363869)); and spatiotemporal multi-sensor Isolation Forest ([DOAJ Water Supply 2023](https://doaj.org/article/2059879f0cf04b0bbec1ded3e13d01ab))
- Preprocessing: removing industrial consumption and smoothing filter-backwash spikes before Isolation Forest — [MDPI Water 17(14):2164](https://mdpi.com/2073-4441/17/14/2164)
- Smart-meter (customer) data combined with SCADA improves DMA anomaly detection — [Univ. Bologna](https://cris.unibo.it/bitstream/11585/1020130/1/Combining%20SCADA%20and%20smart%20meter%20data%20to%20improve%20anomaly%20detection.pdf)
- Class imbalance (few bursts) is a core feature and label problem — [Water 15(9):1662](https://www.mdpi.com/2073-4441/15/9/1662/html)

### Inferences
- Priority features for AquaWatch: (1) night-window inflow residual against a rolling baseline; (2) day-of-week and public-holiday terms in the expected profile, since zone × hour alone ignores weekly cycles; (3) a joint flow-up and pressure-down indicator; (4) persistence features (rolling 6–24 h residual sums, CUSUM statistic); (5) neighbour-zone correlation, so a shared shift points to demand or weather rather than a leak.
- Intermittent supply (common in parts of Jamaica and the Caribbean) breaks MNF assumptions: refilling surges look like bursts, and supply-off periods give zero flow. Supply-schedule flags should be a feature, or those periods should be masked.

### Gaps
- I found no source quantifying the value of weather or temperature features for leak detection (as opposed to demand forecasting).
- No source on leak detection methods under intermittent water supply was retrieved. This is an important gap for the Jamaica context and needs a targeted follow-up.

## 6. Commercial comparators

### Takeaway
Commercial platforms ingest SCADA/DMA flow and pressure (plus AMI, billing and GIS where available), learn expected behaviour statistically, and output prioritised events. These events are categorised (leak, burst, meter fault, boundary-valve issue), assigned to staff and tracked to closure with KPIs. Hardware vendors (Gutermann, FIDO, Aquarius, ASTERRA) cover localisation and pinpointing. Almost all reported results are vendor-published.

### Cited Findings
- **TaKaDu (Central Event Management, CEM)**
  - KUB Knoxville: a leak was flagged 2018-10-06 and found and isolated 2018-10-18 under an interstate. Estimated non-revenue-water loss was 19.2 million gallons in that week, about US$7,718 (vendor) — [KUB case study 2019](https://takadu.com/wp-content/uploads/2024/03/TaKaDu-and-KUB-case-study-April-2019.pdf); [KUB page](https://www.takadu.com/case-study/kub-3/)
  - EPM Medellín (since 2019): earlier detection of early-stage leaks and smaller crew routes via sub-sectoring — [CS-EPM](https://www.takadu.com/wp-content/uploads/2024/03/CS-EPM.pdf); [The Water Network](https://thewaternetwork.com/article-FfV/epm-improves-leak-detection-operational-efficiency-and-long-term-planning-m9HtXtkQSQgi2Zl3I06ujA)
  - Mei Carmel (Haifa): a leak would likely have gone unfound for 6–10 more months — [Mei Carmel 2018](https://www.takadu.com/wp-content/uploads/2024/03/Mei-Carmel-use-case-Feb-2018.pdf)
  - Hunter Water: leakage down 34% compared with 2015–16, with TaKaDu used to prioritise leak detection — [Hunter 2021](https://takadu.com/wp-content/uploads/2024/03/case-HUNTER-October-2021.pdf)
  - Unitywater: reductions in reactive maintenance, breaks, NRW and asset failures — [Unitywater 2016](https://www.takadu.com/wp-content/uploads/2024/03/Use-Case-Unitywater-using-TaKaDus-integrated-event-management-solution-October-2016.pdf)
  - KPI benchmarks document — [Key Performance Benchmarks](https://www.takadu.com/wp-content/uploads/2024/03/Key-Performance-Benchmarks.pdf)
  - Sydney Water real-time leak detection — [AWA article](https://awa.asn.au/resources/latest-news/technology/innovation/data-driving-real-time-leak-detection-at-sydney-water)
  - A 2026 WIOA paper on digital monitoring with TaKaDu reports 401 analysed events and faster detection — [WIOA 2026](https://wioa.org.au/wp-content/uploads/2026/07/Angelina-Isler_Enhancing-leak-detection-through-digital-monitoring-and-operational-expertise.pdf)
- **Autodesk Info360 Insight (ex-Innovyze)**: zone mass balance, daily ILI (CDRL/UDRL), estimation of night-usage period and orifice exponent (needs billing sensors), and pressure anomaly checks — [Autodesk help](https://help.autodesk.com/cloudhelp/ENU/INF360I-UserGuide/files/GUID-9EAF65E8-2C26-45AC-863B-9A160EA21EEA.htm)
- **Xylem (Visenti, Pure Technologies, Idrica)**: virtual DMAs with MNF and water balance ([white paper](https://www.xylem.com/en-ca/resources/white-papers/optimizing-leak-detection-using-virtual-district-metering-areas-dmas/)); high-rate transient pressure monitoring ([Tuas case](https://www.xylem.com/en-gy/resources/case-studies/tuas-power-singapore-identifying-and-eliminating-harmful-transients-improving-system-reliability-and-prolonging-the-effective-life-of-infrastructure-assets/)); Visenti origins in MIT/PUB WaterWiSe ([Allen et al. 2013](https://dspace.mit.edu/bitstream/1721.1/92758/1/Allen%20et%20al%20-%20SNPD2013.pdf))
- **Bentley**: MNF/DMA guidance (50%-of-ADF heuristic, 01:00–05:00 window) — [Bentley blog](https://blog.bentley.com/software/mnfs-and-dmas-new-concepts)
- **ASTERRA (Utilis)**: L-band SAR soil-moisture signature of treated water, delivered as prioritised areas of interest for acoustic follow-up. Affinity: 9,045 km screened, 763 areas, 902 leaks, 59% non-surfacing. SUEZ claims at least 3× effectiveness, and South Staffordshire reported 7× greater leak volume found (vendor claims, methodology unstated) — [SUEZ](https://www.suez.com/en/uk/water-network-management/leakage/satellite-water-leak-detection); [Esri partner page](https://www.esri.com/partners/utilis-a2Tf2000005TDcbEAG/satellite-based-leak-a2df20000056AIUAA2)
- **FIDO Tech**: AI classification of acoustic leak noise, claimed >92% accurate, with small/medium/large size grading trained on United Utilities DMA data. Oldcastle CivilSense (FIDO-powered) claims >93% accuracy and ±1.5 ft location, compared with 40–60% for traditional methods (vendor). Accuracy is verified by physical inspection. Hailey, Idaho found 22 previously undetected leaks. No independent validation was found — [Smart Water Magazine](https://smartwatermagazine.com/news/fido/breakthrough-leak-detection-uk-pioneered-ai-learns-identify-water-leaks-size); [Microsoft feature](https://news.microsoft.com/source/features/sustainability/ai-tool-uses-sound-to-pinpoint-leaky-pipes-saving-precious-drinking-water/); [CivilSense FAQ](https://oldcastleinfrastructure.com/civilsense_real_time_leak_detection_faq/); [Hailey case](https://oldcastleinfrastructure.com/study/leak-detection-technology-saves-hailey/)
- **Gutermann**: ZONESCAN fixed correlating noise loggers and hydrophones (see section 4)
- **Aquarius Spectrum**: fixed and mobile acoustic correlation with cloud processing (see section 4)

### Inferences
- The industry-standard output is not "anomaly yes/no" but a managed event: type, start time, estimated volume or flow rate, zone, cost or water-loss estimate, status workflow, and KPIs such as time-to-detect, time-to-repair and water saved. AquaWatch would look more credible by emitting events with estimated excess m³/h and cumulative loss, not just flagged rows.
- TaKaDu's KUB example (12 days from alert to isolation) shows that analytics value depends on the field response loop, so the prototype should track alert-to-action.

### Gaps
- Ovarro: no source retrieved. It is known for SCADA/telemetry RTUs and acoustic loggers (Enigma), but this is unverified.
- Bentley's current leak analytics product details (e.g. OpenFlows WaterSight) were not retrieved.
- Xylem Idrica (GoAigua) and Pure Technologies (SmartBall, Sahara in-pipe inspection for transmission mains) features were not verified this session.
- Precise detection algorithms of TaKaDu, Info360 and others are proprietary. No published accuracy (precision/recall) figures were found for any platform, only case outcomes.
