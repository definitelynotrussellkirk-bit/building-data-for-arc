# 9baf979683ef

A 0-background grid contains exactly one full-height grey (`5`) divider. All
other coloured cells begin to its left. The output preserves the input and
copies every source cell to the same row at the equal-distance position on the
right of the divider, preserving its colour.

Kind: `per_puzzle`. Selected version: `3.0.0`. Canonical rule hash:
`1fce392f92a1`. The Racket authority and canonical examples are unchanged.

The production distribution supports the three canonical shapes (`7x11`,
`8x9`, `7x13`) and two expanded shapes (`9x12`, `10x15`). Its exact controls
vary profile, divider side, source count (6–8), source palette size (1–4), and
connected/scattered/mixed geometry. Production dividers are one column off the
geometric midpoint and production scenes have more than five source cells,
because both “mirror about the geometric midpoint” and “mirror only the first
five sources” fit all three canonical examples.

Validation includes a strict structural checker, observable override recovery,
an independent Python oracle, declared semantic witnesses/rivals, and
lesson-level identifiability checks. See `notes.md` and
`workspace/audit_distribution.py` for measured coverage and limitations.
