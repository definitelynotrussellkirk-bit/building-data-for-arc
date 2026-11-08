# Proposed ray-template family

Parameter: `template = full | fragment`. `full` is the selected canonical rule byte-for-byte: each marker fragment selects a direction and color, then the entire source template repeats along that ray. `fragment` repeats only the marker's recovered source fragment. Direction decoding, bbox-plus-one stride, marker color, clipping, and preservation of occupied cells remain invariant.

The grammar is setting-independent. Every 2–6-demo prefix distinguishes the two settings, four queries are available independently, and query four is a constructed three-ray 30×30 stress case. `visible_turn()` reveals one masked query at a time with no private metadata or count hints.

```bash
python3 review.py run python3 -m pytest -q generators/b2d6e6b60917/tests
python3 review.py run python3 generators/b2d6e6b60917/workspace/parametric/verify.py --out ../checks/parametric/b2d6e6b60917
```

This is a proposed task-local extension; it is not accepted or training-admitted.
