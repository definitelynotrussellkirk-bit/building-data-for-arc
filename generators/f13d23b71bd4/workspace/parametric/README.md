# Native signal-ranked falling-object family

`fall_policy=all_large` is the exact canonical rule.  Every monochrome
4-connected object with at least four cells falls until its bottom reaches the
canvas bottom.

`fall_policy=signal_ranked` adds a real sequential dependency.  Step A measures
the unique color-1 signal object's size (1–3).  The intermediate is that one-based
rank among large non-signal objects in row-major order.  Step B drops only the
ranked object and leaves every other object at its input position on the fresh
color-7 canvas.

Both settings use identical scenes.  The family supports 2–6 demonstrations and
1–4 prefix-stable queries; the fourth query is a substantive 30×30 case.  Use
`audit_lessons.py` for the bounded teaching, count, setting-neutrality and public
projection audit.  Native qualification and owner acceptance remain separate.
