# Working notes: 4c26a1072222

## 2026-10-23 review `review-d262182682b4f569`

Current generator SHA-256:
`5816599d9ed224a6d95f56745292449c464b6e708cac9373db58e8671b8aa22d`.
Canonical rule hash remains `a86a18b84011`; no Racket authority text or
canonical behavior changed.

### Source-count cue repair

The retained 2.0.0 curriculum coupled every three-color A block to transpose or
anti-transpose while every non-transpose band used two colors. A solver could
therefore gate the transform family on source-color count instead of learning
the A→B relation. Version 2.1.0 keeps three colors for transpose-family bands
but also schedules one causally active three-color non-transpose band in every
lesson (preferring a non-identity transform). The exact source-count gate is now
a declared canonical-fitting shortcut and lesson competitor, with a linked
`source_count_decorrelation` witness. The canonical default, authority selector,
active recoloring, D4 coverage, dimensions, and palette contract are unchanged.

The focused generator suite was driven red-to-green by the cue regression and
passes 24/24 tests. The combined production/prototype scope passes 32/32 tests.

### Forward/inverse application prototype

`workspace/parametric/` adds one episode-fixed hidden value:

- `forward` returns the canonical program byte stream and applies the inferred
  transform to C.
- `inverse` makes one local program change: transform indices 4 and 5 swap when
  applying the learned relation to C; the other six D4 operations are
  self-inverse and the learned color map is unchanged.

Each setting uses four demonstrations and four distinct queries. For a fixed
seed both settings share the same input schedule, and retained inputs force an
observable quarter-turn distinction. Public challenge IDs are computed only
from visible demonstrations and query inputs; the verifier writes those canonical
visible bytes directly, so each `public.json` SHA-256 equals its public ID. Batch
manifest rows are sorted by opaque public ID and duplicate visible payloads fail
closed. Seed, setting, program, sampling receipts, and query labels remain private.

Protected verification produced 32/32 successful Racket executions across two
episodes, exact Python/Racket parity, and one surviving setting after the four
demonstrations in each episode. Public IDs are
`f57aa109d17129d73a4ab44d45bbb53553700b258558e31700713b455d8b702a`
(forward) and
`23e2f57ed080a629c89416522108c1f8908088833db119397ab4307d4ed3b22a`
(inverse). The bounded adversarial probe covered 16 episode cases, 152 unique
inputs, zero/negative/large/fixed seeds, 4/4 and 5/6 demo/query counts, exact
integer grids, hidden-field-stable public IDs, corrupted-label rejection, and
duplicate-query rejection. Its maximum observed construction retry was zero;
explicit exhaustion of the 512-attempt bound was not forced.

This prototype is not catalog approval, an accepted parametric variant, a
production API, or training admission.

## 2026-10-03 review `review-43ce6510b856b5d2`

Baseline generator SHA-256:
`28a057808ae7a607c122c1f799568bde6f7e04877f93d4df759d5f152c9e5908`.
Final generator SHA-256:
`c55bd10cff6e9f5846e33302b895c6316effa805d46c5b85f77bcdcbd1d99580`.

No prior associated review note was available; `evidence/associated_notes.jsonl`
was empty. The immutable packet baseline and retained before checks were the
starting evidence.

### Root cause

The old sampler created four distinct A colors and mapped them to four distinct,
disjoint B colors. Under the canonical selector, any D4 transform then defines a
functional map and every transform receives exact score zero. The fixed lower
transform-index tie-break always chooses identity, so the claimed horizontal
flip branch was dead even when the constructor had used it to make B.

### Repair summary

- Pinned canonical `RULE_HASH = "a86a18b84011"`.
- Replaced nominal branch construction with a pattern bank whose outputs are
  reselected by the same functional-map/score/tie-break logic as the authority.
- Covered all eight D4 branches, including transpose branches absent from the
  public examples.
- Added active partial recoloring, independent per-band relations, complete
  structural/palette validation, exact observable controls, a Python rule
  mirror, semantic signatures, executable witnesses/rivals, and whole-lesson
  identifiability checks.
- Restricted sizes to the canonical three/four-band profiles and changed C from
  four isolated cells to asymmetric 3+1 patterns after density lint failed.
- Made difficulty bands observably different through schedule offsets after the
  first repair draft produced byte-identical bands.
- Synchronized selected base `target_code` to canonical source while preserving
  old text in `raw_code`; no canonical rule behavior changed.

### TDD chronology

The first task-local tests failed on missing hash/mirror/semantic hooks, fake or
unhonored axes, and absent D4 coverage. After the initial implementation, new
regressions reproduced canonical-density failure and dead difficulty bands; both
failed before their fixes. A final source-authority test failed on the old
selected base text before the task-local synchronization patch. The final
portable copied-runtime test stage passes 22 tests.

### Retained evidence

- Completed final battery: `checks/after/` — 12/12 green.
- Earlier interrupted aggregates: `checks/before/` and
  `checks/after-interrupted/`; neither is represented as a finished pass.
- Intermediate defect failures: `checks/after-defect/` and
  `checks/after-defect2/`; final clean rerun: `checks/after-defect3/` and the full
  battery.
- Source-bound whole-lesson census: `checks/lesson-probe.json` — 100 production
  lessons per band, 500/500 unique inputs per band, all witnesses present in
  every lesson, zero declared rival survivors.

### Remaining limitations at the 2026-10-03 review

The generated C domain was deliberately narrower than the full lawful 2x2
domain: only asymmetric 3+1 patterns were used. Three-color A blocks were also
coupled to transpose/anti-transpose branches. The source-count coupling was
resolved in version 2.1.0 on 2026-10-23; the intentionally narrow C morphology
remains and no exhaustive-domain claim is made.
## Current reviewer considerations

Source SHA-256: `5816599d9ed224a6d95f56745292449c464b6e708cac9373db58e8671b8aa22d`.

# Decisions for 4c26a1072222

## D1 — Treat the authority selector as the branch definition

**Input choice.** A constructive A/B template is admissible only when the exact
functional-map, exact-score, and transform-index tie-break procedure reselects
the intended transform.

**Original rationale.** The baseline comments claimed that per-band transforms
would exercise rule branches, but no retained rationale explained why four
unique source colors and disjoint mapped colors would identify a transform.

**Alternatives considered.** (1) Keep constructing B from an intended transform
and trust the label; rejected because that was the root defect. (2) Patch only
`flip_lr`; rejected because the authority has eight branches. (3) Require a
unique winning transform for every example; rejected because the real rule
contains a meaningful tie-break and some two-color canonical-like patterns use
it.

**Probe and failure mode.** `_select_relation(A,B)` runs on every constructed
band and raises if the selected branch differs. Tests enumerate every exact
`first_transform` value. A future edit that changes a template, map, or tie-break
will fail at construction or in `test_every_d4_branch_is_authority_selected`.

## D2 — Use three or four bands, never two

**Input choice.** `n_bands` is exactly `{3,4}`; default sampling alternates.

**Original rationale.** The baseline varied output height with 2–4 bands, but
canonical inputs have three or four bands. The two-band option was diversity for
its own sake rather than canonical support.

**Alternatives considered.** Keeping 2–4 failed the profile-floor intent and
spent lesson capacity off-profile. Fixing four bands only would match one public
shape but unnecessarily lose the other. Three/four preserves both canonical
heights and gives enough bands for multiple independent relations.

**Probe and limitation.** Exact override observations and profile-floor tests
cover both heights. The generator intentionally does not claim validity outside
height 8/11.

## D3 — Expose only two honest exact controls

**Input choice.** The public axes are `n_bands` and `first_transform`. Invalid or
unknown controls are rejected; no silent aliases remain.

**Original rationale.** The baseline advertised fixed, singleton, or weakly
related fields such as `grid_h`, `palette_kind`, and `texture`, producing dead
matrix dimensions and overlapping degenerate values.

**Alternatives considered.** Retaining those names as diagnostics would preserve
API surface but misrepresent curriculum control. Adding controls for every
internal pattern choice would overfit the review harness rather than improve the
task. The two retained axes are directly observable from emitted grids.

**Probe.** The final override gate accepted 2,430/2,430 draws across 27 cases and
three bands, and task tests verify unknown and out-of-domain values fail.

## D4 — Cover all eight D4 transforms

**Input choice.** `first_transform` cycles through identity, both mirrors, both
quarter-turns, 180 degrees, transpose, and anti-transpose. Each grid also
contains one transpose-family branch absent from public examples.

**Original rationale.** The baseline exposed only identity and horizontal
mirror, and in practice even the mirror collapsed to identity. The selected
Racket rule explicitly contains all eight branches.

**Alternatives considered.** Limiting generation to the four branches seen in
canonical pairs would preserve appearance but allow the executable
`canonical_transform_subset` shortcut. Uniformly random branch selection could
leave small lessons without an out-of-canonical witness. The deterministic
schedule guarantees support while palette and templates retain instance-level
diversity.

**Probe and limitation.** Semantic witnesses and the retained 2026-10-03
100-lessons-per-band census showed every complete lesson refuted the subset
shortcut on source `c55bd10c…`. Version 2.1.0 additionally schedules a
three-color non-transpose band and declares the exact source-count gate as a
competitor; focused current-source tests cover the transpose-first three-band
edge schedule. The retained historical census is not relabeled as a run on the
new source bytes.

## D5 — Use two- and three-color A equality patterns without a transform cue

**Input choice.** Transpose/anti-transpose bands retain verified three-color
patterns with a unique maximum exact score. Every lesson also assigns three
colors to one non-transpose band, while remaining non-transpose bands may use
two colors. The non-transpose three-color band is made causally visible under
partial recoloring when needed.

**Original rationale.** Canonical A blocks use two colors, but two colors alone
cannot reliably identify all eight 2x2 symmetries. Four unique colors were the
baseline's failure because they made every functional map possible. The 2.0.0
repair solved that selector problem but left a new shortcut: three source colors
perfectly predicted transpose-family membership.

**Alternatives considered.** Three colors in every band would remove the cue but
make the canonical two-color shortcut irrelevant. Random counts could leave a
small lesson fully correlated by chance. The deterministic schedule preserves
both equality-pattern families while guaranteeing a source-count
counterexample in every lesson.

**Probe.** The pattern bank remains generated from restricted-growth equality
patterns and asserts both map modes for all eight branches. The exact
`source_count_transform_gate` still fits every canonical occurrence, while
current focused tests require every generated lesson—including the
transpose-first three-band schedule—to contain a three-color non-transpose
refutation.

## D6 — Alternate identity and partial recoloring by band

**Input choice.** Even-numbered bands keep source colors; odd-numbered bands
change one source color to a distinct palette color. C includes the changed
source color on recolor bands.

**Original rationale.** The task requires jointly inferring geometry and a color
map. A relation whose recolored source never appears in C is technically lawful
but does not affect the answer and is weak teaching evidence.

**Alternatives considered.** Recolor every source color was rejected because it
recreates the zero-exact-score collapse. Never recolor was rejected because the
`transform_without_recolor` rival would survive. One active changed color keeps
literal matches available for branch scoring while making recoloring causal.

**Probe.** `active_recolor` fires in 600/600 semantic-gate samples and every
lesson in the retained census; the no-recolor rival is refuted in every lesson.

## D7 — Use an asymmetric 3+1 C pattern

**Input choice.** C is an L-shaped three-plus-one equality pattern, with colors
chosen so all eight nonzero colors occur and recolored mappings are exercised.

**Original rationale.** The first repair draft used four isolated colored cells,
which produced at least 26 components and failed canonical object-density
coverage. Public C blocks mostly contain repeated colors.

**Alternatives considered.** Copying literal canonical C blocks would reduce
novelty and risk memorization. Arbitrary random 2x2 colors would often be
symmetric or omit the active mapped color. The 3+1 family is small, asymmetric,
and keeps component density near the canonical 18/24-object neighborhood.

**Probe and limitation.** The distribution gate is clean after this change. The
family is still narrower than all lawful C equality patterns, so the report does
not claim exhaustive C morphology.

## D8 — Keep exactly eight nonzero colors

**Input choice.** Each complete grid uses eight distinct nonzero ARC colors.

**Original rationale.** The canonical examples and selected profile checks use
this palette size, and the baseline already intended eight distinct colors.

**Alternatives considered.** Smaller palettes would make accidental map
collisions and rival survival more likely; using all nine nonzero colors would be
off-profile. Colors are permuted per instance to prevent literal-color shortcuts.

**Probe.** Strict analysis rejects missing/extra palette colors; profile-floor
and diversity gates report canonical support and all 10 ARC values across the
corpus (background plus the changing eight-color selections).

## D9 — Make difficulty observable without changing the rule domain

**Input choice.** Easy, medium, and hard offset the deterministic sample-index
schedule by 0, 1, and 2.

**Original rationale.** The first repaired draft ignored difficulty, so identical
seed/index calls were byte-identical across all bands and defect lint flagged a
dead curriculum axis.

**Alternatives considered.** Inventing easier/harder semantic subdomains would
add unsupported claims. Offsetting the same lawful schedule is enough to avoid a
dead alias while retaining identical validation requirements.

**Probe and limitation.** Task tests require at least two distinct grids across
the three bands for each tested index. This is curriculum variation, not a claim
that the bands have calibrated human difficulty.

## D10 — Share one analyzer across validation and semantics

**Input choice.** `_analyze` drives `self_check`, strict validation, override
observation, the Python rule mirror, semantic signatures, witnesses, and rivals.

**Original rationale.** The baseline `self_check` was effectively absent, and
separate ad hoc interpretations would invite drift.

**Alternatives considered.** A shallow shape-only check was rejected after the
before defect lint showed minimal impostors and degenerate overlap. Duplicating
analysis inside every hook was rejected as unreviewable.

**Probe.** Tests mutate separators, structural columns, block cells, palette,
shape, and raggedness. Final self-check accepts all six canonical occurrences
and rejects 54/60 generic destructive mutations; the six surviving
`duplicate_first_row` mutations are lawful under the task relation rather than
validator misses.

## D11 — Synchronize selected authority text, preserve provenance

**Input choice.** Both selected base `target_code` fields now equal the exact
canonical `program_solution`; their prior source remains in `raw_code` and the
status records that preservation.

**Original rationale.** Generated behavior and canonical behavior already
agreed, but the runner's selected base source was text-divergent and the defect
linter could not certify the binding.

**Alternatives considered.** Changing the canonical rule was unnecessary and
riskier. Deleting the old base source would discard provenance. Leaving the
selection divergent would keep a false source-of-truth ambiguity.

**Probe.** Authority sync reports selected-exact synchronization and execution
parity over two distinct source texts. There is no Racket behavior change.

## D12 — Retain a source-bound whole-lesson probe

**Input choice.** `workspace/lesson_probe.py` inspects 100 production lessons per
band and every cyclic schedule start, using the generator's actual declarations.

**Original rationale.** The battery's 12-lesson semantic sample is a smoke test;
plausible shortcuts fit every canonical pair and required a larger lesson-level
census.

**Alternatives considered.** Counting witness frequency per grid was rejected
because witnesses may fail to co-occur in a complete lesson. Copying rival names
into a standalone script was rejected because declarations could drift. The
probe imports the final source, hashes it, and iterates actual mappings.

**Probe scope.** It found 500/500 unique production inputs per band, all four
witnesses in all 100 lessons per band, and zero surviving declared rivals. This
is finite evidence over the recorded seed ranges, not universal induction.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/4c26a1072222/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
