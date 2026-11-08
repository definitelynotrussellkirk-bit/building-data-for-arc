# f505996a2fdc — Commanded crop transform

The input is an 8–10 by 8–10 zero-background grid. Cell `(0, 0)` contains one command in `1..6`; the rest of row 0 and all of row 1 are blank. A tight, transform-sensitive colored object appears below the separator. Clear the command, crop to the object's nonzero bounding box, then apply:

1. identity
2. rotate 90° clockwise
3. rotate 180°
4. transpose across the main diagonal
5. flip left/right
6. flip up/down

Generator version `3.0.0` uses a deterministic six-slot curriculum. Every six consecutive default samples expose all six commands, cover the five canonical `(height, width, palette-size)` profiles, and use 2–4 by 2–4 objects with 1–3 colors. Every advertised override is exact or rejected; `RULE_HASH = 9bbe263d873a` binds the unchanged canonical Racket authority.

Kind: `per_puzzle`. Approval remains catalog-derived from current code and retained evidence.
