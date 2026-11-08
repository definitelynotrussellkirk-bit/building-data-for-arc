# Working notes: 02b21c59893a

## 2026-10-06 repair

The 3.0.1 generator admitted a noncanonical no-blue fallback and could schedule four fallback demonstrations before a blue-anchor query (reproduced at seed 861). It also declared overlapping ordinary/degenerate texture domains, unreachable canonical palette size 7, weak self-checks, and an unobservable override surface.

Version 4.0.0 removes no-blue and empty-payload production cases, pins the canonical rule hash, exposes one exact observable `scene_profile`, and uses a five-role cycle. Every role refutes source-at-origin and source-at-payload-bbox; two roles refute first-red; two roles refute all-or-nothing clipping. The Racket authority is unchanged.

Reusable independent evidence lives in `workspace/reference_probe.py`; design and implementation rationale are in the adjacent workspace files. Imported associated notes remain unchanged under `evidence/`.
## Current reviewer considerations

Source SHA-256: `66abb67e4ed0161fd60b795abcfd8953e3971749798c5ec7f3f0668377be9317`.

# Decisions — 02b21c59893a

## D1: Preserve the selected authority

The canonical rule hash remains `ba8a3944ecbc`; no Racket or canonical-data bytes changed. The selected rule requires one blue source, chooses the last red in row-major order, translates all other nonzero cells, preserves payload colours, and clips off-grid cells. Changing the rule would have hidden a teaching defect rather than repairing it.

## D2: Remove no-blue and empty-payload production cases

The 3.0.1 sampler could produce no-blue demonstrations and then rely on a Python fallback not present in the selected authority. Seed 861 produced four such demonstrations before a blue query, allowing the source-at-origin rival. Version 4.0.0 requires exactly one blue, one or two reds, and a 2–8-cell multicolour payload. Rejected alternative: retain no-blue as a low-probability degenerate; probability does not prevent an all-degenerate lesson window and the selected Racket calls `first` on blue points.

## D3: Use a five-role deterministic teaching cycle

The roles are `canonical_anchor`, `offset_anchor`, `last_red`, `last_red_clip`, and `clip_multicolor`. Every role refutes source-at-origin and payload-bounding-box source shortcuts. Two roles refute first-red, and two independently exhibit partial clipping, so holding out any one of five pairs leaves at least one witness for every declared rival. Rejected alternative: random weighting. Marginal witness frequency cannot guarantee lesson-level identifiability.

## D4: Retain all four canonical shape/palette profiles

The first four roles exactly realize `(8,9,6)`, `(9,10,7)`, `(7,11,5)`, and `(9,11,7)`. This fixes the baseline's unreachable seven-colour canonical profile while keeping a fifth difficulty-scaled noncanonical clipping role. The profile signature is observable for contract checking, but layouts remain seed-dependent; `checks/profile-nonmemorization-witness.json` shows two `canonical_anchor` seeds with different input and output hashes.

## D5: Collapse the override surface to one exact axis

Only `scene_profile` remains public. It is type-checked, has five finite values, is consumed by a keyed draw, and is exactly recoverable from returned pixels. Unknown keys and unsupported difficulties fail loudly. Rejected alternative: preserve numerous scalar size/texture controls; the baseline declared combinations that were ignored, overlapping, unreachable, or semantically unsafe.

## D6: Make clipping and anchor choice executable competitors

The generator declares four pure rivals: `always_origin`, `payload_bbox_origin`, `first_red`, and `all_or_nothing_clip`. `lesson_identifiable` validates labels and rejects a lesson only when a rival fits all demonstrations and differs on the query. The independent `workspace/reference_probe.py` mirrors the rule without importing private checker functions and can exhaustively test cyclic windows, exact profiles, and live Racket parity.

## D7: Test first and preserve failures

The focused suite was written against the baseline and failed 41 tests while 8 passed (`checks/task-tests-red/pytest-red.log`). The production rewrite then passed 49/49 source-bound tests. The baseline battery and seed-861 reproducer remain packaged rather than being overwritten.

## D8: Stop after source-bound production and rotation coverage were green

The final generator passed all 12 battery stages, 12/12 semantic production lessons, 60/60 required query rotations, a 300-lesson source-bound census with 1,500/1,500 unique pairs and 1,500/1,500 held-out rotations, and an additional 1,500-rotation independent probe. The post-repair visible-only solve passed all four visible demonstrations on revision 1. No remaining blocker justified further distribution expansion.

## Remaining limitations

The rival set is finite and does not prove universal identifiability. Production is intentionally narrower than the broad reference-lawful validator: it uses five role families, one or two red anchors, multicolour payloads, and at least one surviving translated cell. The deterministic role cycle is visible through profile dimensions/palette, though seed-dependent layout prevents direct output memorization; future model-based audits should still search for undeclared geometric shortcuts.
