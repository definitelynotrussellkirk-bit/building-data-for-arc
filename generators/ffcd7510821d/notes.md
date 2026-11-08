# Review notes — review-befb6364b93d8004

Prior notes were a placeholder; no undocumented design intent is attributed to
the original author. Original version 2.2.1 SHA256 `6c0b3cb57d3761838d6452b42936e2f57fb76b12717da1b0cf01b95e4f71c8d7` is retained in the
packet's immutable baseline. Version 3.0.0 SHA256 is `389301c2c8847e304bda9a568a497bbd5ac77f06a2d15f33584a4a06770eec7c`.

The substantive error was equating a nonrectangular blob with an observable
rotation. A plus at seed 0/easy/index 0 is a concrete counterexample. The repair
uses exact scene-orbit size four; removing only rectangular shapes is insufficient.

Defaults schedule marker counts 1–4. Two single-object and two multi-object scenes
per four-index cycle retain an easy crop/turn anchor and disprove largest-only
behavior. Single anchors use canonical-scale dimensions in all bands. The
coefficient-two seed schedule also avoids the diagonal two-residue alias found
in an intermediate implementation. Caller schedules outside this contract still
need lesson validation.

All five remaining axes are real. Full valid integer bounds override difficulty
preferences; removed texture/size aliases raise rather than silently act as no-ops.
The morphology sampler has bounded retries and an explicit L fallback with the
same requested blob count, dimensions, palette, and marker count. Self-checks do
not trust metadata. Off-row markers are not added: their rule behavior is outside
this task distribution, so count-all-markers shortcuts are not claimed refuted.

Retained measurements for seed 0, indices 0–499 in each of three bands: before
40/500 easy inputs were rotationally invariant; final 0/500. The finite-class
four-demo lesson census improved from 298/1,488 ambiguous overlapping windows to
0/1,488. Both before/final sets have 1,500 actual Racket labels and zero Python
cross-check disagreement. Each band has 500 distinct inputs; no cross-band unique
count is claimed. Official final battery: 12 green. Task-local suite: 60 passed.

The root suite has a separately documented startup-sensitive timeout failure
(169 passed / 1 failed); no shared code was patched. Audit targets are also
unchanged. The fresh solve is prior-rule-informed, not blind; masked scores remain
withheld. No model-training improvement or automatic catalog approval is claimed.

Full rationale, rejected alternatives, failures, seed ranges, commands, and evidence
are retained in the return's REVIEW.md, DECISIONS.md, RESULTS.json, and checks/.
## Current reviewer considerations

Source SHA-256: `389301c2c8847e304bda9a568a497bbd5ac77f06a2d15f33584a4a06770eec7c`.

# Decisions and rejected alternatives

Source identity: before `6c0b3cb57d3761838d6452b42936e2f57fb76b12717da1b0cf01b95e4f71c8d7`; final `389301c2c8847e304bda9a568a497bbd5ac77f06a2d15f33584a4a06770eec7c`; unchanged Racket rule `77da9e97370c`.
Finding IDs refer to `REVIEW.md`; tooling recommendations use the same F IDs as
`FEEDBACK_TO_CODEX.md`. Original working notes contain no rationale beyond a
placeholder. Where a purpose is inferred from old code or summary, it is labeled
as an inference rather than attributed to an earlier author.

## D1 / R1 — require a useful rotation witness

The old summary explicitly asserted that a nonrectangular blob makes rotation
visibly different. A plus has bounding-box area nine and five occupied cells, yet
all four rotations agree. The matched baseline census retains 40 such easy cases
among 500 seed-0 draws. The old self-check accepted them.

The selected generator now checks all four rotations of the **whole content
crop**, not an individual component or only its bounding-box dimensions. This
exact finite check rejects half-turn as well as quarter-turn symmetries. It is
cheap at this task's small grid sizes. Nonrectangular blobs remain an independent
morphology constraint, not the proof of rotation observability.

Rejected: ban square bounding boxes, require unequal dimensions, or add a single
arbitrary pixel after generation. Those respectively reject useful asymmetric
squares, miss half-turn symmetry, or can violate connectivity/exact axes. A
bounded resampling loop retains the requested axes; its explicit last fallback
uses uniquely colored L triominoes in separated slots. A uniquely colored L has
no nontrivial rotation symmetry, so preserving each color forces the full scene
to remain asymmetric. No fallback silently reduces blob count.

Limitation: symmetric scenes are not intrinsically invalid ARC examples. This is
an intentionally stronger **witness-generator** domain. A general lesson gate
should examine answer equivalence and allow redundant/symmetric examples when
the rest of a lesson still determines the query; see QUESTION_ANSWER.md.

## D2 / R2 — teach all four marker branches deliberately

The old iid default 1–3 markers apparently aimed to demonstrate nonidentity
rotations; that motive is an inference. It never taught the identity residue in
default lessons, and `EXAMPLES_NEEDED = 4` was only a count, not a guarantee.

The new default marker count is `1 + (2*seed + sample_index) % 4`. Any fixed-seed
four consecutive indices contain counts 1, 2, 3, and 4. Four markers give the
identity operation while keeping a visible instruction cue; zero markers remain
lawful only by explicit override. This is a transparent expansion under the
unchanged modulo-four authority, not a Racket rule change.

An intermediate `(seed + sample_index) % 4` schedule passed fixed-seed windows
but failed diagonal `(i,i)` sampling: only two profiles appeared. The red test in
`checks/diagonal-before.log` caught this. The final `2*seed + index` also traverses
all residues along that diagonal. It does not guarantee coverage under every
adversarial caller schedule or arbitrary resampling of individual examples.

Rejected: merely increase random lesson size, rely on lucky coverage, or make
semantic hooks always return success. The chosen hook intersects the possible
clockwise rotations separately for each marker residue and checks named rivals
against actual demonstrations. Its guarantee is relative to that finite class,
not all possible programs. Explicit overrides can destroy the default coverage;
call the assembled-lesson hook rather than assuming the module constant suffices.

## D3 / R2 — preserve anchors and disprove single-object shortcuts

Every default four-example cycle has two single-blob examples and two multi-blob
examples. Single anchors use heights 8–9 and widths 9–12 in **every** difficulty;
multi scenes use larger preferred dimensions as difficulty increases. This
retains canonical-scale support while exposing why all components must survive
the crop. The old band ranges effectively removed single objects from harder
bands. The final official profile-floor report is retained with its exact draw
schedule; it is support evidence, not an exact canonical morphology match.

Rejected: make every scene large/multi-object for apparent difficulty, or make
all scenes canonical-sized single blobs to maximize profile similarity. The
former loses anchors; the latter permits the largest-object-only shortcut.

Limitation: the schedule creates within-seed correlations between marker residue
and single/multi composition; the pairing changes with seed. Ordered examples
must not become an alternate answer channel. Training users should vary seeds
and may shuffle the already-assembled demonstrations, not independently sample
away required witnesses. Band overlap and constrained grammar reduce the scope
of claimed generalization. No empirical difficulty ranking is asserted.

## D4 / R3 — exact controls instead of a broad fictitious API

The supported axes are `grid_h` (7–14), `grid_w` (8–14), `n_markers` (0–4),
`n_blobs` (1–4), and `palette_kind` (`warm`, `cool`, `varied`). All integer bounds
are honored in all difficulty bands; bool/float coercions and unknown keys are
rejected. `None` requests the normal default. Difficulty is a preference for
unspecified axes, not a second hidden validity domain.

Distinct colors make blob count directly observable. Warm support is 2/4/6/7,
cool support 1/3/5/8, varied support 1–8; these are defined groups, not a claim
about perception. Default varied avoids tying marker semantics to hue. Separated
slots fit up to four blobs even at 7x8. Uniform choices from a sorted frontier
keep generation deterministic without a fixed growth direction. Bounded shape
rejection and L fallbacks may bias morphology; those are documented costs, not
claims of uniform sampling over polyominoes.

Removed `texture`, `density`, `position_bias`, `palette_size`, and
`n_distinct_colors` rather than silently accept ignored aliases. Old texture
presets could override dimensions or mix negative fixtures into ordinary axes.
Mutation fixtures are now separate and metadata cannot waive structural checks.
Also removed the old `palette_kind='default'` alias; use omission/None or `varied`.
This deliberate incompatibility is why the version is 3.0.0. Existing callers
using removed keys need an explicit configuration update.

## D5 — keep the rule's actual boundary

Retain black background, maroon (9) instruction markers on row 0, a blank row 1,
and connected distinct-color content below. Count and erase **row-0 9s only**;
the old summary said “clear all 9s,” which overstates the authority. Off-row 9s
are outside this generator's documented domain, although the Racket program has
behavior there. No claim is made to refute the count-all-9 rival within a domain
where it is indistinguishable. Arbitrary marker colors/rows would change the
task rather than repair its generator, so they were rejected.

## D6 / F3 — authoritative labels, portable evidence

`orbit_census.py --racket` and `audit_targets.py` execute canonical Racket, with
Python used only as a cross-check/rival. A failed direct import of the source
runtime exposed a layout dependency on `scripts.comment_solutions`. The tools
now use `prepare_runtime(Catalog(...), temp_directory, ...)` and retain the exact
runtime manifest/directory. No temporary runtime is shipped.

The census can load the frozen baseline with `--generator`. Its report's
`generator_sha256` identifies that actual imported source; the staged framework
manifest may still contain the current task snapshot. Do not mistake that
framework copy for the overridden census subject. Logs retain the earlier
launcher failure, and a real CLI Racket test guards the corrected path.

## D7 / A2 / F4 — stop at the assignment boundary

The two audits are findings-only; no source changes there. The shared timeout
test's startup dependence is reproduced with unchanged source and three repeated
observations per configuration, but is not repaired inside an unrelated task.
No hidden-query scoring was accessed and no failed model attempt was fabricated.
Finite-sample testing, source hashes, and transparent unresolved findings are the
stopping boundary; only maintainer replay can promote this candidate.

## Parametric reviewer handoff — review-0d862826d72b406f

The approved production generator and canonical Racket program remain unchanged.
A task-local native promotion candidate now lives under
`workspace/parametric/`, with hidden episode setting
`direction = clockwise | counterclockwise`. `clockwise` returns the exact
canonical program bytes (SHA-256
`77da9e97370c0d2e1fa7cad46a1bc45e4087320926f1bf71d1d252a2c21eafcb`);
`counterclockwise` preserves marker counting, row-0 marker removal, tight crop,
and whole-object quarter-turn semantics while reversing direction (SHA-256
`73a91a008bb31284c2ebac153313436e8a8e4ce7a87abaede7168aae144b4a27`).

The causal sequence is: count row-0 maroon markers modulo four and crop the
complete remaining object; retain `(turns modulo four, cropped object)` as the
input-dependent intermediate; then use the private direction to choose and apply
the corresponding rotation. Two protected-Racket witness cases show that
forcing the wrong turn on the same asymmetric crop changes the final answer.

Episodes support 2–6 demonstrations and exactly four distinct queries. The
settings share identical deterministic inputs. Demonstration marker counts are
`1,3,2,4,1,3`; query counts are `2,4,1,3`, so ordinary three-example lessons
identify both direction and count dependence. The final query is a genuine
30×30 scene with four connected nonrectangular colored blobs spanning all four
quadrants and touching outer boundaries.

Fresh evidence: 107 staged task tests passed; 256 deterministic seeds produced
2,560 distinct scenes and 1,024 episodes; four native jobs (two directions by
seeds 0 and 17) passed protected-Racket qualification with one surviving setting
each; the finite named-rival self-review found no demonstration-fitting
query-changing survivor; and two hash-named public challenges passed masking and
saved-byte identity checks. The source-bound manifest SHA-256 is
`ac2d9365feb628445298de5511febac730f52a3203c1a92a16edf239c6ccef78`.

Status is reviewer-ready only. Owner integration, qualification replay on the
exact live bytes, and a fresh acceptance receipt remain required before any
training admission.
