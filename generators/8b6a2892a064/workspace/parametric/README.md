# 8b6a2892a064 parametric family

`rotation_scope=all_components` is the exact canonical rule.
`rotation_scope=modal_length` counts the odd straight-line component lengths,
selects the unique most frequent length, and rotates only that length class.
Other components remain in their original positions.

The sampler is setting-independent, supports 2–6 demonstrations and 1–4
prefix-stable queries, and includes a substantive 30×30 query. The first two
demonstrations vary the modal length and include another repeated nonmodal
length to refute fixed-length and "rotate every repeated length" shortcuts.
