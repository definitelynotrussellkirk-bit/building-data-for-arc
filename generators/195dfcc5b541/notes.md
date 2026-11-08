# Working notes: 195dfcc5b541

## Repair summary

The imported `2.1.0` sampler exposed ten mostly inert or conflicting controls, always placed the stencil on the top border, admitted identity/no-copy mutants, rejected the lawful 11-row canonical example, and had no pinned rule hash or executable lesson-rival contract. Historical `evidence/review_index.json` was used only as a lead; each retained claim was rechecked against the selected source.

Version `3.0.0` replaces that distribution with constructive placement. Four exact axes are recoverable from pixels; unknown and invalid overrides fail loudly. One-cell Chebyshev separation makes planted color-3 copies observable as components and prevents accidental composite copies. Each draw includes a rotation and a reflection-only copy of a chiral stencil, while isolated singleton 3s preserve noisy texture without creating extra matches.

## Semantic contract

`rotations_only` is the strongest retained rival: it reproduces all four canonical training demonstrations but differs on the labelled canonical query. It is declared in `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`; `reflection_required` binds it to a generated witness. Three demonstrations are requested per lesson, and every generated pair individually refutes the rival, so all query rotations in the tested schedules are identifiable against this declaration.

`workspace/reference_probe.py` is an independent geometry oracle with optional selected-Racket parity. `workspace/shortcut_probe.py` discovers the live rival declarations, checks canonical fit, saves exact generated counterexamples, and enumerates every held-out query position for requested cyclic starts. Neither tool is label authority unless the explicit Racket parity path passes.

## Authority handling

The canonical Racket row was not edited. The selected task-specific base solution had behavior-equivalent but text-divergent `target_code`; that selected field was synchronized exactly to canonical text to satisfy active-authority and defect-lint gates. The archival `raw_code` remains unchanged.
## Current reviewer considerations

Source SHA-256: `af8350048eca44100de1d539ba7bb3f295bb82cbf99411f7eef218c4c1e56ed7`.

# Decisions — 195dfcc5b541

## Evidence policy

The pinned baseline generator SHA-256 was
`d6eed96cb049d70223f84e7e900ac604e45e26f2a4158a7916b4553d5b35af2f`.
I read two unverified prior-return excerpts in
`repo/generators/195dfcc5b541/evidence/review_index.json`:
`review-27f8c31f6124f652:v0001` and `review-e8a14a356a4b501b:v0001`.
They were treated as leads only. Their canonical-admission, no-copy,
positional-support, and override-contract claims were independently reproduced
against the pinned source before repair.

## D1 — Preserve the canonical rule

**Choice.** Change the sampler, validator, tests, and teaching contract; do not
change the canonical Racket rule.

**Rationale.** The selected rule reproduced all five canonical outputs and the
independent Python geometry oracle. The defects were distribution, admission,
override honesty, and teaching support—not output semantics.

**Alternatives rejected.** Rewriting the Racket program would add authority risk
without repairing the inert axes or top-edge distribution. A looser “union of
all shape matches” labeler was also rejected because canonical ordering includes
rotation-before-reflection candidate ordering and greedy non-overlap.

**Authority text exception.** The active selected `target_code` was synchronized
byte-for-byte to the canonical program after authority-sync identified an active
text split. This is not a behavior change. Archival `raw_code` remains unchanged.

## D2 — Replace legacy controls instead of preserving aliases

**Choice.** Advertise only `grid_h`, `grid_w`, `shape_variant`, and `copy_count`.

**Original rationale.** The v2.1.0 docstring named many combinatorial axes, but
no durable rationale was recorded for singleton `palette_kind`, singleton
`palette_size`, singleton `position_bias`, `shape_variant="rng"`, ignored
booleans, texture aliases, or degenerate textures. The exact intent is unknown.

**Rationale.** Every retained axis now changes a pixel-observable property and
can be reconstructed by `observe_overrides`. All domain values work in every
difficulty band, so advertised exact overrides never conflict with hidden
band-local ranges.

**Alternatives rejected.** Keeping deprecated aliases would preserve silent or
ambiguous behavior and enlarge the override matrix without adding a meaningful
composition axis. Degenerate modes (`no_stencil`, `no_copies`, `full_grid`) were
removed because they produce non-teaching or validator-rejected inputs.

**Failure modes checked.** Unknown keys, bools, floats, strings, and out-of-range
values are rejected. The final override stage is green, and a direct compact
matrix completed 8,100/8,100 draws over 90 cases and three bands with zero
findings (`checks/override-compact.json` when present; full final evidence is in
`checks/after-final/checks/195dfcc5b541_after_override_results.json`).

## D3 — Canonical-size support and weighting

**Choice.** Support heights 11..18 and widths 17..18 in all bands; use band
weights rather than band-specific legality.

**Rationale.** Canonical inputs include the previously rejected 11×18 case.
The width range matches canonical scale while retaining meaningful exact width
control. Easy favors smaller heights and two copies; hard favors larger heights
and four copies; medium favors the middle, without shrinking the legal domain.

**Alternative rejected.** Keeping 14..18 would knowingly exclude a canonical
pair. Letting difficulty redefine exact axis domains recreated the reproduced
override-contract defect.

## D4 — Two chiral stencil families

**Choice.** Use one canonical-like chiral tetromino and one compact chiral
pentomino; randomize all dihedral orientations.

**Rationale.** Chirality makes a true reflection distinguishable from all four
rotations, enabling a guaranteed counterexample to the strongest canonical
shortcut. Sizes four and five cover the observed canonical stencil-size range.

**Alternatives rejected.** Symmetric shapes cannot teach reflection. Drawing
arbitrary random connected shapes would require a larger chirality classifier,
more placement failure handling, and broader validation than needed for this
repair. Reusing all legacy shapes was rejected because their rationale and
reflection distinctness were not established.

**Limit.** This is a deliberate two-family teaching distribution, not universal
coverage of every lawful polyomino.

## D5 — Constructive semantic copies with isolation

**Choice.** Place two to four copies by backtracking with a one-cell Chebyshev
halo. Force at least one rotation and one reflection-only copy; add only isolated
single-cell color-3 distractors.

**Rationale.** Construction guarantees rule firing and the reflection witness
without repeatedly running a solver inside `generate`. Isolation makes
`copy_count` exactly observable and prevents background 3s from accidentally
forming extra connected copies.

**Alternatives rejected.** Painting copies over unconstrained random 3-noise
made copy count and accidental matches difficult to reason about. Rejection
sampling against the full solver worked experimentally but was slower and
coupled generation to the oracle. Removing those redundant scans reduced a
representative generation cost from about 5.2 ms to 1.7 ms while keeping tests
green.

**Failure modes checked.** A test monkeypatches both solver helpers to fail if
generation or override observation invokes them. Determinism and input
nonmutation are also tested.

## D6 — Randomize stencil region

**Choice.** Draw one of top, bottom, left, right, or interior, then choose a
legal placement in that region.

**Rationale.** The baseline always painted the stencil at row 0, while canonical
examples include non-top placements. Region-first sampling makes the support
explicit rather than hoping uniform coordinates happen to cover every class.

**Alternatives rejected.** A uniform top-left coordinate would cover interior
and edges but weakly sample complete bottom/right contact. An `anchor_corner`
boolean was rejected because it had been inert and collapses several distinct
placement regimes into an unclear flag.

**Probe.** The retained 256-draw test observes all five region classes and more
than 40 distinct normalized locations.

## D7 — Dense canonical palette

**Choice.** Fill background from weighted 0/2/4/7 noise, then paint stencil,
copies, isolated 3 distractors, and explicitly pin 0/2/4/7 outside semantic
objects.

**Rationale.** This preserves the canonical high-noise visual regime while
keeping color 8 unambiguous and color-3 distractors controlled. `self_check`
requires the full palette and at least 60% nonzero density.

**Alternatives rejected.** Clean sparse demonstrations would be easier but
would not match canonical complexity. Allowing background 8 would create
multiple stencil components. Uncontrolled background 3 would undermine exact
copy observability.

## D8 — Semantic admission, not count-only admission

**Choice.** `self_check` validates structure and runs an independent geometry
implementation to require a nonidentity output consisting only of 3→8 changes.

**Rationale.** The baseline admitted a dense, palette-preserving mutant with no
matching copy and identity output. Counts alone do not establish the task law.

**Alternatives considered.** Requiring only a generated-shape component would
be faster but would reject lawful canonical variants and would not check actual
rule firing. The current semantic check accepts all canonical inputs while
remaining independent of Racket execution.

## D9 — Three demonstrations and explicit rival contract

**Choice.** Declare `EXAMPLES_NEEDED = 3`, a `reflection_required` witness, the
`rotations_only` rival, and a `lesson_identifiable` hook. Require arbitrary query
rotations in final diagnostics.

**Rationale.** Rotations-only fits all four canonical training pairs but fails
the labeled canonical test pair. Every generated grid independently contains a
reflection witness, while three demonstrations offer redundancy against other
surface guesses. The hook checks the actual assembled lesson rather than
assuming correct individual labels imply teachability.

**Measured policy.** The wide census used three demos plus one query: 300/300
production lessons and all 1,200 query rotations had no declared-rival ambiguity.
This is finite evidence against the declared rival only.

## D10 — Retained authoring tools and portable tests

**Choice.** Keep `reference_probe.py` as an independent oracle and add
`shortcut_probe.py` for declaration-aware canonical, generated, lesson-window,
query-rotation, and optional Racket checks. Use `reviewer_support.find_root`,
`canonical_path`, and `canonical_pairs` rather than fixed parent depth.

**Rationale.** Future agents need a replayable way to detect the exact shortcut
and to run from copied task-test runtimes. A regression first reproduced the
fixed-`parents[3]` portability problem, then verified the portable helper.

## D11 — Proposed episode-level symmetry and overlap-order parameters

**Choice.** Keep production version `3.0.0` and the selected Racket authority
unchanged. Add a task-local prototype under `workspace/parametric/` with two
episode-fixed parameters: `reflection_mode` (`dihedral` canonical or
`rotations_only`) and `column_order` (`left_to_right` canonical or
`right_to_left`). The default program is byte-for-byte the canonical Racket text.

**Rationale.** Reflection inclusion is the existing strongest canonical shortcut,
while same-row column order is the unresolved source-bound teaching gap. Both
parameters preserve the stencil role, geometric matching, greedy non-overlap, and
3→8 recoloring. Each prototype input starts from a selected-generator draw and
adds one isolated 2×4 color-3 overlap motif; the ordinary generator remains
untouched and continues to emit isolated copies only.

**Teaching evidence.** Each of the four settings has one retained episode with
three demonstrations and four distinct queries. Every individual input has four
distinct setting outputs, so demonstrations reject all three alternate settings
before query answers are considered. The retained verifier executed all 28 stored
labels and 84 rival labels in matching Racket, plus 48 query/rival checks, and
replayed all five canonical labels under the exact default program
(`checks/parametric/195dfcc5b541-symmetry-order-v1-report.json`).

**Adversarial evidence.** A bounded 32-seed × four-setting sweep produced 128
episodes and 256 pairs with no construction failures; the worst accepted search
attempt was 9/512. A 16-demo/16-query boundary episode contained 32 distinct
inputs. A second Racket seed base passed, and public IDs were invariant to private
metadata and query answers but changed with a visible demonstration output
(`checks/parametric/195dfcc5b541-symmetry-order-adversarial.json`).

**Limit.** This is a proposed prototype, not a production repair or approval. It
does not close the historical overlap-order audit for ordinary generation, prove
identifiability against rules outside the four declared settings, or admit any
variant to training.

## Failed and intermediate iterations retained

1. The requested baseline battery was interrupted after lint, self-check, and
   rule-smoke evidence; it is reported as partial, not a completed baseline.
2. The first full repaired battery was 10/12: `defect_lint` and `authority_sync`
   both found selected-vs-canonical active text divergence. That led to the
   allowed selected `target_code` synchronization; no semantic rule edit was
   made.
3. An early exhaustive override run progressed without findings but exceeded
   the foreground tool window because generation repeatedly solved its own
   grids. Constructive generation and structural observation removed that cost;
   the final full override stage passes.

## Remaining limitations

- The sampler covers two chiral stencil families, not arbitrary lawful shapes.
- Production copies remain intentionally isolated; overlap-order teaching exists only in the proposed task-local prototype.
- The census and shortcut probe refute declared rivals over finite sampled
  lessons; they do not prove unique induction against all possible rules.
- The archival base-solution `raw_code` is still textually divergent by design;
  final authority sync explicitly classifies it as archival, not selected.
