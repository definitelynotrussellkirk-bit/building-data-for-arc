# Working notes: 6d19cd1698b1

## Current handoff — review-f5408f5912ca74b7

The selected implementation is version 2.1.0. Racket, its canonical examples,
base solution, shared helpers, and catalog approval metadata are unchanged.
Imported notes retain their original timestamps in `evidence/associated_notes.jsonl`.

### Root cause and changes

Version 2.0.0 never emitted disconnected same-color runs in one row or three
runs in one row. Thus two wrong rules fit all four canonical pairs AND its
entire constructed domain: expand only the outer envelope of each color, or
process only the first two runs per row. Version 2.1.0 retains the original
eight profiles and adds two explicitly observable contrast profiles:

* `repeated_color`: two interior occurrences of the same color with at least
  two intervening zeros, plus another color on another row. Its inward flanks
  refute `color_envelope` on every admitted draw of this profile.
* `three_runs`: three pairwise-distinct-colored interior runs, with randomized
  lengths and gaps. The third has a visible right flank and refutes
  `first_two_runs` on every admitted draw of this profile.

Difficulty previously partitioned grid dimensions, excluding canonical scale
from medium and hard. A common weighted small-scale prior plus a
band-dependent large-size tail now gives every supported dimension positive
probability in every band. Explicit dimensions remain exact. These weights
are a modeling choice, not a claim to have recovered a true data distribution.

### Verification retained in the return

`checks/after-v3/result.json`: strict battery 12 green, zero advisories/failures.
`checks/green-tests-final.log`: 100 selected-task tests passed.
`checks/shortcut-after.json`: 1,152 generated inputs and four canonical pairs
checked against actual Racket; zero mirror disagreements. All 2,187 one-row,
width-seven grids over {0,2,5} also matched Racket (parity-only stress domain).
In 512 default draws (128 seeds reused over four bands), color-envelope was
refuted 76 times and first-two-runs 44 times; both were zero in the baseline.
The standard semantic gate separately verified 57 witnesses for each rival
across 600 draws. See the root handoff for clean-patch replay and repository tests.

### Boundaries and next decision

Keep literal background 0, same-color maximal runs, original-grid flank reads,
and right-run ownership of shared zero gaps. Do not replace Racket labels with
`rule_mirror` or a rival. Existing admission limits (3..10 by 7..14, run length
1..5, max three runs per row, blank row and majority-zero guard) are intentional
calibration restrictions, not universal rule semantics.

Distribution-level witnesses do not guarantee every 2–3-example lesson is
identifiable. No `lesson_identifiable` hook was claimed. The next useful step
is a downstream teacher/learner experiment or an explicit lesson-level
witness schedule, not another geometry rewrite without evidence.
## Current reviewer considerations

Source SHA-256: `72ed3ac218eddf56b680d8fc53dc841ec173bc8e43767811d535cbbcf05b5acf`.

# Decisions — 6d19cd1698b1

Baseline intent comes from the imported source and its retained notes. Where
there was no explicit original justification, the explanation below is marked
as an inference rather than attributed to a previous author. All choices are
input-generation choices; canonical Racket authority is unchanged.

## D1 — Literal background and exact local rule

**Original:** background 0, process maximal same-color horizontal runs, paint
only their immediate originally-zero flanks; right run wins a shared gap.
The rule and canonical examples directly support these choices.
**Decision:** preserve them exactly. Color-renaming foreground is legitimate;
renaming the background or changing collision order is not a harmless
augmentation. Rejected a recursive dilation or output-as-next-input reading.
**Probe:** canonical 4/4 parity and exhaustive 2,187 local rows against Racket,
plus shared-flank and adjacency tests. Python code is never the label authority.
**Limit:** these finite parity tests are not a proof over all colors and widths.

## D2 — Dimensions and difficulty

**Original:** 3..10 high, 7..14 wide; difficulty-partitioned draws. Source was
calibrated to small teaching scenes. Why the old size range was partitioned so
aggressively is unknown. **Failure:** medium/hard had zero canonical profile
support; original before policy warned and the strict after policy rejected it.
**Decision:** retain declared ranges, but give each value positive mass in
every band. Heights use uniform 3..10 plus 16 extra copies of 3, three of 4,
and two of 6; widths use uniform 7..14 plus eight extra copies of 7, four of 8,
and eight of 9. Add two copies of each band's three-value size tail. None uses
only the common prior. Difficulty still changes run-count and tail probabilities.
**Alternatives:** uniform full-range draws dilute small canonical examples;
small-only draws erase scale variation; an opt-out would hide the failure.
**Probe:** 13/60 exact profile hits; nonzero support in every band; 256-seed
per-band tests require canonical profiles and a substantial larger tail.
**Limit:** the mixture weights are review choices, not estimated population
frequencies. Every exact size override remains supported, but not every possible
shape/color combination is guaranteed by an unbounded sampling theorem.

## D3 — Eight original branch profiles

**Original:** independent rows, wide gaps, shared flanks, adjacent distinct
colors, left edge, right edge, both edges and mixed edge/interactions.
Their geometry distinguishes real local-rule branches. **Decision:** retain
all eight and infer requested profile from the visible grid after construction.
**Alternative:** only adding a test fixture would not teach a model those
counterexamples; collapsing profiles to generic random scatter weakens control.
**Probe:** existing tests, explicit profile requests and 64 boundary cases per
profile. **Limit:** a single priority-ordered profile label summarizes a scene;
secondary geometric facts can coexist.

## D4 — Repeated same-row color

**Original:** pair colors forced different; repeats were allowed only on other
rows. That prevented merging touching intervals, but the blanket exclusion
of disconnected same-row repetitions had no retained semantic justification.
**Failure:** color-envelope exactly matches canonical pairs and original domain.
**Decision:** add a repeated-color pair with at least two zeros between runs,
interior flanks, plus a third run in a different color on another row.
The gap cannot merge same-color intervals in the input, and both inward flanks
must grow. Another color retains the existing two-color lesson guard.
**Alternatives:** one-zero same-color gaps also distinguish envelopes but add
a shared-write case to this isolated contrast; mixed-edge repetition can be
added later, but is unnecessary to establish the missing distinction.
**Probe:** every forced repeated-color case refutes the rival against Racket;
76/512 default draws do so. **Limit:** no repeated-color triple or edge-touching
repetition family was added in this bounded change.

## D5 — Three runs in a row

**Original:** generator constructs no more than two runs per row even though
self_check already admitted three. No explicit original justification found.
**Failure:** ignore all runs after the second is canonical-equivalent and fits
the original constructed domain. **Decision:** use three pairwise-distinct
colors, interior placement, lengths 1..5, gaps 0..2, at least one length >=2.
The third run always has a right zero flank, so its omission visibly fails.
**Alternatives:** four or more runs would change calibration limits unnecessarily;
three equal colors would entangle this rival with the color-envelope failure.
**Probe:** 64/64 forced boundary cases and 44/512 default draws refute this rival.
**Limit:** max-three-per-row remains an artificial limit; the intended rule
works beyond it.

## D6 — Run lengths, run counts and visible change

**Original:** lengths 1..5 with at least one run length >=2; 2..6 runs overall,
max three per row; at least two changed cells. Likely teaching-signal and
readability constraints (inference). **Decision:** preserve admission guards.
The constructor samples up to five runs depending on capacity/difficulty;
self_check's upper bound of six is permissive admission, not a promised sampled
count. Hard band does not imply a hard minimum of three when capacity is two.
**Probe:** short-run, count, mutation-negative-control and boundary tests.
Singletons already refuted a third rival in the baseline (335/512); no need to
invent a new singleton-only family. **Limit:** full-width runs, long runs,
one-run scenes and identity outputs remain outside the lesson distribution.

## D7 — Palette, sparse background and blank rows

**Original:** colors sampled from 1..9, two through five actually visible
foreground colors, majority-zero grid and at least one blank row.
Small sparse demonstrations support calibration; exact population frequencies
and the need for every guard are not established. **Decision:** keep guards;
three-run contrasts require at least three palette entries. Foreground colors
are not hard-coded to particular operations. **Alternative:** dense arbitrary
grids broaden formal rule support but may change the intended teaching regime.
**Probe:** canonical admission, self_check, density and palette tests; no rule
color rewrite. **Limit:** observed blank rows and sparse background remain
possible shortcuts for unrelated tasks, not alleged universal necessities.

## D8 — Pure construction, bounded search and cached layouts

**Original:** deterministic named RNG streams and at most 256 attempts to find
a calibrated scene. **Decision:** preserve that bound; derive pair/triple
interval candidates geometrically and cache only immutable tuples keyed by
width/profile, never RNG state or mutable grids. Returned grids remain fresh.
**Alternative:** seed-specific fixtures or modulo dispatch are brittle and were
not used. **Probe:** repeat generation, interleaved calls, global RNG isolation,
mutation tests and battery lint. **Limit:** a finite sweep cannot exclude a
rare search-exhaustion seed; bounded failure is explicit, not an infinite loop.

## D9 — Public controls and failure behavior

**Original:** grid_h, grid_w and scene_profile are the task's declared controls;
unknown keys already raised. **Decision:** preserve these names and exact
observability; reject booleans, floats and strings for integer dimensions.
No silent coercion of 7.0 or True. **Probe:** lower/upper boundaries, all bands,
unknown keys, invalid values and `observe_overrides` checks. **Limit:** no new
palette, exact-count or lesson-level control has been advertised.

## D10 — Semantic claims and proof level

**Original:** no semantic-witness contract, resulting in a no-contract advisory.
**Decision:** register the two geometric predicates, two evaluation-only rivals,
canonical-shortcut names and explicit witness/rival association. The shared
semantic gate invokes Racket to verify actual disagreements, not just predicate
truth. **Probe:** all 114 firing witnesses in its 600-draw run were checked.
**Alternative:** declare `lesson_identifiable` without building a lesson sampler
would overclaim. **Limit:** no per-lesson identifiability guarantee; no learned
model, training throughput or accuracy measurement.

## D11 — Reusable audit tool and evidence

**Decision:** add a task-local source-bound probe instead of changing shared
infrastructure. Use `prepare_runtime` to avoid incomplete source imports, one
protected Racket bridge with bounded batches, all draw parameters, hashes,
optional full case JSONL and first concrete witnesses. Baseline imports are
read-only. Defaults always use the selected current source. A reduced-width
option bounds exhaustive stress work. **Probe:** source-layout launch regression,
full before/after census and clean source-patch replay.
**Limit:** this tool is task-specific; its independent rival suite is not a
universal program search. CLI runs are the supported interface; no promise of
reentrant multi-repository module loading within one Python interpreter.

## D12 — Scope and integration

**Decision:** keep rule, examples, audit targets, shared tools and catalog frozen.
Audit failures are reported, not repaired outside the assignment. Source patch
is bound to the immutable packet/baseline, replayed in a clean extraction and
validated by `package_return.py`. Failed attempts are retained as evidence.
**Alternative:** repacking the entire 92 MB upload duplicates unrelated work and
makes merging harder. **Limit:** the return needs its matching repository to
run; the package does not independently grant approval or train a solver.
