# a178821cc6bf

Two **adjacent** 4-column panels form an `h x 8` input.  For each aligned
column pair, output color `4` iff both input cells are `0`; output `0`
otherwise.  Ordinary draws contain all four occupancy states (`00`, `10`,
`01`, `11`), exclude answer color `4` from the input, and alternate same versus
different panel foreground colors so a two-example lesson refutes raw-value
equality as well as one-panel and occupancy shortcuts.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule hash:
`ff2f0d5fbd0c`.

Focused regression tests live in
`tests/test_generator_a178821cc6bf.py`; they cover all canonical pairs,
shortcut-identifiable consecutive lessons, override observability,
determinism, negative controls, and malformed inputs.
