# Stage 0 scope lock — Team Lead

**Owner:** Nathanael Coote (Team Lead)  
**Date locked:** 18 November 2026  
**Repo:** https://github.com/Quad3211/AquaWatch

## Stage 0 goal

Prove the idea with a **test product** before any “real product” build:

> Can an AI model use flow and pressure patterns to flag unusual service-zone readings and help an operations team decide which zones to investigate first?

## In scope (Phase 1 / Stage 0–1)

- Synthetic CSV input (`data/AquaWatch_Synthetic_Sensor_Data.csv`)
- Zone/hour normal profile
- Simple flow rule baseline (25%)
- Isolation Forest on flow/pressure deviations
- Ranked alerts with short reason + next step
- Streamlit UI: overview, alerts, chart, metrics
- CLI evaluation script matching pitch metrics
- Manual checklist (Mahatma) + automated smoke tests
- Pitch deck + research notes in `docs/`

## Out of scope until Stage 0 passes

Do **not** start these yet:

- Live NWC / Miya telemetry or SCADA integration
- Database, user accounts, cloud hosting
- Mobile app
- Claiming confirmed leaks, pipe location, or real water savings
- Replacing NWC/Miya field programmes

## Honest product claim

**Say:** “AquaWatch flags unusual patterns for investigation.”  
**Do not say:** “AquaWatch confirms leaks” or “outperforms NWC/Miya in the field.”

## Stage 0 done when

1. `pip install -r requirements.txt` works for the team  
2. `python scripts/AquaWatch_Evaluate.py` prints rule vs AI metrics  
3. `python -m streamlit run app.py` loads the synthetic CSV  
4. Work split is assigned (`TEAM_WORK_SPLIT.md`)  
5. Code is on GitHub for the group to clone  

## Next stage gate

Only move to Stage 1 polish / Phase 2 architecture after Mahatma’s checklist passes on a stable build.
