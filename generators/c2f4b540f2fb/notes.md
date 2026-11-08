# Working notes: c2f4b540f2fb

## Current reviewer decision — 2026-10-26

The production generator and selected canonical program remain unchanged. The original finite audit found no base-rule mismatch, but the source is still unapproved and requires owner review.

A separate native parametric family now varies two semantic choices:

- `axis`: source-local `u` or `v`
- `extreme`: `max` or `min`

The default `{axis: u, extreme: max}` returns the selected canonical Racket bytes exactly. All four settings share identical sampled inputs for fixed seed/counts. Each episode supports 2–6 demonstrations and exactly four private queries. Demonstrations 0 and 1 are constructive teaching cases: one has four distinct extrema and one exercises tied extrema. Scenes vary source/target frame orientation, layout, motif symmetry, cyan radius decoys, distractors, boundary contact, and dimensions through a substantive 30×30 case.

The required sequential dependency is: (A) identify the requested local extreme tier in the source frame; intermediate = the complete sorted local coordinate set on that tier; (B) transfer exactly those coordinates through the target frame. A protected-Racket counterfactual replaces minimum-u with maximum-u on a qualified case and changes the final target paint.

### Adversarial finding and repair

The first 30×30 query profile allowed one point to be extreme on two different directed axes, so two declared settings produced the same final output on that stress case. The sampler profile was replaced with a seven-point motif whose four directed extreme sets are distinct while still containing a two-point tie. A focused regression now requires the shared 30×30 input to distinguish all four settings.

The pre-existing task test also assumed a fixed owner-checkout path to canonical data and failed in the packet's staged runtime. It now resolves the library with `reviewer_support.find_root` and reads canonical pairs through `reviewer_support.canonical_pairs`.

### Bounded evidence

- 35/35 task-local pytest tests passed on final bytes.
- The retained adversarial probe covered 12 minimum-demo episodes, 4 maximum-demo episodes, 260 protected-Racket evaluations, a 96-seed crossed-control search, and six malformed/tamper rejections.
- Native base authoring preflight covered 4 settings over seeds 0 and 17: 8 jobs, 48 labeled pairs, and 96 protected-Racket evaluations.
- Public projection produced 32 one-query views; structural checks found no findings, and first-turn checks passed 48 private-field invariance mutations plus 8 positive controls.

These are finite checks over the declared grammar and sampled seeds, not a universal uniqueness proof. Owner source approval, fresh native qualification/acceptance, and any training admission remain pending.
