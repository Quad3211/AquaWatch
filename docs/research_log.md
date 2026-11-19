# Research log (Guide §12)

**Group:** AquaWatch Jamaica — Group 13  
**Project type:** Project G (own idea) — water-network anomaly investigation leads  
**Rule:** Every answer needs a source link. Prefer OUR / NWC / JIS / peer-reviewed or official case studies.

Full source register: [AquaWatch_Research_and_Sources.md](AquaWatch_Research_and_Sources.md)

---

## 1. The problem

| Question | Answer | Owner | Status |
|---|---|---|---|
| Who has this problem? | Utility NRW / leakage / network ops teams (e.g. NWC context) | Nathanael | Draft in sources doc — tighten here |
| How does it cost time/money/safety? | High NRW wastes treated water and crew time hunting which zone to check first | Nathanael | Needs 3 bullets + sources |
| How is it handled today without AI? | Pressure zones, DMAs, loggers, Miya partnership, acoustic/thermal field work | Nathanael | Partial |

**Write final paragraph here (Nathanael):**

> _TODO_

---

## 2. Real examples (two+ worldwide)

| Example | What they did | Reported result (as published) | Owner | Status |
|---|---|---|---|---|
| FIDO Tech / Chicago-area utility | Acoustic sensors + AI to locate hidden main leak | Provider case study: large daily loss estimate; water-loss reduction claimed | Mahatma | Summarise in 5 bullets |
| TaKaDu / SAPAL (Mexico) | Central event management from telemetry | Provider case study: priority cases, repairs, NRW recovered estimate | Mahatma | Summarise in 5 bullets |
| Thames Water / Origin Orbit (optional 3rd) | Satellite + AI leak hunt | Provider/news-reported litres/day estimate | Mahatma | Optional |

**Important:** These are **provider-reported**, not AquaWatch results.

---

## 3. Caribbean context

| Question | Notes | Owner | Status |
|---|---|---|---|
| What is different here? | High NRW reported for NWC; island water scarcity; existing NWC/Miya programmes | Nathanael | Add 3–5 local bullets |
| What must we not claim? | Not “first leak detection in Jamaica”; not replacing NWC/Miya | Nathanael | See STAGE0_SCOPE |

**Write Caribbean bullets here:**

1. _TODO_  
2. _TODO_  
3. _TODO_  

---

## 4. The data

| Question | Answer | Owner | Status |
|---|---|---|---|
| What would a real utility use? | Zone flow/pressure logger exports, DMA/pressure-zone telemetry | Nicholas | Draft |
| What do we use? | Documented synthetic CSV in `data/` | Nicholas | Done |
| Assumptions? | See `data/AquaWatch_Data_Notes.md` | Nicholas | Keep updated |
| Licence / privacy | Synthetic; no real customer identifiers | Nicholas | Done |

---

## 5. The AI

| Question | Answer | Owner | Status |
|---|---|---|---|
| Technique + why | Isolation Forest on zone/hour flow & pressure deviations | Nickel | Write plain-English note |
| Baseline | Flow >25% above zone/hour expected | Nicholas | Done in code |
| Metric | Precision & recall on injected held-out anomalies | Nicholas | Done (~91.7% / 75.9% AI) |
| Limits | Alert ≠ leak; synthetic ≠ field proof | Nickel + Nathanael | Expand |

**Plain-English model blurb (Nickel):**

> _TODO_

---

## 6. Risks / harm

| Risk | Who could be harmed? | Mitigation | Owner | Status |
|---|---|---|---|---|
| Too many false alerts | Crews waste time; operators ignore the tool | Show precision; human verify every alert | Nicholas + Mahatma | Draft |
| Missed real anomalies | Leaks continue longer | Report recall; never claim 100% catch rate | Nicholas + Mahatma | Draft |
| Overclaiming on synthetic data | Trainers/industry lose trust | Banner + data notes + pitch wording | Nathanael | In scope doc |

**Write risk paragraph here:**

> False alerts can waste crew time on checks that do not find an issue, and repeated false alerts can weaken trust in the tool. A missed anomaly can delay investigating a genuinely unusual pattern, so a real issue may go unnoticed longer. NWC says public leak reports are routed to area crews and prioritized by severity; its advisories also list scheduled maintenance, power issues, and pipeline or valve work ([leak reporting](https://www.nwcjamaica.com/report_leak.php); [advisories](https://www.nwcjamaica.com/advisories.php)). That local operating context reinforces the need to verify alerts. In our held-out synthetic test, precision was about 91.7% for both methods, meaning most alerts matched injected anomalous readings in that test; recall was about 37.9% for the simple flow rule and 75.9% for Isolation Forest, which caught more injected readings but still missed some ([synthetic-test results](../data/AquaWatch_Data_Notes.md)). These are synthetic-test results, not evidence of field performance. A person must verify every alert against sensor quality, operating context, and field checks before acting. AquaWatch flags patterns for investigation; the model alone must never be described as confirming a leak.

**Presenter / field-check sentences (Mahatma):**

- **After a false alert:** “Our check did not confirm a leak; we’ll review the sensor and operating context, then keep monitoring.”
- **After a miss:** “The tool did not flag this unusual pattern, so we’ll document it and investigate with normal field checks rather than rely on the alert alone.”

---

## Claims checklist (pitch-safe)

**Can say**

1. AquaWatch flags unusual patterns for investigation.  
2. On this synthetic held-out test, Isolation Forest improved recall vs a simple flow rule at similar precision.  
3. Designed to complement logger data and field checks.

**Must not say**

1. Confirms a leak.  
2. Pinpoints the pipe.  
3. Saves X m³ of real NWC water.  
4. Outperforms NWC/Miya in the field.

Owner: **Nathanael** — keep this list current.
