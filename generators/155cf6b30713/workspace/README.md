# 155cf6b30713 review workspace

`generator.before-review.py` preserves the selected baseline used for this review.

`inspect_lesson.py` is a source-bound curriculum probe. It generates one lesson,
reports the exact generator hash and request, infers the transform/color map,
shows mapped versus pass-through query colors, records structural features, and
measures every declared rival's disagreement with the authority mirror.

Run from the repository root:

```bash
PYTHONPATH=src:shared/runtime python3 \
  generators/155cf6b30713/workspace/inspect_lesson.py \
  991 7 --difficulty hard --panel-size 5 --transform atr --include-grids
```

Use `--out PATH.json` to retain a replayable JSON report.
