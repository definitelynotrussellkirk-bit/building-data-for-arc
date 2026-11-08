# Working notes — review-1905d8c9333a3c51

Version 1.3.0's singleton separation did not protect future stamp footprints.
At seed 101, indices 0–199 in each band, 129/600 inputs had intersecting stamps
and 37 lost original markers in actual Racket output. Every marker was also
restricted to the lower-right quadrant.

Version 2.0.0 reserves complete boxes, keeps exact override values, adds a finite
packing fallback, enumerates connected motif banks, and schedules visible
counterexamples to named shortcuts. An intermediate canonical-support mixture
introduced cross-band duplicates (782/1,200 unique). A failing regression caught
it; normalized difficulty now salts the layout RNG. The final source has
1,200/1,200 unique sampled grids and zero measured footprint defects.

The return's root REVIEW.md and DECISIONS.md contain source hashes, all command
receipts and limitations. Run the task tests explicitly: the repository test
root does not discover them. The inherited override seed/index formula aliases
this profile cycle; the task tests explicitly cover all three residues.

A diagnostic mirror supports witnesses, but generation emits inputs only and
Racket remains label authority. Do not interpret finite-rival identifiability as
unique identification among arbitrary programs. Do not silently admit these
changes for training before independent replay.

Imported associated notes retain their original timestamps and provenance in
`evidence/associated_notes.jsonl`; they were not rewritten.

## Review review-faa6dc1d8ae4a1d2 — version 2.1.1

The inherited version 2.0.0 passed its battery but omitted a load-bearing branch
of the pinned authority: a 1,200-draw baseline probe found zero inputs with more
than one green component, although the rule explicitly selects the largest green
object. A crafted valid input showed that choosing the smallest green component
changes the Racket output.

Version 2.1.1 adds one disconnected singleton green distractor to the default
`free_shape` profile and declares the `smallest_green_template` rival. Every
three-profile default lesson window therefore contains a source-safe witness.
The validator now selects a unique largest green component, permits at most one
singleton green distractor, and includes every green cell in footprint collision
checks. A regression caught an intermediate validator bug that allowed a stamp
to overwrite the distractor; `green_distractor_in_stamp` now retains that case as
a negative fixture.

The distractor and true motif share a reserved packing envelope. This keeps the
unchanged frozen version-2 geometry regression meaningful while guaranteeing
that both actual stamps and conservative all-green footprints are in-bounds and
disjoint. A few geometrically saturated exact override tuples cannot fit that
extra envelope; they retain the documented zero-distractor variant and still
honor every requested override exactly.

The canonical Racket row and rule hash remain unchanged. Finite named-rival
coverage is not a proof of unique induction among arbitrary programs, and the
review does not include a model-training experiment. Root `REVIEW.md` and
`DECISIONS.md` bind measured counts to final source hashes and evidence.
## Current reviewer considerations

Source SHA-256: `d68ecb728463d4ffc5348ac5fbb10003abbc665c342adcfdc2cf5515a9770226`.

# Decisions — 28e5fbc279ab

## G1 — Treat “largest green object” as a teachable semantic branch

**Observed defect.** Version 2.0.0 documented exactly one green component and
produced 0/1,200 multi-green inputs in the baseline sample (seeds 0–39,
indices 0–9, all three bands). The pinned Racket authority nevertheless selects
the largest green object. A valid two-green-component witness made a
`smallest_green_template` rival disagree with Racket.

**Choice.** Expand the lawful input domain narrowly to one unique largest green
reference of size 3–5 plus zero or one singleton green distractor. Add the rival,
semantic witness, and negative fixtures for tied-largest and nonsingleton cases.

**Alternatives rejected.** Leaving the branch unexercised preserved simpler
inputs but continued to train a shortcut. Adding arbitrary numbers and shapes of
green distractors would test more cases, but would enlarge the domain without
evidence that the extra complexity improves this three-example lesson.

**Evidence.** `checks/hypothesis-largest-green/before_coverage.json`,
`checks/hypothesis-largest-green/input.json`, and
`checks/hypothesis-largest-green/racket.json`.

## G2 — Put exactly one witness in each three-profile lesson cycle

**Choice.** The default `free_shape` profile carries the singleton distractor;
`empty_corner` and `nonrectangular_corner` retain their existing jobs. Because
the profile period is three, every consecutive three-demo window gets one
largest-green witness without making every example atypical.

**Alternatives rejected.** A distractor in every draw would overrepresent a
noncanonical feature and reduce the canonical-like profile floor. A new public
override axis would bloat the exact-control contract for a feature intended to
teach the default lesson. Random low-probability injection would not guarantee
that complete lessons contain the witness.

**Failure modes considered.** The witness must remain disconnected from the
reference, must not tie it in size, must survive Racket unchanged, and must not
be overwritten by any stamp.

## G3 — Reserve the complete lesson envelope

**Choice.** For witness-bearing shapes, search for a minimally enlarged packing
envelope containing the motif and a 4-disconnected singleton. Reserve that same
rectangle for the reference and every marker origin. This proves that true stamp
footprints are disjoint and also keeps the unchanged frozen version-2 geometry
regression valid when it conservatively treats all green cells as one shape.

**Alternatives rejected.** Choosing any globally empty cell after marker
placement initially passed ordinary generation but made conservative footprints
clip or intersect. Editing the frozen baseline test helper was explicitly
forbidden and would hide rather than solve that compatibility problem.

**Limit.** A few geometrically saturated exact override tuples cannot fit the
extra envelope. They retain the lawful zero-distractor case; every requested
axis value remains exact. Default draws always have room for the scheduled
witness.

## G4 — Validate collisions against every green component

**Observed intermediate defect.** The first validator revision initialized its
occupied set from only the selected largest component. A crafted marker could
therefore stamp through the singleton distractor while `self_check` returned no
reason.

**Choice.** Initialize occupied geometry from the union of all green components,
then add each complete marker footprint transactionally. Retain the reproducer
as `green_distractor_in_stamp` and a focused regression test.

**Alternatives rejected.** Relying only on generator construction would leave
hand-authored or mutated inputs incorrectly admitted by the public validator.

## G5 — Keep the override API stable

The effective axes remain `grid_h`, `grid_w`, `n_markers`, `motif_size`, and
`anchor_kind`; no compatibility exceptions were added. Existing crossed tests
exercise all schedule residues and every in-range Cartesian tuple. Unknown keys
still fail loudly.

## G6 — Do not change the Racket authority

The canonical rule already expresses the intended largest-object behavior and
matches stored canonical outputs. The repair changes input support, validator
semantics, diagnostic rivals, tests, and probes only. `RULE_HASH` remains
`20f1992162e5`; authority sync and execution parity are verification gates, not a
new rule selection.

## Remaining limitations

The declared rivals are finite and do not prove unique induction among arbitrary
programs. The new domain tests one smaller singleton, not all possible smaller
green objects. No Qwen3.5-9B training run was performed, so improved data value
is inferred from branch coverage and rival refutation rather than measured model
accuracy. Maintainer replay is still required before training admission.
