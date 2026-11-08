# Native diagonal rays and one boundary bounce — `9ce2dcf587b8`

The native adapter exposes one episode-fixed parameter:

| `ray_rule` | Executed behavior |
|---|---|
| `both` (canonical default) | Original markers emit both diagonal axes; exact selected canonical text. |
| `main_only` | The retained prototype's NW–SE axis, with original markers preserved. |
| `one_bounce` | Paint main-axis rays, compute their boundary endpoints, then paint anti-axis continuations once from those frozen endpoints. |

`native_family.py` reuses `prototype.py` for both existing direction settings.
The prototype now reads the adjacent exact `canonical.rkt`, copied through the
public Catalog API. The production generator and its reference rule stay separate.

## Dependency and input grammar

For `one_bounce`, **A** traces each original marker to its two main-diagonal
boundary endpoints. The **intermediate** is this input-dependent endpoint set
and the main-ray grid. **B** paints anti-diagonal continuations from the endpoints
onto that grid. Replacing endpoints with original source positions gives a
different result. Endpoints are frozen: painted pixels never become new emitters,
and the continuation never bounces again. At a corner there is no inward
anti-diagonal continuation. This is a derived geometric dependency, not a claim
of an iterative simulation or recursive reflection.

The shared native grammar is 7–30 rows and columns, background zero, and one to
ten interior markers of one color in 1–9. Markers are separated by Chebyshev
distance at least three and never share a diagonal. This extends the unchanged
production sampler's 7–17 dimensions and one-to-three-marker domain. There are
no advertised production dimension or count overrides for the extension.

## Sampling and teaching

`generate(seed, settings=None, demos=3, queries=4)` supports exact integer seeds
0 through 2**63−1, independently 2–6 demonstrations and 1–4 queries. The native
contract uses six demonstrations for qualification, covering the entire bank;
ordinary calls remain at three. Ten inputs are constructed before slicing,
using separate deterministic input and setting streams. No rejection loop runs.
Changing settings or counts preserves the input bank and relevant prefixes.

Two core demonstrations contain two and five markers with colors that refute
the retained color-quota shortcut. They have off-center geometry and multiple
active boundary continuations. The second core has an interior marker in both
a row and a column, repairing the observed extrema-only source shortcut without
increasing the two-demo minimum. Remaining profiles include a corner-inactive
7×7 query, rectangles through 24×29/29×24, and 30×30 inputs with eight or ten
markers spread across the canvas. Large outputs contain long rays in all four
quadrants. Diversity comes from these ten templates, allowable translations,
colors, and the four symmetries preserving the main axis: identity, rotation
180°, transpose, and anti-diagonal reflection. Arbitrary rotations, general
random layouts, all legal dimensions, and global cross-seed uniqueness are not
claimed. Horizontal or vertical reflection alone would exchange the axes.

`audit_native.py` independently checks geometric labels and a finite set of
plausible wrong rules using only demonstrations to select survivors. Query
disagreement of a survivor is a teaching failure; a rejected program is not a
valid semantic refutation. Reports retain actual protected Racket evidence.

## Run and consume the result

From the outer packet folder, with its selected Python environment:

```bash
python3 review.py run python3 -m pytest generators/9ce2dcf587b8/tests/test_native_family.py generators/9ce2dcf587b8/tests/test_native_audit.py
python3 review.py run python3 -m arcpuzzles parametric qualify 9ce2dcf587b8 --demos 6 --queries 4 --out ../checks/9ce2dcf587b8/qualification-new --summary
python3 review.py preview-public export --qualification ../checks/9ce2dcf587b8/qualification-new/qualification.json --out ../checks/9ce2dcf587b8/preview-new
python3 review.py preview-public verify --bundle ../checks/9ce2dcf587b8/preview-new
```

Use fresh output paths. Native qualification and its sibling execution receipt,
sampler and teaching checks, and causal witness/replay live under
`checks/9ce2dcf587b8/`. Each preview `public/<sha256>.json` contains the same
demonstrations and exactly one query input. Give only that selected file to the
model; keep directory inventories, all other queries, and `private/` controller-side.
The first turn is identical to single-query evaluation. No turn controller or
training loop is added. Owner qualification and acceptance of exact integrated
source remain separate; neither this prototype nor preview admits training.

## Retained earlier prototype

The following describes the earlier three-demo/one-query authoring prototype,
not the native API above. Its public examples and old receipts are historical;
use the qualified one-query previews for current model inputs. Running its old
writer changes source-bound resources and requires a fresh native qualification.

This task-local prototype does **not** alter the production generator or its
selected canonical Racket authority. It evaluates one bounded episode-level
rule parameter:

| Parameter | Allowed values | Original/default |
|---|---|---|
| `diagonal_axes` | `both`, `main_only` | `both` |

`both` is the exact canonical program: each interior marker emits same-color
rays in all four diagonal directions. `main_only` retains the marker role,
source preservation, ray extent, collision behavior, and colors, but emits only
along the NW–SE axis. The alternate Racket text is derived from the canonical
program by replacing its one `diagonal-deltas` occurrence with the literal
`'((-1 -1) (1 1))` direction list.

The setting is selected once from the episode seed and reused for all three
labeled demonstrations and the unlabeled query. Every retained input contains
one interior marker, so every demonstration distinguishes the two settings and
the query answer also depends on the setting. Public challenge files omit the
hidden setting, Racket source, and query answer.

From the outer packet extraction directory, run:

```bash
python3 review.py run python3 \
  generators/9ce2dcf587b8/workspace/parametric/verify.py \
  --out ../checks/parametric/verification.json
```

The verifier executes both exact programs with the bundled Racket bridge,
compares every result against an independent Python mirror, proves the default
text and normalized hash remain canonical, checks demonstration/query
separation, writes opaque public challenges, and records program/source hashes
and full bounded evidence.

Limitations: only the declared two settings and retained seeds are tested. This
is a **proposed prototype**, not production integration, catalog approval, or a
claim about arbitrary rule parameters.
