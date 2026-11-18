# Independent Phase 2 label audit

Audited 2026-11-17 on `feat/phase2-hardening` against base `092fd5e`. This is a read-only assessment of the existing labels; `events.csv` was not edited. Scope: the 18 rows added by `f64fbbb` plus UADH and TSI, whose previously unsourced rows gained citations in Phase 2. Existing GIF, LSTR, SERVI, MIP, and SOPAT rows are outside this requested per-row scope.

## Sequence and raw data

`git log --oneline --date=iso --format="%h %ad %s"` places these commits in this order:

| Commit | Date (+0100) | Relevant change |
|---|---|---|
| `9dbade7` | 2026-11-17 20:36:02 | Added `docs/EVALUATION_PROTOCOL_v2.md` (50 lines). |
| `f64fbbb` | 2026-11-17 20:43:10 | Expanded event registry. |
| `ed3127b` | 2026-11-17 20:50:23 | First added `src/detection/candidates_v2.py` and `outputs/evaluation/phase2_event_hits.csv`. |
| `e9824c0` | 2026-11-17 21:06:34 | Updated event dates and citations, including UADH and TSI. |
| `3a7d4e2` | 2026-11-17 21:13:57 | Hardened candidate pipeline and refreshed derived outputs. |

**Yes:** the protocol commit precedes candidate detector code and hit tables. `git log -- docs/EVALUATION_PROTOCOL_v2.md` returns only `9dbade7`, and `git diff 9dbade7..HEAD -- docs/EVALUATION_PROTOCOL_v2.md` is empty: no later protocol change. `git diff --name-status 092fd5e..HEAD -- bvmt_data/` is also empty: `bvmt_data/` is unchanged against base at the path and Git-object level.

## Source-by-source review

`CONFIRMED` means the cited page supports the company, stated event kind, and **public event date**. Dates of underlying meetings or rulings are distinguished below. `MISMATCH` identifies a material claim or date that the cited page does not support. None of these cited URLs was unreachable. Short quoted strings are the exact page text; the assessment after each quote is mine. A `SOURCE_NEEDED` row without a URL cannot be opened and is outside this source-citation count.

| Event | Verdict | Exact text found and assessment |
|---|---|---|
| UADH-2026 | **MISMATCH** | [BVMT PDF](https://www.bvmt.com.tn/sites/default/files/avis-decisions/uadh-tlyq-ltdwl.pdf): “UADH”; “suspendue à compter du mercredi 25 mars 2026.” Company and suspension match, but the PDF gives **25 March**, not the row's 24 March public date; it has no visible issue date. A separate 24 March publication would be needed to substantiate the current anchor. |
| TSI-2025-inquiry | **CONFIRMED** | [CMF bulletin](https://www.cmf.tn/sites/default/files/pdfs/publications/bulletin-officiel/bo250423.pdf): “MESURES PREVENTIVES RELATIVES A LA SITUATION DE L'INTERMEDIAIRE EN BOURSE TSI”; “Mercredi 23 avril 2025.” The Arabic notice states the inquiry began 9 January, distinct from the 23 April bulletin date. |
| OTH-2021-capital | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/onetech-holding-augmentation-de-capital-approuvee_31068): “OneTech Holding : Augmentation de capital approuvée”; “Publié le 29/10/21 10:34.” The meeting was 27 October; the row uses publication date. |
| LNDOR-2021-capital | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/land-or-l-augmentation-de-capital-approuvee-par-l-assemblee-generale-extraordinaire_31547): “L'augmentation de capital approuvée”; “Publié le 26/11/21 09:33.” Meeting date was 19 November. |
| ATB-2021-capital | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/atb-l-age-approuve-l-augmentation-de-capital-de-28-millions-de-dinars-reservee-a-l-arab-bank_31564): “L'AGE approuve l'augmentation de capital”; “Publié le 26/11/21 18:10.” |
| ADWYA-2022-buyout | **MISMATCH** | [Article](https://www.ilboursa.com/marches/suspension-de-la-cotation-des-titres-adwya_34995): “la cotation des titres ADWYA est suspendue”; “Sans pour autant dévoiler les raisons de la suspension”; “Publié le 07/06/22 09:43.” Company, suspension and date match; this cited document expressly does **not** establish the row's takeover/buyout explanation. |
| CREAL-2022-opa | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/cardinal-brands-nouvel-actionnaire-majoritaire-de-cerealis-lance-une-opa_37790): “Cardinal Brands, nouvel actionnaire majoritaire de CEREALIS, lance une OPA”; “Publié le 14/11/22 16:53.” |
| WIFAK-2023-suspension | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/suspension-de-la-cotation-des-titres-wifak-bank_38650): “WIFAK BANK est suspendue à partir du lundi 09 janvier 2023”; “Publié le 09/01/23 09:07.” The page alone does not establish wrongdoing. |
| STPAP-2023-fire | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/incendie-dans-l-usine-de-sotipapier-cotation-suspendue-a-la-bourse-de-tunis_42802): “son usine a été impactée par un incendie”; “suspension de la cotation”; “Publié le 28/09/23 09:50.” Fire began 25 September; the row's 28 September is the report/suspension date. |
| SPHAX-2023-bankruptcy | **MISMATCH** | [Article](https://www.ilboursa.com/marches/mise-en-faillite-de-la-compagnie-aerienne-syphax-airlines_44054): “a décidé le 11 décembre 2023 de mettre en faillite la société Syphax Airlines”; “Publié le 19/12/23 10:46.” The row calls the **19 December** date `court_ruling`; that is the publication date, while the ruling occurred **11 December**. |
| SMART-2024-capital | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/smart-tunisie-augmentation-de-capital-annoncee_49080): “SMART Tunisie : Augmentation de capital annoncée”; “Publié le 31/10/24 17:11.” Board decision was 28 October. |
| BIAT-2024-capital | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/biat-augmentation-de-capital-annoncee_49512): “BIAT : Augmentation de capital annoncée”; “Publié le 27/11/24 08:35.” Meeting was 1 November. |
| SMD-2025-capital | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/sanimed-lance-une-augmentation-de-capital-de-10-millions-de-dinars_51474): “SANIMED lance une augmentation de capital”; “Publié le 13/03/25 09:03.” The article also mentions a December 2024 decision, a different milestone. |
| TJARI-2025-dividend | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/attijari-bank-propose-un-dividende-de-5-dinars-par-action-et-une-augmentation-de-capital_51499): “propose un dividende de 5 dinars par action et une augmentation de capital”; “Publié le 14/03/25 10:38.” |
| MPBS-2025-split | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/mpbs-propose-un-dividende-de-0-370-dinar-par-action-et-une-operation-de-split_52367): “proposer une opération de split”; “Publié le 28/04/25 17:15.” The row is a proposal, not implementation. |
| DH-2025-split | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/delice-holding-annonce-le-split-de-la-valeur-nominale-de-son-action-a-5-dinars_54085): “La date d'effet de cette division est fixée pour le 1er août 2025”; “Publié le 28/07/25 14:14.” Announcement date matches; effective date differs as expected. |
| SIAME-2025-dividend | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/la-siame-reporte-la-distribution-des-dividendes-au-titre-de-2024-sous-instruction-judiciaire_57655): “un report décidé sous instruction judiciaire”; “Publié le 14/11/25 14:37.” |
| PGH-2026-buyout | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/le-cmf-demande-la-suspension-de-cotation-des-titres-poulina-et-land-or_59920): “PGH” and “LAND'OR” suspended “jeudi 19 février 2026”; “Poulina va racheter ... sa participation dans le capital de Land'Or.” This is one shared notice. |
| LNDOR-2026-buyout | **CONFIRMED** | [Same article](https://www.ilboursa.com/marches/le-cmf-demande-la-suspension-de-cotation-des-titres-poulina-et-land-or_59920): “PGH” and “LAND'OR” suspended “jeudi 19 février 2026”; the stated stake transaction concerns Land'Or. Correlated with PGH row. |
| ASSMA-2026-dividend | **CONFIRMED** | [Article](https://www.ilboursa.com/marches/assurances-maghrebia-dividende-de-2-900-dinars-et-attribution-d-actions-gratuites_60570): “Dividende de 2,900 dinars et attribution d'actions gratuites”; “Publié le 19/03/26 16:28.” The article describes a proposal to be voted on later. |

**Tally: 17 confirmed, 3 mismatched, 0 unreachable (20 rows).**

## Date corrections and primary-window effect

The protocol defines an inclusive window of event date minus 30 through plus 5 **calendar days**. No CSV was changed.

| Event | Recommended action | Window implication |
|---|---|---|
| UADH-2026 | The cited PDF alone supports a 2026-03-25 suspension, not a 2026-03-24 public announcement. Unless a dated 24 March notice is supplied, correct `event_date` to **2026-03-25** and `event_date_type` to `suspension`. | Moves 2026-02-22–2026-03-29 to **2026-02-23–2026-03-30**: drops 22 February, adds 30 March. |
| SPHAX-2023-bankruptcy | **Do not silently move the public-date anchor.** Correct `event_date_type` from `court_ruling` to `public_announcement` if 2023-12-19 remains the earliest verified public date. If the intended label is instead the actual court ruling, its date is **2023-12-11**, but public availability on that day is not established by this source. | A conditional move to 11 December would change 2023-11-19–2023-12-24 to **2023-11-11–2023-12-16**: adds 11–18 November and drops 17–24 December. A type-only correction leaves the window unchanged. |

ADWYA needs a narrower event description or a separate takeover source, not a date change. The other 17 reviewed rows have no source-based date correction identified.

## Edits after candidate code existed

Candidate code and `phase2_event_hits.csv` first appeared in `ed3127b` (2026-11-17 20:50:23 +0100). Commit `e9824c0` followed at 21:06:34. Its entire `data/evaluation/events.csv` change is below; `event_date` and `event_date_type` were unchanged for all three rows.

| Event | Old → new event_date | Old → new event_date_type | Old source → new source | Did a detector's hit/miss change? |
|---|---|---|---|---|
| GIF-2024-radiation | 2024-10-25 → 2024-10-25 | suspension → suspension | `https://www.ilboursa.com/marches/la-bourse-de-tunis-decide-la-radiation-de-la-societe-gif-filter_49247` → `https://tunis-stockexchange.com/en/node/6451` | No. The committed hit table is identical immediately before and after this commit. |
| LSTR-2024-bankruptcy | 2024-07-23 → 2024-07-23 | suspension → suspension | `https://www.ilboursa.com/marches/en-cessation-de-paiement-le-tribunal-declare-la-faillite-de-la-societe-electrostar_47391` → `https://managers.tn/2024/07/23/la-societe-electrostar-declaree-en-faillite/` | No. The committed hit table is identical immediately before and after this commit. |
| SERVI-2024-bankruptcy | 2024-01-11 → 2024-01-11 | suspension → suspension | `https://www.ilboursa.com/marches/le-tribunal-de-tunis-declare-la-faillite-de-la-societe-servicom_45451` → `https://www.ilboursa.com/marches/suspension-de-la-cotation-du-titre-servicom_44316` | No. The committed hit table is identical immediately before and after this commit. |

`git diff --name-status e9824c0^ e9824c0 -- outputs/evaluation/` is empty. The committed pre/post `phase2_event_hits.csv` and `phase2_comparison.csv` are identical; no recorded method hit or miss changed. Their unchanged contents do not prove that a fresh rerun was performed at `e9824c0`, but unchanged dates, roles, and inclusion fields also mean the source swaps alone would not change the computed hit windows.
