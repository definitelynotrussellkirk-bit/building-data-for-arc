# Working notes: 1ea6c72cb7e3

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review review-57a2813eebf68022 (2026-10-02)

Baseline hard draws excluded every canonical dimension/count profile. The
structural checker did not provide an executable lesson-level contract. Two
wrong rules (only recognize watcher colors 2/3/4; make conflicts only for
exactly two watchers) fit all four canonical pairs. Added canonical anchors
and all-four-rival contrast samples in a seed-rotated three-role schedule.
The two additional rivals treat watchers as opaque or ignore walls.

Before/final replay: 390 actual Racket-backed lessons (100 pinned lessons per
band plus 30 cyclic-start lessons per band). Surviving-rival lessons 175 -> 0;
query-discriminating ambiguities, union over rivals, 55 -> 0. These are not
model error rates. See `checks/lesson-before-final-rivals.json`,
`checks/lesson-final.json`, and their complete compressed lesson records in
the return. 1,380 unique generated inputs per source, 1,560 pair occurrences.

An intermediate repair passed semantic probes but failed default draw
provenance: dimensions/count were overwritten after being recorded. Corrected
by selecting anchor domains before keyed draws; retained the failed source,
full battery, and regression. Final generator source:
`2a0ccefe674e9ec4c42ae6db6c96bc6229594924f72708a7744612f79a912d6b`.
All 12 final battery stages are green; Racket authority unchanged.

Do not silently widen the claim to one/two demonstrations, independently
shuffled samples, arbitrary palettes, arbitrary wall shapes, or model learning.
No Qwen training or independent maintainer scoring occurred here.
## Current reviewer considerations

Source SHA-256: `2a0ccefe674e9ec4c42ae6db6c96bc6229594924f72708a7744612f79a912d6b`.

# Decisions and rejected alternatives

Evidence identity: B/I/F hashes and source-bound counts are defined in
`REVIEW.md`. All final generator decisions below refer to F. Historic intent is
only attributed where stated in the inherited source; otherwise it is unknown.

| Choice | Original rationale / known evidence | Decision, alternative, and failure boundary |
|---|---|---|
| 0 background, 5 wall, preserved singleton sources | Explicit canonical rule and all four examples | Preserve. Palette permutation of 0/5 would change the task, not diversify it. No Racket edit. |
| Distinct watcher colors excluding 0/5/8 | Inherited semantics keep visible-color voting separate from the reserved conflict marker | Keep 3–4 watchers, exact override. Repeated colors or input8 broaden the problem beyond reviewed domain; rejected in this repair. |
| Canonical trio 2/3/4 | Canonical examples; inherited sampler favored it | Keep on anchors, force at least one noncanonical legal color on contrasts. All-2/3/4 would perpetuate R2; using only new colors would lose canonical anchoring. |
| Dimensions 9..13 by 9..14 | Inherited published axis envelope; reason for precise outer bounds otherwise unknown | Preserve full exact-override domain. Anchor shape set {(9,9),(10,10),(11,11),(10,11)} with 3 watchers recreates all canonical dimension/palette profiles. Hard-only large sizes caused R1. |
| Four wall morphologies | Source explicitly aimed to reproduce long canonical bars/crosses, not isolated wall pixels | Preserve cross, ladder, split_cross, split_ladder and difficulty priors. Arbitrary mazes would expand semantic domain and dilute tested canonical support. |
| Background strict majority and isolation | Inherited lawful-scene validator and canonical compatibility | Keep. Avoid changing domain while repairing teaching support. The word “strict” denotes this domain validator, not exact canonical image similarity. |
| All zero/one/multi branches, every watcher owns a sole-visible cell | Inherited rule-hiding prevention | Preserve. A novel palette alone is not enough: its watcher must have an observable effect, and actual output differences are still tested. |
| Material walls | Inherited checker required visibility-set occlusion | Retain and add actual `ignore_walls` output refutation. A branch flag can be present without changing output; A2 independently demonstrates that risk. |
| Three-role schedule | New; baseline was independently sampled without lesson-level guarantee | `(seed+sample_index)%3` gives anchor/contrast/broad in any three consecutive draws at fixed seed. One third each preserves broad variation while giving an explicit contrast per lesson. Independent random mixture was rejected because even high witness frequency leaves unlucky complete lessons ambiguous. |
| Contrast placement | New, needed to refute R2 | Construct two collinear and one perpendicular watcher around a zero cell, then reject until all four rival outputs differ. Fourth watcher remains allowed. Uniform random rejection alone makes triple visibility less predictable and less efficient. |
| Anchor implementation | New | Select singleton feasible default bounds before keyed draws; explicit controls use their full published bounds. Rejected the first overwrite-after-draw implementation after R4 failed provenance. The three-cycle role is not exposed as an additional public override axis. |
| Two canonical shortcuts, four lesson competitors | Canonical-only colors and exactly-two conflicts each fit 4/4 canonical pairs; opaque-watchers and no-walls need not | Declare the distinction explicitly. Avoid claiming all competitors are canonical ambiguities. The retained probe imports current declarations and checks claimed canonical fits. |
| `lesson_identifiable` checks demos only | New | Report named rivals not refuted by demonstrations. Never access a query label in this hook. The external Racket probe separately distinguishes query-equivalent survival from consequential query ambiguity. |
| Python diagnostics versus label authority | Canonical Racket is authoritative | Python per-cell model is used for witnesses/rivals; separate ray-accumulation tests and actual Racket comparisons check it. Generated labels remain Racket-derived. Merely comparing a generator to its own mirror would be circular. |
| Malformed cells | Baseline added an error but continued into hashing, crashing on list/dict values | Return validation errors immediately before set/Counter use. Preserve acceptance of every canonical input. Add explicit regression cases. |
| Tests and portability | Frozen root fixture must remain untouched | Add task-local tests and run them explicitly; also execute the original fixture from a staged standalone runtime. No helper or fixture edits. |
| Audit targets | Assignment is findings-only | Leave both targets unchanged. Save canonical/generated counterexamples, target hashes, output authority, exact seeds, and validator results; do not hide findings merely because the audit process exits 0. |
| Fresh solve | Required after final source | Disclose earlier exposure; use only visible challenge during solving. Independent segment implementation, one genuine candidate. No artificial failed candidate and no claim about masked answers. |

## Limits and falsifiers

Three consecutive demonstrations are essential to the scheduling statement.
One/two demos or independent shuffling need a new assembly policy and new probe.
An override can intentionally replace a canonical anchor's shape/count; override
correctness takes priority over an exact default profile claim. The 20-draw
per-band profile floor is a finite pinned census, not a theorem about arbitrary
sets of twenty unrelated seeds.

Named rivals are a finite approximation to the hypothesis class. An unseen
rival, more complex morphology, repeated-color watchers, altered special colors,
or an alternative dataset split can invalidate generalization without causing
these gates to fail. Adding a rival must include a lawful counterexample, prove
any claimed canonical fit, and rerun all cyclic starts and 100 lessons per band.
Construction rejects at most 120 wall layouts × 180 position proposals before
raising; no infinite fallback or silent shape/count relaxation was added. Runtime
exhaustion was not observed in the retained finite draws, not ruled out globally.

A diagnostic study of Qwen3.5-9B could next compare matched training tokens and
held-out lesson accuracy with/without contrast scheduling. It has **not** been
run here. This return establishes generation validity, specific teaching
counterexamples, and reproducibility—not a measured model improvement.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/1ea6c72cb7e3/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
