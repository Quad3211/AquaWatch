# AquaWatch Jamaica — research notes and source register

Research prepared for the Smart Caribbean Utilities proof-of-concept pitch, 17 November 2026.

## 1. Jamaican problem and user

**Potential business user:** a water utility's network operations, non-revenue-water (NRW), or leakage-control team. AquaWatch is proposed as decision-support software that helps sort zone-level flow/pressure readings into explainable investigation leads.

The Office of Utilities Regulation (OUR) 2024–2025 Annual Report reports NWC non-revenue water at **74.19%** of production for FY2024/25, or **243,935,368 m³**. The report defines NRW to include water that does not generate revenue, typically leaks or unauthorised consumption, and notes that meter inaccuracies/data handling and authorised unbilled use also contribute to the water balance. Therefore, NRW must not be described as “the percentage of water physically leaking from pipes.”

**Date clarification:** In an October 1, 2026 Jamaica Information Service report, an NWC official described NRW as “now at 70 per cent.” That is a later public statement and may use a different reference period or rounding basis than the OUR's FY2024/25 annual calculation. Present the dated figures separately; do not combine them as if they were the same measurement.

## 2. Local organisations and services

### National Water Commission (NWC)
NWC is the primary potential utility user, not a startup competitor. Its published NRW programme describes a partnership with Miya Jamaica, remote data loggers measuring flow and pressure over 24 hours, pressure management, network investigations and field repairs. NWC's programme page lists 146 pressure zones in operation and reports an average of 1,292 active leak detections per month in Kingston and St Andrew in 2021; these are historical programme milestones, not current operating statistics.

A 2025 NWC news release says 20 NWC employees were undertaking leak-detection technology training at UTech.

### Miya Jamaica
Miya is a specialist water-efficiency / NRW co-management partner working with NWC. JIS reporting on the Portmore programme describes pressure zones, district-metered areas, hydraulic modelling, meter replacement, leak detection and repairs. The same report quoted the programme manager describing a reduction in system water requirement from about 42,000 to 32,000 m³/day while serving the same population and revenue base. This is a programme-reported operational outcome, not an AI-model result.

### HTG Engineering Consultants Ltd.
HTG Engineering is a Kingston-based private engineering consultancy whose public website lists water leak detection, thermal imaging and ground-penetrating radar. Its thermal-imaging page lists water leaks among its applications. Public information reviewed for this pitch establishes detection/diagnostic services, not an AI model for utility-wide network anomaly ranking.

### Lapidary Plumbing
Lapidary advertises leak detection and pipe repair in Kingston, describing acoustic listening equipment, thermal imaging and pressure testing. Its public page is focused on building/property-level leak detection and repair. The reviewed page does not establish utility-wide AI monitoring.

**Market interpretation:** Jamaica already has utility-scale NRW programmes and private leak-detection services. AquaWatch should not claim to be Jamaica's first leak-detection service or to replace NWC/Miya, acoustic surveys or plumbing contractors. Publicly available sources reviewed here do not establish whether NWC or Miya currently uses an AI model comparable to the proposed Isolation Forest workflow; do not claim that they do not.

## 3. International businesses and real-world examples

### FIDO Tech — Chicago-area water utility (United States)
FIDO Tech's case study, dated 23 June 2024, describes a pilot in which eight acoustic sensors gathered overnight pipeline noise data. FIDO AI analysed the readings and helped locate a hidden main leak that had not been found by previous methods. The case study reports an estimated 350,000 gallons/day of water loss, a 28% water-loss reduction and a stated value of water saved of US$213,000. These are supplier-published case-study results, not an independent comparative trial.

### TaKaDu / IIASA — SAPAL, León (Mexico)
TaKaDu's case study describes an AI-based Central Event Management platform used through IIASA's Knowledge-as-a-Service model. It continuously monitors telemetry, identifies and interprets hydraulic/telemetry events, validates them and prioritises cases for the utility's field teams. For June 2025–August 2026, the case study reports 89 priority cases, 504 leaks repaired, 15 inter-sector transfers corrected and an estimated 1.149 million m³ of NRW recovered. These are provider-published results.

### Thames Water / Origin Orbit — United Kingdom
Thames Water reported on 24 August 2026 that an initial 19-week satellite-AI trial with Origin Orbit helped identify more than 800 leaks and was estimated to save 8.7 million litres/day. Thames Water also described use of acoustic sensors across its network. This illustrates a different sensing route (satellite observations) alongside acoustic monitoring.

## 4. How AquaWatch can add value in Jamaica

AquaWatch should be positioned as a **low-cost, explainable software layer that complements existing loggers and field investigations**:

1. **Use data already collected where possible.** NWC's programme page describes remote loggers that measure flow and pressure throughout the day. The student prototype can accept a CSV export rather than requiring new hardware.
2. **Learn each zone's own normal pattern.** Compare readings by zone and hour to reduce the risk of treating ordinary morning/evening demand as abnormal.
3. **Combine signals.** Look for combinations such as elevated flow with falling pressure, rather than relying on one fixed flow threshold.
4. **Prioritise and explain.** Show the affected zone, which readings deviated, how long the pattern persisted, and a suggested next check. Do not present the alert as a confirmed leak.
5. **Close the loop.** Let a field team mark the result as confirmed leak, no leak, meter issue, sensor fault or operational event. These outcomes could support future calibration.
6. **Design for a practical pilot.** Start with one district-metered area / pressure zone and a CSV export, compare alerts with engineer investigations, and only expand when false-alert burden and operational value are acceptable.

This is a proposed differentiation, not proof that AquaWatch is superior to existing NWC/Miya systems. The group should ask its trainer or a utility/engineering contact whether comparable internal analytics are already in use before claiming a market gap.

## 5. Proof-of-concept scope and honest claim

**Business question:** Can an AI model use flow and pressure patterns to flag unusual service-zone readings and help an operations team decide which zones to investigate first?

**Minimum prototype:** CSV input; zone/hour baseline; Isolation Forest anomaly detection; ranked alert table; chart showing readings behind an alert; simple rules baseline; precision/recall evaluation; documentation of synthetic-data limitations.

**Demo:** show a normal zone, inject a leak-like rise in flow and fall in pressure, and show an investigation alert with an explanation.

**Claim to make:** “AquaWatch flags unusual patterns for investigation.”

**Claims not to make:** “AquaWatch confirms leaks,” “AquaWatch pinpoints the pipe,” “AquaWatch saves a specific volume of water,” or “AquaWatch outperforms NWC/Miya in the field.”

## 6. Sources

1. Office of Utilities Regulation (OUR), *Annual Report 2024–2025*, NRW details and Figure 16, pp. 69–71. https://our.org.jm/wp-content/uploads/2025/12/Annual-Report-2024-2025-low-res-compressed.pdf
2. National Water Commission, *NRW Programme*. https://nwcipay.nwcjamaica.com/nrw.php
3. Jamaica Information Service, *NWC Working to Reduce Water Loss*, 1 October 2026. https://jis.gov.jm/nwc-working-to-reduce-water-loss/
4. NWC, *Leak detection training boosts NWC’s efforts to cut Non-Revenue Water*, 13 October 2025. https://nwcjamaica.com/Articles/4-20251013-News%20Release%20-%20Utech%20Training%20Updated.pdf
5. Jamaica Information Service, *NWC/MIYA Non-Revenue Water Reduction Programme Yielding Positive Outcomes*, 30 January 2023. https://jis.gov.jm/features/nwc-miya-non-revenue-water-reduction-programme-yielding-positive-outcomes/
6. HTG Engineering, *Water Leak Detection / Services*. https://htgengineering.com/ and https://htgengineering.com/service/thermal-imaging/
7. Lapidary Plumbing, *Leak Detection & Pipe Repair in Jamaica*. https://lapidaryplumbing.com/services/leak-detection-repair
8. FIDO Tech, *Chicago, IL | Leak Locate*, 23 June 2024. https://fido.tech/case-studies/chicago-water-utility-fido-direct/
9. TaKaDu, *From Telemetry Data to Recovered Water — SAPAL*. https://www.takadu.com/case-study/sapal/
10. Thames Water, *Thames Water uses satellites, AI and thousands of acoustic sensors to hunt down leaks*, 24 August 2026. https://www.thameswater.co.uk/news/2026/aug/thames-water-uses-satellites-ai-and-thousands-of-acoustic-sensors-to-hunt-down-leaks-as-south-east-drought-pressure-intensifies
11. Smart Caribbean Utilities Project Guide, Sections 3, 4, 11–16 and 20 (user-provided course guide).
