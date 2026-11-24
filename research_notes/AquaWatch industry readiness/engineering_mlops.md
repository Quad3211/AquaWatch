# Engineering and MLOps Standards: AquaWatch Jamaica, from Prototype to Production

Scope: software-engineering and MLOps practice for turning a small pandas + scikit-learn Isolation Forest prototype (Streamlit UI, a few pytest tests, a committed 3.7 MB joblib model, loose requirements.txt, no CI, CSV data in the repo, about 6 students) into a credible production system for near-real-time utility telemetry and alerting. Research date: 2026-11-21.

Note on evidence: items under "Cited Findings" were checked against sources this session. Tool recommendations that rest on general engineering knowledge and were not checked this session appear under "Inferences" and are labelled. Version numbers not checked this session are listed under "Gaps".

---

## 1. Project structure and packaging (pyproject.toml, uv/poetry, lock files, src layout, ruff, mypy/pyright, pre-commit)

### Takeaway
The current standard is a single `pyproject.toml` with a committed lock file. uv is the mature, actively released default, and GitHub Dependabot now updates `uv.lock` for both version and security updates. Add `uv lock --check` to CI to guard against lockfile drift.

### Cited Findings
- uv is under very active development. Release v0.12.22 was dated 2026-10-01, and v0.12.0 (2026-07-28) was a breaking release that changed pre-release preference and the rules for pylock.toml filenames. Recent releases (v0.12.20, v0.12.22) improved lockfile reuse and hash verification when relocking. This is from a search summary of the uv changelog and Renovate PR mirrors, not the official changelog read directly. — [uv CHANGELOG (GitHub raw)](https://raw.githubusercontent.com/astral-sh/uv/main/CHANGELOG.md); [newreleases.io uv 0.12.0](https://newreleases.io/project/github/astral-sh/uv/release/0.12.0); [Codeberg Renovate PR uv 0.12.22](https://codeberg.org/astrelion/gitmirror/issues/23)
- Dependabot version updates for uv became generally available on 2025-03-13. — [GitHub Changelog 2025-03-13](https://github.blog/changelog/2025-03-13-dependabot-version-updates-now-support-uv-in-general-availability/)
- Dependabot security updates added uv support in December 2025, so a vulnerable locked dependency now produces an alert and a fix PR. — [GitHub Changelog 2025-12-16](https://github.blog/changelog/2025-12-16-dependabot-security-updates-now-support-uv/)
- You enable it by adding `package-ecosystem: "uv"` to `dependabot.yml`. uv's docs say some use cases still don't work. — [uv docs: Dependabot integration](https://docs.astral.sh/uv/guides/integration/dependency-bots)
- Pitfall: Dependabot's uv ecosystem reportedly ignores `versioning-strategy` and always uses "increase". That can rewrite lower bounds in `pyproject.toml` and break CI. The author recommends running `uv lock --check` in CI. — [Classmethod dev blog](https://dev.classmethod.jp/en/articles/dependabot-uv-versioning-pitfall/)
- Dependabot only updates dependencies that are declared with version specifiers in pyproject.toml. — [example repo, kaihendry/pycallfoo](https://github.com/kaihendry/pycallfoo)

### Inferences
- **Minimum credible (week 1):** move from `requirements.txt` with loose ranges to `pyproject.toml` plus a committed `uv.lock`, and pin the Python version (`requires-python`, `.python-version`). Use a `src/aquawatch/` package layout so tests import the installed package and not the working directory. The repo already has `src/`, but it should become an importable package with `__init__.py` and be installed with `uv sync`. Poetry is a valid alternative. uv is the better fit here because it handles the Python version, the venv and the lock in one fast tool, and Dependabot supports it (general engineering judgement).
- **Linters and formatters (unverified this session):** Ruff as both linter and formatter, replacing flake8, black and isort. Add mypy or pyright for type checks, starting in non-strict mode on `src/` only. The pre-commit framework runs ruff, a ruff format check, trailing-whitespace and large-file checks (`check-added-large-files` would have blocked the 3.7 MB joblib), plus `uv lock --check`.
- For a 6-person student team, pre-commit plus a CI job running the same hooks is what keeps code consistent across members with different editors.

### Gaps
- I did not verify the current versions of Ruff, mypy, pyright or pre-commit as of November 2026. Check PyPI before pinning.
- I did not read the PyPA "src layout vs flat layout" guide this session (packaging.python.org). The recommendation above rests on general knowledge.

---

## 2. Testing (unit, data validation, property-based, model-metric regression, Streamlit AppTest, coverage)

### Takeaway
Industry ML testing goes well beyond unit tests. Google's ML Test Score defines 28 tests across Data, Model, Infrastructure and Monitoring. CD4ML names four test types: data validation, component integration, model-quality thresholds or ratchets, and slice and fairness checks. Pandera (0.30.x) covers schema tests, and Streamlit's native AppTest covers headless UI tests in pytest/CI.

### Cited Findings
- CD4ML (Thoughtworks, on martinfowler.com, 2019) lists four ML-specific test types: data validation (schema, ranges, feature logic); component integration (contract tests, and checks that exported models match the originals); model quality (threshold tests, or ratcheting against a baseline); and bias/fairness across data slices. — [Sato, Wider, Windheuser, CD4ML](https://martinfowler.com/articles/cd4ml.html)
- ML Test Score "Data 1: feature expectations are captured in a schema" and "Data 7: all input feature code is tested". The paper warns that feature bugs can be "almost impossible to detect" once they appear in both training and test data. — [Breck et al., ML Test Score (PDF)](https://storage.googleapis.com/gweb-research2023-media/pubtools/4156.pdf)
- ML Test Score "Model 5: a simpler model is not better" recommends regularly testing against a very simple baseline. "Model 6" requires quality to be sufficient on all important data slices. — [ML Test Score PDF](https://storage.googleapis.com/gweb-research2023-media/pubtools/4156.pdf)
- ML Test Score "Infra 1: training is reproducible". Training twice on the same data should ideally produce identical models, which enables diff-testing of refactors. — [ML Test Score PDF](https://storage.googleapis.com/gweb-research2023-media/pubtools/4156.pdf)
- Pandera's latest release found is 0.30.1 (2026-03-18). It supports pandas, polars, pyspark, ibis and pyarrow backends, and pandas use goes through `pip install 'pandera[pandas]'` / `import pandera.pandas`. — [CERN PyPI mirror: pandera](https://simple-repository.app.cern.ch/project/pandera); [pandera docs](https://pandera.readthedocs.io/en/latest/)
- Pandera 0.18.1 added `PANDERA_VALIDATION_DEPTH`, which selects schema-only checks, data checks, or both. — [pandera discussion #1522](https://www.github.com/unionai-oss/pandera/discussions/1522)
- Streamlit's native `streamlit.testing.v1.AppTest` simulates user input and inspects rendered output. Its examples use pytest. Constructors are `from_file` (recommended), `from_string` and `from_function`. It supports secrets, session state and query params, has no native multipage support, and has a dedicated "Automate your tests" CI guide. — [Streamlit app testing docs](https://docs.streamlit.io/develop/concepts/app-testing); [AppTest API](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.AppTest); [Beyond the basics](https://docs.streamlit.io/develop/concepts/app-testing/beyond-the-basics)

### Inferences
- **Recommended test pyramid for AquaWatch:**
  1. **Unit tests** for feature engineering (rolling windows, flow/pressure deltas, timestamp handling, missing-reading logic). This is ML Test Score Data 7.
  2. **Data contract tests** with a pandera `DataFrameSchema` for raw telemetry: column types, non-negative flow, plausible pressure ranges, monotonic timestamps per sensor, null-rate limits. Run the same schema at training and at ingestion/scoring time (ML Test Score Data 1 / Monitor 2). Great Expectations is the heavier alternative. Pandera is lighter and more Pythonic for a student team (judgement).
  3. **Property-based tests** with Hypothesis (unverified this session) for invariants such as "the scoring function returns one score per row", "output does not depend on row order", "no NaN scores for valid input", and "scaling invariance where expected".
  4. **Model regression tests:** a small frozen labelled or synthetic-injected anomaly set, with assertions on precision@k / recall on injected leaks, and checks that scores for a fixed golden input match within tolerance. Also compare against a simple baseline such as a z-score or rolling-median threshold (ML Test Score Model 5). Isolation Forest is unsupervised, so injecting synthetic anomalies (step changes, flat-lines, spikes, night-flow increase) into clean data is the practical way to get metrics.
  5. **Reproducibility test:** train twice with a fixed `random_state` and assert identical predictions (Infra 1).
  6. **UI smoke tests** with Streamlit AppTest: the app loads without exceptions, the key widgets render, and an upload/filter path works.
  7. **Coverage target (judgement):** 70-80% line coverage on `src/` via pytest-cov, enforced in CI with `--cov-fail-under`. Exclude the Streamlit script from the threshold and cover it with AppTest instead. Coverage is a floor. The ML-specific tests above matter more.

### Gaps
- I did not verify current Hypothesis or Great Expectations (GX Core) versions or GX's current OSS packaging this session.
- I found no authoritative industry "standard" coverage percentage for ML projects. 70-80% is a common convention, not a cited standard.

---

## 3. CI/CD with GitHub Actions (lint, test, type-check, security scan, reproducible builds, Docker)

### Takeaway
Every maturity model makes automated builds and tests on version-controlled code the first rung. Microsoft Level 1 is "builds are automated, application code has automated tests, code is version controlled." Supply-chain scanning matters for ML specifically: OWASP ML06 covers ML supply-chain attacks.

### Cited Findings
- Microsoft MLOps Level 1 ("DevOps but no MLOps"): builds are automated, application code has automated tests, and code is version controlled. Model results are still difficult to trace and reproduce at that level. — [Microsoft Learn: MLOps maturity model (updated 2026-06-03)](https://learn.microsoft.com/azure/architecture/ai-ml/guide/mlops-maturity-model)
- Google's level 2 says rapid and reliable pipeline updates need a robust automated CI/CD system. — [Google Cloud: MLOps continuous delivery and automation pipelines](https://docs.cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning)
- OWASP ML06:2023 "ML Supply Chain Attacks": attackers target the ML supply chain, including open-source dependencies. Mitigations include keeping dependencies current and using dependency-checking tools. — [OWASP ML06:2023](https://owasp.org/www-project-machine-learning-security-top-10/docs/ML06_2023-AI_Supply_Chain_Attacks.html)
- Australia's cyber agency recommends an AI Bill of Materials (AIBOM) alongside an SBOM for AI/ML systems. — [cyber.gov.au AI/ML supply chain guidance (PDF)](https://www.cyber.gov.au/sites/default/files/2026-10/Artificial%20intelligence%20and%20machine%20learning%20%28March%202026%29.pdf)
- Dependabot supports uv for version and security updates (see section 1). — [GitHub Changelog](https://github.blog/changelog/2025-12-16-dependabot-security-updates-now-support-uv/)
- Streamlit documents running AppTest in CI. — [Streamlit: Automate your tests](https://docs.streamlit.io/develop/concepts/app-testing/automate-tests)

### Inferences
- **Minimum credible CI workflow** (`.github/workflows/ci.yml`, on push and pull_request): checkout, `astral-sh/setup-uv`, `uv sync --locked`, `uv lock --check`, `ruff check`, `ruff format --check`, `mypy src`, `pytest --cov` (including pandera, AppTest and model regression tests), and `pip-audit` against the locked deps. Protect `main` with required status checks and at least one PR review. The team already works through PRs, so this is cheap to add.
- **Security layer (free for public repos; unverified this session):** Dependabot (pip/uv plus `github-actions` ecosystems), CodeQL default setup for Python, secret scanning with push protection, and pip-audit in CI. Pin third-party Actions to a commit SHA or major tag.
- **Reproducible builds:** the lock file plus a pinned Python version plus a Docker image (`python:3.x-slim` base, `uv sync --frozen --no-dev`, non-root user). Build the image in CI and push it to GitHub Container Registry (GHCR) on tagged releases. Optionally generate an SBOM (for example with syft or `docker buildx --sbom`) to meet the AIBOM/SBOM guidance.
- **CD:** at the student stage, deploy on a tag to a free or low-cost host. At production, deploy through environments with manual approval (GitHub Environments).
- A separate, scheduled `train.yml` workflow can retrain, evaluate against the regression gates, and register the model. It moves the project toward Google Level 1 / Microsoft Level 2.

### Gaps
- I did not verify the current versions of pip-audit, CodeQL action, `setup-uv` action or the Docker base images this session.
- I did not verify the GitHub Advanced Security free-tier rules for private repos in 2026. Features differ between public and private repos.

---

## 4. Model and data versioning (MLflow, DVC, registry, why not commit joblib, skops, experiment tracking, reproducibility)

### Takeaway
Do not commit the joblib/pickle model to Git. Pickle-family formats can execute arbitrary code on load, and they are tied to the exact scikit-learn, numpy and scipy versions. Store models as versioned artifacts in DVC remote storage or an MLflow registry using aliases such as `@champion`, prefer skops.io for safer loading, and record the environment alongside each model.

### Cited Findings
- scikit-learn docs: pickle, joblib and cloudpickle all use the pickle protocol, so loading can execute arbitrary code. They assume you absolutely trust the file's source. — [scikit-learn: Model persistence](https://scikit-learn.org/stable/model_persistence.html)
- skops.io avoids pickle and only loads files whose types and function references are trusted. `skops.io.get_untrusted_types` lets you review unknown types before passing the trusted ones to `load`. — [scikit-learn: Model persistence](https://scikit-learn.org/stable/model_persistence.html)
- The docs call ONNX the most secure option for inference-only serving, but not every model or estimator is supported. — [scikit-learn: Model persistence](https://scikit-learn.org/stable/model_persistence.html)
- None of these persistence methods support loading a model trained with a different version of scikit-learn, and possibly numpy/scipy. — [scikit-learn: Model persistence](https://scikit-learn.org/stable/model_persistence.html)
- OWASP ML06 classes tampered or malicious ML artifacts and dependencies as supply-chain attacks. — [OWASP ML06:2023](https://owasp.org/www-project-machine-learning-security-top-10/docs/ML06_2023-AI_Supply_Chain_Attacks.html)
- CD4ML: DVC stores large files outside Git, records checksums in small metadata files committed to Git, tracks the pipeline dependency graph and commands so others can reproduce results, and pushes and pulls models to external storage. A changed checksum can trigger a pipeline run. CD4ML notes that DVC does not fully solve provenance or schema evolution. — [CD4ML](https://martinfowler.com/articles/cd4ml.html)
- MLflow Model Registry aliases are named references to a model version, for example `models:/MyModel@champion`. Databricks recommends aliases for managing deployment status. The workflow guide covers setting, updating and deleting aliases. — [MLflow Model Registry docs](https://mlflow.org/docs/latest/ml/model-registry); [MLflow 3.3.2 registry workflow](https://mlflow.org/docs/3.3.2/ml/model-registry/workflow); [Databricks: models in UC](https://docs.databricks.com/aws/en/mlflow/models-in-uc)
- MLflow 3 introduced `LoggedModel` and `mlflow.create_external_model()`, and its default registry URI on Databricks is `databricks-uc`. That last point applies to Databricks. OSS users run their own tracking server. — [Databricks MLflow 3 docs](https://docs.databricks.com/aws/en/mlflow/models-in-uc)
- Microsoft Level 2 ("Automated training") requires centralized tracking of training performance, model management, version control for both training code and models, and tracked experiment results. — [Microsoft Learn: MLOps maturity model](https://learn.microsoft.com/azure/architecture/ai-ml/guide/mlops-maturity-model)
- ML Test Score Infra 7 says serving models can be rolled back quickly and safely, and operators should practise rollback. — [ML Test Score PDF](https://storage.googleapis.com/gweb-research2023-media/pubtools/4156.pdf)

### Inferences
- **Immediate actions:**
  1. `git rm --cached` the joblib, add `*.joblib` / `models/` to `.gitignore`, and make the model a build output of `train.py`.
  2. Move the CSV into DVC with a free remote (Google Drive, a DagsHub free tier, or an S3-compatible bucket), or at least Git LFS.
  3. Save the model with `skops.io.dump`, plus a metadata JSON holding the training data hash, git SHA, `random_state`, sklearn/numpy versions, hyperparameters and evaluation metrics.
  4. Set `random_state` everywhere, including the IsolationForest and any splitting.
- **Experiment tracking and registry:** MLflow OSS with a local SQLite backend (or a small hosted server), logging params, metrics and the skops artifact for each training run, with aliases `@champion` / `@challenger`. Serving loads `models:/aquawatch-iforest@champion`, so rollback means re-pointing the alias (Infra 7). The combination "DVC for data, MLflow for runs/registry" is common and free. A team that wants fewer tools can use DVC alone (`dvc.yaml` stages plus `dvc exp`).
- Isolation Forest artifacts are small and simple, so skops coverage should be fine. ONNX (via skl2onnx) is an option if a non-Python serving runtime is ever needed (judgement; skl2onnx IsolationForest support not verified this session).

### Gaps
- I did not verify the exact current MLflow OSS version (late 2026) or DVC version. The newest MLflow docs found were 3.3.x.
- I did not confirm the current skops version, or that it supports sklearn 1.8/1.9 IsolationForest. Check skops release notes.

---

## 5. ML maturity frameworks (ML Test Score, Google MLOps levels, Hidden Technical Debt, Microsoft maturity)

### Takeaway
Use the ML Test Score as the scorecard and the Google/Microsoft levels as the roadmap. AquaWatch is currently at ML Test Score 0 ("more of a research project") and Google Level 0 / Microsoft Level 0-1. A realistic student target is an ML Test Score of 1-2 and Microsoft Level 2 ("automated training").

### Cited Findings
- **ML Test Score (Breck, Cai, Nielsen, Salib, Sculley; IEEE Big Data 2017)** defines 28 tests in four sections of seven. — [Google Research page](https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/); [PDF](https://storage.googleapis.com/gweb-research2023-media/pubtools/4156.pdf)
  - *Data:* schema for feature expectations; all features beneficial; no feature too costly; features meet meta-level requirements; privacy controls in the pipeline; new features can be added quickly; all input feature code tested.
  - *Model:* model specs reviewed and checked in; offline and online metrics correlate; hyperparameters tuned; impact of staleness known; a simpler model is not better; quality sufficient on important slices; tested for inclusion.
  - *Infrastructure:* training reproducible; model specs unit tested; ML pipeline integration tested; model quality validated before serving; model debuggable on a single example; canary before serving; serving models can be rolled back.
  - *Monitoring:* dependency changes notify; data invariants hold for inputs; training and serving not skewed; models not too stale; models numerically stable; no regression in computing performance; no regression in prediction quality on served data.
  - *Scoring:* 0.5 point per test run manually with documented and distributed results, 1 point if automated and repeated. Each section is summed, and the final score is the **minimum** of the four section scores.
  - *Interpretation:* 0 = more a research project than a productionized system; (0,1] = not totally untested, but possibly serious holes in reliability; (1,2] = first pass at productionization; (2,3] = reasonably tested, with more automation possible; (3,5] = strong automated testing and monitoring, appropriate for mission-critical systems; >5 = exceptional.
  - Across several dozen Google teams surveyed, no test was implemented by more than 80% of teams.
- **Google MLOps levels:** Level 0 is a manual, script-driven, interactive process, with ML disconnected from ops and no active performance monitoring. Level 1 automates the ML pipeline for continuous training, deploying a training pipeline that runs recurrently and not just a model. Level 2 adds automated CI/CD of the pipeline itself. Last reviewed 2024-08-28. — [Google Cloud architecture doc](https://docs.cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning)
- **Microsoft MLOps maturity model (updated 2026-06-03)** has five levels. 0 No MLOps (manual builds, deployments, testing and training; the end result is a single model file handed off manually); 1 DevOps but no MLOps (automated builds, app-code tests, version control); 2 Automated training (training automated, experiments tracked centrally, model management, training code and models version controlled, scheduled or event-driven retraining); 3 Automated model deployment (CI/CD-managed releases, A/B testing, full traceability from deployment back to data); 4 Full MLOps automated operations (drift or regression signals trigger retraining, verbose centralized metrics, policy-based promotion). Microsoft treats the levels as a continuum. — [Microsoft Learn](https://learn.microsoft.com/azure/architecture/ai-ml/guide/mlops-maturity-model)
- **Hidden Technical Debt in ML Systems (Sculley et al., NIPS 2015)** names ML-specific debt: boundary erosion, entanglement, hidden feedback loops, undeclared consumers, data dependencies, configuration debt, changes in the external world, glue code and pipeline jungles. Pipeline jungles grow organically in data preparation as sources are added. — [NeurIPS proceedings PDF](https://proceedings.neurips.cc/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf); [Google Research page](https://research.google/pubs/hidden-technical-debt-in-machine-learning-systems/); [acolyer summary](https://blog.acolyer.org/2016/02/29/machine-learning-the-high-interest-credit-card-of-technical-debt/)
- A secondary summary claims mature systems may be "at most 5%" ML code. That figure is from a blog estimate, not verified in the paper text. — [acolyer summary](https://blog.acolyer.org/2016/02/29/machine-learning-the-high-interest-credit-card-of-technical-debt/)

### Inferences
- **AquaWatch today:** Microsoft Level 0. Its own text, "end result is typically a single model file … handed off manually", matches the committed joblib. ML Test Score is 0 because the Monitoring and Infra sections are essentially 0, and the minimum rule means the weakest section sets the score.
- **Student-achievable target:** ML Test Score of about 1-2 (at least 1-2 points in every section), Microsoft Level 2, Google Level 0→1. Because of the minimum rule, the team should spread effort across all four sections and not perfect testing while ignoring monitoring. That fits a 6-person team: assign one owner per ML Test Score section.
- **Most relevant debt risks for AquaWatch:** data dependencies (utility SCADA/AMI feeds changing units or sampling silently, which is Monitor 1), changes in the external world (seasonality, drought, network repairs), configuration debt (thresholds and contamination parameters scattered in code), and hidden feedback loops (if crews only inspect flagged sites, labels become biased).

### Gaps
- I did not consult the earlier 2016 NIPS workshop version of the ML Test Score, nor any newer Google follow-up rubric.

---

## 6. Production architecture for streaming telemetry anomaly detection

### Takeaway
For utility telemetry (minutes-level readings from flow and pressure meters), a micro-batch architecture is the realistic production design: ingest, store in a time-series DB, score on a schedule every 5-15 minutes behind a FastAPI/worker service, deduplicate into incidents, alert, and review in a case workflow. CD4ML's "model as a separate service" pattern applies. WhatsApp alerting is viable but now costs money per utility message (from 2026-10-01), so SMS/email fallbacks and alert deduplication matter.

### Cited Findings
- CD4ML describes three model-serving patterns: embedding the model in the consuming app, deploying it as a separate service, or publishing the model as data the app ingests at runtime. — [CD4ML](https://martinfowler.com/articles/cd4ml.html)
- Since 2025-07-01, WhatsApp Business Platform charges per template message. Twilio adds $0.005 per message, and Meta's utility/authentication rates start around $0.0034 per message and vary by country. — [Twilio WhatsApp pricing](https://www.twilio.com/en-us/whatsapp/pricing); [Twilio notice July 2025](https://support.twilio.com/hc/en-us/articles/30304057900699-Notice-Changes-to-WhatsApp-s-Pricing-July-2025); [Meta pricing docs](https://developers.facebook.com/docs/whatsapp/pricing)
- From 2026-10-01, Meta again charges for all utility messages, including those sent inside an open 24-hour customer service window. Twilio's general pricing page may still show the older "free in window" rule. — [Twilio notice: WhatsApp pricing changes Oct 2026](https://support.twilio.com/hc/en-us/articles/53100480177819-Notice-Changes-to-WhatsApp-s-Pricing-October-2026)
- WhatsApp reach in Jamaica: I found no current national penetration figure. A 2016 Office of the Children's Advocate survey of 514 students found WhatsApp the most popular app among Jamaican teens. Facebook Messenger (a different app) had about 948,000 users in Jamaica in April 2026. A study cited by Radio Jamaica says 70% of the electorate is reachable via social media. — [Jamaica Observer 2016](https://www.jamaicaobserver.com/2016/06/27/whatsapp-youtube-most-used-social-media-among-teens); [NapoleonCat Messenger Jamaica](https://stats.napoleoncat.com/messenger-users-in-jamaica/2026/04/); [Radio Jamaica](https://radiojamaicanewsonline.com/local/study-reveals-70-of-jamaican-electorate-reachable-via-social-media)
- Microsoft Level 3 requires full traceability from deployment back to data, and A/B testing of model performance. ML Test Score Infra 6 recommends canarying models before they enter production. — [Microsoft Learn](https://learn.microsoft.com/azure/architecture/ai-ml/guide/mlops-maturity-model); [ML Test Score PDF](https://storage.googleapis.com/gweb-research2023-media/pubtools/4156.pdf)

### Inferences (engineering judgement; tool facts not verified this session)
- **Reference architecture (staged):**
  1. **Ingestion:** MQTT (for example the Eclipse Mosquitto or EMQX open-source broker) suits low-bandwidth field devices and cellular IoT, which is common for Caribbean utilities. Kafka or Redpanda are overkill for a student team until volumes are large. Early on, the utility will likely provide batch exports or a SCADA historian API. Start with a scheduled pull or an SFTP/CSV drop, and design the ingestion interface so MQTT can be added later.
  2. **Storage:** TimescaleDB (a PostgreSQL extension, which keeps one familiar SQL database for telemetry, alerts and cases) or InfluxDB. Raw readings go in a hypertable, with aggregates in continuous aggregates.
  3. **Scoring:** batch or micro-batch scoring (every 5-15 min via cron, APScheduler or Prefect) is simpler, cheaper and easier to test than true streaming. Isolation Forest on rolling-window features doesn't benefit from per-event streaming. Move to streaming (for example Bytewax or Faust, or Kafka consumers) only if latency requirements demand it.
  4. **Serving API:** FastAPI service (`/score`, `/health`, `/model-info`) loading the `@champion` model, with Pydantic request schemas mirroring the pandera schema. The "separate service" pattern lets Streamlit, Grafana and alerting share one model.
  5. **Event management:** convert raw anomaly scores into incidents. Apply a threshold, require N consecutive anomalous windows (hysteresis), deduplicate per sensor or DMA, suppress during known maintenance windows, and give each incident a state machine (open → acknowledged → investigating → resolved/false-positive). Operator outcomes become the labels for later evaluation and close the feedback loop CD4ML describes.
  6. **Alert delivery:** a channel abstraction (email via SMTP/SES/SendGrid free tier, SMS, and WhatsApp via Twilio or Meta Cloud API with pre-approved utility templates). WhatsApp is now charged per utility message, so send digests and escalations, not every anomaly, and keep email or SMS as fallback. Local SMS aggregators and the cost of Digicel/Flow routes would need checking.
  7. **Dashboards:** Grafana (OSS) on TimescaleDB for operational time-series views and alert rules. Keep Streamlit for analyst exploration, model explanation and the case review UI. Dash is an alternative to Streamlit but offers little extra here. Grafana is the industry norm for operations telemetry dashboards.
  8. **Deployment:** Docker Compose (broker, TimescaleDB, API, scheduler/worker, Grafana, Streamlit) on a single VM is enough for a pilot.

### Gaps
- I found no reliable 2025-2026 WhatsApp penetration statistic for Jamaica. DataReportal/GWI "Digital 2026: Jamaica" would be the source to check.
- I did not research Jamaican SMS gateway providers or costs (Digicel, Flow), or Jamaica's Data Protection Act 2020 obligations for storing customer phone numbers. Both are relevant.
- I did not research the National Water Commission (NWC) telemetry systems or data formats (SCADA/AMI vendor).

---

## 7. Monitoring (data drift, concept drift, sensor health, alert volume, retraining policy, observability)

### Takeaway
Monitor four layers: inputs (schema, data invariants, sensor health), model outputs (score distribution drift, alert volume), outcomes (operator-confirmed precision), and system (latency, errors, staleness). Evidently (Apache-2.0, 0.7.x) handles drift reports. NannyML's label-free performance estimation (CBPE) targets classifiers, so it fits an unsupervised Isolation Forest poorly.

### Cited Findings
- ML Test Score monitoring tests: dependency changes notify; data invariants hold in training and serving inputs ("the first line of defense"); training and serving features compute the same values (compare min, max, mean and missing fraction, with tuned alert thresholds to limit false positives); models not too stale; numerical stability; computing performance not regressed; prediction quality on served data not regressed. — [ML Test Score PDF](https://storage.googleapis.com/gweb-research2023-media/pubtools/4156.pdf)
- Monitor 1 rationale: partial outages, version upgrades and other source-system changes can radically change a feature's meaning without producing values strange enough to trigger other monitoring. — [ML Test Score PDF](https://storage.googleapis.com/gweb-research2023-media/pubtools/4156.pdf)
- Evidently is open source (Apache-2.0) with 100+ built-in metrics, from data drift detection to LLM judges. `DataDriftPreset()` is the basic drift example. Recent official releases include 0.7.10 and 0.7.17. A third-party directory lists 0.7.23 (2026-09-11), unverified against PyPI. — [Evidently README](https://cdn.jsdelivr.net/gh/evidentlyai/evidently@main/README.md); [Evidently blog](https://www.evidentlyai.com/blog-category/evidently); [Enterprise DNA directory](https://enterprisedna.co/directories/open-source/evidently); [PyPI](https://pypi.org/project/evidently/)
- NannyML's CBPE estimates performance without labels using calibrated probabilities. It supports binary and multiclass classifiers, and it is weakened by calibration deterioration under shift. Research extensions (M-CBPE, PAPE) exist, and whether they ship in the library is unconfirmed. — [NannyML docs](https://github.com/NannyML/nannyml/blob/v0.6.0/docs/how_it_works/performance_estimation.rst); [arXiv 2401.08348](https://arxiv.org/html/2401.08348v3)
- Microsoft Level 4: drift or regression signals trigger automatic retraining, the deployed model emits verbose centralized metrics, and promotion is policy-based. Google Level 0 is characterised by a lack of active performance monitoring. — [Microsoft Learn](https://learn.microsoft.com/azure/architecture/ai-ml/guide/mlops-maturity-model); [Google Cloud](https://docs.cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning)
- CD4ML recommends logging model inputs, outputs, the decisions taken with predictions, and user feedback, to close the loop. Its example uses the EFK stack. — [CD4ML](https://martinfowler.com/articles/cd4ml.html)

### Inferences
- **Sensor health is separate from anomaly detection.** It must be monitored first, or the model will report dead or stuck meters as "leaks". Rule-based checks: missing-data rate per sensor, stale last-seen timestamp, flat-line (zero variance over N hours), out-of-physical-range, sudden unit-scale jumps (Monitor 1), clock drift and duplicate timestamps. Route these to a "maintenance" alert channel, not the "anomaly" channel.
- **Drift:** run Evidently weekly (scheduled GitHub Action or cron) comparing recent feature windows with the training reference. Save HTML reports as artifacts and push summary metrics to the DB/Grafana. For an unsupervised model, watch the **anomaly-score distribution** and **alert rate per sensor per week**. A sudden jump usually means data or pipeline breakage. A slow creep is real-world change (seasonality, network modification).
- **Concept drift / quality:** with no ground truth, use operator case outcomes (confirmed vs false-positive) as delayed labels and track precision of alerts over time (Monitor 7). NannyML CBPE does not directly apply to Isolation Forest scores (judgement based on CBPE's classifier/calibration requirement).
- **Alert-volume monitoring:** set an alert budget (for example a maximum of N alerts per day per region). Exceeding it is itself a page to the engineering team, which protects against alert fatigue and WhatsApp costs.
- **Retraining policy (start manual, then scheduled):** retrain monthly or quarterly on a rolling window of data, excluding confirmed incident periods. Retrain only through the CI training workflow. Promote to `@champion` only if the regression tests pass (injected-anomaly recall, alert-rate within band, no worse than baseline). Keep the previous champion for one-click rollback. Event-triggered retraining (Microsoft Level 4) is out of scope for a student team.
- **Observability (unverified tool facts):** structured JSON logs (Python `logging` + `structlog`), Prometheus metrics from FastAPI (request latency, scoring duration, rows scored, model version, data freshness), Grafana dashboards, and OpenTelemetry instrumentation for FastAPI if tracing is needed. A model-staleness gauge (time since training) implements Monitor 4.

### Gaps
- I did not verify current NannyML maintenance status or version (the company's commercial status may have changed).
- I did not verify current OpenTelemetry Python or Prometheus client versions.
- I found no published source on drift thresholds suited to water-utility telemetry. Thresholds will need empirical tuning.

---

## 8. Documentation (ADRs, model cards, runbooks)

### Takeaway
Documentation is part of maturity. The ML Test Score gives half credit only when manual tests are "documented and distributed", and rollback must be a practised procedure. Minimum: README with architecture, ADRs for key decisions, a model card for the Isolation Forest, and runbooks for alert triage and rollback.

### Cited Findings
- ML Test Score: half a point is awarded for running a test manually only when the results are documented and distributed. — [ML Test Score PDF](https://storage.googleapis.com/gweb-research2023-media/pubtools/4156.pdf)
- ML Test Score Infra 7: rollback is an emergency procedure, so operators should practise it. Infra 5: there should be an easy, well-documented process for feeding a single example through the model for debugging. — [ML Test Score PDF](https://storage.googleapis.com/gweb-research2023-media/pubtools/4156.pdf)
- Microsoft Level 0 is characterised by a single model file handed off manually and a scoring script that is not version controlled. Documentation and traceability increase with level. — [Microsoft Learn](https://learn.microsoft.com/azure/architecture/ai-ml/guide/mlops-maturity-model)

### Inferences
- **ADRs** (Michael Nygard format, in `docs/adr/NNNN-title.md`): uv over poetry, skops over joblib, TimescaleDB vs InfluxDB, batch vs streaming scoring, WhatsApp vs SMS alerting, DVC/MLflow choice. Each is short: context, decision, consequences. ADRs suit a rotating student team because they preserve reasoning across semesters.
- **Model card** (Mitchell et al. 2019 format; not fetched this session): intended use (decision support for NWC/utility staff, not automatic shut-off), training data period and sensors, features, contamination parameter, evaluation on injected anomalies and operator-confirmed incidents, known failure modes (seasonality, sensor faults, new DMAs), ethical and operational considerations (false alarms send crews out; missed leaks waste water), owners and retraining cadence.
- **Datasheet / data card** for the telemetry dataset: source, units, sampling rate, known gaps, privacy (customer meter IDs are personal data under Jamaica's Data Protection Act — unverified).
- **Runbooks** (`docs/runbooks/`): "Alert received: how to triage", "Sensor offline", "Alert storm / volume spike", "Roll back model to previous champion", "Retrain and promote model", "Ingestion pipeline down". Rehearse rollback once per semester (Infra 7).
- Also: `CONTRIBUTING.md` (branching, PR checklist, how to run checks locally), `SECURITY.md`, CODEOWNERS, and PR/issue templates.

### Gaps
- I did not fetch the Model Cards paper (Mitchell et al., 2019), Google's Model Card Toolkit, the Nygard ADR post or the adr.github.io templates this session. These are well-known primary sources the report writer can cite as such, but they were not checked.

---

## Consolidated prioritised checklist (synthesis; justification cross-references sections above)

**Tier 0: Minimum credible (1-2 weeks; ML Test Score toward 0.5-1, Microsoft Level 1)**
1. `pyproject.toml` + `uv.lock` + pinned Python. Delete the loose `requirements.txt` or generate it from the lock (S1).
2. Remove the committed joblib from Git and `.gitignore` model artifacts. Rebuild via `train.py` with a fixed `random_state` (S4; sklearn pickle-security and version-lock warnings).
3. Ruff (lint + format) + pre-commit (including the large-file check) (S1).
4. GitHub Actions CI: lint, type-check (lenient), pytest, `uv lock --check`, pip-audit. Branch protection on `main` (S3; Microsoft L1).
5. Dependabot (uv + github-actions), CodeQL, secret scanning (S3; OWASP ML06).
6. pandera schema for telemetry plus unit tests for feature code (S2; ML Test Score Data 1, Data 7).
7. README architecture section plus the first ADRs (S8).

**Tier 1: Credible ML engineering (a semester; ML Test Score 1-2, Microsoft Level 2, Google Level 0→1)**
8. Persist the model with skops plus metadata JSON. Data in DVC (S4).
9. MLflow tracking and registry with `@champion`/`@challenger` aliases, and a rollback procedure (S4; Infra 7).
10. Model regression tests on injected anomalies, a baseline comparison and a reproducibility test (S2; Model 5, Infra 1, Infra 4).
11. Streamlit AppTest smoke tests, Hypothesis property tests, coverage at or above 70% on `src/` (S2).
12. Dockerfile plus Compose, with the image built in CI and published to GHCR on tags (S3).
13. Model card, runbooks, data card (S8).
14. Scheduled training workflow with quality gates before promotion (S3/S4; Google L1, Microsoft L2).

**Tier 2: Production pilot (ML Test Score 2-3, Microsoft Level 2→3)**
15. Ingestion service (scheduled pull, then MQTT), TimescaleDB, micro-batch scoring worker, FastAPI scoring service (S6).
16. Sensor-health rules separated from the anomaly model, plus incident deduplication and a case workflow that captures operator labels (S6, S7).
17. Alert channels: email plus SMS plus WhatsApp utility templates, with an alert budget, aware of per-message cost from 2026-10-01 (S6).
18. Grafana operations dashboards. Evidently drift reports on a schedule. Prometheus/OTel metrics, a model staleness gauge, alert-volume monitoring (S7).
19. Shadow or canary a new model before promotion, and practise rollback (Infra 6, Infra 7).

**Tier 3: Mature (beyond the student scope)**
20. Drift- or regression-triggered retraining, policy-based automated promotion, A/B testing, full lineage from deployment back to data (Microsoft L3-L4; Google L2).
