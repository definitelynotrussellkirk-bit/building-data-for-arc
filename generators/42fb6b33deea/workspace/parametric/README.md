# Selector-area rectangle gate

This native family preserves the exact canonical rule and adds one nearby,
episode-fixed alternative on matched inputs.

- `all_exact_four` is the canonical Racket program byte-for-byte: every nonzero
  color occurring exactly four times fills its complete bounding box.
- `selector_area_gate` first finds the unique three-cell selector and measures
  its bounding-box area. It then fills only exactly-four colors whose own
  bounding-box area is at least that input-derived threshold.

The alternative has a real sequential dependency. Step A identifies the unique
three-cell selector and produces its bbox area. Step B compares each exactly-four
target bbox against that value, so the set of rectangles to paint cannot be
chosen before Step A completes. Skipping Step A collapses to the canonical
fill-all rule and changes the bounded witness output.

Inputs are independent of the private setting. Every scene has targets below,
equal to, and above the selector threshold, including qualifying non-corner
four-cell targets. Two demonstrations distinguish both settings and the retained
finite rivals. Requests support 2–6 demonstrations and 1–4 queries; generation
materializes the full schedule before taking prefixes. The fourth query is a
substantive exact 30×30 case.

`prototype.py` also exposes `public_view` and `public_id` helpers for one-query
sequential projection. Test answers, settings, and programs stay outside the
public view. Owner qualification/acceptance and training admission remain
separate.
