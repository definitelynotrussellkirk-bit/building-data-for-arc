# Rectangle completion followed by component selection

Native authoring adapter for `89c85768abe1`. The selected production generator
and its canonical Racket authority remain unchanged. This proposal requires
owner exact-source acceptance before the native accepted export route can use it.

| Private episode setting | Executed rule |
| --- | --- |
| `{"mode":"all"}` | Exact canonical program bytes: complete every colored rectangle. |
| `{"mode":"largest_component"}` | Complete the rectangles, find the largest four-neighbor foreground component ignoring color, retain its original completed colors, erase the other components. |

The second setting has a causal dependency: completion can join differently
colored rectangles whose original corner markers are disconnected. Selection
uses the resulting component partition and its **total occupied-cell areas**.
The output preserves gaps in an L-shaped group; it does not paint its bounding
box. Equal maxima choose the component whose first cell is earliest in row-major
order. That tie behavior is tested for totality; generated lessons and queries
deliberately have a unique largest component, so short lessons need not teach ties.

## Teaching and supported inputs

Requests accept exact integer seeds `0..2**63-1`, independent `demos=2..6` and
`queries=1..4`. Ordinary use is **three demonstrations and four queries**. Every
input in an episode is distinct. Sampling and input order are identical across
the two settings, and the first query is identical for one-query/four-query
requests at the same seed and demo count. The hidden setting stays fixed.

Inputs contain 2–4 colors, each at two non-collinear opposite corners, on a zero
background. Completed rectangles are disjoint but can touch along edges or
diagonals. The separate prototype validator supports dimensions up to 30×30;
the production generator's narrower axis bounds are not extended. No new
production override is advertised.

The first two demonstrations are constructive:

1. Two small rectangles become one L-shaped component, beating a larger
   individual rectangle by **one cell**. Counting only newly painted cells
   reverses that choice, and treating diagonal contact as connected joins a
   distractor incorrectly.
2. An isolated rectangle beats a two-rectangle component, even though that
   smaller component has a larger bounding box and more original markers.
   A blank column separates it even under eight-neighbor connectivity.

These share role colors and a geometric transform so the winning role changes.
Additional demonstrations and queries vary colors, two/three/four-rectangle
scenes, rotations/reflections, scales, offsets, and boundary contacts. The fourth
query is 30×30 with scaled rectangles and at least 210 completed cells in the
supported profiles, rather than a small scene surrounded by padding.

`teaching_report` fits 16 named programs using demonstrations only, then checks
each surviving program against every actual query. It separately requires a
unique declared setting. Tested alternatives include wrong connectivity,
largest individual rectangle, bounding-box ranking, rectangle counts, newly
painted area, selection before completion, positional/color shortcuts and the
inherited diagonal shortcuts. This is a finite check, not universal uniqueness.
Every generated label is a Python claim until checked through Racket.

## Run and export

From the outer packet directory, using the interpreter that passed
`review.py python-check` and the bundled Racket selected by `review.py setup`:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/89c85768abe1/workspace/parametric/export.py \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/89c85768abe1/new-examples

WORK/.venv/bin/python review.py run python3 \
  generators/89c85768abe1/workspace/parametric/export.py \
  --verify ../checks/89c85768abe1/new-examples
```

Output directories must be new. The writer checks every label with protected
Racket before publication. The verifier checks serialized content and repeats
Racket label execution. This verifies data against current source, not owner
acceptance or authenticity of an arbitrary untrusted manifest.

`private.jsonl` holds settings, seeds, programs, answers, runtime identity,
teaching checks and ordered turn mappings. `public/` is the controller's bulk
challenge set with all stored query inputs; **do not serve that full set as a
model turn**. Serve one `turns/<visible-bytes-hash>.json` at a time using the
private mapping. Each turn has the demonstrations and exactly one query input,
with no answer, future-query input, total-count hint or last-turn flag. The first
turn has the same bytes and identifier in single-query and multi-query use.
Public IDs hash only exact visible bytes. Records are sorted by public ID and
duplicate visible episodes are rejected before output creation.

## Qualification and owner handoff

Focused tests live in `../../tests/test_parametric*.py`. The native inventory
binds adapter/prototype/Racket resources, test sources and compact evidence.
The submitted `checks/89c85768abe1/qualification/` includes the mandatory native
qualification plus its sibling protected execution receipt. The causal witness
in `checks/89c85768abe1/causal/` executes selection-before-completion and
largest-individual-rectangle counterfactuals against qualified examples.

Owner steps after source integration are native qualification and acceptance of
the exact integrated bytes, as documented in `docs/parametric-promotion.md`.
Reviewer `ready` does not mean `accepted`; no training admission is granted.
