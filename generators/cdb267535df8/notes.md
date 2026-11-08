# cdb267535df8 repair notes

## Authority and original defect
The selected canonical task is Wall-Geodesic Voronoi, not contact-degree
recoloring. Version 1.2.0's validator rejected all four usable canonical inputs;
its missing rule pin and obsolete controls were independently caught by the
before battery. No previous pending return was used as evidence of this source:
the immutable packet baseline is the comparison. The associated task notes did
not supply a usable earlier repair. The original author's rationale for the
cross-task sampler is unknown.

## Generator contract
`generate` returns inputs only. Racket labels remain authoritative. `RULE_HASH`
is `cb6c4f271562`. Diagnostic Python BFS is used to reject examples that fail to
teach the named distinctions, not to return labels. A separate per-seed BFS in
the regression tests agrees with canonical outputs and all tested exact controls;
the retained public-API probe also cross-checks 40 cases against Racket.

Exact axes: height 9..13, width 11..15, seed cells 4..6, seed colors 2..4.
All 225 joint combinations are lawful in every band. Unsupported old controls,
unknown keys, out-of-range values and non-integer values fail explicitly. No
requested exact value is silently clipped or widened. `None` is no override.
`observe_overrides` recovers the four values directly from pixels.

Default sizes favor the four canonical dimension profiles without replaying any
canonical grid. All eight nonzero, non-wall colors remain usable. Four wall
families—gapped crosses, bars, scatter, and closed chambers—vary topology,
positions, gaps and lengths. Difficulty changes topology weights, not rule or
legal axis ranges. The default four-draw pattern is repeated/repeated/four-seeds/
four-seeds. With at most four colors, five or six seed cells necessarily repeat;
conditional sampling makes that repeat causally relevant. Default four-seed
profiles may also repeat when the color count is two or three.

## Teaching argument and limits
In every four consecutive accepted default draws, at least two refute both
`tie_by_seed` and `first_seed_only`. Holding out any one draw leaves at least one
such demonstration. Every draw refutes `ignore_walls`, `eight_neighbors`, and
`lowest_color_tie`. This is a guarantee relative to the declared rival functions,
conditional on generation succeeding; it is not universal rule identifiability.
The generator raises after 512 attempts rather than returning a non-teaching
fallback. The production census recorded no rejected outer sampling attempts.

Exact overrides can intentionally suppress repeated colors, so arbitrary override
lessons are not promised rotation-safe. Neither shorter lessons nor rules absent
from the five-rival set are certified. Empty/no-wall scenes, one-color scenes,
identity examples and grids outside the declared generator range are not sampled.
The validator's broader 3..30, 2..8-seed manifold is still not the entire lawful
Racket domain. These are training-distribution restrictions, not assertions that
excluded inputs are reference-invalid.

## Retained evidence
Final generator SHA-256: `1b860d59e505465a7266b509834a2d30fa94ff883bb2b8659bafbf1c7e533f83`.
See packet `REVIEW.md` and `RESULTS.json` for exact commands, source binding,
failed iterations and fresh replay. The 49 tests include 675 joint override cases
and 384 overlapping cyclic query holdouts over 105 generated inputs. The separate
100-lessons-per-band Racket-backed census materializes 1,200 unique inputs and
1,200 query rotations; do not count rotations as new inputs.
## Current reviewer considerations

Source SHA-256: `1b860d59e505465a7266b509834a2d30fa94ff883bb2b8659bafbf1c7e533f83`.

# Decisions and scope — cdb267535df8

All final measurements refer to generator `1b860d59e505465a7266b509834a2d30fa94ff883bb2b8659bafbf1c7e533f83`. Before-source hash:
`13df55a112d273518c8919915c0c1d375b1efcb72639ad4a60775b548f557d91`. The selected canonical source is unchanged; its source pin expands to
`cb6c4f271562e20dc0208fdd088b3a291e4aaf35c1af590caead8da9cf4cbaa5`. A separately hashed executable wrapper can have another text hash;
these fields are not interchangeable.

## R1 — Replace the unrelated sampler, not the selected rule
Original: contact-chain placement and touch-degree validation. Rationale for
this task mapping is unknown. Evidence: all four canonical inputs were rejected;
5 of 12 before stages failed, with semantic gate advisory rather than green.
Decision: replace the sampler with wall-geodesic seed scenes, pin the canonical
rule and update the summary. Rejected: change the canonical rule to bless old
samples; that would change the assigned problem. No historical pending patch was
used as proof about the pinned baseline. The archival authority divergence was
already present; selected execution parity passes before and after.

## R2 — Make controls exact and observable
Height 9..13, width 11..15, 4..6 seeds, 2..4 colors; all joint combinations work
in every difficulty band. Seed colors come from all eight values except 0 and 5.
Removed touch/contact/palette-category axes cannot honestly describe this rule,
so they now error rather than silently doing nothing. Unknown keys, wrong types
and out-of-range values error. The default keyed draw records actual values,
not a value subsequently clipped to satisfy the schedule. Rejected: preserving
old controls for cosmetic compatibility, or making difficulty silently narrow
exact ranges. Tests exercise all 675 joint band/axis cases, including equality
between observations and requested values.

## R3 — Preserve canonical-scale support without replay
75% of size-profile draws favor one of the four canonical dimension pairs,
using heavily weighted but still full-domain axis options. The remaining
size-profile draws broaden within the same advertised bounds. Four colors are
favored, with positive probability of two or three. This keeps actual examples
at canonical scale while allowing more seed interactions. Rejected: fixed
canonical dimensions, copied scenes, and uncontrolled large grids that raise
Racket cost. Measured profile gate: easy 14/20, medium 15/20, hard 11/20 exact
size/palette matches; no crashes or canonical rejections. Exact seeds are in the
shared pinned recipe/report, not fresh random draws. Size/seed-count correlations
are disclosed distribution cues; they cannot by themselves label arbitrary cells.

## R4 — Vary wall topology and preserve lawful corner cases
Gapped cross, parallel bars, scatter and closed chambers have randomized
positions, gaps, orientation and placement. Difficulty only changes weights.
Seeds can occur on either side of walls or in pockets. All nonzero cells survive;
unreachable blanks stay zero. Rejected: a single fixed maze or forcing all seeds
into one connected free-space region. The 300 input probes observed unreachable
blanks in 25/100 easy, 35/100 medium and 37/100 hard draws, and all eight seed
colors in every band. These are input/diagnostic measurements, not 300 additional
Racket executions.

## R5 — Teach the same-color distinction redundantly
A single repeated-color example in a four-pair lesson would disappear if it
became the query. Hence two repeated profiles in each four-draw cycle, with
5 or 6 seeds and at most 4 colors. Witness rejection requires both tie-by-seed
and first-seed-per-color predictions to differ. The other three rivals differ
on every accepted input. Rejected: two inference guesses as a substitute for
teaching support, or merely checking individual witness frequency. Tests cover
105 distinct generated input positions, 96 overlapping four-pair windows and
384 query holds. The separate production census has 300 lessons, 1,200 unique
inputs, 1,200 rotations and zero reported rival ambiguities. It uses requested
starts 0..99 per band and records accepted indices; all outer sampling rejections
are empty. The small four-phase argument complements, not replaces, those tests.

## R6 — Use bounded diagnostic computation, not Python labels
Per-seed BFS diagnostics have a bounded immutable LRU cache of 128 grids/modes.
A sample has at most 512 candidate attempts and raises on failure, with no
non-teaching fallback. Geometry and colors are genuinely resampled, not selected
from stored canonical examples. Racket remains label authority. The separately
implemented test oracle, per-color solve implementation, geometric/palette
metamorphic tests and 40 public-API Racket comparisons reduce common-mode risk;
finite agreement is not proof for all inputs. Rejected: changing the slow
canonical Racket implementation during a sampler repair.

## R7 — Validation is a chosen training manifold
Validator: rectangular integer cells 0..9, dimensions 3..30, blank and wall cells,
2..8 seeds, at least 2 seed colors. It accepts all canonical inputs and intentionally
does not require isolated seed components or distinct seed colors. It is broader
than the generated range but not a validator for the entire mathematical rule.
No-wall, one-color, identity, all-tied or very large scenes are outside this
sampling study. Arbitrary explicit override lessons and lessons with fewer than
three demonstrations are not certified as rotation-safe.

## Experiments, failures and provenance
Initial regression run: 9 failed, 4 passed against the baseline. The first repair
passed those 13 tests; expanded final tests pass 49/49. An intermediate standalone
lint invocation was externally interrupted at 200 seconds: its retained status
is running/incomplete, exit code unknown, never a pass. The final battery's lint
completed cleanly. The documented strict-rotation flag is not exposed by the
public `check` CLI (exit 2); a first workspace attempt mistakenly supplied a
positional ID (also retained). The corrected route uses `workspace --id` and
invokes the unchanged native semantic gate, while the production census already
uses required rotations. None of these harness failures is hidden or represented
as a generator failure. See `RESULTS.json` for actual statuses.

The exposed solve was prepared after generator bytes were frozen. It has prior
rule exposure explicitly marked yes; no generator, rule or private answers were
consulted during that solve phase. Both solve records have one real revision and
3/3 visible examples matched; query scores remain withheld. No fabricated failed
solve or token-level model trace is claimed.

## Self-review
Witness-conditioned rejection and a deterministic seed-count schedule narrow the
training distribution; uniform unrestricted Voronoi sampling and universal
identifiability are deliberately not claimed. The exact same-color witness,
independent oracle, palette/geometry equivariance tests, accepted-index census
and all cyclic start residues were checked for new shortcut regressions, with
no new defect detected within the declared five-rival/default-lesson scope.
