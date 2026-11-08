# Working notes: 9ea9f1e62275

## Current decision

Build one distance-metric family around the unchanged framed Voronoi rule. The private setting is `metric` with `manhattan` (canonical default), `chebyshev`, and `euclidean_sq`. These variants preserve the same object grammar and differ only in the distance vector consumed by the unique-minimum/tie step, so the family has a real sequential dependency rather than a cosmetic switch.

## Base repair

The imported generator was not safe to promote as written: it omitted the required literal `RULE_HASH`, treated the frame as if it always had exactly one cell of outer padding, and did not implement a strict observable override contract. The repair adds the canonical rule hash, structural frame analysis independent of padding, strict `grid_h`/`grid_w`/`n_seeds` axes, deterministic labeled RNG, exact override observation, and a Python mirror used only by tests and prototypes. The shared canonical Racket authority was not edited.

## Parametric design

All settings use the same input bank. The first two demonstrations distinguish all three metrics and also reject lowest-color, highest-color, first-seed tie breaking, vertical-only, horizontal-only, row-heavy, and column-heavy distance shortcuts. Episodes accept 2–6 demonstrations and exactly four hidden queries: one substantive 30×30 case, one 9×26 thin-wide case, one 26×11 tall-narrow case, and one boundary-seed mixed case. Query generation and ordering are independent of demonstration count.

## Adversarial reversals

- The first quality checker re-parsed a fully colored output as a sparse seed input; it was changed to reuse the source input's frame bounds.
- The first fixed-canvas stress bank kept the frame at one position; a regression now requires varied 30×30 frame boxes and boundary contact.
- Merely requiring the three metric outputs to differ allowed weak one-cell separations; a nontrivial disagreement-margin regression was added.
- Python equality allowed `True` to masquerade as color `1`; certificate validation now checks literal integer cell types and dimensions before comparing outputs.

The retained 96-seed probe covers 960 scenes, 5,760 crossed color/transpose controls, 876 distinct metric signatures, 33 distinct 30×30 frame boxes, all four first-query roles, and six protected-Racket certificates with no findings. Native authoring preflight and the three-case protected-Racket causal witness passed. Public projection checks covered 24 one-query files, six first turns, 36 private-field invariance mutations, and six positive controls.

## Finite limit and next action

The standalone native override battery was interrupted by packet transport after 1,000 of 4,140 planned draws, with 1,000 accepted and zero findings; this finite battery is not claimed complete. The task-local strict-axis tests, native lint/selfcheck/rule-smoke, protected-Racket authoring preflight, and source-bound adversarial checks all passed. Next, the owner should review the patched base and family source, refresh the native inventory if any source changes, then run owner qualification and fresh acceptance. Reviewer readiness does not imply owner acceptance or training admission.
