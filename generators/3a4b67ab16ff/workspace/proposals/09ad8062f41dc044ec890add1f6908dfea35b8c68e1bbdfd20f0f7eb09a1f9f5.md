# Review: `3a4b67ab16ff` generator `3.1.0`
Task/source: `3a4b67ab16ff`; final generator SHA-256 `fb837ad93ced67cb30cb20dc6981352c03c2b92c89b4578f3db0f711ac6e3ef2`; canonical rule hash `32c694357bd0`.
Defect: the retained curriculum let a first/last-occurrence bounding-box shortcut agree with the canonical examples.
Repair: added a recoverable `split_extrema` lesson whose four non-corner markers jointly determine all extrema and defeat that shortcut.
Teaching contract: named `endpoint_only_bbox` as a rival and bound it to `split_extrema_refutes_endpoint_only_bbox`.
Boundary repair: `generate` now rejects bool/non-integer seeds and sample indices and rejects negative sample indices.
Checks: 17 focused authored tests passed; all 12 final source-bound lint, Racket, distribution, semantic, diversity, override, grammar, and authority stages passed.
Exact Racket: 120/120 rule-smoke applications succeeded with 0 crashes, 0 parity mismatches, 101 distinct outputs, and input purity.
Prototype: built a separate proposed `layer_order={ascending,descending}` episode writer with 3 demos and 4 distinct exact-Racket queries per setting.
Limit: aggregate `task_tests` is blocked before pytest by the issued frozen fixture's non-portable root calculation; that fixture remains byte-identical as required.
Reference rule: canonical Racket is unchanged; only the selected base `target_code` text was synchronized exactly to canonical formatting, while archival `raw_code` stayed untouched.
Disposition: repair is ready for maintainer replay; the parameter variant is a proposal only and grants neither approval nor training admission.

## Concrete generator repair

The canonical transformation uses **all** occurrences of each marker color to obtain its bounding box. The prior examples did not force that distinction strongly enough: a shortcut taking only the first and last row-major occurrences could still produce the same box. The new `split_extrema` profile places four markers so that:

- no marker is at a bounding-box corner;
- separate markers supply the top, bottom, left, and right extrema;
- the first/last row-major pair has a different box from the full marker set; and
- the full box still intersects the gray rectangle in a lawful, recoverable lesson.

The generator recognizes this profile, supports it in every difficulty band, exposes it through `observe_overrides`, and samples it in the default curriculum. Adding the profile initially reduced fixed-schedule canonical-profile support, so the final weighting preserves the strict profile floor by increasing the existing public-profile weight rather than removing the new lesson. Final profile evidence records 19 exact canonical-profile hits in 60 draws, with support in easy, medium, and hard.

A machine-readable semantic contract now names the exact shortcut:

- rival: `endpoint_only_bbox`;
- witness: `split_extrema_refutes_endpoint_only_bbox`;
- binding: `WITNESS_RIVALS`.

The final semantic gate sampled 600 generated inputs. The witness fired 47 times across all three bands, and the rival disagreed with the authoritative output on all 47/47 checked witnesses, with no oracle or rival errors. See `checks/final-semantic-gate/checks/3a4b67ab16ff_after_semantic_gate.json`.

The public `generate` boundary now also rejects coerced scalar inputs. In particular, booleans, floats, strings, and `None` no longer silently enter seed/sample-index logic, and negative sample indices are rejected. These are covered by focused regressions in `tests/test_split_extrema_repair.py`.

## Proposed parametric extension

`workspace/parametric/prototype.py` implements a task-local `layer_order` proposal while leaving production and canonical behavior unchanged:

- `ascending` is the exact canonical program and remains the default;
- `descending` changes only the final color traversal order;
- each episode fixes one setting;
- paired episode seeds share the same sampled inputs, so the hidden setting does not select easier grids;
- inputs use the production `overlap_priority` grammar, where overlap reveals which layer wins;
- each retained setting has 3 labeled demonstrations and 4 distinct public query inputs;
- both demonstrations and queries distinguish the alternative setting;
- public IDs hash only visible public bytes; settings, programs, seeds, and query answers remain private.

The evidence build executed 28 protected-Racket calls, replayed all four canonical pairs under the default program, checked four split-extrema examples, and retained complete public/private manifests. The report is `checks/parametric/3a4b67ab16ff-layer-order-v1/report.json`. This is deliberately separate from the generator API and is not an approval or admission decision.

## Verification performed

- Focused regressions: `checks/focused-tests-final/pytest.log` — **17 passed**.
- Lint and self-check: `checks/final-lint/`, `checks/final-selfcheck/` — pass.
- Exact-Racket smoke: `checks/final-rule-smoke/checks/3a4b67ab16ff_after_rule_smoke.json` — 120 applied, 0 crashes, 101 distinct outputs, 120/120 mirror parity.
- Strict defect lint: `checks/final-defect-lint/` — 0 flagged.
- Distribution/profile support: `checks/final-dist-gate/`, `checks/final-profile-floor/` — pass; 19/60 exact profile hits.
- Semantic rival gate: `checks/final-semantic-gate/` — pass; 47/47 witness-rival disagreements.
- Diversity: `checks/final-diversity/` — 300 pairs, 76% unique inputs and outputs, 0 flagged.
- Override contract: `checks/final-override/` — 1530/1530 accepted across 17 cases and 3 bands, 0 findings.
- Grammar and canonical Racket lint: `checks/final-grammar/`, `checks/final-racket-lint/` — pass.
- Authority synchronization/parity: `checks/final-authority-sync/` — pass; selected source synchronized, archival source intentionally divergent, execution parity preserved.
- Parametric exact-Racket build: `checks/parametric/3a4b67ab16ff-layer-order-v1/` — pass.

## Remaining limit

The issued frozen test `tests/test_generator_3a4b67ab16ff.py` computes its repository root with a fixed `Path.parents[...]` depth. In the portable task-test runtime this resolves beneath the task and preflight cannot locate `data/canonical/puzzles.jsonl`. The retained diagnostic is `checks/final-task-tests-frozen-blocker/result.json`. Per assignment rules, the frozen fixture was restored to and remains at baseline SHA-256 `b6aa65b4bf7fe0dc7f5ce267300cd5b2871e990ef2a17f460230377436a46244`; separate authored-test success is not reported as aggregate task-test success.

## Supplementary tickets

- `parameter_queries`: the pinned peer prototype is source-current and privacy-clean for both settings, but its retained episodes contain only one query, not four, and explicitly remain unapproved. See `checks/tickets/ticket-8d220547d8048f66/`.
- `allocation_quality`: the unsafe pending focal generator is correctly excluded from the 113-task reviewed-safe pool despite a legacy weight of 1.0. A bounded 7-pair probe was mechanically clean but cannot exceed 18×18; production allocation should remain zero pending full review. See `checks/tickets/ticket-684825f5c790f7f2/`.
