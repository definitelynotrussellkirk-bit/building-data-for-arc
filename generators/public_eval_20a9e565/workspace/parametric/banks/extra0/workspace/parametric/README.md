# Additive growth and a future crop

This is a reviewer-authored native **prototype** for public parent `20a9e565`.
The canonical Racket program is byte-identical to the task's `reference.rkt`.
Registration, owner qualification, exact-source acceptance and any training
admission are separate owner actions.

## Rule and setting

The input contains a spatial sequence of increasingly large objects and two
opposite gray L corners. The corners specify an inclusive crop of a future
member, sometimes after a skipped member and sometimes showing only part of it.

The Racket program derives one common rule from the visible sequence. It aligns
the leading edges, learns a complete palette permutation from all overlapping
cells, and undoes that permutation at each observed step. Consecutive normalized
supports differ by added components. Their geometry/translation periods and
their color periods are inferred separately. The program continues those
tracks, places each future object using the observed gap, locates the requested
member, advances its palette phase, and returns the crop.

| Private episode setting | Executed behavior |
| --- | --- |
| `{"output_part":"whole"}` | Return the entire reconstructed target within the crop; exact canonical default. |
| `{"output_part":"new_shell"}` | Return only coordinate support added at that target step, with its correct colors. Inherited cells whose displayed colors change remain background. |

The setting is fixed throughout an episode. Inputs are identical across the two
settings for the same seed. The first two demonstrations include a layered
object with differently colored new components and a recoloring wave with a
skipped member. They distinguish the settings and the principal tested
shortcuts before any query is answered.

## API and resource boundary

`program(settings)` returns complete standalone `(rule! ...)` Racket source.
`generate(seed, settings, demos=3, queries=4)` supports exact integer seeds in
`0..2**63-1`, 2–6 demonstrations, and 1–4 queries. Booleans and unknown fields
are rejected. The complete six-demonstration and four-query banks are built
before either requested prefix is selected. A seed-specific private shuffle
orders the whole query bank before selection, preserving first-turn content
when evaluation stops early. Each public view contains exactly one query.

All native resources stay inside this directory. `prototype.py` contains the
self-contained constructive sampler; its corresponding ordinary sampler is
kept in `generator.py` because ordinary and native stages have separate resource
closures. Focused tests compare complete inputs. The sampler constructs known
future coordinates directly rather than obtaining its expected labels from the
inference program. Protected Racket execution checks those expected labels.

The ordinary generator exposes `shape_family` and `sequence_axis` overrides.
It returns only input grids; the reference runtime supplies ordinary labels.
The five constructive grammars vary stems and bars, ladders, layered lobes,
periodic waves, and nested arches. Dimensions, increments, gaps, colors, crop
windows, placement and D4 orientation vary within the declared grammar.
The native bank separates demonstration/query domains structurally, and the
last query exercises a substantive 30×30 layered or ladder sequence.

## Sequential dependency

**A:** Infer the palette permutation and component tracks, reconstruct future
object spans, and use the marked window to determine the requested target index.
Its intermediate contains that index, actual spatial intervals, learned periods
and the palette permutation.

**B:** Consume that intermediate to reconstruct the selected future support,
select its new coordinates when requested, recolor to its phase, and crop it.
Replacing A's target by the immediate successor changes the result on an
executed skipped-member example. The protected witness and replay live under
`checks/public_eval_20a9e565/causal/` in the return.

## Reproduce from the returned packet checkout

From the outer extraction directory, after applying the return patch:

```sh
WORK/.venv/bin/python review.py task-tests public_eval_20a9e565 \
  --phase after --timeout 180 --out ../checks/public_eval_20a9e565/fresh-tests

WORK/.venv/bin/python review.py run python3 \
  -m arcpuzzles.review_public_creation preflight public_eval_20a9e565 \
  --root . --out ../checks/public_eval_20a9e565/fresh-preflight
```

Use fresh output paths. The current packet's bundled offline Racket and Python
environment are required; no sibling checkout or environment is used. The
ordinary task tests stage an unregistered family, so their root comes from the
actual staged task path rather than a canonical-ledger lookup.

## Explicit domain and evidence limits

- Background is 0 and crop metadata is 5. Either opposite-corner orientation is
  supported. The output includes the marker extrema, replacing marker cells.
- The reference requires exactly one mass-monotone projection before learning
  the recurrence and aligns the leading edge along the sequence direction.
  These constraints hold for the authored sampler; the independent oracle can
  try both edge anchors and recurrence-filtered axis candidates.
- At least three complete objects, a constant positive gap, additive aligned
  support, a completely identified palette bijection, and stable component
  correspondence are required. Added components use four-neighbor connectivity.
- Every geometry period must actually repeat in the observations with one
  constant displacement. Color continuation uses the least compatible period.
  Monochrome component geometry may vary periodically; multicolor components
  require fixed geometry. These are declared sequence assumptions, not a proof
  that arbitrary future patterns have a unique continuation.
- The crop must fall within one future object's interval along the sequence
  axis. It may clip the perpendicular extent. Unshown target support can extend
  beyond the canvas; only the in-canvas marked crop is returned.
- Finite rival checks cover named alternatives and recorded seeds. They do not
  prove universal learnability, all-seed correctness, or owner acceptance.

See the task's `notes.md`, current source inventory and returned evidence for
the actual checks and resolved findings.
