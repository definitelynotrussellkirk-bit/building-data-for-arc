# Working notes: 8ead1e696890

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-26 repair and native parametric build

Decision: preserve rule hash `e3401b50999e` and the exact canonical default, rebuild ordinary generation around exact separated component placement, then add the nearby `selection = border|top_area` family. The base repair removes dead controls, supports the documented 5–18 grid boundaries, generates 3–8 border and 1–8 interior components when compatible, and fails closed on unknown, impossible, or degenerate-incompatible overrides.

The alternate lesson identifies the unique top-border reference, measures its input-derived area, and keeps every component with that area; examples include a matching interior component and a wrong-area border distractor. Inputs are independent of the setting, four query inputs remain stable across demonstration counts, and a 32-seed bounded census passed for 2 and 6 demonstrations (128 episodes, 1,024 labeled pairs, maximum 30×30). The protected-Racket authoring preflight, causal witness/replay, one-query export checks, and first-turn privacy checks all passed.

Current status: reviewer-ready only. Owner acceptance and training admission were not performed; the next useful action is exact-source integration followed by native owner qualification and fresh acceptance replay. Primary evidence is under `checks/8ead1e696890/qualification/`, `checks/8ead1e696890/causal/`, and `checks/8ead1e696890/first-turn.json`.

## 2026-10-26 second audit

The second audit found two shortcuts. Fixed dimensions encoded a fixed top-reference area, and ordinary base samples contained only singleton border components, reducing the canonical rule to keeping nonzero border cells. Parametric generation now uses seed-keyed shuffled blocks over areas 1–5; the two smallest profiles were enlarged so every area remains feasible. The base generator now always includes a two-cell border component extending to a fully interior cell. A separate stress regression corrected left-border placement that could leave the lower-left quadrant empty.

Round-2 evidence: 75/75 combined focused tests, 44/44 isolated task tests, a 32-seed census covering every area on every fixed profile, 128 ordinary-generator census samples, 512 additional ordinary fuzz samples, and independent sweeps of every documented numeric axis with zero failures. Fresh source-bound preflight, witness, and public-projection evidence is generated under the round-2 check directories.
