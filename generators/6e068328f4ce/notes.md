# Component Center Markers — current decisions

## Authority and domain

Version 2.0.1 preserves canonical Racket rule `c3726fc6c507`. For every
four-connected component of one nonzero color, write that color at the inclusive
bounding-box midpoint `((r_min+r_max)//2, (c_min+c_max)//2)` on a zero-filled grid
of the original shape. Separate components may share colors; diagonal contact
does not merge them. A midpoint can be an input background cell. The fixed zero
background follows the rule and is not an interchangeable palette role.

The Racket rule is broader than this sampler. It permits singleton components
and overlapping bounding boxes. If two centers coincide, the later component
in row-major discovery order overwrites the earlier marker. These boundary
semantics are retained in `counterexamples/component_centers.json`, with live
Racket evidence, but are outside the helpful production distribution.

## Repair rationale

Prior choice: capped blob placement, a different color for every blob, and a
validator that counted cells per color. This never distinguished one bbox per
color from one bbox per component; diagonal connectivity was likewise untested.
Several advertised controls were unused, the easy/hard branches ignored
`n_blobs`, and degenerate metadata bypassed validation. The supposed shared-center
fixture actually had centers (1,1) and (5,5).

Current choice: constructive disjoint slots with exact counts, independent
component validation, and an alternating teaching schedule. Two same-color
elbows touch only diagonally. Their asymmetric even-width bboxes have empty
midpoints, separating component identity, connectivity, rounding, centroids,
and existing-cell-only hypotheses. Layout construction has no capped retry or
silent-short-batch path. All nonzero palette values remain available.

## Honest controls

| Control | Accepted integer range | Observable meaning |
| --- | --- | --- |
| `grid_h`, `grid_w` | 7..16 each | Returned grid dimensions |
| `n_blobs` | 2..5 | Four-connected same-color component count |
| `n_distinct_colors` | 1..5, at most `n_blobs` | Foreground palette cardinality |

An explicit color count increases an unspecified component count when needed.
An explicit impossible count pair raises a structured incompatibility. Booleans,
floats and strings are rejected; `None` means use the default. `sample_index`
must be a nonnegative integer. Defaults and overrides both retain keyed-draw
provenance, and `observe_overrides` recovers these four controls from pixels.

The unused or duplicate legacy controls `palette_kind`, `palette_size`,
`position_bias`, `density`, and `texture` are retired and now raise an explicit
unsupported-control error. Callers wanting palette cardinality must use
`n_distinct_colors`. The former metadata-only degenerates no longer bypass checks.

## Production lessons and support

The declared semantic schedule has period two in `sample_index`, in every band.
Even indices draw two distinct-colored 3x3 filled rectangles on a randomly
selected canonical-size profile: 9x9, 9x11, 10x10 or 11x11. Odd indices draw
3..5 components, including a repeated-color diagonal elbow pair. In default
draws its pre-transpose height varies from 3 up to the available slot height
(at most 6); width is an even 4, 6 or 8 when the canvas fits it. Optional extra
components are rectangles, bars, frames or elbows. Translation, reflection,
transposition, palette, counts and sizes vary through keyed RNG draws.

`EXAMPLES_NEEDED = 3`. Every three consecutive default draws include a rich
witness; every four consecutive default draws contain two. Therefore a
three-demo/one-query episode has a witness after any one-pair query holdout,
provided the accepted schedule stays consecutive. The source-bound census and
fixed-seed schedule enumeration exercise actual accepted indices, rejections,
and rotations. Finite checks cover only the six declared rivals, not all
possible inductive rules or all seeds.

Exact overrides can intentionally remove teaching witnesses, for example
`n_distinct_colors == n_blobs`, or a narrow canvas requiring smaller elbows.
The full rival-refutation claim is for ordinary defaults; constrained lessons
need their own identifiability check. Smaller grids remain lawful exact draws.

## Limits and reusable checks

Generated bboxes are disjoint, every component has at least two cells, and the
shape family is bounded. Nested/interleaved components, coincident centers,
singletons, and orthogonal contact between different-colored components are
not sampled. The canonical and rich profiles remain structured curricula;
the repair does not establish coverage of all connected polyominoes or prove
model learning. These are explicit distribution limits, not authority changes.

`tests/test_component_centers.py` uses portable canonical helpers and independent
component/center calculations. `workspace/probe_component_support.py` retains
independent boundary geometry, exact draw provenance and no-mutation checks.
The packet's before, intermediate, final, lesson and fresh-replay receipts
distinguish measured source hashes. No current review-index or prior associated
notes were supplied; this repair does not resolve unrelated audit findings.
## Current reviewer considerations

Source SHA-256: `96cbe5e3a78eb4ceed303e8cb6d73f2240024d473d3ab39aed6a8b353fc37f99`.

# Decisions for 6e068328f4ce

## Context and authority

The pinned baseline is v1.1.1, SHA-256 `fefed50051fb506105704bf728ab02125a6ff4f7cd19302f3f2a75636cb101cf`. No current task review index or substantive associated notes were supplied, so historical design intent beyond the generator/docstring is unknown. I used the supplied source and live checks as evidence; an older claimed repair was not substituted for the pinned draw.

Canonical Racket rule `c3726fc6c507` and all canonical examples remain unchanged. Its exact callable text SHA-256 is `a24c9744e603105be2b2dd4ee01822c4c5a193b7e158670a0412c779b783acca`. Python component and center calculations in tests and rival hooks are independent diagnostics. They never replace Racket as the label authority.

## Input and curriculum choices

| Choice | Prior state and rationale | Current choice and reason | Alternatives, failure modes and limits |
| --- | --- | --- | --- |
| Background and colors | Fixed zero background; original broader rationale unknown. | Preserve zero and all nonzero values 1..9 because color 0 is fixed by the canonical rule. | A random nonzero background would require different authority semantics. Palette relabeling only permutes nonzero colors. |
| Object identity (G1) | Each blob got a unique color. This made grouping by color observationally sufficient. | Reuse colors across distinct four-connected components; rich draws include same-color diagonal contact. | Unique-color-only data or recoloring after placement does not teach component identity. Some exact overrides intentionally request unique colors. |
| Shape family and center | Blob rectangles/Ls supplied weak or uneven distinguishing evidence. | Alternate familiar 3×3 rectangles with asymmetric elbows whose even-width boxes and empty midpoints refute six plausible rivals; extra shapes include bars, rectangles, frames and elbows. | Unbounded random walks create difficult-to-control counts and unclear support. The selected family is still narrow and does not cover all polyominoes. |
| Placement (G2) | Capped placement/retry logic could miss intended support. | Use constructive disjoint slots, then translation, reflection and transposition. No capped placement loop silently drops a component. | Raising minimum dimensions to avoid all hard combinations would hide a control problem. Disjoint boxes exclude nesting, interleaving and center collisions from production. |
| Dimensions | Multiple controls/branches were inconsistent. | Exact integer height and width in 7..16; preserve requested orientation after transposition. Core defaults select canonical-size profiles; rich defaults allow larger shapes. | Scalar booleans, floats and strings must fail. Increasing the range without a new support proof would invalidate slot assumptions. |
| Component/color counts | Difficulty branches could ignore n_blobs; palette controls were partly inert or duplicate. | Exactly 2..5 components and 1..5 foreground colors, with colors no greater than components. A requested color count can raise an unspecified component count. | A genuinely impossible explicit color/count pair raises structured incompatibility. Silently clipping either control is rejected. |
| Public controls (G2) | palette_kind, palette_size, position_bias, density and texture did not provide reliable independent exact behavior. | Retire these keys with explicit errors; keep grid_h, grid_w, n_blobs and n_distinct_colors with pixel observations and keyed draw provenance. | Accepting unused keys would perpetuate false controllability. This is a versioned API change; use n_distinct_colors for palette cardinality. |
| Difficulty | Branch-specific behavior overrode requested counts. | Bands influence ordinary default size/count draws, while exact controls retain priority. | No claim that these bands establish human or model difficulty. Their actual profile support is measured by the battery. |
| Teaching schedule (G1) | No executable teaching contract; canonical-compatible shortcuts could survive the entire sampled family. | Period two: even core rectangle draws, odd component witnesses. Three demonstrations and one query give two rich pairs in a consecutive four-pair default window. | Independent random witness frequency does not ensure a complete lesson teaches the distinction. The guarantee is conditional on consecutive accepted default indices; census receipts check actual materialization and rotations. |
| Validation (G3) | Counts by color hid singleton components; degenerate metadata bypassed checks. | Validate rectangular integer grids, range, component count and minimum two cells per component; metadata cannot exempt an invalid grid. | The validator remains broader than the sampler in some dimensions/shapes, supporting canonical and diagnostic inputs without claiming they are generated. |
| Boundary semantics (G4) | A purported shared-center fixture actually had different centers. | Retain six small live-rule witnesses, including repeated colors, diagonal contact, rounding, empty centers, different-color contact and nested center overwrite. | Canonical singleton/collision behavior is documented and tested as authority behavior, not advertised as production coverage. |

## Iteration evidence and rejected fixes

The original 45-case regression run had 36 failures and 9 passes without changing the generator. The first repair fixed the intended control and component behavior, and its census passed. Its full battery still caught accepted Boolean/negative sample indices and a linter warning on the local Python identifier `objects`. The final repair rejects invalid indices and renames that local variable to `components`; the latter is a diagnostic false-positive workaround, not a semantic change.

Primary elbow size was then broadened. An initial test asking for any large elbow already passed because an extra component could satisfy it; that run is retained and is not called a failing regression. The stronger test required two large same-colored elbows, failed in all four difficulty settings on the intermediate implementation, and passed after the primary pair's dimensions were expanded. The current 54 tests cover the resulting behavior. All intermediate source/test receipts remain separate from final-source measurements.

I rejected altering the Racket rule to fit the sampler, using Python-generated labels, metadata-only witness assertions, weakening exact controls, and manufacturing failed solve attempts. The evidence supports changing the distribution and validation while preserving authority.

## Reusable tools built

The task-owned `workspace/probe_component_support.py` uses public `reviewer_support.find_root(__file__)` and independent traversal. It discovers the actual declared rivals, fails on unknown/missing supported rival implementations, checks 2,240 joint-control cases and 64 rich defaults, and writes a fresh source-bound report. From WORK:

```bash
PYTHONPATH=repo/shared/runtime python3 -B repo/generators/6e068328f4ce/workspace/probe_component_support.py --out checks/new-support-report.json
```

The optional general policy prototype in `checks/teaching-gate-prototype/` consumes existing source-bound census reports. It makes missing contracts and unrefuted canonical-compatible rivals visible as gate failures, rather than silently treating query agreement as sufficient teaching. It is kept outside the selected task delta, with baseline/final demonstrations and explicit limitations; installing it in shared export/admission code is a separate maintainer decision.

The offline helper `checks/runtime-bootstrap/bootstrap_from_installed.py` reconstructs wheels from already installed distribution bytes, records their hashes, and installs them into an independent local venv. It resolved a real user-site-only pytest prerequisite failure while preserving the task runner's isolation. Dependencies used were Python 3.12.14, pytest 9.1.1, NumPy 2.3.5, Pillow 12.3.0, iniconfig 2.3.1, pluggy 1.6.0, Pygments 2.21.0 and packaging 26.3; bootstrap itself also requires the installed wheel package. The receipt records executable paths and copies. No installed environment or dependency tree is included in the return.

Both complete census JSON files are retained as deterministic gzip members with exact original-byte manifests and a tested restoration utility. This keeps the return small without replacing full evidence with summaries or discarding failures.

## Scope and unresolved work

Audit targets are findings only. In 69b886e1df03, a valid small packing disproves the generator's incompatibility assertion; repair should use a constructive fallback or accurately distinguish exhausted search from impossible controls. Its distant same-color placement also leaves eight-connectivity untested in the 180 draws checked. Neither audit modifies production source.

Four broad repository-test failures reproduce on the pristine original packet and remain outside the selected task scope. The full failure receipts are retained rather than rewriting unrelated tests. The task repair's final battery, portable tests and finite teaching evidence pass independently.

Future expansion of this task should address nested/interleaved components, singleton and center-collision support, and constrained-override lesson assembly only when those distributions are intentionally required. Each would need its own teaching/geometry checks. Current finite rival refutation is not evidence of universal induction or measured training improvement.
