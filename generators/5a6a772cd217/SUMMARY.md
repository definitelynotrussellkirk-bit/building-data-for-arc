# 5a6a772cd217 — Frame Interior Gallery

Version: `3.0.0`. Canonical rule hash: `64fd3246321b`.

Inputs contain exactly two or three separated hollow gray (`5`) rectangular frames on a zero background. Each frame has one distinct non-gray interior color and a nonempty mixture of colored and zero cells. Frames are read in row-major order: top row first, then left column.

The unchanged Racket authority extracts each complete frame interior, top-aligns the panels to the tallest interior, and concatenates them horizontally. Any panel narrower than three columns gains one zero column: after the first panel's content, but before every later narrow panel's content.

The sampler exposes two exact, pixel-observable axes:

- `canvas_profile`: four canonical profile shapes plus two modest broad-support profiles, with exactly two or three frames.
- `density`: `sparse`, `balanced`, or `dense` interior color occupancy.

The deterministic teaching schedule alternates a row-order conflict profile with a canonical left-to-right profile. Three demonstrations plus one query eliminate the declared rivals under every tested query rotation. `generator.py` also exports the structural validator, exact override observer, Python rule mirror, semantic witnesses, and executable rivals used by the task-local tests and shared gates.
