# 2d4e8c8fa10e native controller-axis family

The default `all_exact_squares` setting is the exact canonical Racket program.
The `controller_axis` setting uses the same inputs but adds a causal selector:
find the unique largest non-square straight magenta component, derive its row or
column axis, then keep only exact 2×2 squares intersected by that axis.

Two through six demonstrations and one through four queries are supported. The
first two demonstrations use horizontal and vertical controllers respectively;
every scene contains both aligned and off-axis exact squares. The fourth query
is a 30×30 stress case with eight exact squares and eight non-square components.
`audit.py` checks count boundaries, matched inputs, finite rivals, controller
coverage, and output separation; protected-Racket preflight remains the label
authority.
