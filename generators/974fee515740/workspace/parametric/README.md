# `974fee515740` composition-order family

Parameter: `composition_order = rotate_then_combine | combine_then_rotate`.

- `rotate_then_combine` is the byte-exact catalog authority: read the operation
  and rotation controls, rotate the normalized blue component, then combine it
  with normalized red.
- `combine_then_rotate` uses the same controls and matched inputs, but first
  forms the operation-specific red/blue mask and then rotates that derived
  intermediate.

The first two demonstrations are a subtraction/90-degree case and an
intersection/270-degree case. Together they reject the other setting plus the
bounded direction, fixed-rotation, fixed-operation, and subtraction-direction
rivals implemented in `audit.py`. Episodes support 2–6 demonstrations and
1–4 prefix-stable queries. The fourth query is a distributed 30×30 stress case.
