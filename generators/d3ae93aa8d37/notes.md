# Working notes: d3ae93aa8d37

## Current native parametric acceptance

The retained prototype is now native-qualified and accepted on its exact current source; see `parametric/accepted.json` and `evidence/parametric-acceptance/`. A thin adapter adds independent 2–6 demonstration and 1–4 query counts, with the normal three-demo/four-query request verified across both settings and seeds 0/17. Original rule/sampler code remains selected within that adapter. Earlier proposed-status descriptions below are superseded only for these exact accepted bytes; canonical audit findings and training admission are separate.

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 canonical lesson-schedule repair

- Replaced independent 30%-chance wall placement with a deterministic four-profile lesson cycle: horizontal forced detour, open offset path, vertical forced detour, and dense reachable offset scene.
- Every consecutive four default samples now contains two obstacle-forced witnesses, so the retained seed-8/start-1 straight-row shortcut is refuted by the demonstrations rather than first failing on the query.
- Added strict malformed-grid, literal-cell, palette, endpoint-count, reachability, unknown-control, and exact-axis validation.
- Exact controls now support 6×6 through 30×30, endpoint geometry, Manhattan distance, wall count, and scene profile; every generated scene preserves an explicit open path.
- Evidence: `WORK/checks/task4-racket-parity.json` matches five generated scenes exactly against the canonical Racket authority, including the scheduled four-example lesson and a 30×30/100-wall boundary case.

## 2026-10-24 shortest-path tie-break prototype

- Added a task-local hidden parameter with two exact Racket programs: `canonical_udlr` keeps the canonical authority byte-for-byte, while `horizontal_first` changes only the single BFS neighbor-order expression to left, right, up, down.
- The independent Python mirror reconstructs BFS parents and paints only path interiors. A fixed 6×6 witness selects distinct top/left versus bottom/right Manhattan-length routes around a central 2×2 wall block.
- Episode sampling uses lawful `open_path`/`offset` production-generator draws, supports 2–6 demonstrations and exactly four queries, always includes a 30×30 case, and retains only inputs where both policies stay shortest and disagree.
- Evidence: `WORK/checks/d3ae93aa8d37-parametric-final-evidence/` executes 28 Racket rule applications plus two canaries, matches all 28 against the mirror, refutes both rivals from demonstrations, records eight held-out query disagreements, and emits sorted leak-free public challenges with private source-bound receipts.
