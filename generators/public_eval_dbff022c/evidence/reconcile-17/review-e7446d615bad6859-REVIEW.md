# Two public-parent authoring builds — review-e7446d615bad6859

Targets: `public_eval_62593bfd` and `public_eval_dbff022c`; source version 1.0.0.
Baseline: both task homes contained only their frozen public-parent provenance.
Repair: authored general Racket references, standalone generators and two native settings per parent.
Original-label checks: 4/4 + 4/4 protected-Racket matches; no answer lookup in references.
Final suites: 28/28 and 31/31 official staged tests; 84/84 combined tests including 25 helper tests.
Preflight: four jobs per parent, current source-bound authoring evidence; NOT native qualification.
Self-review: 192 finite-audit lessons per parent, 17/22 declared policies; no harmful surviving rival.
Causal replays: wrong area intermediate changes 54/46 cells on substantive 30x30 queries.
Public export: 16+16 independently shuffled sequential views; saved-byte/leakage checks pass.
Status: reviewer-ready, needs owner registration, native qualification and acceptance; training not admitted.
Limits: finite rival sets and admitted sampler grammar, not universal rule uniqueness; author self-review only.

## 62593bfd: area-frequency relocation

The canonical rule discovers **same-color eight-connected components**, measures
occupied area and its multiplicity across components, then moves repeated-area
objects to the top and unique-area objects to the bottom. Columns, pixels and
colors are preserved. Repeated colors are not merged across spatial objects.
The native `match_by=bbox_area` setting changes only the measurement; the default
`occupied_area` program is byte-identical to `reference.rkt`.

The sampler varies colors and nonzero backgrounds, six to eight components,
repeated-size groups including triples, diagonal connectivity, equal-size unequal
shapes, unequal-size equal boxes, rings, isolated distractors and boundary contact.
It supports 2–6 prefix-stable demonstrations and exactly four distinct queries.
The 30x30 case has distributed actual content. Destination footprints are disjoint
by construction; arbitrary overlapping destinations are outside this sampler's
grammar and are not claimed order-independent.

Current evidence (the older `preflight/` directory is superseded by `preflight-final/`):
- `checks/public_eval_62593bfd/preflight-final/{preflight,execution,original-pairs}.json`
- `checks/public_eval_62593bfd-tests-final/{result.json,task_tests.xml}`
- `checks/public_eval_62593bfd/audit.json`: 32 seeds × 3 demo counts × 2 settings = 192 lessons, 1,472 pairs, 17 named policies.
- `checks/public_eval_62593bfd/protected-rivals.json`: 44 protected-Racket rival/parity evaluations.
- `checks/public_eval_62593bfd/delivery/`: 16 public views, 40 protected boundary labels, causal witness and fresh replay.
- `checks/public_eval_62593bfd/handoff-validation.json`: 215 checks, 152 source-bound files, fresh protected replay.

The causal case uses occupied-area multiplicities versus bounding-box-area
multiplicities to choose different destinations. It changes **54 cells**, not
just a metadata field or an equivalent ordering.

An initial official staging run had 27 passing tests and one failing runtime-root
lookup: `reviewer_support.find_root` walked out of the unregistered staging tree
and selected the outer packet runtime. The test now uses its explicit staged task
layout; all 28 tests pass in the new official run. The failed receipt is retained
as resolved evidence, not counted as a passing run. Preflight was refreshed after
the test-source change.

## dbff022c: inward legend and enclosed regions

The canonical rule finds the solid multicolor, two-cell-thick edge legend and
reads each pair **inward** from the canvas boundary. It discovers four-connected
background regions that do not reach the canvas edge; a monochromatic enclosing
boundary supplies the directed legend key. It fills mapped regions, leaving open
background, unmapped regions, boundaries and the legend unchanged. Mapping is
one-step, not transitive or bidirectional.

`fill_scope=all` exactly preserves the authored reference. `largest_per_color`
uses the same region records but fills only maximum occupied-area regions for each
boundary color, keeping all ties across distinct objects. The sampler varies all
four legend edges, colors/backgrounds, multiple holes in one object, multiple
objects of one color, tied sizes, irregular holes, diagonal enclosures, open
shapes, absent keys and self-maps. Generated legends have unique keys and separated
components. Ambiguous corner-table geometries are outside the admitted grammar.

Evidence:
- `checks/public_eval_dbff022c/preflight/{preflight,execution,original-pairs}.json`
- `checks/public_eval_dbff022c-tests/{result.json,task_tests.xml}`
- `checks/public_eval_dbff022c/audit.json`: 192 lessons, 1,472 pairs, 22 named policies.
- `checks/public_eval_dbff022c/protected-rivals.json`: 36 protected-Racket rival/parity evaluations.
- `checks/public_eval_dbff022c/delivery/`: 16 public views, 40 protected boundary labels, causal witness and replay.
- `checks/public_eval_dbff022c/handoff-validation.json`: 215 checks, 152 source-bound files, fresh protected replay.

The causal case substitutes bounding-box areas for exact region areas. The
compact 35-cell hole and an 11-cell L-shaped hole (box area 36) exchange selection,
changing **46 cells** on a 30x30 query.

### Actual teaching failure retained and repaired

The initial minimum lesson allowed a `paint_hole_boxes` rival to fit both
visible demonstrations yet change the held-out 30x30 query by four cells.
`pre-repair-counterexample.json` retains the exact programs, inputs and labels;
six protected executions confirmed the discrepancy. Small self-colored diamond
holes hid the wrong boundary painting. The first demonstration now maps that
nonrectangular hole to a distinct color; alternating scenes retain true self-maps.
This schedule does not inspect query inputs or labels. The added regression failed
before the repair and passes after it.

`checks/replay_pre_repair_case.py` replays the frozen proof without importing the
now-repaired sampler. Its fresh `pre-repair-replay.json` again records differences
`[0, 0, 4]`. Its tests reject empty evidence and altered saved labels. The broad
finite audit was rerun on the repaired sampler. Benign equivalent policies are
reported explicitly rather than misrepresented as distinguishable.

## Reproducibility and tools

Task-local audit and protected-rival scripts ship with each build. Reused
`checks/authoring_evidence.py` verifies current source hashes, regenerated episodes,
complete finite audits, boundary outputs, exact saved public bytes, independent
query permutations, no settings/program/answer/future/count exposure, and the
actual owner witness schema. Its regression fixture now discovers a ready target
from `RESULTS.json` rather than hardcoding a previous task.

`checks/verify_source_delta.py` applies the source patch to the exact uploaded
baseline and compares every reconstructed file with the tested tree. It does not
execute user code or assert owner acceptance. The two tools are reused from the
previous return and re-tested, not represented as newly authored this round.

Replay commands are executed from the outer extracted packet:

```sh
python3 review.py run python3 -m pytest --import-mode=importlib generators/public_eval_62593bfd/tests generators/public_eval_dbff022c/tests ../checks/tests -q
python3 review.py run python3 ../checks/authoring_evidence.py verify --root . --preflight ../checks/public_eval_62593bfd/preflight-final/preflight.json --out ../checks/public_eval_62593bfd/delivery --replay --report ../checks/public_eval_62593bfd/handoff-validation.json
python3 review.py run python3 ../checks/authoring_evidence.py verify --root . --preflight ../checks/public_eval_dbff022c/preflight/preflight.json --out ../checks/public_eval_dbff022c/delivery --replay --report ../checks/public_eval_dbff022c/handoff-validation.json
python3 review.py run python3 ../checks/replay_pre_repair_case.py --root . --proof ../checks/public_eval_dbff022c/pre-repair-counterexample.json --report ../checks/public_eval_dbff022c/pre-repair-replay.json
```

The combined final suite is recorded in `checks/final-tests.xml` and
`checks/final-tests-command.json`. These are the complete assigned-task suites and
helper tests, not a claim that every unrelated generator in the full snapshot
was tested. Earlier red tests and the resolved first staging failure are retained.
Temporary copied staging runtimes and caches are excluded from the delta.

## Final author review / owner boundary

Reviewed the two references, Python parity implementations, adapters, samplers,
finite audits, invalid-request handling, standalone relocation, and public export
and witness bindings. The full Racket label checks are separate from the larger
Python rival audits. No independent subagent review was available.

No shared source, canonical authority, catalog, approvals or training gates were
modified. Both defaults equal their authored root references byte-for-byte;
standalone `generator.py` and the native `model.py` remain identical copies.
Registration under `ee_62593bfd` / `ee_dbff022c`, exact-live-source qualification,
owner acceptance and training admission remain owner steps. `ready` and
`completion_state=complete` mean the reviewer authoring return is complete only;
the round's two-owner-acceptance objective is still pending.

## Source-patch reconstruction

The exact uploaded baseline plus the returned source patch reconstructs all 26 changed source files byte-for-byte against the tested tree. `checks/source-delta-roundtrip.json` binds this proof to the patch SHA-256 and each reconstructed file; changes are confined to the two assigned homes. The packet's return validator, full decompression/CRC, path safety and packaged artifact hashes were also checked.
