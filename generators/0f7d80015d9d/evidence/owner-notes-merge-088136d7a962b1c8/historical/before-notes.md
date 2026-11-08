# Working notes: 0f7d80015d9d

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `2bcf9589c3a7c35f27df8976a57635e91cfc05e09bdd2368b7682982a004ea09`.

# DECISIONS

## Context and prior lead

The baseline was the packet-pinned generator SHA `f576456b685e460e55ddfcd13d3554b45e6b391505bf80e7e4a3a618e23a7e8f`, not an unintegrated prior patch. I used the associated note from return `review_response_external-local-random-be3fbf8285ff_x` / assignment copy `local-random-be3fbf8285ff` only as a lead: it motivated preserving the four-profile lesson schedule and midpoint witness, but all current probes were rerun from the pinned baseline and final source.

## D1 — Make canonical anchors relational, not merely dimensional

**Original rationale:** Canonical anchors were intended to retain support for the official geometry while generalized scenes broadened the distribution. The original code pinned a canonical `(grid_h, grid_w, rect_h, rect_w)` tuple but did not pin the official relation that both markers sit immediately above the rectangle; the old `strict_canonical_like` therefore certified loose marginals as strict.

**Decision:** In anchor blocks, sample both markers on `rect_top - 1`, and require that cap-row relation in `strict_canonical_like`.

**Alternatives rejected:** (1) Rename the old predicate “geometry-only” and leave the data unchanged: this would preserve misleading strict-profile evidence. (2) Put all generated markers on the cap row: this would erase useful vertical nuisance variation. The selected design makes only the explicitly scheduled strict block canonical.

**Probe and failure mode:** `test_canonical_anchor_blocks_put_both_markers_on_the_rectangle_cap_row` and `test_strict_profile_rejects_canonical_geometry_with_noncanonical_marker_rows` failed before the repair. Final source produces 186 scheduled anchors per band in the 128-seed six-pair probe, all 186 cap-row and strict. The finite probe does not prove every future canonical relation remains encoded if the canonical dataset changes.

## D2 — Sample the full lawful rectangle-size manifold

**Original rationale:** The input grammar only requires an aspect class and enough room for markers/destination, but the baseline used arbitrary caps: wide/tall thickness at most 4 and square size at most 6. This trained a shortcut that “wide” or “tall” meant thin.

**Decision:** Enumerate every lawful `(rect_h, rect_w)` pair within the selected grid satisfying `wide`, `tall`, or `square`, then sample uniformly from that set. A single marker row above is sufficient; only the eventual output side needs an exterior column.

**Alternatives rejected:** (1) Raise the caps from 4 to another constant: still an artificial boundary. (2) Sample dimensions independently and reject until aspect fits: valid but less transparent, with harder-to-audit weighting. (3) Weight all sizes by area: no evidence justified that curriculum choice.

**Probe and failure mode:** On forced 19×19 scenes, final support reaches wide `rect_h=17` / `rect_w=18` with 77 observed size pairs, tall `rect_h=18` / `rect_w=17` with 75 pairs, and square size 18 with 16 pairs across seeds `0..127`. Uniformity over candidate dimension pairs is a design choice; it is not uniform over rectangle area or rendered grids.

## D3 — Permit lawful contact on the non-destination side

**Original rationale:** The rule needs one exterior destination cell only on the side opposite red. Requiring margins on both sides removed lawful cases and made edge position a shortcut.

**Decision:** For `left_opposite`, allow the rectangle to touch the left edge while preserving a right margin. For all profiles whose true output is left, allow right-edge contact while preserving a left margin.

**Alternatives rejected:** (1) Keep bilateral margins to simplify rivals: this lets implementation convenience define the training grammar. (2) Allow contact on the destination side and clip/wrap output: that would change the task rule and authority.

**Probe and failure mode:** Forced 9×9 draws observed 73/128 left-edge contacts for `left_opposite` and 71/128 right-edge contacts for `right_opposite`; all true outputs remain in bounds. The exact frequencies arise from uniform legal placement and are not a promised balance target.

## D4 — Keep declared rivals total on the widened lawful domain

**Original rationale:** A counterfactual competitor is useful only if it produces a prediction for every lawful lesson input. Edge contact caused wrong-side competitors to raise when their imagined stamp fell outside the grid.

**Decision:** A rival whose wrong-side destination is unavailable returns the recolored grid without that impossible extra stamp. The authoritative mirror and Racket rule are untouched and never enter this branch because generation preserves their destination side.

**Alternatives rejected:** (1) Remove edge cases: rejects D3's valid domain. (2) clamp or wrap rival stamps: invents a second unsupported transformation. (3) drop the rivals on those inputs: weakens identifiability evidence exactly where the hypotheses differ.

**Probe and failure mode:** The retained red run `checks/tdd-red-rivals/result.json` reproduced the exception; the final test checks every declared lesson competitor on generated edge scenes. Omitting an impossible counterfactual stamp is one explicit semantics for these rivals, not a claim that every human wrong rule would behave that way.

## D5 — De-alias periodic anchors from the actual lesson window

**Original rationale:** Four consecutive indices share a profile-complete anchor decision, and one block in four was intended to be strict. However, the sampler always begins near index 0; the old phase made every six-pair production episode contain four anchors, despite a 25% long-run claim. Once D1 made anchors truly canonical, this repeated geometry collapsed the intermediate diversity result to 76% unique inputs and 57% unique outputs.

**Decision:** Derive an anchor-block phase `0..3` from `(seed, task, version)` and anchor blocks whose index modulo 4 matches that phase. Each anchor decision still spans all four teaching profiles. Over every 32 indices per seed there are exactly 8 anchors; across six-pair episodes the observed count varies with seed.

**Alternatives rejected:** (1) Offset the fixed phase to another constant: merely moves the alias. (2) decide independently per example: can hide one profile behind a scale change and weaken lesson identifiability. (3) decide each block with an unconditioned Bernoulli draw: long small schedules would have noisy strict coverage and harder reproducibility.

**Probe and failure mode:** Seeds `0..127` produced six-pair anchor counts `{0:70, 2:23, 4:35}` and exactly `2048/8192 = 25%` over 64 indices; every four-example block is homogeneous. A small batch can legitimately have zero anchors, so consumers requiring a strict example in every individual episode must request a different schedule contract.

## D6 — Leave the Racket authority unchanged

**Original rationale:** All discovered defects were in input support, evidence semantics, or lesson scheduling. The selected Racket program continued to match canonical outputs and the Python mirror.

**Decision:** Keep declared rule hash `9744dc525afc` and all canonical rule text unchanged.

**Alternatives rejected:** No rule edit was justified. Changing Racket to accommodate wrong-side edge cases would have altered labels instead of fixing the generator/rivals.

**Probe and failure mode:** Rule smoke, Racket lint, semantic gate, and authority sync are green in the final battery; authority execution parity is PASS. The archival raw-code divergence reported by authority sync remains outside the selected task-local repair and was not hidden.

## D7 — Preserve fixed-query production, report rotated-query limits

**Original rationale:** Production assembles four demonstrations followed by the query; the four profiles are designed as a complete teaching set. The required diagnostic also rotates each pair into the query slot, which is a stronger assembly policy than production actually uses.

**Decision:** Treat 0/300 production ambiguities as the relevant production result, but retain the census exit code 1 and explicitly report 675/1,500 ambiguous rotations. Do not weaken the rival set or relabel the command as a pass.

**Alternatives rejected:** (1) Omit `--rotate-query`: would hide a useful domain limit. (2) call the entire generator ambiguous: conflates unsupported reordering with actual downstream assembly. (3) redesign every five-pair rotation to be identifiable: would require a larger or redundant teaching schedule and was not requested by the fixed-query consumer.

**Probe and failure mode:** `checks/lesson-census-summary.json` records both statuses. If downstream assembly changes to arbitrary query placement, this decision no longer holds and the schedule must be repaired first.


## D8 — Keep the source-bound probe read-only

**Original rationale:** The reusable probe dynamically imports a selected generator by path so it can compare frozen baseline and final bytes. Its first portable implementation worked functionally but allowed Python to create `__pycache__` beside the inspected source, mutating the evidence tree and contaminating patch discovery.

**Decision:** Disable bytecode emission only while `exec_module` loads the selected generator, then restore the interpreter's prior setting in `finally`. The probe still bootstraps the packet or staged runtime without relying on `PYTHONPATH`.

**Alternatives rejected:** (1) Launch every documented command with `-B` or `PYTHONDONTWRITEBYTECODE`: that shifts a read-only-tool invariant onto callers. (2) delete caches after loading: that performs a second mutation and can remove pre-existing user artifacts. (3) ignore caches in patch assembly only: that hides the side effect rather than removing it.

**Probe and failure mode:** `test_distribution_probe_does_not_write_bytecode_beside_source` copied the generator into a clean directory and first failed because `__pycache__` appeared. The final 22-test suite passes, direct baseline/final probe runs leave zero source-adjacent cache directories, and the clean-copy patch replay also leaves none.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/0f7d80015d9d/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
