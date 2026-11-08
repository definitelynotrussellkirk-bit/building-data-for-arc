# c1b80aa665e4 isolation-selector family

`all_isolated` is the selected canonical Racket program byte-for-byte.
`largest_cluster_color` first identifies the unique largest non-singleton
component, retains its input-derived color, then recolors only isolated cells of
that color to 9. The retained color is a real selector consumed by the second
step; choosing the smallest component's color changes the final output.

Inputs are matched across settings, deterministic and prefix-stable, support
2–6 demonstrations and 1–4 private queries, and include a substantive 30×30
fourth query. The first two demonstrations deliberately move the largest
component between first and non-first row-major positions, change its color,
and make another color larger only in aggregate, refuting fixed-color,
first/last-component, smallest-component and aggregate-color shortcuts.
