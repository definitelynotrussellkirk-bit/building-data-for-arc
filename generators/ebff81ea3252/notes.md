# Working notes: ebff81ea3252

## Review 2026-10-03 — assignment `review-1d2a6298f21cafad`

### Baseline findings

The pinned v2.1.0 source (`a6432ed0…775705`) passed rule smoke and basic
profile checks but failed the completed before battery in three blocking stages:

- `lint`: missing `RULE_HASH`; two advertised one-token axes were not probeable.
- `defect_lint`: degenerate textures occupied the ordinary texture domain and
  all four “helpful” texture values were byte-identical to the default draw.
- `override`: declared domains were incompatible with band-specific draw ranges,
  several exact axes were not consumed, and unknown override keys were silently
  accepted. The report contained more than 20,000 rejected declared cases.
- `semantic_gate` was only advisory because no semantic contract existed.

More importantly, the phrase “exact plus” in the old prose was stronger than
the selected authority. The Racket predicate is local: it recolors a green
center plus its four green cardinal neighbors even when those five cells belong
to a larger connected component. The baseline generated only isolated targets,
so the canonical-fitting rival “recolor only components exactly equal to a
five-cell plus” was never contradicted.

### Repair

Version 3.0.0 pins `RULE_HASH = "deb3ac96cc89"` and replaces the ten mostly
nominal controls with four exact, observable axes:

- `grid_h`: 8..11
- `grid_w`: 9..11
- `n_pluses`: 1..3
- `context_mode`: `isolated|attached`

Motifs are packed into separated 3×3 tiles. Attached targets add one corner
cell to the five-cell cross, producing a six-cell component while preserving
the same local center predicate. Every input also contains one separate
P-pentomino decoy, a connected five-cell component with no cross center.

Default sample indices alternate attached/isolated context and cycle target
counts 1/2/3. Any three consecutive demonstrations therefore contain both
contexts and refute both declared canonical shortcuts:

- `component_exact_only`: recolor only isolated five-cell cross components.
- `size_five_components`: recolor every green component of size five.

Executable witnesses, rivals, witness-to-rival claims, a strict canonical-like
hook, lesson identifiability, override observation, malformed-input fixtures,
and a Python authority mirror are retained in `generator.py` and the focused
test file.

### Evidence

- Focused tests: 24/24 pass.
- Final after battery: 12/12 stages green; no advisory or failed stages.
- Semantic gate: strict 600/600, canonical accepted 5/5, both witnesses firing,
  both rival claims verified, 12/12 smoke lessons identifiable.
- Extended source-bound census: 100 lessons per band, 300/300 identifiable,
  1,097 unique inputs across 1,200 pairs, zero Python-mirror/Racket mismatches,
  and neither declared rival survived any demonstration set.
- Final generator SHA-256:
  `660d584a79505d9c4a5804874160076185133bf8bc26c40deceaaafca0dbb34f`.

### Deliberate limits

The generated palette remains fixed to colors 0 and 3 because the selected rule
is color-specific. Each input uses one P-pentomino decoy; this strongly teaches
the negative branch but repeats one morphology family. Difficulty skews default
canvas dimensions, while explicit overrides retain the full declared domain in
every band. The finite rival census measures the two declared shortcuts, not all
possible induction failures.

No prior unintegrated return was used as a repair source. Existing packet notes
were empty; the baseline battery and canonical authority were the evidence.
The Racket authority was not changed.
## Current reviewer considerations

Source SHA-256: `660d584a79505d9c4a5804874160076185133bf8bc26c40deceaaafca0dbb34f`.

# Decisions — ebff81ea3252 review

## D1 — Treat the selected executable authority as the semantic source of truth

**Choice.** Model the rule as a local five-cell cardinal-cross predicate, not as
an “exact connected component” predicate suggested by the legacy title/prose.

**Evidence.** The canonical Racket rule checks the center and four cardinal
neighbors only. A six-cell attached target is changed by Racket. The old sampler
never produced that case.

**Rejected alternative.** Preserve isolated pluses and merely clean the linter
metadata. That would make the battery tidier while retaining the central
teaching shortcut.

**Failure mode guarded.** `component_exact_only` fitting every generated pair.

## D2 — Reduce the public control surface to four honest axes

**Choice.** Keep only canvas height, canvas width, target count, and target
context. Every declared value is accepted in every difficulty band, observed
from the output grid, and tested.

**Original rationale.** Unknown. The v2.1.0 file advertised palette, texture,
density, position, and color-count controls that did not alter the task.

**Rejected alternative.** Add behavior solely to make the old nominal axes
non-dead. Palette variation would contradict a color-specific authority, and
single-token “axes” are not meaningful controls.

**Failure mode guarded.** Silent typo acceptance, band-dependent override
rejection, and metadata that overstates actual diversity.

## D3 — Use separated 3×3 motif tiles

**Choice.** Pack targets and the decoy into 3×3 boxes at stride four. The minimum
8×9 canvas has four slots, enough for three targets plus one decoy.

**Alternatives.** Rejection sampling was simpler but could under-produce at the
smallest exact overrides and made observability harder to prove.

**Failure mode guarded.** Accidental component merging or an unintended second
cross center.

## D4 — Teach component-independence with a one-cell attachment

**Choice.** In attached context, add one corner cell to each cross. The component
has six cells but exactly one qualifying center.

**Alternatives.** Extending an arm was rejected because some extensions can
create another qualifying center or make the visual cue less controlled.

**Failure mode guarded.** Learning “target iff component size is five.”

## D5 — Include one connected five-cell non-cross in every input

**Choice.** Use a rotated/reflected P-pentomino as a negative example.

**Alternatives.** Singles, dominoes, and partial pluses are useful negatives but
do not refute the size-five-component shortcut. Random arbitrary pentominoes
would broaden morphology but require more complex proof that none contains a
cross.

**Failure mode guarded.** `size_five_components` recoloring all five-cell objects.

**Limitation.** One repeated pentomino family can itself become a cue. A future
version may safely broaden to a verified library of non-cross pentominoes.

## D6 — Make three-demo lessons identifiable by construction

**Choice.** Alternate context by sample-index parity and cycle target count modulo
three. Any three consecutive examples contain attached and isolated cases.

**Alternatives.** Independent random context had a nonzero chance of three
isolated demonstrations, so a query could remain ambiguous despite good global
witness frequency.

**Failure mode guarded.** Witnesses existing in the pool but missing from an
individual lesson.

## D7 — Keep validation canonical-backed but distinguish generated observability

**Choice.** `self_check` accepts canonical inputs and lawful five/six-cell target
components; `observe_overrides` additionally requires the generated morphology,
including exactly one five-cell non-plus decoy.

**Alternatives.** Requiring the generated decoy in `self_check` would reject the
canonical ledger. Making `observe_overrides` equally permissive would make exact
axis recovery ambiguous.

## D8 — Do not alter the Racket authority

**Choice.** Pin the existing hash `deb3ac96cc89`; change only the input curriculum,
contracts, tests, and documentation.

**Reason.** Canonical outputs and the selected executable rule agree. The defect
was the generator's narrower teaching distribution, not the transformation.

## D9 — Retain both local regressions and a large source-bound census

**Choice.** Add 24 focused tests plus a reusable Racket-backed probe over 100
lessons per band and all six cyclic schedule starts.

**Alternatives.** The 12-lesson semantic battery is an appropriate smoke test but
not enough to characterize a deterministic schedule or quantify rival survival.

**Limits.** The census checks declared rivals only, counts exact-byte uniqueness,
and does not prove universal identifiability.

## Review 2026-10-25 — assignment `review-08d0cd0ce36b9d08`

The reviewed base generator and canonical Racket rule remain unchanged. A native
three-setting family was added under `workspace/parametric/`: byte-exact `none`,
plus `nearest` and `farthest` variants. Step A applies the canonical local-plus
recoloring and recovers the resulting orange centers; step B measures surviving
green decoy components from those input-derived centers and recolors the unique
nearest or farthest decoy to 8. Matched inputs support 2–6 demos and 1–4
independent queries, include attached targets and up to 20 distributed decoys,
and exercise substantive 30×30 scenes.

The bounded self-audit covered 12 seed/demo/setting jobs and 128 protected-Racket
executions; fixed-corner, largest-object, topmost-object, and alternate-setting
rivals did not survive all visible demonstrations. The retained wrong-intermediate
witness replaces the detected center with the fixed upper-left corner and changes
16 final cells. Public projection produced 24 one-query views; 36 private-field
invariance mutations and 6 visible-change controls passed.

The inherited focused test now resolves its repository and canonical pairs with
`reviewer_support.find_root` and `canonical_pairs`, eliminating its staged-runtime
path warning. The authoring qualification passed all 6 setting/seed jobs and all
5 original labels. This is reviewer evidence only; exact-source owner qualification,
acceptance, and training admission remain pending.
