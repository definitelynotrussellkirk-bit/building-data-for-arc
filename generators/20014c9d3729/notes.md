# Working notes: 20014c9d3729

## Review 2026-10-03 — assignment `review-a6326ce8b7ee2943`

No prior return was used as an implementation lead: `evidence/associated_notes.jsonl` was empty. The selected `3.0.0` baseline executed the intended rule but failed five required
review gates. It did not pin `RULE_HASH`; `self_check` rejected canonical inputs
where a color had only one object; two advertised axes had only one meaningful
value; texture declarations overlapped or were dead; no default draw hit a full
canonical profile; and most advertised overrides were inert or accepted unknown
keys. The retained before battery is under `checks/before/`.

Version `4.0.0` replaces that contract with five exact, observable axes:
`grid_h`, `grid_w`, `n_colors`, `total_objects`, and
`threshold_counterexample`. It uses complete bounded backtracking over cached D4
shape translations, fails loudly rather than returning a partial layout, keeps
within-color sizes unique, accepts all four canonical inputs, and pins canonical
rule hash `0149d1fbd1ae`. No Racket authority or canonical data changed.

All public examples also fit a fixed absolute threshold: kept objects have size
at least four and discarded objects have size at most three. The repaired default
schedule alternates canonical-pattern examples with a decisive same-color size-4
loser / size-5 winner. Thus every consecutive two-example lesson contains a
counterexample to that rival while preserving canonical-scale anchors.

`workspace/lesson_probe.py` checks the assembled lesson rather than only isolated
witness frequency. Its claims are intentionally narrow: it covers the generator's
actual consecutive-window sampler and declared rivals, not all possible human or
model hypotheses.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `3ddb8251733e4dcb9d0722c636154b6ed01a8eed95df9403852c798e2e810c1f`.

# Decisions for `20014c9d3729`

Assignment: `review-a6326ce8b7ee2943`
Final generator: version `4.0.0`, SHA-256
`3ddb8251733e4dcb9d0722c636154b6ed01a8eed95df9403852c798e2e810c1f`

## Evidence policy and original rationale

`evidence/associated_notes.jsonl` was empty. Therefore no prior return supplied an
implementation rationale. The baseline source comments claimed that broad random
sizes, colors, shapes, and positions were intended to improve diversity, but the
reason for its nine-axis public contract, negative textures, and “return the last
partial grid” fallback is **unknown**. I retained the useful intent—varied lawful
objects—while replacing claims that could not be observed or verified.

## D1 — Preserve the canonical rule; pin it instead of rewriting it

**Choice.** Keep the existing Racket/canonical transformation and add
`RULE_HASH = "0149d1fbd1ae"`.

**Rationale.** The baseline rule-smoke and authority-sync stages passed. The
failure was in generation and validation, not output authority. Changing a correct
rule would add risk without addressing any failed gate.

**Alternatives rejected.** Rewriting the Racket rule to mirror new Python code was
rejected because it would duplicate a verified authority and require a canonical
change. Treating the hash as optional was rejected because it had already caused a
blocking lint failure.

**Probe.** Final rule smoke applies 120 generated inputs and compares the Python
mirror with Racket; 120/120 agree and no call crashes. Authority sync reports one
exact selected/canonical group and 3/3 train plus 1/1 test execution parity.

**Failure mode/limit.** `rule_mirror` is not authority. It is safe for bulk probes
only while the separate Racket parity check remains bound to the same source hash.

## D2 — Replace the nine-axis surface with five exact observable axes (R1, R3)

**Choice.** Advertise only `grid_h`, `grid_w`, `n_colors`, `total_objects`, and
`threshold_counterexample`.

**Rationale.** A control should change a measurable property of the returned grid.
The baseline advertised singleton axes, palette aliases that did not affect bytes,
invalid textures inside the normal domain, and height/width overrides that were
ignored. The smaller contract is strong enough to control task complexity and can
be recovered exactly by `observe_overrides`.

**Alternatives rejected.** Patching each legacy axis individually was rejected:
`position_bias` and `size_spread` had no alternatives; palette “textures” were
semantic no-ops; `n_distinct_colors` duplicated `n_colors`; and degenerate fixtures
were not lawful training inputs. Marking them diagnostic would preserve confusing
surface area without training value.

**Probe.** The final override checker exercises 318 cases in all three bands,
performing 28,620 accepted draws with zero findings or warnings. Task tests cover
minimum, maximum, and stress combinations plus the complete 128-case boundary
cross-product.

**Failure mode/limit.** The contract intentionally offers no direct shape-family,
position-bias, or palette-family axis. Those properties still vary stochastically,
but callers cannot demand an exact value.

## D3 — Use canonical-size anchors on even sample indices (R4)

**Choice.** Cycle through `(8,9,3)`, `(9,9,2)`, `(9,10,3)`, and `(10,10,3)`, where
the third value is the number of nonzero colors. Use five total objects on these
anchor draws.

**Rationale.** The baseline generated larger scenes and missed every exact public
profile in the 60-draw gate. Anchors give regular demonstrated-scale support while
odd draws retain broader difficulty-aware size variation.

**Alternatives rejected.** Shrinking every draw to a public profile would overfit
the four examples. Depending on low-probability random profile hits would make the
profile floor seed-sensitive. A separate `canonical_profile` axis was unnecessary;
sample scheduling provides the support without expanding the public contract.

**Probe.** Final profile floor accepts all 4 public inputs, observes 33/60 exact
profile hits and 37/60 envelope hits, with at least one exact hit in every band.

**Failure mode/limit.** Half the deterministic schedule is anchored. This is a
training distribution choice, not a claim that only those four profiles are valid.

## D4 — Make the public-example shortcut a first-class semantic rival (R5)

**Choice.** Declare `fixed_size_threshold_four` in both `CANONICAL_SHORTCUTS` and
`LESSON_COMPETITORS`; declare witness `relative_size_not_absolute`. Odd sample
indices create a same-color size-4 loser and size-5 winner.

**Rationale.** All four public pairs support both the intended “largest per color”
rule and the absolute `size >= 4` rule. Pointwise lawful generation is insufficient
if each training lesson leaves this rival viable. A witness must occur in the
demonstrations, not merely somewhere in a large sample pool.

**Alternatives rejected.** Randomly sampling the counterexample was rejected because
a healthy aggregate frequency does not guarantee each assembled lesson teaches it.
Making every example a counterexample was rejected because canonical-pattern scenes
are also useful and preserve demonstrated morphology. Adding a prose warning alone
would not be executable.

**Probe.** The built-in semantic gate sees 306 witness draws out of 600 and verifies
the rival on 60/60 checks. `workspace/lesson_probe.py` checks all 100 cyclic starts
per named band: every two-demo window refutes the rival, and no rival fits all demos
while differing on the query.

**Failure mode/limit.** Only declared rivals are tested. The schedule does not prove
universal identifiability to Qwen3.5-9B or exclude unknown hypotheses.

## D5 — Bound object sizes to 1–6 and require uniqueness within color

**Choice.** Each color receives one winner of size 4–6 and zero or more losers of
size 1–3, except the explicit threshold witness, which includes size 4 and 5 in the
same color. Sizes are pairwise distinct within each color.

**Rationale.** Unique sizes make the canonical rule unambiguous. The 1–6 bound packs
reliably on the smallest 8×9 canvas while supporting nontrivial polyomino geometry.
The winner range preserves the public threshold pattern on anchor examples; the
witness deliberately breaks it.

**Alternatives rejected.** Baseline sizes up to 8 were rejected for the new minimum
canvas and exact 8-object boundary contract because they increase packing failure
risk without a demonstrated need. Equal-size ties were rejected as outside this
task's demonstrated manifold rather than treated as ordinary texture.

**Probe.** `self_check`, `observe_overrides`, semantic witnesses, the 160-draw broad
sweep, and the boundary cross-product jointly verify this plan.

**Failure mode/limit.** Tied-largest behavior and objects larger than six are not
covered. This is explicit rather than silently accepted.

## D6 — Use D4 shape variants plus complete bounded backtracking (R6)

**Choice.** Build a small connected shape library for sizes 1–6, take rotations and
reflections, cache every in-bounds translation, and backtrack over placements in
descending size order. Same-color objects may not touch cardinally.

**Rationale.** The baseline attempted a limited number of random placements and then
returned the last grid even if incomplete. Exact axes require either a valid scene
or a clear error. Cached candidates make exhaustive placement practical at these
small bounds, while D4 closure gives orientation diversity.

**Alternatives rejected.** Unbounded random retries were rejected as nondeterministic
and potentially slow. A greedy-only placer was rejected because legal dense cases
can require moving an early object. Silently reducing object count was rejected
because it violates exact overrides.

**Probe.** The smallest-canvas/largest-count stress combinations and all 128 boundary
cross-products construct valid exact scenes. The final 28,620-draw override audit
contains zero packing or validity failures.

**Failure mode/limit.** The search has a 500,000-node cap. It is complete only within
that bound; future expansion of axes or shapes should rerun the exhaustive boundary
suite and may need a stronger solver.

## D7 — Make `self_check` match the demonstrated task, not the baseline generator

**Choice.** Accept a color with one object, provided the full grid has 2–4 colors,
5–8 objects, at least one repeated color, lawful ARC cells, sizes 1–6, distinct
sizes within each color, and a unique largest object.

**Rationale.** Three public inputs contain a color with only one component. For such
a color, that component is trivially the unique largest and is kept. Requiring two
objects per color was a generator-specific assumption that contradicted authority.

**Alternatives rejected.** Special-casing the four public grids by hash was rejected
as brittle. Removing structural checks entirely was rejected because it would make
semantic and override observations meaningless.

**Probe.** All 4 public inputs pass. Ragged rows, invalid colors, blank grids,
ambiguous sizes, and out-of-manifold dimensions/counts are covered by focused tests
or battery mutation checks.

**Failure mode/limit.** The validator enforces the selected training manifold, not
the entire mathematical domain of the Racket rule.

## D8 — Reject unknown controls and invalid difficulties immediately

**Choice.** Accept only `None|easy|medium|hard`, reject unknown override keys, and
require a true Boolean for `threshold_counterexample`.

**Rationale.** Silent acceptance created false provenance in the baseline. A caller
must not believe a typo or unsupported control changed the data.

**Alternatives rejected.** Ignoring unknown keys for forward compatibility was
rejected because generation records would then assert effects that never occurred.

**Probe.** Focused tests exercise unknown key and invalid-difficulty rejection. The
override gate reports `unknown_key_verdict = rejected`.

**Failure mode/limit.** This is intentionally strict and can break callers that were
relying on ignored keys; such callers should be corrected.

## D9 — Add both pointwise and episode-level semantic checks

**Choice.** Keep `rule_mirror`, `strict_canonical_like`, witness/rival declarations,
and `observe_overrides` in the generator. Add `workspace/lesson_probe.py` for actual
lesson windows.

**Rationale.** Battery stages verify pointwise legality, rule parity, and witness
frequency. They do not by themselves prove that every assembled set of demos
eliminates a known shortcut. The probe fills that gap and discovers rivals from the
source rather than duplicating their names.

**Alternatives rejected.** Hardcoding `fixed_size_threshold_four` in the probe was
rejected because declarations can evolve. Labeling all 900 occurrences with Racket
was rejected as unnecessary after final-source 120/120 mirror parity; the mirror is
far cheaper for exhaustive cyclic windows.

**Probe.** Seed `20014`, starts `0..99`, two demos plus one query, three bands,
300 windows, 204 unique inputs, zero ambiguities. The report records its sampler,
domain limits, source hash, and canonical-rival compatibility.

**Failure mode/limit.** If the mirror or rival declaration is wrong in the same way
as the generator, this local probe can mislead. Retaining independent Racket parity
and canonical checks is mandatory.

## D10 — Keep authority and audit work separate

**Choice.** Do not modify canonical data, the selected Racket bank, or either audit
target. Package audit counterexamples as evidence only.

**Rationale.** The assigned repair is source-scoped, and the two random audits are
adversarial reports, not permission to patch unrelated tasks.

**Probe.** Fresh patch replay lists only six selected-task paths. Authority sync
remains synchronized. `AUDIT.md` records the exact target hashes and domain status.

**Failure mode/limit.** Audit targets remain defective until separately assigned and
repaired.

## Review 2026-10-25 — assignment `review-9432a0bfd332a6c9`

The selected 4.0.0 base generator was retained byte-for-byte. Its canonical rule,
ordinary generation, exact controls, lesson witness and focused tests were already
healthy, so this review adds a native parametric family rather than changing the
production source.

The canonical setting `selection_policy=per_color_largest` keeps the unique largest
connected object of each nonzero color. The added setting
`selection_policy=min_winner_threshold` first identifies those per-color winners,
records their sizes, relays the minimum winner size, then keeps every object whose
size meets that input-dependent threshold. The protected counterfactual relays the
maximum winner size instead; its different Racket output is the causal witness that
step B consumes step A's computed intermediate.

`workspace/parametric/prototype.py` supports independently requested 2–6
demonstrations and 1–4 queries with deterministic matched inputs and prefix
stability. The fourth query is a substantive 30x30 scene. Constructive lessons
separate both settings and the declared shortcut rules without using query labels.
The task-local `audit.py` checked seeds 0, 17 and 97 at 2, 3 and 6 demonstrations:
18 setting/count reports, 61 protected-Racket labels and zero surviving declared
shortcuts. Authoring preflight, causal replay, four-query public projection,
first-turn invariance and 39 focused tests passed. This is reviewer-ready source,
not owner acceptance or training admission.
