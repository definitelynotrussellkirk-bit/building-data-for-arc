# Blocked-fallback regression

`input.json` is a minimal ordinary-domain witness synthesized from the canonical
rule.  It contains one pair where both L paths are clear, one where horizontal is
blocked but vertical is clear, and one where both are blocked by color-8 walls.
The authority still selects the vertical fallback, paints around walls, preserves
walls, and resolves path overlap in row-major first-color order.

`expected.json` is produced by the independent reviewer oracle and is covered by
`tests/test_generator.py`; Racket parity is also required when the packet runtime
is available.
