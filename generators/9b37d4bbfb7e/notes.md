# 9b37d4bbfb7e — current design, version 3.0.0

## Rule and authority

On background 0, an object is a **same-color four-connected component**. Erase
the whole object if any cell touches any outer border; preserve every wholly
interior object. Diagonal contact does not connect objects, and cardinal contact
between different colors does not connect them. The selected Racket rule remains
unchanged, pinned by `RULE_HASH = "b41941e8090e"`.

## Decisions replacing version 2.0.1

The original rationale was not recorded: notes were a skeleton and associated
notes were empty. Its four fixed, distinct-color stamps silently ignored count
and palette requests; its validator joined all nonzero neighbors across colors.
Its description called the fourth stamp right-border even though its columns
were interior. These choices are replaced by constructive monochromatic object
placement, observable exact controls, and a validator with the rule's topology.

The documented domain is 6–12 rows by 7–14 columns, 2–6 components, 2–6 used
nonzero colors, and both erased and retained objects. Shapes grow from connected
seeds without overwriting cells, merging same-color objects, or changing their
border roles. `n_blobs` counts rendered components; `n_distinct_colors` counts
rendered foreground colors. Colors cannot outnumber objects. The full canvas
bounds are available in every difficulty band; band defaults only reweight sizes.

`palette_size` aliases the foreground color count; `texture` aliases
`palette_kind`. Their conflicts are explicit errors naming the conflicting axes.
Unknown keys, noninteger scalar controls, booleans and invalid enum values are
rejected. Aliases and the fixed sparse/mixed policies are diagnostic axes, not
independent Cartesian controls. Warm/cool policies each have six available
colors, so their advertised maximum count is achievable.

## Ordinary lesson assembly

Use four consecutive demonstrations and one query. The declared schedule period
is four, with top/right/bottom/left orientations by sample index. At even
positions the default usually has three objects and three foreground colors,
with one nonsingleton interior survivor; occasionally it has six objects. At odd
positions it has five or six objects and supplies repeated-color, diagonal-link,
different-color-contact, and unequal-interior-size distinctions. Opposing-edge
objects and a third erased object expose edge and count shortcuts.

Every five-pair window has at least two diagnostic odd positions, so at least one
remains when any pair is held out. Required-rotation tests check the other four
demonstrations for actual rival refutation. `CANONICAL_SHORTCUTS` contains seven
rules that each fit all four usable canonical pairs; `LESSON_COMPETITORS` adds
six simpler alternatives. These finite rivals are evidence of teaching coverage,
not a proof of unique induction against every possible rule.

The first v3 candidate overconcentrated on diagnostic five/six-object layouts.
The structural check identified lost canonical support. The current mixture
restores the canonical three-object/three-color/no-singleton structure and
weights the canonical canvas/palette profiles, while retaining diagnostic grids
after every query holdout. The retained return documents both failed iterations.

## Fixtures, tools, and limits

`counterexamples/` keeps legal semantic separators and the three former negative
textures as explicit data. No-border and all-border cases are Racket-lawful but
outside the ordinary mixed-outcome training domain; their texture names now
raise errors. `tests/` checks topology, canonical acceptance, exact controls,
minimum canvases, alias conflicts, deterministic generation, and lesson holdouts.
`workspace/` holds portable authoring and evidence-verification tools.

Exact overrides can deliberately request simpler grids; they do not inherit the
default lesson-refutation guarantee. The sampler remains sparse and structured,
has fixed background 0, bounded small objects, and does not claim full support
over every input accepted by the Racket program. The preserved canonical-style
branch counters an always-multiple-survivors heuristic, but a model could still
learn untested template-specific shortcuts. Broader deployment should retain
these limits and add newly discovered rivals rather than interpret a finite
census as universal correctness.

## Open shared-tool finding

F1 in the return's `FEEDBACK_TO_CODEX.md` remains open: the shared semantic gate
unconditionally warns `declared_period_not_enumerated` for a declared period and
cannot consume a separately completed enumeration. The return includes both a
300-lesson required-rotation census and complete fixed-seed period enumeration,
plus a verifier that checks their source binding and actual coverage. It does
not suppress the raw warning, change the shared gate, or grant training approval.
## Current reviewer considerations

Source SHA-256: `721dd5dac679d41722e20f174628c892f06cc61f91f109dae2040b5e0335e044`.

# Design decisions — 9b37d4bbfb7e

Assignment `review-45ba7e74d228c452` is unchanged. The selected generator moves
from 2.0.1 to 3.0.0. Final generator SHA-256:
`721dd5dac679d41722e20f174628c892f06cc61f91f109dae2040b5e0335e044`.
All source changes stay under `repo/generators/9b37d4bbfb7e/`; neither audited
task nor shared source is patched. This is an authoring work log, not a captured
token-level conversation or model-likelihood record.

## D1 — Match object identity to the authority

**Prior choice:** the text said four-connected nonbackground blobs, while the
validator traversed every nonzero cardinal neighbor regardless of color. The
selected Racket program operates on same-color four-connected objects. The
original notes supplied no rationale for this mismatch.

**Decision:** use the shared component helper with both semantic arguments
explicit: `same_color=True, connectivity=4`, background zero. A 6×7 input with
color 2 at (0,2) and color 3 at (1,2),(2,2) has a border object and an interior
object. The old validator merged them and rejected it. Racket erases only 2;
the new validator accepts it. The retained fixture, focused regression, and
public Racket probe make that distinction executable.

**Rejected alternative:** describe mixed-color connectivity as the intended
rule and edit Racket. It would change the selected authority to accommodate a
validator bug. No canonical or generated-label evidence justified that change.

## D2 — Make exact controls describe the rendered grid

**Prior choice:** four fixed stamps and four sampled colors irrespective of
advertised `n_blobs`, palette count, or palette policy. Unknown keys were also
ignored, and scalar controls were not consistently validated.

**Decision:** construct exactly 2–6 monochromatic components with exactly 2–6
used foreground colors, then grow each component without overwrites or merges.
Growth keeps each component's chosen border status. The rendered observability
hook independently counts components and distinct nonzero colors. All 15 legal
count/color combinations are checked at the smallest canvas in each difficulty;
the independent review also checked every orientation and four canvas corners.

The only mathematical count conflict is more colors than components. Error
objects name the participating axes, including whichever alias the caller used.
Dimensions remain available over the full stated range in every difficulty.
Literal integer validation rejects booleans, floats and numeric strings for
exact numeric controls, and unknown keys produce an actionable error.

**Rejected alternative:** reduce the advertised count axes to a fixed four to
make the old drawing pass. That would preserve avoidable coverage restrictions.
Another rejected design was unrestricted rejection sampling: constructive
placement makes the small-canvas combinations predictable and avoids acceptance
bias from variable retries.

## D3 — Preserve compatibility without counting aliases twice

`palette_size` means the number of used foreground colors and aliases
`n_distinct_colors`; background zero is excluded. `texture` aliases
`palette_kind`. Either spelling gives the same seeded result. Supplying both
with conflicting values is an explicit error. `position_bias` and `density`
retain their single documented mixed-outcome/sparse policies.

These four compatibility/fixed controls have diagnostic probe metadata. They
are not independent dimensions of a Cartesian experiment. Focused tests still
exercise every palette alias, exact color count and alias conflict. This avoids
misrepresenting alias combinations as independent degrees of freedom. Warm and
cool palettes each supply six nonzero choices so all advertised counts work.

## D4 — Teach component semantics, not global color erasure

**Prior choice:** each object had a distinct color. Erasing every occurrence of
a color found on the border therefore matched its ordinary outputs. The same
shortcut also fits all four canonical pairs. This is the strongest simple rival
chosen for the review question; it requires no connected-component reasoning.

**Decision:** diagnostic samples contain a border object and a disconnected
interior object of the same color. They also place same-colored objects in
diagonal contact and differently colored objects in cardinal contact. These
deliberately separate whole-color removal, eight-connectivity and mixed-color
connectivity. A third border object, right-only border contact, and differently
sized interior objects separate several further canonical-fitting rivals.

The seven declared canonical shortcuts are executable and each fits 4/4
canonical pairs. The six additional lesson competitors include ignoring each
other edge, changing only border pixels, identity and erasing everything. Probe
tools read the module's actual declarations; they do not maintain a copied list.
All Python predictions are hypotheses. Public Racket application supplies the
authoritative counterexample labels.

## D5 — Make the guarantee about complete lessons

The ordinary contract uses four consecutive demonstrations and one query.
`LESSON_SCHEDULE_PERIOD=4` records top/right/bottom/left orientation. Both
opposing edges are represented in each normal pair of related layouts. Odd
positions supply the diagnostic distinctions. Every five-consecutive-pair
window contains at least two odd positions, so holding out any one query still
leaves at least one diagnostic demonstration.

Focused tests require every competitor to be refuted by the remaining four
demonstrations for every held-out query; they do not merely accept a rival that
also happens to agree on that particular query. The public battery checks
12 ordered lessons and 60 required rotations. The larger production census
checks 100 lessons per band, 300 total, with 1,500 pair instances and 1,500
rotations; its 1,500 inputs are unique. Separately, seed 0 enumerates all four
starting residues across three bands: 12 lessons, 60 rotations and 9 unique
inputs. These last 60 pair instances overlap heavily and are not 60 independent
grids. Both final censuses report no ambiguity, scoring errors or materialization
errors under the declared rival contract.

**Rejected alternative:** rely on witness frequency in unrelated individual
draws. A witness appearing somewhere in a sample says nothing about whether it
appears in a particular four-demo lesson. Another rejected alternative was an
ordered-only guarantee; the chosen construction can retain named-rival teaching
support under every single-query holdout and is therefore tested with the
required policy.

The census reporting modulus of six is not the generator's schedule period of
four. The reusable receipt verifier reconstructs coverage from lesson records,
starting indices and query positions, rather than trusting the modulo-six
summary buckets or a claimed `complete_fixed_seed` status alone.

## D6 — Retain canonical structure as well as diagnostics

The first v3 candidate had diagnostic layouts at every default position. It
passed 109 focused tests but the after battery flagged disjoint canonical
object-count and marker-related profiles. Three added per-band structural
regressions failed on that candidate. The new mixture normally uses three
distinct-color objects at even positions, one nonsingleton interior object and
two border objects, while odd positions keep the richer diagnostic layouts.
Occasional six-object layouts add count variation.

Dimensions and color count favor the canonical profiles without restricting
the explicit bounds. The baseline had 0/60 exact canonical-size/palette hits;
the final profile-floor check has 35/60, split 12/20 easy, 11/20 medium and
12/20 hard. The final defect linter passes. This is measured support for the
checker-defined profiles, not a claim to reproduce the full unknown canonical
data distribution. All 4 canonical inputs pass the domain hook, and all 600
semantic-gate draws pass the explicit strict domain.

## D7 — Keep negative fixtures outside ordinary training

The old production `texture` enum also advertised `no_border_blobs`,
`no_interior_blobs` and `all_border`. These contradict the intended mixed-outcome
domain. They now live as exact regression data under `counterexamples/`; the
production texture names reject them. Their Racket outputs remain valid: the
first is unchanged and the other two become blank. Rejecting them from this
generator's ordinary domain is distinct from claiming the reference rule is
undefined on them.

## D8 — Preserve the shared warning and build a useful check

The final battery exits 1 with 11 green stages and one semantic-gate warning:
`declared_period_not_enumerated`. The shared gate unconditionally emits that
warning for an honestly declared period and cannot import completed external
enumeration. Removing truthful schedule metadata would conceal the limitation;
editing shared code would exceed this assignment's allowed source delta.

The return instead retains the raw warning, runs the requested enumeration,
and adds a task-local standard-library verifier that checks source hashes,
declared metadata, report consistency and complete period/query coverage.
It rejects stale or incomplete evidence and issues a bounded receipt without
granting approval or claiming the raw gate passed. F1 describes the shared
integration change still requiring a maintainer decision.

## D9 — Remaining limits and review discipline

The default generator is still a sparse, structured curriculum. Small grown
objects, fixed background 0, bounded canvases, and a recurring diagnostic
arrangement are deliberate limits; a sufficiently specialized untested rival
could exploit them. Canonical-style samples refute an always-multiple-survivors
shortcut, and rotation/edge and shape variation reduce several simpler biases,
but finite rivals cannot establish universal identifiability. Exact overrides
may request simple lawful cases and do not inherit the ordinary lesson claim.

Independent code review found no critical or important functional issue after
240 corner/count constructions and explicit holdout checks. Its two remaining
comment inaccuracies were corrected before the final source-bound checks.
Earlier failures and superseded hashes remain retained with clear labels.
The fresh solve has one genuine visible-success attempt, an honest earlier-rule
exposure declaration, and unknown private correctness. The exact patch replay
and focused tests in a fresh extraction are recorded in `RESULTS.json` and the
final handoff evidence; completion does not silently waive the shared warning.
