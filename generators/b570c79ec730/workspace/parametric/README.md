# Proposed bbox-border policy for `b570c79ec730`

This opt-in prototype preserves the task's per-component bbox reasoning and
varies one semantic choice:

- `preserve_existing` — canonical: erase only component cells strictly inside
  the bbox; keep only boundary cells that already exist.
- `complete_bbox` — nearby alternative: perform the same interior erasure, then
  complete the full bbox perimeter in the component color.

It is proposed and unaccepted; production source and canonical authority are
unchanged.  Every demonstration contains a connected thick notched rectangle,
so the retained full-bbox-outline shortcut is a concrete distinguishing witness
rather than an accidental fit.  Inputs are setting-neutral; demo/query counts
are independent (2–6 and 1–4); query four is substantive 30×30.

Focused check:

```bash
python3 review.py run python3 -m pytest -q generators/b570c79ec730/tests/test_parametric.py
```

Protected qualification executes both exact Racket programs and all four query
labels.  Public turns include demonstrations and only the current query input.
