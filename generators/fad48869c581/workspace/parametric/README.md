# Native L completion: canonical or square halo

`mode=canonical` returns the selected canonical Racket source byte-for-byte. It
finds every 2×2 window containing exactly three cells of one nonzero color and
one background cell, then fills the missing corner with that color.

`mode=square_halo` is a genuine two-stage rule. Stage A runs that exact
completion, producing solid monochrome 2×2 squares. Stage B reads the completed
snapshot and expands each derived square by one cell in every direction, filling
only background cells with the square's own color. Existing nonzero distractors
are preserved. A pre-completion L is not a solid square, so applying Stage B to
the original input does not produce the declared result.

The deterministic bank is built before slicing and supports 2–6 demonstrations
and 1–4 queries. Ten distinct matched inputs cover varied dimensions, colors,
missing corners, boundary contact, isolated distractors, and deterministic
geometry changes across seeds. Two 30×30 scenes distribute 16 and 18 Ls across
all quadrants; their halo outputs contain substantial content rather than padded
small puzzles. Qualification uses three demonstrations and four private queries.
Owner source review, native acceptance, and training admission remain separate.

The bundled `preflight_compat.py` launcher handles this legacy task's singleton
canonical `test` record by wrapping it in memory for the shared authoring
preflight. It does not edit catalog data or weaken source, Racket, or drift checks.
