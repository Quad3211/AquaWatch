# Mahatma — Phase 1 manual test checklist

**Owner:** Mahatma Williams  
**Backup:** Nathanael Coote  

This is your main job. You do **not** need to write model or Streamlit code.

Before pitch day, every box should be checked on the latest build.

## Setup (once)

- [ ] Can open the project folder
- [ ] Ran `pip install -r requirements.txt` (or teammate confirmed it for you)
- [ ] Can start the app with `python -m streamlit run app.py`
- [ ] App opens in the browser without an error page

## Core scenarios

- [ ] **Load data:** Overview tab shows about 1,680 rows and 5 zones
- [ ] **Alerts appear:** Alerts tab is not empty on the synthetic CSV
- [ ] **Alert has a reason:** At least one row shows a short reason + next step
- [ ] **Zone 03 chart:** Chart tab → Zone 03 shows flow and pressure lines
- [ ] **Metrics visible:** Metrics tab shows Simple flow rule and Isolation Forest
- [ ] **Honest claim:** App text says alerts are for investigation, not confirmed leaks

## Demo path (pitch day)

- [ ] Can tell the story in ≤ 2 minutes: normal pattern → unusual pattern → alert
- [ ] Backup screenshots saved (Overview, Alerts, Chart, Metrics)
- [ ] If live app fails, can present from screenshots + pitch deck

## Bug notes (copy/paste as needed)

| Date | What I clicked | What I expected | What happened | Screenshot |
|---|---|---|---|---|
|  |  |  |  |  |

## Out of scope for Mahatma

- Editing Isolation Forest code
- Building new Streamlit pages
- Changing the CSV generator / metrics math
- Cloud deploy or database setup
