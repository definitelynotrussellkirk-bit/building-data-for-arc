# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## `lesson_rivals.py` — lesson-level rival audit

This is test tooling, not a label authority. It holds an independent Python oracle for the canonical rule: a same-color 4-connected bbox outline on a blank canvas. It also holds four rivals: `fill_bbox`, `union_outline` (keep the blob, add the outline), `outline_8conn` and `outline_per_color`.

From the packet root:

```bash
# Racket-labelled lessons (validates the oracle: oracle_mismatches must be 0)
python3 run_with_racket.py python3 -m arcpuzzles generate 61f255726e2e --count 100 --seed 11 \
  --difficulty hard --train 3 --test 1 --allow-unapproved --timeout 900 --out /tmp/e.jsonl
python3 repo/generators/61f255726e2e/workspace/lesson_rivals.py /tmp/e.jsonl

# Python-only lessons for any generator file (fast; 300 lessons per band)
python3 repo/generators/61f255726e2e/workspace/lesson_rivals.py \
  --generator repo/generators/61f255726e2e/generator.py --lessons 300 --out /tmp/audit
```

`--timeout 900` is needed: the default 180 s covers the whole batch, and about 100 episodes exceed it.

The report shows:
- how often each rival fits every demo yet answers the query differently (the lesson cannot identify the rule);
- how often a rival fits the whole lesson (the difference is never exercised);
- component counts, bbox shapes and hollow-interior rates.
