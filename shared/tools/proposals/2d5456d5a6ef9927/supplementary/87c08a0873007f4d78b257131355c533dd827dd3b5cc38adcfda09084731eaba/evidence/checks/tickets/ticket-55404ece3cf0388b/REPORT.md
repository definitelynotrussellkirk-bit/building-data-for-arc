# Allocation-quality ticket report

Ticket: `ticket-55404ece3cf0388b`  
Consumer: `bounded_owner_allocation_experiment_proposal`  
Pinned primary: `9c69eb63c11a`  
Ticket seed: `071fbf7046fed63e096027ecaf7eff66d6304afd0576bffa887d44b4c53ae009`

## Result

Completed one seeded three-record inspection and one targeted Racket-backed probe. No production weight, approval, source, audit resolution, or training job changed.

The deterministic sample was the primary target plus the first two other main-pool IDs ordered by `SHA256(ticket_seed + ":" + task_id)`:

| Family | Packet state | Weight | Current evidence | Bounded implication |
|---|---:|---:|---|---|
| `9c69eb63c11a` | unapproved / unverified | 1.0 | One unresolved current-source audit: advertised 3–5 blob/color controls collapse to exactly three; no task tests, semantic hook, parameter manifest, or `RULE_HASH` constant. | Spend only enough time to reconfirm or repair the already-localized support/axis defect. |
| `bb75d495c809` | approved / reviewed-safe / improved | 1.0 | One needs-triage current-source audit: unknown override and unsupported difficulty are silently accepted; bounded semantic distribution probe found no rule issue. No task tests or semantic hook in this packet. | Highest near-term leverage: repair the public API boundary on an approved family. |
| `9adaf46a8128` | unapproved / unverified | 1.0 | Three unresolved audits: marker 4 absent from demonstrations creates an answer-changing lesson ambiguity; color-count overrides are ignored; some advertised dimension endpoints are unusable. | Preserve substantial time for a real teaching repair plus exact-axis cleanup. |

## Actual draw and representation context

The packet includes 500 generators selected from 3,941 owner generators. The main draw is uniform over the included pool; priority affects inclusion/rotation, not per-record main-draw probability. Selection reasons were 320 coverage, 150 unfinished approved originals, 28 recent returns, two public-evaluation coverage entries, and one runtime dependency. Catalog weights in the selected pool were 498 at 1.0 and two at 0.0.

The dated training context reports an older frozen r6 export of 18,852 accepted episodes from 1,558 generators, with materialized token shares ARCpuzzles 37%, NVARC 36%, ARC-GEN 16%, and RE-ARC 11%. It also reports output side at least 20 for 7.3% of the ARCpuzzles export versus 47% of public evaluation. These are historical measurements, not fresh quality estimates for this packet. The seeded peer sample contains no ARC-GEN or RE-ARC record, and the packet supplied no current source-specific rejection/ambiguity/grammar receipts for those sources, so no source-level quality comparison is established here.

## Targeted probe

For `9c69eb63c11a`, one fixed default episode used three demonstrations and four queries (sample indices 0–6):

- seven distinct lawful inputs;
- all seven `self_check` results clean;
- 7/7 Python outputs matched the pinned Racket rule;
- no tested answer-changing rival fit all three demonstrations;
- `keep_second_largest` fit all demonstrations but also agreed on all four queries, because every generated input contained exactly three blobs.

The last item is answer-equivalent on current support, not query ambiguity. It is nevertheless diagnostic: the advertised wider 3–5-blob domain is absent, so “middle-sized” and “second-largest” cannot be separated in production lessons.

## Bounded allocation hypothesis

**Baseline:** 20/20/20 authoring minutes across `9c69eb63c11a`, `bb75d495c809`, and `9adaf46a8128`.

**Alternative:** 10/30/20 minutes.

This is an authoring-time hypothesis, not measured training quality or a global optimum. It caps work on the already-reproduced `9c69` support defect, prioritizes the approved `bb75` API-boundary repair, and retains substantial time for the explicit `9ada` lesson ambiguity and ignored-axis defects.

**Success metric:** accepted identifiable query targets per Racket-labelled grid and per authoring minute, with advertised-axis and semantic-role coverage reported separately.

**Bounded test and stopping rule:** for each family, attempt at most four episodes with three demonstrations and four queries and at most eight generation attempts. Require current source/rule hashes, seven distinct lawful inputs, Racket labels, and demonstration-only rejection of relevant answer-changing rivals. Stop a family immediately on source drift or label disagreement. Do not expand volume when fewer than three of four episodes pass, or when duplicate/rejection cost exceeds two attempts per accepted episode.

## Evidence

- `selection.json` — deterministic sample and draw-policy facts.
- `inspection.json` — source identities, catalog state, tests/hooks, and unresolved current-source audit summaries.
- `allocation-context.json` — pool composition and dated training context.
- `probe.json` — seven-grid Racket parity and finite-rival results.
- `report.json` — compact machine-readable outcome and proposal.
- `command.json`, `stdout.log`, `stderr.log`, `probe.py` — retained one-probe execution record.
