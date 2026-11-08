# Periodic cross with phase-locked vertical stripe

The default `canonical` setting is the exact selected source program. It extends
the vertical and horizontal seed sequences independently, with the horizontal
stripe owning the final crossing cell.

The `phase_locked` setting adds a real sequential dependency. Step A tiles the
horizontal seed. Its input-dependent crossing color is the intermediate. Step B
finds that color in the vertical seed, rotates the vertical period so the same
color lands at the crossing, and tiles the column. A wrong crossing color changes
the entire vertical phase.

The deterministic grammar supports 2–6 demonstrations and 1–4 queries. Every
scene distinguishes the settings, and the fourth query is a substantive 30×30
cross whose output spans all 59 cells of the selected row and column. Labels in
the adapter are Python claims; native preflight re-executes every pair through
the protected Racket backend.
