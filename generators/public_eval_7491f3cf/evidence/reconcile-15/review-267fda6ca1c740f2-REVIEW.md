# Review return — review-267fda6ca1c740f2

Both assigned missing public-evaluation references were authored as general protected-Racket rules and promoted into reviewer-ready native parametric families. The default program in each family is byte-identical to its new `reference.rkt`; no official grid or answer lookup is used. All supplied demonstrations and supplied test gold pass under the protected runtime.

## public_eval_7491f3cf — panel-region composition

The canonical rule parses four equal framed panels. In panel one it derives the largest 8-connected divider and floods the singleton marker's 4-connected side without crossing that divider. It then composes panel two inside the derived marked region and panel three outside it into panel four; divider cells accept either source, with the marked-side source winning overlaps.

The episode-fixed family parameter is `source_assignment`:

- `second_in_marked` — canonical behavior.
- `third_in_marked` — swaps source roles while preserving segmentation and composition.

The family supports 2–6 demonstrations and 1–4 queries with stable prefixes, matched setting-neutral inputs, presentation order independent of query ordinal, and one-query public turns without total-count hints. The first two demonstrations reject the retained alternative-setting and structural shortcuts. The seed-17 fourth query is 30×29, contains 870 nonzero input cells, and the two settings disagree on 83 output cells.

The protected causal witness changes the Step-A region constructor from 4-connected flood to 8-connected flood. That altered intermediate changes 31 final output cells.

## public_eval_3dc255db — spacecraft exhaust relocation

The canonical rule treats each mixed-color 8-connected component as a spacecraft. The majority color is its hull and the minority cells are stored exhaust particles. It derives a geometric nose and signed heading from hull extremes, alignment with the widest full-component cross-sections, and particle depth. It removes the stored particles and emits the minority color from the derived nose along that heading, clipped by the canvas. Monochrome components remain unchanged.

The episode-fixed family parameter is `extension`:

- `particle_count` — canonical behavior; extension length equals stored-particle count.
- `to_edge` — preserves all object analysis but extends to the canvas edge.

The family supports the same count, privacy, matched-input, stable-prefix, and sequential-presentation contract. Generated scenes cover all four headings, varying exhaust counts, clipping, and unrelated singleton components. The seed-17 fourth query is 30×30 with 126 nonzero input cells; the two settings disagree on six cells.

The protected causal witness reverses the Step-A signed heading before Step B. That changed intermediate changes 20 final output cells.

## Verification retained in the return

- Official protected-Racket labels: 5/5 for `7491f3cf`, 4/4 for `3dc255db`.
- Staged changed-target tests: 23/23 per target; combined direct suite 46/46.
- Per-target bounded audit: 320 episodes, 2,176 labeled pairs, 1,024 public views, 40 protected-Racket evaluations, 64 finite-rival checks, and 64 large stress episodes.
- Saved public-export conformance: 16/16 files per target.
- Source-bound causal replay: `reviewer_replayed` for both targets.
- Cross-target final review: current preflight source hashes, canonical/reference byte identity, maximum seed, minimum/maximum counts, matched inputs, stable prefixes, four distinct queries, and setting discrimination all passed.

These finite rival checks establish the declared bounded teaching audit, not universal rule uniqueness. Final code review was an author self-review because no independent reviewer subagent was available.

## Remaining owner steps

This return is reviewer-ready authoring work only. Owner registration, exact-source review, unchanged native qualification, fresh acceptance, and any training admission remain pending for both targets. `training_admitted` is not claimed.
