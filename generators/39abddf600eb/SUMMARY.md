# 39abddf600eb

A strictly inset rectangular frame contains exactly two colored seeds. The selected rule redraws the frame and seeds on black, then paints color 9 at every strict-interior cell whose Manhattan distance to the two seeds is equal. Opposite-parity seed coordinates have no integer-grid bisector and lawfully produce an unchanged input.

Kind: `per_puzzle`. Selected generator version: `3.1.0`.

## Declared input controls

- `grid_h`: 8–16
- `grid_w`: 8–18
- `frame_color`: 2–8
- `seed_geometry`: `identity|axis|diagonal`
- `seed_color_relation`: `same|different`

Every exact combination is constructive; there are no declared incompatibilities. Four of every five default draws use a canonical-profile canvas, while the fifth explores the full declared size range. The six-step geometry schedule is rotation-safe for the canonical-fitting `diagonal_only` rival.

The selected canonical rule is unchanged and pinned by `RULE_HASH = "38c495fef5e9"`. Final reviewed source SHA-256: `420745b489f4080dca7e147cbf5882155aa610d4231aee0cf6303bccff731a06`.

Approval remains catalog-derived; this review does not self-promote training safety.
