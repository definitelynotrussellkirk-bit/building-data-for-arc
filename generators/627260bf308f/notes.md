# Review notes — review-0867d19380f40c97

The imported v2.0.1 source had no task-specific explanatory evidence. It sampled
larger grids only, exposed ignored axes, and lacked a RULE_HASH/semantic contract.
The before battery reproduced lint, defect-lint, override and profile problems.

The strongest teaching counterexample is baseline seed 0, easy, indices 7–10:
a bounding-box-area ranker agrees with all three demonstrations and disagrees
with the actual Racket query output at 13 cells. All seven retained rivals fit
the three canonical pairs, so canonical agreement alone is insufficient.

The v3 repair alternates witness and broad draws. A four-cell square is above
a three-cell L with the same bounding-box dimensions and diagonal contact;
an additional singleton and a nonmonotone header refute remaining shortcuts.
Shapes are placed atomically, with a constructive fallback rather than omission.
Broad draws use varied connected polyominoes, including sizes through 14.

The targeted regression suite passed 82 tests before handoff. Baseline failures
and subsequent checks are in the small returned evidence archive, not duplicated
under this task home. The immutable canonical rule and all audit targets were
left unchanged. No empirical downstream Qwen training gain is asserted.
## Current reviewer considerations

Source SHA-256: `07ee110e1e46147138b48c2cac3c544ef628cb595a53bc5eb5955fcb58c89b1f`.

# Decisions and rejected alternatives

Task `627260bf308f`, v3.0.0, final source
`07ee110e1e46147138b48c2cac3c544ef628cb595a53bc5eb5955fcb58c89b1f`.

## G1 — Make the control contract truthful

The imported rationale is largely unknown: task notes contained no explanatory
evidence. The old implementation already aimed for irregular components rather
than a fixed rectangle, but advertised axes did not match its actual behavior.
The before battery measures 16,170 findings, two warnings and 38,040 explicit
rejections across 95,760 planned override draws. Those raw categories are not
all distinct bugs; see the report's grouped root causes rather than summing them
as independent defects.

Keep four observable axes: grid height, grid width, component count and palette
order. Their domains are global, independent of difficulty. Difficulty weights
default counts only; it no longer makes otherwise legal overrides fail. Remove
`palette_size`, `palette_kind`, `n_distinct_colors`, `density`, `texture` and
`position_bias`, because their old advertised promises were not implemented.
Unknown/retired controls now raise ValueError. This deliberate v3 API change is
preferable to silently accepting a parameter with no measurable meaning. Existing
callers passing retired controls must remove them or use `n_components` for the
actual count; no truthful alias mapping is invented for unrelated controls.

Boolean, string and floating-point values are not accepted as exact integer
controls. The current controls can be recovered from returned pixels, so tests
check output observations rather than trusting metadata. After repair the
shared override battery accepts all 14,940 positive draws without findings;
the local full Cartesian probe adds 12,240 joint combinations at seed 867.

## G1 — Restore canonical-scale support without collapsing variety

Restricting every draw to the two canonical footprints would overfit canvas
size. Keeping only large grids would retain the observed zero-support defect.
Choose a deterministic even/odd mixture: even draws use canonical-sized witness
profiles by default, odd draws use the full legal canvas range. Explicit shape
controls override either default without invalidating the component layout.
Measured canonical-profile support is 34/60, with nonzero support in every band;
this finite check is not a claimed asymptotic probability.

The palette contains 2..5 distinct colors from {1,2,3,4,5,6,7,9}; 0 is background
and 8 is the placeholder. The chosen order is independently sampled, with even
witnesses nonascending by default. If shuffling accidentally returns ascending
order, swap two colors so the exact `unsorted` contract remains true.

## G2 — Construct complete lawful inputs

The original best-effort placement could structurally exhaust its attempts
without stamping an intended component; no measured missing-component rate is
claimed here. A larger retry limit alone would not establish a complete layout.
Instead, reserve a provably feasible layout, try bounded randomized placements,
and discard the entire tentative grid on any failure. The fallback is stamped
only if every component fits. Forced-collision tests exercise both fallback
families with five components on the minimum canvas.

Four-neighbor separation is intentional; eight-neighbor exclusion hid the
difference between two connectivity rules. Diagonally touching components are
allowed. Body shapes vary in pixel count and geometry; `_grow` constructs a
connected shape of the requested size inside a finite rectangle, without
truncating it. Distinct feasible sizes are reserved before drawing, preventing
late-object starvation on a small canvas. Broad sizes can reach 14; the size
cap is a documented sampler choice, not a canonical rule restriction.

The validator checks rectangular integer-color grids, distinct header entries,
a blank separator, lawful body colors, exact header/component cardinality and
distinct component sizes. Canonical ties have a reference-defined order, but
this sampler deliberately excludes ties so no hidden tie convention must be
inferred. `strict_canonical_like` means lawful within this task's chosen domain,
not identical appearance or distribution to the few canonical examples.

## G3 — Teach the distinction, not merely produce correct labels

All seven executable rivals agree with all three canonical pairs. Unstructured
random draws sometimes leave a wrong rule viable throughout the demonstrations.
Baseline easy seed 0, demos at indices 7–9 and query 10, reproduces that failure
for bounding-box-area rank: three matches followed by a 13-cell disagreement
with actual Racket. The independent local probe finds 135/768 such ambiguous
normal-query windows in aggregate, not necessarily for this one rival alone.

One witness-only position per four-pair block would become a blind spot when
that position is held out as query. Instead place witnesses at **every even
index**, each of which independently refutes all seven rivals under default
controls. Every consecutive four-pair window has two even positions; holding
out any one pair leaves at least one witness among the other three. No rejecting
sampler draws are needed for the constructive inputs. Tests enumerate overlapping
windows and the actual Racket-backed census tests the production sampler.

The core contrast is a square of size four spatially above an L of size three;
they share box area, height and width but have the opposite intended rank. They
touch diagonally, exposing eight-connectivity as wrong. A singleton gives a
nonconsecutive size set [1,3,4], exposing absolute-size indexing. A nonmonotone
palette exposes numeric sorting. Horizontal reflection, L orientation, header
positions/colors and whole-group translation vary.

An all-witness generator would introduce a new template shortcut. The broad
half varies shapes/counts/sizes, so the implementation is not confined to those
three silhouettes. Nevertheless this mixture is deliberately structured; no
finite rival list proves arbitrary induction. The guarantee is for default
three-demo/one-query consecutive windows and single-query rotations, not fewer
demonstrations, arbitrary shuffled grouping, or all possible multi-query splits.
Overrides can disable individual witnesses; a rival that agrees on both demos
and query is not query ambiguity. The pipeline should check its actual assembly.

## T1 — Build reusable tests without replacing label authority

Use a separate independent Python component-rank calculation for fast
counterexample searches. It matches all supplied canonical pairs; a retained
baseline lesson is independently checked with actual Racket. The production
census and strict semantic run supply Racket-backed results, so the fast probe
is never presented as a second reference authority. The probe reads current
rival declarations and stores both generator and rival-source hashes.

The 1,056 final-source grid examinations contain 443 unique inputs because the
same seed/index is deliberately replayed in each band. This is a real diversity
limitation of seed reuse, not 1,056 independent samples. Use disjoint seed streams
or deduplicate downstream. The separately seeded production census has 1,200
unique inputs. No attempt was made to inflate these denominators or count
namespaced aliases as independent rival theories.

## Scope and workflow

No shared source, canonical ledger, active/archival Racket mirror, audit source
or frozen fixture was changed. Only the assigned task's generator, tests and
authoring notes/tooling are patched. Root pytest (362 tests) and the explicit
portable task-test stage (82 tests) are separate successful runs. The latter
uses `reviewer_support.find_root` and `canonical_pairs`, not fixed source-depth
assumptions. Both genuine solve attempts and exposure declarations are preserved.
The small reconciliation harness initially looked for a nested JSON key at the
wrong level; the retained failed log is a tooling error, corrected without
changing the generator or authority.

The first exact-delta replay applied correctly but a reviewer-only provenance
assertion assumed one generator entry per runtime manifest. The portable test
runtime has two identical mapped views. The corrected checker requires a
nonempty set of entries all equal to the final hash, rather than requiring a
one-element list. A second fresh extraction repeats Git-root verification,
patch check/apply and all 82 portable tests successfully. Both helper versions
and actual outcomes remain in `checks/handoff/` and `checks/handoff-final/`.

## 2026-10-25 — native rank-to-remote-payload family

The ordinary generator and canonical authority were rechecked and left unchanged.
The native family now uses `finish_mode=rank_only|rank_relay`; `rank_only` is the
exact selected canonical Racket source. In `rank_relay`, stage A performs the
canonical occupied-size rank recoloring, the input-dependent intermediate is the
palette color assigned to the first component hit by a color-9 selector ray, and
stage B uses that color to choose a matching remote bottom-row swatch and paint
its reserved vertical corridor color 9.

The sampler supplies matched inputs across settings, independent prefix-stable
2–6 demonstration and 1–4 query streams, and a substantive 30×30 fourth query.
Two demonstrations distinguish both settings and reject the declared reverse
rank, fixed-swatch, endpoint-size, and marker-column shortcuts. The retained
bounded audit covers seeds 0 and 17, 12 count/setting episodes, 40 protected
Racket labels, and two skip-A counterfactuals. The packet-native authoring
preflight passed four jobs and 32 protected-Racket evaluations; the replayable
witness proves that skipping rank recoloring changes the payload result. Public
projection produced 16 one-query views and passed 24 private-field invariance
checks plus four positive controls.

Status is reviewer-ready only. Exact-source owner review, native qualification,
acceptance, and any training admission remain separate downstream gates.
