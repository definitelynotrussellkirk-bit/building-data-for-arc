# Working notes: ed98575459d2

## Review repair: version 3.0.0

The selected baseline executed the canonical rule correctly, so the Racket authority was left unchanged. The defects were in the generator contract and teaching distribution:

- no pinned `RULE_HASH` or executable `self_check`,
- stale/dead axes and exact overrides that were accepted but not honored,
- ordinary generation forced 1–2 vertical walls even though `n_walls=0` was advertised,
- no required canonical-size/palette profile in the hard band,
- no executable rivals, witnesses, or lesson-level identifiability contract, and
- every canonical pair contained a vertical divider, allowing the shortcut “apply gravity only when a vertical wall exists.”

The repaired schedule deliberately makes zero-vertical-wall scenes ordinary at two of every five positions. Horizontal-only and mixed partitions teach that color-8 walls define connected chambers, rather than merely delimiting vertical strips. Constructive wall placement leaves at least two interior rows and columns per chamber. Pebble placement gives every chamber an occupant, reserves a top empty cell for visible motion, and creates an ordered stack whenever count exceeds chamber count.

Difficulty changes placement depth and color order without changing the exact structural axes. This avoids a byte-dead difficulty knob while keeping semantics constant.

Declared rivals cover the strongest canonical-fitting shortcut, horizontal-wall omission, dropping stacked pebbles, color-sorting a stack, identity, and downward gravity. The reusable `workspace/curriculum_probe.py` reads those declarations directly, checks every cyclic profile start, and materializes an ordinary witness for each canonical shortcut.

## Retained evidence

- Baseline battery: `checks/before/checks/ed98575459d2_before_battery_summary.json`
- Final battery: `checks/after/checks/ed98575459d2_after_battery_summary.json`
- Final selected-task tests: `checks/task-tests-final-221/result.json`
- 300-lesson source-bound census: `checks/lesson-census-final.json`
- Cyclic declaration-driven probe: `checks/curriculum-probe-final.json`
- Exact Racket-confirmed shortcut witness: `checks/shortcut/ed98575459d2/evidence.json`

The original rationale for the stale baseline axes and vertical-wall-only ordinary distribution is unknown. Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `2dec769ef0b86be5809bb589af04b56f0786b6d5c2239b8c6ce10a069787eb06`.

# Decisions for `ed98575459d2`

## D1 — Preserve and pin the Racket authority

**Decision.** Keep the canonical program unchanged and add `RULE_HASH = "7798fc567577"` to the generator.

**Evidence.** The untouched baseline passed `rule_smoke`, `racket_lint`, and `authority_sync`, and all five official pairs agree with the new Python mirror. The repair therefore targets generation and validation, not reference behavior.

**Rejected alternative.** Rewriting the rule to match the baseline's vertical-only prose. That would narrow a correct connected-chamber rule and create an unsupported authority change.

## D2 — Keep only five exact, observable axes

**Decision.** Expose `grid_h`, `grid_w`, `n_walls`, `n_hwalls`, and `n_pebbles`. Reject unknown axes and invalid types/ranges. Support every legal boundary cross constructively.

**Original rationale.** Unknown. The baseline advertised controls that were dead, overlapping, or accepted without changing the returned input.

**Rejected alternative.** Retain decorative palette/texture knobs. The rule needs a fixed wall/background vocabulary and colors 2–7 are useful semantic tokens; decorative aliases add override ambiguity without teaching another rule dimension.

**Probe.** The task suite exhaustively crosses both grid bounds, all wall counts, both horizontal-wall counts, both pebble-count bounds, and all four difficulty values. The shared override stage is green.

## D3 — Use a five-profile ordinary curriculum

**Decision.** Cycle through `(0v,0h)`, `(1v,0h)`, `(0v,1h)`, `(1v,1h)`, and `(2v,0h)`. Set `EXAMPLES_NEEDED = 5`.

**Rationale.** Every canonical pair contains an internal vertical wall. A single-chamber or horizontal-only ordinary case is therefore necessary to falsify “do nothing without a vertical wall.” A horizontal-only and mixed case also distinguishes true connected chambers from vertical-strip-only packing.

**Rejected alternatives.** Caller-only no-wall degenerates are too easy for the lesson sampler to miss. Random wall counts offer frequency but no guarantee that a complete lesson contains the decisive control. A shorter four-profile cycle would drop either the two-wall canonical geometry or one of the no-vertical/mixed controls.

**Failure mode controlled.** Every cyclic five-demo window includes every profile once. `workspace/curriculum_probe.py` checks all cyclic starts rather than assuming index zero.

## D4 — Match canonical dimensions and palette in every band

**Decision.** Use five fixed canonical-linked dimensions between 8×11 and 10×13 inside the broader exact override bounds, and require colors `{0,2,3,4,5,6,7,8}` in every ordinary sample.

**Rationale.** This guarantees profile-floor support in easy, medium, and hard while preserving exact size controls for targeted testing.

**Rejected alternative.** Band-specific dimension bounds. They made globally advertised exact overrides fail in some bands and caused the baseline override-stage failures.

## D5 — Construct geometry and motion instead of retrying blindly

**Decision.** Enumerate legal full-line wall positions leaving at least two cells per chamber dimension. Place at least one pebble in every chamber, reserve a top cell in a moving column, and fill remaining positions without occupying protected cells.

**Rationale.** Construction proves exact count and chamber coverage, avoids rejection-loop bias, and prevents accidental no-op examples at minimum geometry.

**Intermediate failure retained.** The first repair allowed filler pebbles to occupy a protected top cell in a small horizontal split, making a generated case a no-op. The failing test and fix are retained under `checks/tdd-green-1/` and the later green task-test reports.

## D6 — Teach multiplicity and order explicitly

**Decision.** Whenever pebble count exceeds chamber count, create a same-column two-pebble stack with a deliberately nonsorted top-to-bottom color order. Preserve all values and their input order during compaction.

**Rationale.** This falsifies “keep only the topmost pebble” and “sort colors while packing,” both plausible visual shortcuts.

**Rejected alternative.** Only one pebble per column. That teaches direction and chamber isolation but leaves multiplicity/order unspecified.

## D7 — Make difficulty observable but semantically neutral

**Decision.** Vary anchor depth and color order by difficulty while keeping the same exact structural profile.

**Rationale.** The first complete after battery found easy/medium/hard byte-identical for equal seed/index, correctly flagging a dead difficulty knob. The fix changes displacement/order, not rule semantics or advertised axes.

**Retained evidence.** `checks/after-failed-dead-bands/` is the completed intermediate battery; `checks/tdd-red-difficulty.log` demonstrates the regression before the fix.

## D8 — Add an executable domain contract

**Decision.** Implement a strict `self_check`, `strict_canonical_like`, exact `observe_overrides`, a generic connected-region Python mirror, semantic observables, six rivals, six witnesses, and lesson-level identifiability checks.

**Rationale.** Metadata alone did not reveal stale axes or whether complete lessons killed a rival. Executable hooks let shared gates and task-local tests measure the intended behavior.

**Domain boundary.** The validator claims complete full-row/full-column color-8 partitions with rectangular chambers. The authority can process more general color-8 barriers, but expanding the generator to irregular mazes would be a separate design decision and is not needed to cover the canonical manifold.

## D9 — Build a reusable declaration-driven probe

**Decision.** Add `workspace/curriculum_probe.py` and test it through the selected-task suite.

**Rationale.** A copied list of rival names silently goes stale. The probe reads `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` directly, verifies canonical fit, rotates through every cyclic schedule start, counts unique inputs, and emits exact shortcut witnesses.

**Limitation.** It uses the Python mirror for volume. Decisive witnesses are separately confirmed with the public Racket `apply` command.
