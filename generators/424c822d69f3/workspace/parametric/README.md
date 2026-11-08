# Native rectangle-anchor parametric family

**Status:** reviewer-ready prototype only. The production generator, selected
canonical rule, catalog approval, and training admission are unchanged. Exact-source
owner qualification and acceptance remain separate required steps.

## Active native contract

`adapter.py` promotes the reviewed `bbox_anchor/` implementation through the native
parametric interface. Every episode fixes exactly one private `anchor` setting:

| `anchor` | Horizontal point used before nearest-marker selection |
| --- | --- |
| `midpoint` | `(left + right) // 2`; byte-for-byte canonical default |
| `left_edge` | rectangle's left bounding-box column |
| `right_edge` | rectangle's right bounding-box column |

The input is still the source task: read the colored row-0 markers, find each solid
color-5 rectangle, compute its setting-selected horizontal anchor, choose the unique
nearest marker, and recolor the full rectangle. The domain rejects an exact tie under
**any** declared anchor, so all three programs are total on every admitted input.

The public API supports 2–6 demonstrations and exactly four distinct queries. Inputs
are matched across settings for a fixed seed/count request. Every demonstration set
contains both left-edge and right-edge witnesses, so fitting the three actual Racket
programs to demonstrations alone leaves only the requested setting. Query answers are
not used during setting identification.

Each episode reserves one substantive 30×30 query with six rectangles, 218 color-5
cells, left/right/bottom boundary contact, and an anchor-sensitive label. The other
inputs come from the approved constructive generator.

## Sequential dependency

Step A extracts each rectangle's bounding box and computes the selected horizontal
anchor. Its intermediate is the per-rectangle `(bbox, anchor_column)` record. Step B
uses that computed column to select the unique nearest row-0 marker and paint the
rectangle with that marker's color. Step B cannot choose a marker or output color
before Step A has produced the input-dependent anchor. The returned review evidence
contains a protected-Racket wrong-intermediate witness.

## Focused checks and native handoff

From the packet root:

```sh
python3 review.py run python3 -m pytest \
  generators/424c822d69f3/tests/test_parametric_anchor.py -q

python3 review.py run python3 -m arcpuzzles parametric qualify 424c822d69f3 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/424c822d69f3/qualification --summary
```

`promotion.json` is the native bounded contract. `evidence/manifest.json` binds the
adapter closure, the selected generator/reference authority, focused tests, and the
small declared evidence directory. Qualification executes every label and every
finite rival program through protected Racket.

Public challenges contain only demonstration inputs/outputs and query inputs. Private
settings, seeds, programs, source bindings, and query answers are excluded; IDs hash
the exact visible bytes only. Four queries are stored in a stable order so an external
controller can reveal one query per user turn without exposing future inputs or a
total-count hint.

## Retained historical prototype

The older root `prototype.py`/`verify_evidence.py` nearest-versus-farthest experiment
is retained as prior authoring evidence but is **not** the active native promotion.
The only current root contract is `anchor=midpoint|left_edge|right_edge`; no Cartesian
anchor-by-nearest/farthest product is claimed.

Finite teaching checks cover the other two anchor programs plus the source task's
`rank_order` and `vertical_overlap_only` shortcuts. They do not prove uniqueness
against every conceivable program. No output is accepted or training-admitted merely
because these checks pass.
