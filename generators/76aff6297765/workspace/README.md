# 76aff6297765 review tools

`probe_relation_curriculum.py` is a source-bound finite curriculum probe. It:

- verifies that each declared canonical shortcut actually fits every canonical pair;
- checks every query rotation of every six-slot cyclic lesson window supplied;
- checks all declared lesson competitors against the five demonstrations; and
- enumerates all 16 pointwise Boolean functions over the four aligned occupancy states for every generated grid.

Run from the extracted packet root:

```sh
python3 WORK/run_with_racket.py python3 \
  generators/76aff6297765/workspace/probe_relation_curriculum.py \
  --seeds 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,31,54,57,70,72,91,2026 \
  --difficulties easy,medium,hard \
  --out ../checks/relation-curriculum-probe-final.json
```

The tool loads the staged runtime module when available and otherwise falls back to the sibling `generator.py`. Its Python mirror is diagnostic; Racket-backed battery and census checks remain authoritative. The finite seed/rival set is not a proof against undeclared hypotheses.
