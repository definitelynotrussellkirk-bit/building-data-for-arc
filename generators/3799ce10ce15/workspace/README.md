# Workspace — 3799ce10ce15

`reference_probe.py` is the reusable independent review tool for this generator.
It does not import parsing or rule helpers from `generator.py`.

It provides:

- canonical pair loading through portable reviewer support;
- independent legend/frame parsing and intended output calculation;
- the canonical-fitting fixed-window rival and exactly-once rival;
- observable-axis and distribution summaries;
- deterministic A–B–A checks; and
- optional comparison with the selected canonical Racket authority.

Typical source-tree use from the packet's `repo/` directory:

```text
python3 generators/3799ce10ce15/workspace/reference_probe.py \
  --count 100 --out ../checks/independent-audit.json --racket
```

The selected implementation remains `../generator.py`. The focused portable tests
are in `../tests/test_generator.py`; they use `reviewer_support.find_root` and do
not rely on fixed parent depths.
