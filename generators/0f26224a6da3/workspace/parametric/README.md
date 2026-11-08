# Isolated-source color scope

The native family preserves the exact canonical `all_isolated` Racket program
and adds `rarest_color`. Every input contains at least two isolated-source
colors with one uniquely rarest frequency, plus a small connected domino that
must remain inert. Inputs are identical across settings; demonstrations teach
which isolated sources are selected.

The rule is sequential: **A** detects four-neighbor-isolated cells and either
selects all of them or selects the uniquely rarest source color; the
intermediate is the selected coordinate/color set; **B** expands exactly those
sources one cardinal step, clipped to the grid, while preserving existing
foreground. Replacing the selected source set changes the protected-Racket
result.

The adapter supports 2–6 demonstrations and 1–4 queries independently. The
minimum lesson includes a boundary source, a same-color diagonal pair that is
4-isolated but not 8-isolated, and inert connected foreground. The fourth query
is a distributed 30×30 scene with 18 isolated sources. `rival_audit.py` checks
named isolation, source-selection, fixed-color, connected-foreground, and
constant-output shortcuts over bounded seeds.
