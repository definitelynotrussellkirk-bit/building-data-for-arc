# Working notes: 85dcd5c922b9

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Exact first-row control

`first_row_load` accepts only the integers 2 and 3; `None` retains the shared
no-override convention. Use `draw_int_strict` so fractional floats, whole-number
floats, numeric strings and booleans cannot be silently coerced into an integer
request. The prior `draw_int` call accepted `2.75` and generated two tokens,
which then failed the generator's own exact-override check.

The focused regression is `tests/test_first_row_load_boundary.py`; the portable
before/after reproducer is `workspace/probe_first_row_load.py`. The bounded
review evidence in `checks/85dcd5c922b9/{before,after}.json` records five accepted
noninteger requests before repair and zero afterward, twelve unchanged legal
grids across the three scheduled profiles and both blank-row settings, three
unchanged `None` defaults, and twelve matching canonical Racket outputs. The
selected rule remains `6ab6552b1d13`. Canonical grammar, curriculum and seed
version are unchanged. This control check does not establish broader teaching
coverage or resolve unrelated inherited limitations.
