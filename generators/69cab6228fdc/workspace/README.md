# Native parametric recolor-scope family

`workspace/parametric/` promotes one native family for the legend-recolor task.
The production generator and canonical authority remain unchanged.

`recolor_scope=all_sources` is the exact selected canonical Racket program: crop
the three header rows, parse every source→target legend pair, recolor every
mapped source cell, and preserve zero plus unmapped colors.

`recolor_scope=most_frequent_source` adds an input-dependent composition. Step A
counts each legend source in the body and identifies the unique most-frequent
source. Step B consumes that selected source and applies only its paired legend
mapping, preserving all other source and passthrough colors.

The adapter supports 2–6 demonstrations and 1–4 queries independently, uses
matched inputs across settings, and keeps prefixes stable. Every input has a
unique source-count maximum and visible passthrough evidence. The fourth query
is an exact 30×30 scene with four legend pairs and more than 400 nonzero body
cells. `public_turn()` reveals one query input without private settings,
programs, answers, future inputs, or total-query hints.

`workspace/parametric/audit.py` executes both settings and five additional
plausible rivals through protected Racket and stress-checks 128 seeds at minimum
and maximum counts. The result is finite evidence, not a universal uniqueness
proof. Owner native acceptance and training admission remain separate.
