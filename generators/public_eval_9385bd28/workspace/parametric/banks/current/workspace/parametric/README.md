# `public_eval_9385bd28` authoring family

The canonical program reads the two-column key and applies its rows from bottom
to top. A target of zero or the modal background restores the original rectangle;
other targets fill the source bounding rectangle, retaining disconnected source
fragments. A single connected source object is replaced.

`finish=highlight_largest_change` first performs that full composition, then
finds the largest 4-connected component of cells whose visible value changed and
recolors it 9. `wrong-intermediate.rkt` uses the largest raw operation rectangle
instead, before accounting for later transparent cuts.

Quick checks from the packet root:

```bash
python3 review.py run pytest -q generators/public_eval_9385bd28/tests
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight \
  public_eval_9385bd28 --root . --out ../checks/public_eval_9385bd28/preflight
```
