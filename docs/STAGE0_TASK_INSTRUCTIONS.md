# Stage 0 task instructions (beginner-friendly)

**Read this first if you are unsure what to do.**  
These are the current Stage 0 tasks. You do **not** need to invent work.

**Repo:** https://github.com/Quad3211/AquaWatch  
**Board:** https://github.com/users/Quad3211/projects/1  
**Due for research notes:** Friday 21 November 2026 (end of day)  
**Due for UI inject/chart work:** Friday 27 November 2026

## Before anyone starts (5 minutes)

1. Open https://github.com/Quad3211/AquaWatch  
2. Click **Code → Open with GitHub Desktop** (or ask Nathanael to help you clone)  
3. On your computer, open a terminal in the project folder and run:

```bash
git pull
pip install -r requirements.txt
python scripts/AquaWatch_Evaluate.py
python -m streamlit run app.py
```

4. If `streamlit` is “not recognized”, always use: `python -m streamlit run app.py`  
5. Open the Project board and drag **your** issue from **Todo** to **In Progress**  
6. When finished, drag it to **Testing** (for Mahatma/Nathanael to check) or **Done**

---

## How to edit a doc on GitHub (no coding needed)

Use this for research tasks (Nathanael, Nickel, Nicholas, Mahatma):

1. Open the file link in your issue  
2. Click the pencil icon (**Edit this file**)  
3. Replace every `_TODO_` / empty section that belongs to you  
4. Scroll down → **Commit changes**  
5. If GitHub asks for a Pull Request, create one and ask Nathanael to merge  
6. Add one row to [`docs/CONTRIBUTION_LOG.md`](CONTRIBUTION_LOG.md) with today’s date and what you did

---

# Nathanael Coote — Team Lead

## Your jobs right now

### A) Issue [#7](https://github.com/Quad3211/AquaWatch/issues/7) — fill the research log (problem + claims)

**File to edit:** [`docs/research_log.md`](research_log.md)

**Do this exactly:**

1. Open `docs/research_log.md`  
2. In **Section 1 (The problem)**, replace `> _TODO_` with **one short paragraph** that answers:
   - Who has the problem? (utility water-loss / leakage team)
   - Why it costs money/time (treated water lost; crews don’t know which zone to check first)
   - How it is handled today (NWC/Miya zones, loggers, field repairs — not “no system exists”)  
3. Copy facts only from [`docs/AquaWatch_Research_and_Sources.md`](AquaWatch_Research_and_Sources.md) and keep the source links  
4. In **Section 3 (Caribbean context)**, replace the three `_TODO_` bullets with 3 real local bullets (NRW figure, NWC/Miya programme, why alerts must stay “investigate not confirm”)  
5. Check the **Claims checklist** at the bottom:
   - Keep the “Can say” / “Must not say” lists
   - Add one source link under each major claim if missing  
6. Commit, then add a contribution-log row

**Done when:** no `_TODO_` left in sections 1 and 3, and claims list is clear enough to read on pitch day.

### B) Keep the team moving (ongoing)

1. Twice a week (Mon + Thu): 15-min check-in — what finished / what’s next / blockers  
2. Update [`docs/BLOCKERS.md`](BLOCKERS.md) if someone is stuck  
3. Merge PRs when teammates finish docs/code

---

# Nickel Small — Data & Model (primary)

## Your job: Issue [#6](https://github.com/Quad3211/AquaWatch/issues/6)

**Goal:** Explain Isolation Forest so a non-programmer judge understands it.

**File to edit:** [`docs/research_log.md`](research_log.md) → **Section 5 (The AI)**

**Do this exactly:**

1. Open Section 5  
2. Replace `> _TODO_` under **Plain-English model blurb** with about **150–250 words** that covers:
   - What “normal” means here (each zone’s usual flow/pressure at that hour)
   - What Isolation Forest does in plain words (“finds readings that look unusual compared with normal history”)
   - What we output (**investigation alert**, never “this is definitely a leak”)  
3. Add a heading **Failure modes** and list **exactly 4**:
   1. Sensor / logger fault  
   2. Planned valve/pump/supply change  
   3. Normal demand spike that looks big  
   4. Missing or dirty data  
4. Add **3 bullets** titled **What this means for AquaWatch**  
5. Optional helper links (read, don’t copy blindly):
   - scikit-learn IsolationForest docs  
   - Our code: `src/aquawatch/model.py`  
6. Commit + contribution log row

**You do NOT need to change model settings unless metrics break.**  
If you change code, run:

```bash
python scripts/train_and_save_model.py
python scripts/AquaWatch_Evaluate.py
```

and tell Nathanael if the event-level table changes (see `data/AquaWatch_Data_Notes.md` for the current numbers).

**Done when:** Section 5 has the blurb, 4 failure modes, and 3 AquaWatch bullets.

---

# Nicholas Smalling — Data & Model (support)

## Your jobs

### A) Issue [#9](https://github.com/Quad3211/AquaWatch/issues/9) — with Mahatma

**File:** [`docs/research_log.md`](research_log.md) → **Section 6 (Risks / harm)**

**Do this exactly:**

1. Open Section 6  
2. Replace `> _TODO_` with a short paragraph that explains:
   - **False alert harm:** crews waste time; people stop trusting the tool  
   - **Missed anomaly harm:** unusual pattern not flagged; investigation delayed  
3. Connect to our synthetic metrics in plain words:
   - Both the rule and the AI caught all 3 held-out test events, far better than random alarms  
   - The AI raised more separate false alarms (about 2 per zone per week vs 0.7 for the rule); with only 3 events we cannot claim either is better  
4. Write 2 mitigation sentences:
   - Humans must verify every alert  
   - We never claim confirmed leaks from the model alone  
5. Ask Mahatma to add 2 “field crew” sentences (what a tester/presenter would say)  
6. Commit + contribution log

### B) Keep data notes honest (ongoing)

1. Open [`data/AquaWatch_Data_Notes.md`](../data/AquaWatch_Data_Notes.md)  
2. Confirm it still says: synthetic data; labels not model features; chronological split  
3. If anything in the CSV changes, update this file the same day

**Done when:** Section 6 is filled and data notes still match reality.

---

# Jason Williams — Interface (primary)

## Your jobs (with Romaro on inject demo)

### A) Issue [#4](https://github.com/Quad3211/AquaWatch/issues/4) — wire Romaro’s inject demo into Streamlit

**You are the person who connects UI controls to working app behaviour.**

**Do this exactly:**

1. Pull latest code and run the app (`python -m streamlit run app.py`)  
2. Confirm you see the yellow banner: **Research Prototype: Simulated Utility Data**  
3. Work with Romaro on a new control in `app.py` (Chart tab or sidebar), for example:
   - Dropdown: choose zone (default Zone 03)
   - Button: **Inject leak-like pattern**  
4. When clicked, the app should:
   - Temporarily raise flow and lower pressure for some hours in that zone **or** jump to the existing SIM-04 window and show the alert  
   - Show an alert row with **reason** and **next step**  
5. Keep wording safe: “investigation needed”, never “leak confirmed”  
6. Test the full path yourself once, then move issue to **Testing** for Mahatma

**If you are stuck on Python/Streamlit:**

1. Do not rewrite `src/aquawatch/model.py`  
2. Ask Nickel/Nicholas only for “what function do I call?”  
3. Keep UI changes inside `app.py`

**Done when:** a teammate can click one button and see an alert with a reason in under 2 minutes.

### B) Small UI hygiene

1. Make sure Overview / Alerts / Chart / Metrics tabs still work after inject changes  
2. If the saved-model checkbox breaks, tell Nickel and use in-session training temporarily

---

# Romaro Dixion — Interface (support)

## Your jobs

### A) Issue [#5](https://github.com/Quad3211/AquaWatch/issues/5) — make the chart understandable

**File mostly:** `app.py` (Chart tab)

**Do this exactly:**

1. Run the app and open the **Chart** tab  
2. Select **Zone 03**  
3. Replace/improve the basic line chart so a visitor can see:
   - Flow over time  
   - Pressure over time  
   - A shaded or marked window where the injected unusual pattern happens  
4. Prefer **Plotly** (already in `requirements.txt`)  
5. Add a caption under the chart like:
   - “Unusual pattern window highlighted for investigation (synthetic data).”  
6. Forbidden words in labels: “confirmed leak”, “pipe break found”, “guaranteed savings”

**Simple success test:** show the chart to someone outside the group for 10 seconds; they should point to the unusual window.

### B) Issue [#4](https://github.com/Quad3211/AquaWatch/issues/4) — inject demo (with Jason)

1. Design the button/slider behaviour (what the user clicks)  
2. Jason wires it into Streamlit if you are less comfortable with code  
3. Practice the spoken line: “Watch flow rise and pressure drop — then the alert appears.”

**Done when:** chart highlight works and inject demo path is clickable.

---

# Mahatma Williams — Tester & Presenter (lightest technical load)

## You do NOT need to write the AI model or build Streamlit pages.

## Your jobs

### A) Issue [#8](https://github.com/Quad3211/AquaWatch/issues/8) — case studies + demo script

**Files:**

- [`docs/research_log.md`](research_log.md) Section 2  
- Optional notes in a short demo card (can paste into issue comment first)

**Do this exactly:**

1. Open [`docs/AquaWatch_Research_and_Sources.md`](AquaWatch_Research_and_Sources.md) sections on FIDO and TaKaDu  
2. In research log Section 2, write **5 bullets for FIDO** and **5 bullets for TaKaDu**:
   - What they did  
   - What result they reported  
   - End each set with: “Provider-reported; not AquaWatch results.”  
3. Write a **2-minute demo script** with these exact beats:
   1. “This is synthetic utility-style data.”  
   2. Show a normal-looking period  
   3. Show / inject unusual flow↑ + pressure↓  
   4. Show the alert + reason  
   5. Say: “This flags investigation, it does not confirm a leak.”  
4. Put the script in the issue comment **and** in `tests/MAHATMA_TEST_CHECKLIST.md` under Demo path (or a short `docs/DEMO_SCRIPT.md` if easier)  
5. Add contribution-log row

### B) Issue [#9](https://github.com/Quad3211/AquaWatch/issues/9) — help Nicholas

Add 2 sentences from a presenter/tester view:

- What you would say if the tool raised a false alert  
- What you would say if it missed something  

### C) Issue [#10](https://github.com/Quad3211/AquaWatch/issues/10) — later (not this week’s first priority)

1. Use [`tests/MAHATMA_TEST_CHECKLIST.md`](../tests/MAHATMA_TEST_CHECKLIST.md) every time Jason says “try this build”  
2. Before board review: record a backup phone/laptop video of the demo  
3. With Nathanael: test a fresh clone on another computer

**Done for this week when:** FIDO/TaKaDu bullets + 2-minute script are written.

---

# Everyone — Issue [#3](https://github.com/Quad3211/AquaWatch/issues/3)

After every work session, add **one row** to [`docs/CONTRIBUTION_LOG.md`](CONTRIBUTION_LOG.md):

| Date | Your name | What you finished | File/link | Blocker? |

If you did nothing that day, do not invent work — just skip.

---

## What “good enough” looks like

| Person | One-sentence finish line |
|---|---|
| Nathanael | Research log problem/Caribbean/claims filled |
| Nickel | Isolation Forest explained in plain English with 4 failure modes |
| Nicholas | Risks section filled + data notes still accurate |
| Jason | Inject button path works in the app |
| Romaro | Chart shows the unusual window clearly |
| Mahatma | 10 case-study bullets + 2-minute demo script |

## Who to ask

| Stuck on… | Ask |
|---|---|
| GitHub / merge / board | Nathanael |
| Model / metrics numbers | Nickel or Nicholas |
| App layout / buttons | Jason |
| Chart look / demo click | Romaro |
| “Does the demo make sense?” | Mahatma |
