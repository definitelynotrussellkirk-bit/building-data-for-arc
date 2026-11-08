# Working notes: ce40117f40f9

## Current native parametric acceptance

The retained prototype is now native-qualified and accepted on its exact current source; see `parametric/accepted.json` and `evidence/parametric-acceptance/`. A thin adapter adds independent 2–6 demonstration and 1–4 query counts, with the normal three-demo/four-query request verified across both settings and seeds 0/17. Original rule/sampler code remains selected within that adapter. Earlier proposed-status descriptions below are superseded only for these exact accepted bytes; canonical audit findings and training admission are separate.

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 generator contract repair

- Reproduced the prior false-positive validator on blank, marker-only, blob-only, and Boolean-cell grids; all are now rejected.
- Unknown overrides now fail loudly. Declared dimensions and blob sizes are literal, bounded controls (`6..30`, `2..6`) rather than ignored metadata.
- Source/marker placement is constructive and clipping-safe. Default lessons cycle through southeast, northwest, northeast, and southwest marker directions instead of teaching one placement shortcut.
- The blob is exactly sized, monochrome, compact, and 4-connected; the validator also checks a single marker, crop fit, and marker/source separation.
- Evidence: `WORK/checks/task2-racket-parity.json` executes four boundary/direction cases through the exact canonical Racket authority, including 6×6 and 30×30, with exact Python parity. `WORK/checks/task2-default-direction-probe.log` covers 300 default draws evenly across all four directions.

## 2026-10-24 marker-anchor parametric artifact

- Added `workspace/parametric/prototype.py` with `top_left` as the exact canonical/default Racket source and `bottom_right` as a one-site anchor substitution.
- Inputs come from the repaired production generator; both anchors fit without clipping, every demonstration and query separates the two settings, and each retained episode includes a 30×30 stress case.
- Retained evidence has one episode per setting, three demonstrations and four distinct queries each. Both rivals are refuted from demonstrations alone; all eight queries also disagree.
- Real-Racket evidence: 28 rule applications plus two canaries, 28/28 independent Python-mirror matches, sorted opaque public exports, and source hashes in `WORK/checks/ce40117f40f9-parametric-final-evidence/`.
