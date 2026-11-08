# Current review notes: 9971f3a5882c

## Selected rule and domain

Color 3 forms a sparse rectangular lattice: complete boundary rows/columns and
optional complete internal lines. Exterior color-6 markers name sides of its
original bounding box. The nearest marker on an occupied side sets the new
boundary one cell toward the lattice. Outer lines move; internal line coordinates
stay fixed; all markers remain color 6. The canonical Racket rule remains
`f753f2c684d9`, with exact source SHA-256
`b1b4ad49109b21cae627cbc9c0a39b3695abe47fa0ab44a4b4dc3c89b5028527`.

Selected generator SHA-256 after this review:
`ac6f4a04bb8a7947d942a3eb5232eafd065956f1d1226a3190e727f75ac84e14`.
The task's current review index contained no unresolved audits at this draw.
Approval and training admission are maintained separately; this review does not
rewrite either status or the review index.

## Retained distribution decisions

The earlier repair (review-d9ccd3d6d96df1a5:v0001, selected source
`5235171e7b63356bd8b76162c2fd4aa63c61a73c83e4cb59bc6a8b63768a1c00`)
replaced a filled-rectangle model with the demonstrated sparse-lattice grammar.
Keep that repair: all eight canonical inputs remain accepted and correctly
labelled. The four canonical canvas profiles plus one broader profile retain
canonical support without fixing dimensions to the original examples. The four
lattice profiles and ten marker profiles expose exact observable controls; all
200 Cartesian combinations remain legal. Difficulty changes placement and
expansion, not color roles or the transformation.

The marker schedule alternates joint top-plus-double-side witnesses with simpler
examples. This retains coverage against the declared canonical-fitting rivals
`ignore_top_markers` and `farthest_same_side_marker`. Three demonstrations plus
one query are the checked lesson shape. Neither witness frequency nor correctness
of individual labels alone establishes sufficient teaching demonstrations.

## R1 — Exact replay arguments

Previously `generate` accepted booleans, floats and strings as seeds/indices and
accepted negative indices. The before battery reported 33 strict-scalar warnings.
Now the public generator rejects nonliteral integer seeds and nonliteral or
negative integer indices before sampling. Signed integer seeds and arbitrarily
large nonnegative indices remain valid. Keep VERSION 2.0.0: this boundary repair
does not change the keyed RNG mapping for valid calls. The retained 112-call
baseline fixture matches every post-repair input hash.

Evidence: `counterexamples/invalid_replay_arguments.json`,
`tests/test_scalar_contract.py`, and `tests/fixtures/valid_call_baseline.json`.
The new scalar tests changed from 52 failures / 5 passes to 57 passes.

## R2 — Consecutive schedule diagnostics

The old probe wrapped sample indices at 12, even though the combined canvas,
lattice and marker profile period is lcm(5,4,12)=60. That missed 28 of 40 visible
profile tuples and substituted artificial transitions near the wrap. This was a
coverage defect, not a demonstrated production-label defect.

`workspace/lesson_probe.py` now uses the portable selected-source loader,
checks real `start + offset` calls, defaults to all 60 profile phases, includes
observed profiles in its receipts, and labels explicit short runs as partial.
Its outputs use the Python mirror. The corrected fixed-seed probe passed
960/960 rotations across default/easy/medium/hard; 189 exact inputs were unique.
The ordinary Racket-backed production census separately materialized 300 lessons
and 1,200 rotations with zero declared ambiguity and 1,112 unique inputs.

## P1 — Proposed parametric authoring tool

`workspace/parametric/` contains a separate nearest/farthest marker-selection
prototype. It chooses one rule value per episode, materializes matching Racket,
and verifies every saved label through Racket. The canonical nearest text is
preserved byte for byte. The farthest setting changes only side extrema; object
roles, fixed internal lines, and marker preservation remain intact.

The retained evidence includes both teaching settings, an intentionally ambiguous
lesson, and an answer-equivalent control. A reusable episode audit distinguishes
harmful query ambiguity from an equivalent surviving rival. This remains a
proposed, unapproved authoring extension; it is not wired into production.

## Fresh verification and limits

The after battery passed all 12 stages, including 11,700/11,700 override draws,
600/600 strict semantic draws, eight canonical inputs and 51/60 exact profile
hits (easy 17/20, medium 19/20, hard 15/20). Portable task tests passed 531/531,
with zero failures, errors or skips. Both visible-only solves matched 3/3 visible
examples on their first revisions; their query labels remain unscored.

The finite census tests declared rivals and listed seeds; it does not prove
universal identifiability. Named sampling profiles are a bounded subset of the
structural validator domain. Parameter evidence is bounded to two settings,
one retained seed, and explicit witnesses; it is not training approval. Current
review receipts are in the accompanying return's `checks/` tree.
## Current reviewer considerations

Source SHA-256: `ac6f4a04bb8a7947d942a3eb5232eafd065956f1d1226a3190e727f75ac84e14`.

# Decisions for 9971f3a5882c

## D1 — Keep the selected sparse-lattice rule and valid input distribution

The pinned source already repaired the earlier filled-rectangle error. Its
current review index has no open audit, and the canonical examples support its
sparse row/column grammar. We retain its object roles, palette, five canvas
profiles, four lattice profiles, ten marker profiles and difficulty behavior.
The 112 valid-call input hashes retained before editing all match afterward.
Changing VERSION would perturb the keyed draws unnecessarily, so it stays 2.0.0.
The canonical Racket text, selected authority files and catalog are unchanged.

Rejected alternatives: a new unrestricted sampler would dilute canonical
profile support; a cosmetic reskin would not satisfy the requested rule
parameter. Earlier repair notes and review-d9ccd3d6d96df1a5:v0001 were context,
not measurements of this return. All reported checks were rerun here.

## D2 — Parameterize nearest versus farthest marker selection

This is a small semantic change already exposed by a canonical-fitting rival.
The original/default value is `nearest`; the alternate is `farthest`. Both use
the same lattice, exterior marker association, boundary displacement, stationary
internal lines and marker restoration. Only the extremum on each occupied side
changes. With one marker per side, the settings agree; double markers provide
the decisive teaching witness.

The parameter is selected once from the episode seed. It never changes between
the three demonstrations and one query. Public challenges contain only ordinary
input/output demonstrations and query inputs. Parameters, rules, seeds, query
answers and provenance stay in private authoring records. `nearest.rkt` is
checked against canonical text; four asserted substitutions materialize the
alternate program. Saved labels come from Racket, with an independent Python
mirror as a parity check.

The extension is **prototype/proposed**, not a production API or an approved
training family. Its focused tests and `checks/parametric/evidence/` retain both
settings, a harmful-ambiguity diagnostic, an equivalent control and a lawful
all-four-side witness where 36 output cells differ. The hand-built witness is
in the structural validator domain but outside the named sample bank. Its
farthest boundaries pass through nearer markers, which must remain color 6;
output grids therefore must not be checked using the input-lattice validator.

Rejected alternatives: resampling the rule independently for each pair would
make a lesson incoherent; requiring every rival to be refuted would reject
answer-equivalent lessons. Wider parameters such as affine movement of internal
lines would add a second reasoning change without a clear need in this review.

## D3 — Reject invalid replay arguments at the generator boundary

The before battery found 33 accepted invalid scalars: booleans, floats and
strings for seed/index, plus negative indices. Type annotations and the shared
context did not reject them; schedule code also coerced indices with `int()`.
The repair validates literal Python integers before any draw and requires a
nonnegative index. Signed seeds remain lawful. New tests failed 52 cases before
the repair and passed all 57 afterward, including valid replay controls.

Evidence: `checks/before/checks/9971f3a5882c_before_defect_lint.log`,
`checks/scalar-red.log`, `checks/scalar-green.log`, and the task-local
`counterexamples/invalid_replay_arguments.json`. Coercing values deliberately
was rejected because it hides caller errors and weakens sample identity.

## D4 — Check real consecutive windows over the combined profile period

The old local probe and inherited cyclic tests checked index residues modulo 12.
The generator's canvas, lattice and marker profiles have periods 5, 4 and 12.
Their combined profile period is 60; pixel layouts still depend on absolute
indices. Wrapping generated calls at 12 missed 28 of 40 observable profile tuples
and invented transitions at starts 9–11. A retained relocated copy also failed
because its source lookup assumed a fixed parent depth.

The repaired probe calls the public selected-source loader and generates
`start + offset` directly. It checks 60 start positions by default, keeps all
four query placements, records actual profiles and reports explicit shorter
runs as partial. The three new regression tests failed before this repair and
pass after it. The existing tests remain as narrow historical regressions.

Evidence: `checks/canonical-review/`, `checks/lesson-probe-red.log`,
`checks/lesson-probe-green-final.log`, and
`checks/consecutive-lesson-probe.json`. The corrected mirror probe passes
960/960 rotations at seed 7331. The independent production sampler census uses
Racket labels: 300/300 lessons, 1,200/1,200 rotations, zero declared ambiguity,
1,112 unique inputs. These two scopes are reported separately.

## D5 — Keep failures, private answers and approval states explicit

Both blind and post-repair solves match 3/3 visible examples on revision 1.
The first was completed before authoring sources were read. The second records
earlier rule exposure and no reference consultation during the solve. Query
correctness remains unknown; no artificial failed solve was created.

The prototype's ambiguous episode is intentionally constructed diagnostic
evidence. Its audit exit code 1 is expected and retained, not a failed repair.
The two assigned adversarial reviews are findings-only and leave their selected
sources intact. Existing unresolved findings stay unresolved. Environment setup
initially failed because package-network access was unavailable; the isolated
environment was then installed successfully and all 531 task tests executed.

No GPU work, model training, approval refresh or training admission was performed.
The main repair is suitable for routine acceptance; the separate prototype and
audit follow-ups retain their own review decisions.

## D6 — Promote the nearest/farthest prototype to a native qualified contract

The old prototype fixed episodes at three demonstrations and one query and kept
its own legacy evidence flow.  The native contract now supports 2–6
demonstrations and 1–4 independent, prefix-stable queries, with four distinct
queries retained for sequential reveal.  Input draws are identical across
settings; public bytes exclude settings, programs, future queries and query
answers.  The fourth query is a substantive 30×30 sparse lattice rather than a
padded small case.

The canonical `nearest` program is unchanged byte-for-byte.  `farthest` changes
only the four marker-extremum choices.  A reusable protected-Racket audit checks
both settings, six executable shortcut rivals, private/public projection,
setting-independent sampling, prefix stability and 30×30 labels.  It passed 12
jobs with 53 distinct Racket executions and no surviving rival.  Native
qualification independently passed 4/4 setting/seed jobs with 32 Racket
evaluations.  The source-bound inventory replaced the stale prototype manifest.

The required sequential dependency is: A computes the original lattice bbox,
full rows/columns and side-partitioned markers; B consumes that exact partition
to choose an extremum and redraw the lattice.  A protected-Racket ablation that
decrements bbox `c1` before classification reclassifies an edge-aligned marker
and changes 90 final cells on an exact qualified query.  Evidence is under
`workspace/parametric/evidence/current/`, `checks/9971f3a5882c/qualification/`,
and `checks/9971f3a5882c/causal/`.

This return is reviewer-ready only.  Owner acceptance on exact integrated bytes
and any training admission remain pending; production generator and canonical
ledger bytes were not changed.
