# Data Governance, Cybersecurity, Legal and Procurement Requirements for Piloting AquaWatch Jamaica with a Water Utility

Research date: 21 November 2026. This is not legal advice. Items marked "lawyer needed" should be confirmed by Jamaican counsel (for example a data protection practice such as those listed in the Chambers guide) before a pilot agreement is signed.

Source-quality note: The most authoritative secondary source found is the Chambers Global Practice Guide, Data Protection & Privacy 2026, Jamaica chapter (Ramsay & Partners). I extracted its text directly. Official JIS/OIC/Gleaner items supplied status updates. Standards facts in section 3 and 5 that cite canonical publisher pages (NIST, ISA, ISO) are well known publication facts, but those pages were not re-fetched in this session. They are flagged where relevant.

## 1. Jamaica Data Protection Act 2020 (DPA): status, regulator, scope, obligations, penalties

### Takeaway
The DPA's operative provisions have applied since 1 December 2023. The regulator is the Information Commissioner, Celia Barclay, at the Office of the Information Commissioner (OIC). Obligations such as 72-hour breach notice, DPO, annual DPIA and transfer restrictions apply now. However, data controller registration has been paused since 1 December 2025, and the Commissioner told Parliament that full enforcement is not expected until 2028. A pilot should be built to full compliance anyway, because NWC is a public authority that will itself be the controller.

### Cited Findings
**Commencement and status**
- The Act's requirements took effect on 1 December 2023 after a transitional period. Barclay was appointed Information Commissioner on 1 December 2021. — [JIS, Registration of Data Controllers Begins Dec. 1](https://jis.gov.jm/registration-of-data-controllers-begins-dec-1/); [OIC article on the new Information Commissioner](https://oic.gov.jm/content/jamaicas-new-information-commissioner-talks-meeting-dpa-mandate-ground)
- The governing instruments are the Data Protection Act 2020, the Data Protection Regulations 2024, and the Data Protection (Data Controller Registration) Regulations 2024. The Chambers authors say these are Jamaica's only data protection laws, with no sectoral regimes. — [Chambers GPG Data Protection & Privacy 2026, Jamaica](https://chambers.com/downloads/gpg/1129/013_jamaica.pdf)
- Text of the Act — [Jamaica Parliament, The Data Protection Act, 2020 (PDF)](https://japarliament.gov.jm/attachments/article/339/The%20Data%20Protection%20Act,%202020.pdf)
- July 2026: Barclay told Parliament's Public Accounts Committee that the OIC would not be able to fully enforce the DPA until 2028 at the earliest, because of staffing and other challenges. — [Gleaner, "Data defence delay", 30 Jul 2026](https://jamaica-gleaner.com/article/news/20260730/data-defence-delay)
- Data controller registration has been suspended since 1 December 2025 while the OIC portal is upgraded. It was expected to resume around the end of September 2026. Obligations to comply continue during the pause. — [Gleaner, 30 Jul 2026](https://jamaica-gleaner.com/article/news/20260730/data-defence-delay); [Esirom (commercial blog, fact-checked Aug 2026)](https://esirom.com/jamaica-data-protection-act-not-an-it-project/)
- The OIC said in March 2026 that it will not impose liability for processing without registration while the platform is offline. The minister (Andrew Wheatley, June 2026) said: "We have the law. What we have not yet done is fully enforce it." — [Esirom](https://esirom.com/jamaica-data-protection-act-not-an-it-project/). This is a secondary source; verify on oic.gov.jm.
- Chambers (2026) states that the OIC's investigative arm is not fully established and that the provisions giving the Commissioner certain enforcement powers are not yet in effect. No enforcement action has been taken for failure to register. — [Chambers 2026](https://chambers.com/downloads/gpg/1129/013_jamaica.pdf)
- In October 2025, eight additional OIC posts were approved, bringing the total to 31. — [Gleaner / JIS via search summary](https://jis.gov.jm/oic-commits-to-building-strong-culture-of-data-privacy/)

**Scope**
- The DPA is extraterritorial. It applies to non-residents who use equipment in Jamaica for processing, or who process data of people in Jamaica in connection with offering goods or services or monitoring their behaviour. — [Chambers 2026](https://chambers.com/downloads/gpg/1129/013_jamaica.pdf)
- Anonymised data, where no individual is identifiable, falls outside the DPA. Processing for research is permitted if it is not used for decisions about particular individuals and does not cause substantial damage or distress. — [Chambers 2026](https://chambers.com/downloads/gpg/1129/013_jamaica.pdf)
- Jamaica has no specific guidance on personal data in AI systems and no comprehensive AI regulation. — [Chambers 2026](https://chambers.com/downloads/gpg/1129/013_jamaica.pdf)
- Data subjects have a right to ask that decisions significantly affecting them are not made solely by automated processing. — [Chambers 2026](https://chambers.com/downloads/gpg/1129/013_jamaica.pdf)

**Core obligations** (all from [Chambers 2026](https://chambers.com/downloads/gpg/1129/013_jamaica.pdf) unless noted)
- There are eight data protection standards: fairness and lawfulness, purpose limitation, data minimisation, accuracy, storage limitation, data subject rights, technical and organisational security measures, and cross-border transfer restriction.
- Registration: all controllers must register with the Commissioner before processing and pay registration and annual fees. They must keep processing records covering purposes, categories, recipients and transfers abroad.
- DPIA: unless the Commissioner indicates otherwise, controllers must submit a DPIA to the Commissioner annually. Esirom says it is due within 90 days after each calendar year. — [Esirom](https://esirom.com/jamaica-data-protection-act-not-an-it-project/)
- DPO is mandatory for: public authorities; processors of sensitive or criminal data; large-scale processing; and controllers the Commissioner designates. NWC is a statutory body and would likely qualify as both a public authority and a large-scale processor. That is an inference; lawyer needed.
- Breach notification: report to the Commissioner within 72 hours of becoming aware, and to each affected data subject within 72 hours. The notice must cover the facts, nature, consequences and remedial measures, and is filed through the Commissioner's online portal. Breach records must be kept. The 72-hour rule is also attributed to the Data Protection Regulations 2024. — [Gleaner/JIS search summary](https://jamaica-gleaner.com/article/news/20260730/data-defence-delay)
- Processors must have a written contract and act only on the controller's instructions. — [Esirom](https://esirom.com/jamaica-data-protection-act-not-an-it-project/)
- Subject access requests must be answered within 30 days.

**Cross-border transfers** (from [Chambers 2026](https://chambers.com/downloads/gpg/1129/013_jamaica.pdf))
- Personal data may not be transferred outside Jamaica unless the destination ensures adequate protection. Adequacy factors include the nature of the data, the destination's law, its international obligations, codes of conduct, and security measures.
- Exceptions include: consent; contract necessity; substantial public interest; legal claims; vital interests; public registers; terms of a kind approved by the Commissioner (contractual safeguards); transfers authorised by the Commissioner; and national security or crime.
- No filings or approvals are required for international transfers, and there are no data localisation or residency obligations by sector or data category.

**Penalties** (from [Chambers 2026](https://chambers.com/downloads/gpg/1129/013_jamaica.pdf))
- Bodies corporate face a fine of up to 4% of annual gross worldwide turnover for the preceding year of assessment.
- Individuals face fines up to JMD 5 million (about USD 31,100) and/or up to 10 years' imprisonment. Some secondary sources describe the individual maximum differently; lawyer needed.
- Civil compensation is available for damage, and for distress in some cases. Remedies also include enforcement notices, information and assessment notices, injunctions and declaratory relief.

**Are smart meter readings personal data?**
- The DPA applies to personal data, meaning data about an identifiable individual. Anonymised data falls outside it, and device identifiers become regulated once they can identify a person. — [Chambers 2026](https://chambers.com/downloads/gpg/1129/013_jamaica.pdf)
- NWC is rolling out Diehl solid-state meters islandwide. These are capable of remote reading, and a fixed-network automatic reading pilot ran at Long Mountain covering 525 residential units. — [JIS, NWC Continues to Install New Water Meters](https://jis.gov.jm/nwc-continues-to-install-new-water-meters-islandwide/); [Diehl case study](https://www.diehl.com/metering/en/case-studies/jamaica-fixed-network)

### Inferences
- Household-level meter reads linked to an account number, premises address or meter serial that maps to a customer are very likely personal data under the DPA's identifiability test. High-frequency interval data can also reveal occupancy and behaviour, as European regulators have treated it. Aggregated DMA-level, bulk-meter or SCADA flow and pressure telemetry is generally not personal data. AquaWatch should start with SCADA, DMA and bulk telemetry only. That keeps it largely outside the DPA and simplifies the pilot.
- If customer meter data is used, NWC is the data controller and AquaWatch or the university is a processor. A written processing contract is required. AquaWatch must support NWC's 72-hour breach clock, which in practice means notifying NWC within something like 24 hours. Pseudonymise meter IDs before ingestion.
- The "research" condition may help a university pilot, but not if alerts are used to act on individual customers, for example by flagging a customer-side leak. That would be a decision about a particular individual. Lawyer needed.
- The slow pace of enforcement is not a licence to cut corners. Utilities will still apply the law in procurement and legal review, and civil claims remain available.

### Gaps
- I could not confirm from the OIC site itself whether registration reopened in late September 2026, as targeted. Check oic.gov.jm.
- The Act's exact statutory definition of "personal data" was not quoted, because the parliament PDF was not text-extracted. There is no Jamaican guidance specifically on utility or smart meter data.
- I found no OIC-approved standard contractual clauses for transfers. Whether any "terms approved by the Commissioner" exist yet is unknown.
- I did not verify whether the DPA has a statutory definition of "large scale".

## 2. Other Jamaican laws, policies and institutions (Cybercrimes, national cyber strategy, JaCIRT, critical infrastructure, ATI, OUR, procurement)

### Takeaway
Jamaica criminalises unauthorised access under the Cybercrimes Act 2015, amended in early 2026. It does not yet have a cybersecurity act imposing mandatory standards or incident reporting on critical infrastructure. That law is being developed, and JaCIRT is seeking powers to require standards and reporting. Public procurement is governed by the Public Procurement Act 2015 (in force 1 April 2019) and GOJEP. A pilot that involves payment or a contract with NWC will fall under these rules unless structured as an unpaid research collaboration. Lawyer needed.

### Cited Findings
**Cybercrimes Act**
- The Cybercrimes Act 2015 criminalises unauthorised access to and interference with systems and data, including non-personal data. A breach can carry both DPA and criminal liability. — [Chambers 2026](https://chambers.com/downloads/gpg/1129/013_jamaica.pdf)
- The Cybercrimes (Amendment) Act was debated in the House in late January 2026 and passed by the Senate. JaCIRT said in October 2026 that the Act "was amended in February". The amendments include offences for making, selling or possessing tools built mainly for cybercrime, and higher penalties for offences against minors. — [Jamaica Observer, 28 Jan 2026](https://www.jamaicaobserver.com/2026/01/28/house-opens-debate-cybercrime-bill-bolster-child-protection-law-enforcement/); [JIS, Senate Passes Cybercrimes (Amendment) Act](https://jis.gov.jm/senator-passes-cybercrimes-amendment-act/); [Jamaica Observer, 21 Oct 2026](https://www.jamaicaobserver.com/2026/10/21/jamaica-braces-cyber-stress-test/)

**Cybersecurity Act (pending) and national strategy**
- Jamaica has no cybersecurity act yet. The government is developing one, focused on prevention and on systems supporting essential sectors, distinct from the Cybercrimes Act. The next step reported was Cabinet approval to issue drafting instructions. — [JIS, Government Advances Work On New Cybersecurity Act](https://jis.gov.jm/government-advances-work-on-new-cybersecurity-act/); [JIS, Government to Develop Cybersecurity Act](https://jis.gov.jm/government-to-develop-cybersecurity-act/)
- A new national cybersecurity strategy will build on the 2015 strategy and the 2021–2025 strategy. — [JIS](https://jis.gov.jm/government-advances-work-on-new-cybersecurity-act/)
- An IDB-backed "Strengthening Cybersecurity in Jamaica" project runs from September 2025 to March 2031. — [Search summary of JIS/OPM reporting](https://opm.gov.jm/post-cabinet-press-briefing-report-january-28-2026/). Verify the project details on iadb.org.

**JaCIRT**
- JaCIRT is a division of the Office of the Prime Minister and is evolving into a national cyber authority. — [Jamaica Observer, JaCIRT evolves into national cyber authority](https://jamaicaobserver.com/business/jacirt-evolves-into-national-cyber-authority-for-enhanced-cybersecurity)
- As of October 2026, the national cybersecurity standards framework and the national incident response plan are finalised. JaCIRT's director wants legislative authority to require organisations to meet standards and report incidents. A national exercise, CyberXJM26, involves telecoms and other critical sectors. — [Jamaica Observer, 21 Oct 2026](https://www.jamaicaobserver.com/2026/10/21/jamaica-braces-cyber-stress-test/); [JIS, CIRT Division to Stage Cybersecurity Exercise](https://jis.gov.jm/cirt-division-to-stage-cybersecurity-exercise-oct-28/)
- A December 2025 report says incident reporting to JaCIRT continues even without mandatory legislation. — [Jamaica Observer, 24 Dec 2025](https://www.jamaicaobserver.com/2025/12/24/cyber-vulnerabilities-watch-despite-melissa-distractions/)
- The 2024 cyberattack on the Bureau of Standards Jamaica was reported to JaCIRT. It shows that public bodies are targeted. — [Gleaner, BSJ hit by cyberattack, May 2024](https://past.jamaica-gleaner.com/article/lead-stories/20240511/bsj-hit-cyberattack)

**Public procurement**
- The Public Procurement Act 2015 (as amended), the Public Procurement Regulations 2018 and the Reconsideration and Review Regulations 2018 entered into force on 1 April 2019. The Office of Public Procurement Policy (Ministry of Finance) issues policy, guidance and training. — [Ministry of Finance](https://www.mof.gov.jm/?p=4879); [Act text, Jamaica Parliament](https://japarliament.gov.jm/attachments/339_The%20Public%20Procurement%20Act,%202015%20new.pdf)
- The Act uses Tier 1, 2 and 3 value thresholds. Direct contracting is now called "Single Source Procurement". GOJ standard bidding documents include single-source templates. — [Act text](https://japarliament.gov.jm/attachments/339_The%20Public%20Procurement%20Act,%202015%20new.pdf); [MoF single-source template](https://www.mof.gov.jm/wp-content/uploads/annex-g2-good-single-source-april-2019.docx)
- A November 2026 Gleaner commentary reports a "GOJEP 2.0" upgrade and says the government raised single-source thresholds to speed up procurement. — [Gleaner, 15 Nov 2026](https://jamaica-gleaner.com/index%2ephp/article/focus/20261115/jeanette-calder-gojep-20-progress-enforcement-must-finish-job)
- The US Commercial Guide gives an overview of selling to the Jamaican public sector. — [trade.gov](https://www.trade.gov/country-commercial-guides/jamaica-selling-public-sector)

**NWC context**
- NWC runs non-revenue water (NRW) programmes, including a Kingston and St Andrew co-management contract with Miya, which cut losses from about 60% to 40%. A Portmore NRW programme for 2021–2026 targets 60% down to 30%. — [Smart Water Magazine](https://smartwatermagazine.com/news/miya/miya-jamaica-joins-forces-nwc-reduce-severe-water-losses-kingston-and-st-andrew); [NWC NRW page](https://www.nwcjamaica.com/nrw.php)

### Inferences
- An unpaid university-utility research collaboration under an MoU and data-sharing agreement likely sits outside the Public Procurement Act, which governs procurement of goods, works and services for consideration. Any paid follow-on would need a competitive or justified single-source process on GOJEP. Plan the pilot as a no-cost MoU and design the exit criteria so they feed into a later tender. Lawyer or OPPP guidance needed.
- Because there is no mandatory critical-infrastructure regime yet, NWC's security requirements for vendors will come from its own internal policies, the GOJ ICT standards, and JaCIRT's new standards framework. Expect these to be benchmarked against NIST and IEC 62443 (see section 3).
- The Cybercrimes Act cuts both ways. AquaWatch must never probe or scan NWC systems beyond the access it is authorised for, and the agreement should define authorised access in writing.

### Gaps
- I found no source tying OUR licence conditions or regulation to cybersecurity or data handling for NWC. OUR's role, which covers tariffs and service standards, was not verified for this topic.
- I did not verify any formal Jamaican critical-infrastructure designation that covers water. None was found.
- The Access to Information Act 2002 was not researched in this session. It is relevant because NWC is a public authority, so documents AquaWatch provides, including evaluation reports, could be requested by the public unless an exemption applies. Commercial-confidentiality exemptions need legal confirmation.
- Current Tier threshold amounts and any explicit GOJ policy on proof-of-concept or innovation procurement were not found.

## 3. OT/ICS security for water: standards, advisories, incidents, and what a third-party analytics tool must do

### Takeaway
Water-sector incidents have overwhelmingly exploited internet-exposed OT, remote-access tools and default passwords: Oldsmar 2021 (TeamViewer), Aliquippa 2023 (Unitronics PLCs with default passwords exposed to the internet), and American Water 2024 (IT systems, billing paused). A third-party analytics tool will be judged on whether it adds any path into OT. The accepted design is one-way, read-only data export from the SCADA historian through an OT DMZ, optionally via a data diode, with no write or control capability. It should be documented against IEC 62443 zones and conduits and NIST SP 800-82r3.

### Cited Findings
**Incidents**
- Oldsmar, Florida, 5 February 2021: an intruder used TeamViewer remote access on a plant computer and changed sodium hydroxide from about 100 ppm to 11,100 ppm. An operator reversed it, the water supply was not affected, and remote access was then disabled. — [Dark Reading](https://www.darkreading.com/attacks-breaches/hacker-raised-chemical-settings-at-water-treatment-plant-to-dangerous-levels/d/d-id/1340095); [TechTarget](https://www.techtarget.com/cybersecurity/news/252496102/Florida-citys-water-nearly-poisoned-in-TeamViewer-attack)
  - Contested: in 2023 the former Oldsmar city manager said the incident was not a cyberattack and was likely employee error. Cite Oldsmar as "reported" or "disputed". — [Cisco blog, 31 Mar 2023 update](https://blogs.cisco.com/security/oldsmars-cyber-attack-raises-the-alarm-for-the-water-industry)
- Aliquippa, Pennsylvania, November 2023: IRGC-affiliated "CyberAv3ngers" compromised a Unitronics Vision PLC/HMI at a booster station. They likely exploited poor password security and internet exposure. CISA's advice was to change default passwords, require MFA, and disconnect PLCs from the open internet. The campaign hit multiple US sectors between November 2023 and January 2024. — [CISA AA23-335A](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-335a); [Insurance Journal](https://www.insurancejournal.com/news/east/2023/12/01/750322.htm)
- American Water, October 2024: the largest US regulated water utility detected unauthorised activity on 3 October 2024. It disconnected some systems and took the MyWater customer portal offline, pausing billing. It said water and wastewater operations were not affected. — [SecurityWeek](https://www.securityweek.com/american-water-confirms-hack-customer-portal-and-billing-services-suspended/); [TechTarget](https://www.techtarget.com/cybersecurity/news/366612830/American-Water-discloses-breach-utilities-unaffected)

**US agency and industry guidance**
- The CISA/EPA/FBI "Top Cyber Actions for Securing Water Systems" fact sheet (February 2024) recommends, among other things, reducing exposure to the public internet, conducting regular assessments, changing default passwords, inventorying OT and IT assets, developing incident response plans, backups, reducing third-party and supply-chain risk, and training. It points to CISA's free vulnerability scanning. — [EPA PDF](https://www.epa.gov/system/files/documents/2024-02/top8factsheet.pdf); [CISA water sector page](https://cisa.gov/water)
- EPA offers a free Water Cybersecurity Assessment Tool and checklist, and a Water Sector Cybersecurity Evaluation Program. — [EPA checklist fact sheets, June 2024](https://www.epa.gov/system/files/documents/2024-06/watercybersecuritychecklistfactsheets.pdf)
- AWWA's Water Sector Cybersecurity Risk Management Guidance v4.0 and its free Assessment Tool are aligned with the NIST CSF. They offer small-system, full or CSET-based assessments, and are recognised by EPA, CISA and NIST. — [AWWA Cybersecurity & Guidance](https://www.awwa.org/resource/cybersecurity-guidance/)
- A GAO report (2024) on EPA water cybersecurity documents sector-wide weaknesses. — [GAO-24-106744](https://www.gao.gov/assets/gao-24-106744.pdf)

**Standards** (canonical publisher pages; not re-fetched this session)
- ISA/IEC 62443 is the OT security standards series. It segments systems into zones joined by conduits. Security Levels SL1–SL4 range from casual or coincidental violation to sophisticated, state-level attackers. 62443-2-4 sets requirements for service providers and 62443-4-1 for secure product development. EPA lists the series as a water resource. — [ISA 62443 series overview](https://www.isa.org/standards-and-publications/isa-standards/isa-iec-62443-series-of-standards); [EPA reference in search results](https://www.epa.gov/node/283760)
- NIST SP 800-82 Rev. 3, "Guide to Operational Technology (OT) Security", was published September 2023. It covers OT architecture, segmentation, DMZs and unidirectional gateways, and applies the CSF to OT. — [NIST CSRC SP 800-82r3](https://csrc.nist.gov/pubs/sp/800/82/r3/final)
- NIST Cybersecurity Framework 2.0 (February 2024) adds a "Govern" function, covering supply-chain risk management, alongside Identify, Protect, Detect, Respond and Recover. — [NIST CSF 2.0](https://www.nist.gov/cyberframework)

### Inferences: what AquaWatch must do to be acceptable
- **No path into the control network.** AquaWatch should ingest from a historian replica or export placed in NWC's OT DMZ (Purdue level 3.5), never from PLCs or RTUs directly. Data should flow outbound only, ideally through a hardware data diode or unidirectional gateway, or at minimum a DMZ broker that pushes files or MQTT to AquaWatch. No inbound connections from AquaWatch to OT, no VPN into OT, and no TeamViewer-style remote access.
- **Read-only by design.** The tool should have no write-back, setpoint or command capability, and this should be stated in the architecture document and the contract. Alerts go to people by email, SMS or dashboard, and operators act through their own SCADA. This is the key differentiator from the Oldsmar and Aliquippa failure modes.
- **Document against IEC 62443.** Provide a zone and conduit diagram showing AquaWatch as an external zone with one conduit from the DMZ, and target an SL that NWC specifies (SL2 is a common baseline for non-control analytics). Map controls to the NIST CSF 2.0 functions, and complete the AWWA tool self-assessment for the AquaWatch component.
- **Hygiene that utilities will check.** MFA everywhere, no default credentials, an asset and SBOM list, a vulnerability disclosure contact, patch cadence, logging shared with NWC, and an incident response plan with notification SLAs aligned to the DPA's 72-hour rule.
- **Start offline.** Phase 0 should be a historical data extract (CSV or Parquet) delivered by NWC through secure transfer. This needs zero network connectivity and is the lowest-friction way to get approved.

### Gaps
- I found nothing on NWC's actual SCADA architecture, vendor or OT security policy.
- I did not locate a Caribbean-specific water OT incident.
- I did not verify ISA's current SL definitions or 62443-2-4 clause details from the primary source this session.

## 4. Cloud hosting, data residency, certifications, secrets and access control

### Takeaway
Jamaican law has no data localisation requirement, but cross-border transfer of personal data needs adequacy or an exception such as contractual safeguards or consent. Using non-personal SCADA and DMA telemetry avoids most of this. Utilities typically expect ISO/IEC 27001 or SOC 2 from vendors. A student team will not have these, so it should host in a provider that does and present a control mapping.

### Cited Findings
- No data localisation or residency obligations exist by sector or data category, and no approvals are needed for international transfers. Personal data transfers still need adequacy or an exception, including Commissioner-approved contractual terms. — [Chambers 2026](https://chambers.com/downloads/gpg/1129/013_jamaica.pdf)
- A May 2026 report says a cybersecurity firm called for a Caribbean cloud region by year-end. This suggests in-region hosting is not yet widely available. — [Jamaica Observer, 2 May 2026](https://www.jamaicaobserver.com/2026/05/02/cybersecurity-firm-calls-caribbean-cloud-year-end/) (headline only; article not fetched)
- CISA/EPA guidance lists third-party and supply-chain risk reduction among the top actions for water systems. — [EPA Top Cyber Actions](https://www.epa.gov/system/files/documents/2024-02/top8factsheet.pdf)

### Inferences
- **Hosting.** Use a major cloud region in the US, for example us-east, which has ISO 27001 and SOC 2 attestations, or NWC-hosted on-premises infrastructure. For any personal data, rely on DPA transfer exceptions such as contractual safeguards. Get NWC's explicit written approval of the region. Lawyer needed for transfer-clause wording.
- **Certifications.** A student project cannot obtain ISO 27001 or SOC 2 in pilot timeframes. Instead, provide the cloud provider's reports, a short security plan mapped to ISO 27001 Annex A or NIST CSF 2.0, and a completed vendor security questionnaire such as SIG Lite or CAIQ.
- **Secrets.** No credentials in the repo. Use a cloud secrets manager or environment variables injected at deploy time, rotate keys, and use per-environment keys. The current repository is a Streamlit app and should be checked for hard-coded keys.
- **Access control.** Least privilege, SSO or MFA for NWC staff, role-based dashboards (operator, analyst, admin), audit logs, encryption in transit (TLS 1.2+) and at rest, and data retention and deletion at pilot end as written into the data-sharing agreement.

### Gaps
- I found no NWC- or GOJ-specific cloud policy, such as a GOJ cloud-first policy or eGov Jamaica hosting rules. I did not verify whether any Caribbean hyperscaler region now exists.

## 5. Responsible AI: explainability, human-in-the-loop, not over-claiming

### Takeaway
Jamaica has no AI-specific law or guidance. The DPA's automated-decision right applies only if alerts are used for decisions about individuals, such as billing or disconnection. NIST AI RMF 1.0 and ISO/IEC 42001 give the vocabulary utilities and funders recognise. AquaWatch should present outputs as "anomaly alerts requiring verification", with confidence, evidence and a human decision step.

### Cited Findings
- Jamaica has no AI-specific requirements on personal data and no comprehensive AI regime. — [Chambers 2026](https://chambers.com/downloads/gpg/1129/013_jamaica.pdf)
- Data subjects can object to decisions that significantly affect them and are based solely on automated processing. — [Chambers 2026](https://chambers.com/downloads/gpg/1129/013_jamaica.pdf)
- NIST AI Risk Management Framework 1.0 (January 2023) is organised into Govern, Map, Measure and Manage. Its trustworthiness characteristics include valid and reliable, safe, secure and resilient, accountable and transparent, explainable and interpretable, privacy-enhanced, and fair. A Generative AI Profile (NIST AI 600-1) followed in July 2024. — [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) (canonical page; not re-fetched)
- ISO/IEC 42001:2023 (December 2023) is a certifiable AI management system standard. — [ISO 42001](https://www.iso.org/standard/81230.html) (canonical page; not re-fetched)

### Inferences
- **Wording.** Every alert should say something like "possible leak or anomaly, unverified", never "leak detected". Report precision and recall from back-tested historical data with known confirmed leaks, plus false-alarm rate per DMA per week. Utilities lose trust fastest from alert fatigue.
- **Explainability.** Show why an alert fired: the flow or pressure deviation against baseline, the minimum night flow trend, contributing sensors and a plot. Prefer interpretable baselines or statistical methods alongside any ML model.
- **Human in the loop.** An operator acknowledges, dismisses or dispatches each alert, and the outcome is logged as confirmed leak, false alarm or meter fault. These labels feed evaluation. There should be no automated action, especially none affecting customers' billing or supply.
- **Governance artefacts.** A one-page model card covering data, limits, known failure modes, intended use and prohibited uses, and a risk register mapped to the AI RMF functions. ISO 42001 certification is not needed for a pilot, but citing alignment helps.

### Gaps
- I found no Caribbean utility AI policy or OIC AI guidance.

## 6. How utilities run pilots with startups and universities: agreements, criteria, sandboxes, Caribbean examples

### Takeaway
The Caribbean route is through IDB, IDB Lab's "Source of Innovation" alliance and the regional associations CWWA and CAWASA. IDB has already piloted a data-sharing platform for Caribbean water utilities, with CWWA support. Successful utility pilots have a utility partner from design, written agreements (MoU, data-sharing agreement, NDA), clearly stated outcome KPIs, and a defined path to scale or procurement.

### Cited Findings
- In October 2023, IDB launched a one-year pilot of a data-sharing platform and virtual community for Caribbean water utilities, built with H2bid through the Source of Innovation alliance. It was aimed at post-storm recovery, with possible pooled procurement later. CWWA, the Caribbean Water & Sewerage Association (CAWASA) and the Caribbean Development Bank supported the launch. — [IDB news](https://www.iadb.org/en/news/idb-pilots-innovative-data-sharing-platform-caribbean-water-utilities); [Jamaica Observer, 24 Oct 2023](https://www.jamaicaobserver.com/2023/10/24/idb-pilots-innovative-data-sharing-platform-for-caribbean-water-utilities/)
- IDB Lab's Source of Innovation reports that 71% of its approved projects have a utility or service provider as client or partner from the design stage. — [IDB Source of Innovation](https://www.iadb.org/en/topics/water-and-sanitation/initiatives/source-innovation); [IDB blog](https://www.iadb.org/en/blog/water-sanitation-and-solid-waste/source-innovation-fostering-innovation-water-sanitation-and-waste-management-latin-america-and)
- IDB has a publication on lessons from innovation pilots in Latin American and Caribbean utilities. It emphasises clearly stated key outcomes as the basis for a scaling case. — [IDB publication (PDF; 403 on fetch, summary from search only)](https://publications.iadb.org/publications/english/document/Integrating-Innovative-Solutions-in-Water-and-Sanitation-Utilities-Lessons-from-Innovation-Pilots-in-Latin-America-and-the-Caribbean.pdf)
- IDB Lab's AQUACERTA challenge and its AquaConnect programme fund water-sector startups. — [AQUACERTA Challenge](https://challenges.adb.org/en/challenges/boosting-water-sector-innovation)
- NWC already uses performance-based NRW contracts with private operators (Miya). This shows a precedent for KPI-based external partnerships on leakage. — [Smart Water Magazine](https://smartwatermagazine.com/news/miya/miya-jamaica-joins-forces-nwc-reduce-severe-water-losses-kingston-and-st-andrew)

### Inferences: practical pilot package for AquaWatch
1. **MoU** between the university (or AquaWatch) and NWC. It covers scope (one or two DMAs), duration (3–6 months), no fees, roles, a named NWC champion in the NRW or operations unit, IP ownership (university or students, with a licence for NWC to use pilot outputs), publication rights subject to NWC review, and the Access to Information position.
2. **Data Sharing Agreement / Data Processing Agreement.** Lists the exact data fields and sensitivity, sets NWC as controller and AquaWatch as processor, and covers purpose limitation, pseudonymisation, no onward sharing, hosting region and transfer safeguards. Also covers security controls (section 3–4 list), breach notification to NWC within 24 hours, retention, and deletion and certification at pilot end. Lawyer needed.
3. **NDA**, mutual, covering network topology and SCADA details. Note that disclosing these is itself a security risk.
4. **Security annex.** Architecture diagram (one-way, read-only, DMZ), IEC 62443 zone and conduit mapping, NIST CSF 2.0 control summary, completed AWWA or EPA self-assessment for the tool, and named contacts.
5. **Sandbox and phasing.** Phase 0: historical extract, offline back-test, report. Phase 1: shadow mode, with daily batch feeds and alerts reviewed by NWC staff but not acted on. Phase 2: live alerts to staff, with field verification of a sample.
6. **Success criteria agreed up front.** For example, detection lead time against reported bursts, precision at N alerts per week, the share of field-verified alerts that were real leaks, estimated m³/day of losses found, and staff usability score. Also include exit criteria, defining what would justify a procurement step on GOJEP.
7. **Regional leverage.** Present results through CWWA's annual conference and CAWASA, and explore IDB Lab Source of Innovation or AQUACERTA funding. A regional funder's involvement can de-risk procurement for the utility.

### Gaps
- The IDB pilot-lessons PDF could not be fetched (403), so its specific recommendations are not quoted.
- I found no published NWC innovation or university partnership policy. I found no example of a Caribbean utility data-sharing agreement template.
- CWWA conference innovation tracks and dates were not confirmed from CWWA's own site.
