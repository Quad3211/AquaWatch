# Data Sources, Telemetry Formats, Benchmark Datasets and Synthetic Data Generation for Water-Network Leak Detection

Context: AquaWatch Jamaica currently uses a hand-made hourly CSV (flow_index, pressure_index, 5 fictional zones, 14 days, 6 injected events). These notes cover (a) what real utility data looks like, (b) public benchmarks, (c) physically based synthetic generation, and (d) time-series handling. Research was done 2026-11-21 under a tight tool-call budget, so some items are flagged as unverified in the Gaps sections.

## What real utility telemetry looks like (SCADA, AMI/AMR, loggers, GIS), its data quality problems, protocols and data models

### Takeaway
Real leak-detection data is a mix of SCADA flow, pressure and tank-level signals (often 1 to 15 minute averages) and AMI/AMR consumption at 15-minute to hourly intervals. It is noisy and incomplete: roughly 10% missing and 3 to 35% dubious values are documented, with flatlines and timestamp inconsistencies the most common faults. Open data models exist (OGC WaterML 2.0, OGC SensorThings API, FIWARE Smart Data Models WaterNetworkManagement and WaterDistributionManagementEPANET). AquaWatch should ingest raw units (L/s, m or bar), not normalised "index" values.

### Cited Findings
- The BattLeDIM benchmark, modelled on a real Cypriot network, is a realistic template for a utility sensor set. It has 1 tank level sensor, 3 flow sensors and 33 pressure sensors, each reporting "the average pressure of the last 5 minutes", plus 82 AMRs in "Area C" that give aggregated consumption of groups of consumers. — [BattLeDIM Problem Description and Rules v1.3](https://battledim.ucy.ac.cy/wp-content/uploads/2020/01/BattLeDIM_Problem_Description_and_Rules-v1.3.pdf)
- The BattLeDIM EPANET model and SCADA data "were generated based on a real water distribution network in a city in Cyprus". — [BattLeDIM site](https://battledim.ucy.ac.cy/)
- A quality-assurance study of utility meter data found about 10% of measurements absent and 3 to 35% dubious or erroneous. Flatlines and timestamp inconsistencies were the most common anomalies for flow and pressure. — [Tandfonline / Urban Water Journal 2019 (doi 10.1080/1573062X.2019.1611884)](https://informahealthcare.com/doi/abs/10.1080/1573062X.2019.1611884)
- SCADA data gaps commonly come from network or server failure, and redundant comms links do not prevent loss when the SCADA server itself fails. — [WWD Magazine: Data Integrity in a Regulatory World: SCADA Systems](https://www.wwdmag.com/utility-management/article/10938813/data-integrity-in-a-regulatory-world-scada-systems)
- Spikes are often operational, not faults. Examples include spikes caused by filter backwash, which researchers smoothed before anomaly detection. — [Unibo: Combining SCADA and smart meter data to improve anomaly detection](https://cris.unibo.it/bitstream/11585/1020130/1/Combining%20SCADA%20and%20smart%20meter%20data%20to%20improve%20anomaly%20detection.pdf)
- A DMA-level study found anomaly detection on 15-minute or hourly flows and on DMF (district meter flow) to be complementary. — [Unibo paper (same as above)](https://cris.unibo.it/bitstream/11585/1020130/1/Combining%20SCADA%20and%20smart%20meter%20data%20to%20improve%20anomaly%20detection.pdf)
- Vendor material says residential leak detection needs reads as often as every 15 minutes for 24+ hours. Continuous significant early-morning consumption is used as a leak signature (the night-flow principle). This is vendor-sourced. — [Badger Meter blog](https://badgermeter.com/blog/better-data-better-process); [CSA: Meter data management for water utilities](https://www.csa1.com/meter-data-management-for-water-utilities-what-system-operators-need-to-know/)
- A 2023 JWRPM study on the Austin and Tucson networks found SCADA systems poor at detecting realistic-sized leaks, while AMI identified small failures. Pressure-supplemented AMI was needed for good localisation in large networks. (This is reported via the search summary; the full paper was not read.) — [search result pointing to the Jun & Lansey study; see WaterWorld AMI + Data Management for context](https://www.waterworld.com/home/article/14070667/ami-data-management)
- **OGC WaterML 2.0** is a standard information model for water observation data, based on OGC/ISO 19156 Observations and Measurements. — [OGC WaterML](https://www.ogc.org/standard/waterml/)
- **OGC SensorThings API** exchanges sensor data and metadata (historic and current) as RESTful JSON, using entities Thing, Datastream and ObservedProperty (plus Observation, Sensor, Location). A WMO 2024 deck maps water-quantity and water-quality use cases onto it and notes WaterML 2.0 being considered for an API-based best practice with SensorThings. — [WMO: SensorThings API and WaterML 2.0 (2024)](https://public.wmo.int/sites/default/files/2024-02/SensorThings%20API%20and%20%20WaterML2.0%20.pdf)
- **FIWARE Smart Data Models**: the original FIWARE dataModels repository is archived. Work continues in the smart-data-models GitHub organisation, led by FIWARE Foundation, TM Forum, IUDX and OASC. — [FIWARE/dataModels](https://github.com/FIWARE/dataModels); [smart-data-models GitHub](https://github.com/smart-data-models)
- **dataModel.WaterNetworkManagement** defines harmonised Junction and Pipe entities, among others, for the water network management vertical. — [fork of WaterNetworkManagement](https://gh.hhj520.top/franckLG/dataModel.WaterNetworkManagement) (unofficial fork; the canonical repository is in the smart-data-models organisation)
- **dataModel.WaterDistributionManagementEPANET** adds SimulationScenario and SimulationResult entities and is described as EPANET-compatible. — [ecosyste.ms listing](https://awesome.ecosyste.ms/projects/github.com%2Fsmart-data-models%2FdataModel.WaterDistributionManagementEPANET)
- **WaterQualityObserved** (Smart Data Models) represents water quality parameters at a water body. The mirror page says the latest version is on GitHub. — [WaterQualityObserved spec (mirror)](https://caa06d9c-datamodels.readthedocs.io/en/latest/Environment/WaterQualityObserved/doc/spec/index.html)
- Research on FIWARE-enabled data models for raw-water supply modelling exists (NTUA). — [ITIA NTUA](https://www.itia.ntua.gr/en/docinfo/2383/)

### Inferences
- **Typical sampling rates.** The 5-minute averages in BattLeDIM are a credible target for SCADA, and 15-minute to hourly is typical for AMI. AquaWatch's hourly data is too coarse for night-flow analysis and transient detection. Moving to 5 or 15-minute resolution would make it look like real utility exports.
- **Units.** Real exports carry engineering units: flow in L/s or m3/h, pressure in m head or bar/psi, level in m. The prototype's dimensionless "index" columns should become `flow_lps`, `pressure_m` and so on, with a unit column or schema metadata.
- **Protocols (not verified this session; general industry knowledge).** Field RTUs and PLCs typically speak Modbus RTU/TCP or DNP3, the latter common in North American utilities. Newer systems use OPC UA and MQTT, with Sparkplug B for IIoT payloads. Data is usually archived in a historian such as AVEVA PI (formerly OSIsoft PI), and analysts usually get CSV/Excel exports or PI Web API pulls. A student prototype should not implement Modbus or DNP3. Ingesting CSV/Parquet and optionally an MQTT or SensorThings JSON stream shows "industry-shaped" ingestion without touching operational technology.
- **Quality issues to simulate and validate against:** gaps (comms or server outage), flatlines (stuck sensor or held last value), spikes (operational events such as backwash, pump starts and valve operations), timestamp problems (clock drift, DST/timezone shifts, duplicate or out-of-order rows) and meter faults (AMI under-registration, zero reads).
- SensorThings is the lightest-weight standard to mirror in the AquaWatch schema: Thing = zone/DMA asset, Datastream = sensor channel with unitOfMeasurement, Observation = timestamped value.

### Gaps
- Primary specification pages for Modbus, DNP3, OPC UA, MQTT/Sparkplug and the AVEVA PI historian were not fetched. The protocol statements above come from general knowledge and should be verified before being cited.
- No source was found that gives standard sampling-rate tables for RTUs and data loggers. The 5-minute figure comes from BattLeDIM, the 15-minute figure from vendor AMI material.
- The canonical smart-data-models WaterNetworkManagement and WaterObserved schemas were not read directly. Only a fork and a mirror were found.
- No Jamaica-specific sources (e.g. National Water Commission telemetry) were researched.
- The 2023 Austin/Tucson SCADA vs AMI paper was known only through a search summary. Its exact citation and URL were not confirmed.

## Public benchmark datasets for leak detection (size, resolution, labels, licence, URL, evaluation)

### Takeaway
The two core open benchmarks are **BattLeDIM 2020 / L-Town** (realistic 1-year, 5-minute SCADA + AMR, CC BY 4.0, 550 MB) and **KIOS LeakDB** (1,000 labelled scenarios each on Net1 and Hanoi, 30-minute labels, CC BY 4.0, 13.9 GB zip). Both are simulated. Fully labelled real data is rare, apart from small lab testbeds such as LeakTestbed. The WaterBenchmarkHub and EPyT-Flow Python packages load these benchmarks and reproduce their scoring.

### Cited Findings
**BattLeDIM 2020 (L-Town)**
- Zenodo record "Dataset of BattLeDIM" (DOI 10.5281/zenodo.4017659, concept 4017658), v1 published 2020-09-07. Licence CC BY 4.0, total 550.5 MB. Files: per-year (2018, 2019) Leakages CSV, SCADA XLSX, and SCADA Demands, Flows, Levels and Pressures CSVs, plus `L-TOWN.inp`, `L-TOWN_Real.inp`, `dataset_configuration.yaml`, `README.txt` and `2018_Fixed_Leakages_Report.txt`. — [Zenodo 4017658](https://zenodo.org/record/4017658)
- Creators: KIOS (University of Cyprus), TU Delft, Technion and Tsinghua. It is documented by DOI 10.5281/zenodo.3902046. — [Zenodo 4017658](https://zenodo.org/record/4017658)
- The 2018 historical SCADA covers 1 year at 5-minute intervals, with a 2018 leak repair report and an EPANET model. The 2019 SCADA (2019-01-01 00:00 to 2019-12-31 23:55, 5-minute steps) is the evaluation set. — [BattLeDIM site](https://battledim.ucy.ac.cy/?p=33); [Rules v1.3 PDF](https://battledim.ucy.ac.cy/wp-content/uploads/2020/01/BattLeDIM_Problem_Description_and_Rules-v1.3.pdf)
- Sensors: 33 pressure, 3 flow, 1 tank level, and 82 AMRs in Area C. — [Rules v1.3 PDF](https://battledim.ucy.ac.cy/wp-content/uploads/2020/01/BattLeDIM_Problem_Description_and_Rules-v1.3.pdf)
- L-Town has 785 nodes and 909 pipes and is the network used most often in the ML-for-WDN literature surveyed. — [Survey of ML in WDNs, arXiv 2410.12461](https://arxiv.org/html/2410.12461)
- Evaluation: teams submit a results file of detected leak location (link ID) and start time, e.g. "p1, 2019-02-03 10:00", scored with `Scoring_Algorithm.m` (MATLAB + EPANET-MATLAB Toolkit). Repository licence EUPL-1.2. A CodeOcean capsule runs the evaluation. — [KIOS-Research/BattLeDIM GitHub](https://github.com/KIOS-Research/BattLeDIM); [BattLeDIM site](https://battledim.ucy.ac.cy/)
- EPyT-Flow provides BattLeDIM loaders whose scoring "reproduces the official leaderboard results". — [epyt_flow.data.benchmarks.battledim source](https://epyt-flow.readthedocs.io/en/latest/_modules/epyt_flow/data/benchmarks/battledim.html)
- Workshop presentations from competing teams are on Zenodo. — [Zenodo 4139603](https://zenodo.org/record/4139603); [BattLeDIM 2020 Zenodo community](https://zenodo.org/communities/battledim2020/records)

**KIOS LeakDB**
- 1,000 scenarios on Net1 and 1,000 on Hanoi. Each gives pressure, demand and flow at every node and link as CSV, plus `Labels.csv` with 1 or 0 (leak present) per 30-minute time step. Leaks are abrupt and incipient, and not every scenario has a leak. — [WaterBenchmarkHub: KIOS LeakDB](https://waterfutures.github.io/WaterBenchmarkHub/benchmarks/KIOS-LeakDB.html)
- Full dataset on Zenodo: LeakDB.zip, 13.9 GB, CC BY 4.0, v1 2024-10-24 (DOI 10.5281/zenodo.13985057). It includes a MATLAB scoring algorithm and four demo detection algorithms. — [Zenodo 13985057](https://zenodo.org/records/13985057)
- The extracted Hanoi set is about 25 GB according to a loader note. — [water_benchmark_hub.leakdb docs](https://waterbenchmarkhub.readthedocs.io/en/dev/water_benchmark_hub.leakdb.html)
- The GitHub repository (generator + MATLAB UI, `CCWI-WDSA2018/main.m`) is EUPL-1.2. — [KIOS-Research/LeakDB](https://github.com/KIOS-Research/LeakDB)
- Citation: Vrachimis, Kyriakou, Eliades and Polycarpou (2018), "LeakDB: A benchmark dataset for leakage diagnosis in water distribution networks", WDSA/CCWI Joint Conference. Original DOI 10.5281/zenodo.1313116. — [WaterBenchmarkHub](https://waterfutures.github.io/WaterBenchmarkHub/benchmarks/KIOS-LeakDB.html)
- WaterBenchmarkHub exposes `compute_evaluation_score()` and can load LeakDB scenario configurations into EPyT-Flow for re-simulation. — [WaterBenchmarkHub LeakDB docs](https://waterbenchmarkhub.readthedocs.io/en/dev/water_benchmark_hub.leakdb.html); [PyPI water-benchmark-hub](https://pypi.org/project/water-benchmark-hub)

**Other datasets**
- **LeakTestbed** is a physical PVC pipe testbed. It is billed as the first fully labelled open dataset for leak detection and localisation in WDS, with 280 signals across leak types and no-leak cases. — [WaterBenchmarkHub LeakTestbed](https://waterfutures.github.io/WaterBenchmarkHub/benchmarks/LeakTestbed.html); [PMC10147960](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10147960/)
- **Hanoi multiple-leakage dataset** (Mendeley Data): 25,000 multiple-leak conditions simulated with EPANET emitters. Not part of LeakDB. — [Mendeley ncdkkp3bfg](https://data.mendeley.com/datasets/ncdkkp3bfg/1)
- Networks in the literature: Hanoi (32 nodes, 34 pipes), Anytown, L-Town, and real-data sources such as UK, Austin and Rhine. — [arXiv 2410.12461](https://arxiv.org/html/2410.12461)
- The survey states that real measurements are "frequently not publicly available", ground truth such as the exact start of a small leak is usually unknown, and class imbalance is severe, so research relies on simulation. — [arXiv 2410.12461](https://arxiv.org/html/2410.12461)
- The ATMN toolbox (PyPI `atmn`) offers parallel scenario generation and a LeakDB-compatible data-loading API. — [arXiv 2410.12461](https://arxiv.org/html/2410.12461); [PyPI atmn](https://pypi.org/project/atmn/)

### Inferences
- For AquaWatch, the most credible upgrade is a "BattLeDIM mode": load the 2018 L-Town SCADA (training, with the repair report as weak labels), run the detector on 2019, and score with the EPyT-Flow port of the official scoring. Its 5-minute data and its pressure, flow, level and AMR mix closely resemble a real utility export.
- LeakDB suits per-timestep classification metrics (precision, recall, F1, detection delay) because it has clean 0/1 labels at 30-minute resolution. Download only a subset of scenarios, because the full set is large.
- Hanoi and Net1 are small textbook networks. Results on them are weaker evidence of realism than results on L-Town.
- Typical evaluation axes in this literature are detection rate (true and false positives), time to detection, and localisation distance or correct link ID. BattLeDIM additionally used an economic score (see Gaps).

### Gaps
- The exact number of 2019 BattLeDIM leaks was not confirmed. 23 is frequently quoted (training knowledge), and the search could not verify it. The official economic scoring formula was not read; it is in the Rules PDF.
- C-Town, Net3, Modena and other EPANET example networks: no dataset pages were fetched. They are common EPANET/WNTR example `.inp` files without leak labels (unverified).
- Kaggle water-leak datasets were not reviewed. Their quality and licences are unknown.
- The licence of the WaterBenchmarkHub and EPyT-Flow packages themselves was not confirmed (MIT is believed but unverified).
- No public dataset with **real, utility-confirmed labelled leaks at network scale** was found. This should be stated as a limitation in any AquaWatch claims.

## Generating physically realistic synthetic data (EPANET 2.2, WNTR, LeakDB generator, EPyT-Flow)

### Takeaway
Replace the hand-made CSV with hydraulic simulation. Load an EPANET `.inp` network (or a small custom "Jamaica-like" network with 5 DMAs) in WNTR, switch to pressure-dependent demand, add leaks with `junction.add_leak(...)` (WNTRSimulator) or emitters (EpanetSimulator), randomise demand patterns, run at 5 to 15-minute steps, then add sensor noise, drift, gaps and flatlines in post-processing. EPyT-Flow is an alternative with built-in leak and sensor-fault events and benchmark loaders.

### Cited Findings
- WNTR (USEPA/Sandia) is a Python package to simulate and analyse WDN resilience, including adding disruptive events such as pipe leaks. It is licensed Revised BSD (BSD 3-clause). PyPI shows releases up to 1.5.0. — [PyPI wntr](https://pypi.org/project/wntr/); [OSTI DOE code 3818](https://www.osti.gov/doecode/biblio/3818); [GitHub USEPA/WNTR](https://github.com/USEPA/WNTR)
- Leak model (WNTRSimulator only): `node.add_leak(wn, area=..., start_time=..., end_time=...)` with times in seconds. Flow follows the Crowl and Louvar orifice form d = Cd·A·p^α·√(2/ρ), with default Cd = 0.75 and α fixed at 0.5. Pipe breaks use a large area, and a leak mid-pipe is done by splitting the pipe. — [WNTR hydraulics docs](https://usepa.github.io/WNTR/hydraulics.html)
- WNTRSimulator ignores emitter coefficients. With EpanetSimulator, leaks are modelled with emitters. — [WNTR hydraulics docs](https://usepa.github.io/WNTR/hydraulics.html)
- PDD: set `wn.options.hydraulic.demand_model = 'PDD'` (or 'DD'). Parameters are `required_pressure` (example 21.097 m / 30 psi), `minimum_pressure` (example 3.516 m / 5 psi) and `pressure_exponent` (default 0.5). Only the WNTRSimulator supports per-junction PDD values. — [WNTR hydraulics docs](https://usepa.github.io/WNTR/hydraulics.html)
- EpanetSimulator wraps the EPANET Toolkit; 2.2.0 is the default and supports DD and PDD (Global Gradient Algorithm, water quality). WNTRSimulator uses Newton-Raphson and Hazen-Williams only, has no water quality, and supports leaks and pause/restart. — [WNTR hydraulics docs](https://usepa.github.io/WNTR/hydraulics.html)
- EPyT-Flow is built on EPANET-PLUS (EPANET + EPANET-MSX). It offers pre-defined events (abrupt leakage, sensor faults), sensor configurations, global and local uncertainties, benchmark access with evaluation, a step-wise control environment and a REST API. — [EPyT-Flow docs](https://epyt-flow.readthedocs.io/en/latest/)
- The LeakDB generator (MATLAB, EUPL-1.2) produced "artificially created but realistic" scenarios with abrupt and incipient leaks, 30-minute labels and per-node and per-link outputs. — [KIOS-Research/LeakDB](https://github.com/KIOS-Research/LeakDB); [WaterBenchmarkHub](https://waterfutures.github.io/WaterBenchmarkHub/benchmarks/KIOS-LeakDB.html)

### Inferences
Below is a concrete recipe. The WNTR API calls are based on the fetched hydraulics docs. Treat the other parameter values as starting assumptions to tune.

1. **Network.** Start from `Net3.inp` or L-Town's `L-TOWN.inp` (CC BY 4.0), or build a small network with 5 DMAs whose inlets are metered pipes, giving one flow sensor per zone plus 2 or 3 pressure nodes.
2. **Demand patterns.** Use a 24-hour residential multiplier with morning and evening peaks and a night minimum around 0.3 to 0.5 of the mean. Add a weekday/weekend variant. Scale each junction's base demand by a random factor (e.g. ±10 to 20%) and add per-step multiplicative noise so zones are not identical.
3. **Intermittent supply** (relevant to Jamaica and Caribbean systems). Schedule source valve or pump controls on and off, e.g. supply 05:00 to 21:00. PDD mode is mandatory here, because demand-driven mode yields nonsense negative pressures when supply is cut.
4. **Leaks.** Use the WNTRSimulator with `add_leak(area, start_time, end_time)` for abrupt leaks. For incipient leaks, which add_leak's static area cannot model directly, run step-wise (pause/restart) and grow the area over time. For a background-leakage baseline, apply a small leak to many nodes. Record ground-truth labels (zone, node, start, end, area) in a separate events table.
5. **Simulation settings.** Use a hydraulic and reporting timestep of 300 s or 900 s and a duration of 30 to 365 days to capture weekly and seasonal cycles.
6. **Sensor layer (post-processing).** Sample only the sensor locations. Add Gaussian noise (e.g. ±0.5 to 1% of reading for flow, ±0.1 to 0.5 m for pressure), a slow linear or random-walk drift on some sensors, quantisation, random gaps (around 1 to 10%), flatline segments, spikes, and occasional timestamp shifts. These match the fault classes documented in the QA study above.
7. **Export** to long-format Parquet (`timestamp_utc, zone_id, sensor_id, quantity, value, unit, quality_flag`) and a labels table, mirroring BattLeDIM's split of SCADA files and Leakages CSVs.

Minimal WNTR sketch (API names per the WNTR docs; not executed this session):
```python
import wntr
wn = wntr.network.WaterNetworkModel("Net3.inp")
wn.options.hydraulic.demand_model = "PDD"
wn.options.hydraulic.required_pressure = 20.0   # m
wn.options.hydraulic.minimum_pressure = 3.5     # m
wn.options.time.duration = 30 * 24 * 3600
wn.options.time.hydraulic_timestep = 900
wn.options.time.report_timestep = 900
j = wn.get_node("123")
j.add_leak(wn, area=0.0005, start_time=10 * 24 * 3600, end_time=14 * 24 * 3600)
res = wntr.sim.WNTRSimulator(wn).run_sim()
pressure = res.node["pressure"]   # DataFrame indexed by seconds
flow = res.link["flowrate"]       # m3/s
leak = res.node["leak_demand"]    # ground-truth leak flow
```

### Gaps
- No published, sourced parameter ranges for sensor noise or drift magnitudes were found. The values above are engineering assumptions.
- WNTR's current release notes (1.5.x features, any incipient-leak support) were not read. Check the [WNTR GitHub](https://github.com/USEPA/WNTR) changelog.
- The LeakDB generator's exact leak-size distributions, demand uncertainty and noise settings were not documented on the pages fetched. They are likely in the 2018 paper.
- EPyT-Flow code examples, version and licence were not captured.
- No sources on Jamaican or Caribbean intermittent-supply demand patterns were researched.

## Time-series data handling: storage, resampling, timezones, validation

### Takeaway
At prototype scale, use Parquet (via pandas/pyarrow or DuckDB) with UTC timestamps and a long/tidy schema, and validate with pandera. TimescaleDB or InfluxDB only become worthwhile with live streaming ingestion. No sources were fetched for this section in this session, so the points below are unverified recommendations.

### Cited Findings
- No sources were fetched for this question within the tool budget. Everything below is in Inferences and Gaps.

### Inferences
- **Storage.** For datasets of a few GB or less, partitioned Parquet (by zone/month) queried with DuckDB or pandas is simplest and reproducible. TimescaleDB (a PostgreSQL extension with hypertables and continuous aggregates) suits a hosted demo that ingests live data. InfluxDB is a dedicated TSDB alternative.
- **Timezones.** Store everything in UTC and convert to local time only for display. Jamaica uses EST (UTC-5) with no daylight saving time. Imported US/European data or BattLeDIM files may need explicit tz handling, and night-flow windows (e.g. 02:00 to 04:00) must be computed in local time.
- **Resampling.** Align irregular reads to a fixed grid (`df.resample("15min")`), using mean for flow and pressure and sum for volumes or AMI consumption. Never forward-fill across long gaps; flag them instead. Keep a `quality_flag` column rather than silently imputing.
- **Validation.** Use pandera DataFrame schemas for column types, units, value ranges (e.g. pressure 0 to 150 m), monotonic unique timestamps per sensor, and maximum gap length. Flatline detection (rolling std == 0 over N steps) and spike detection (rolling z-score or Hampel filter) can be custom checks. Great Expectations is heavier and fits pipeline-level data docs. pandera fits a Python/pytest prototype better.

### Gaps
- TimescaleDB, InfluxDB, pandera and Great Expectations documentation and current versions (2026) were not fetched. Verify versions and licences before citing: pandera is MIT and TimescaleDB uses Apache-2 plus the Timescale License, but both are unverified.
- No utility-specific data-validation standard (e.g. an AWWA guide) was located.
