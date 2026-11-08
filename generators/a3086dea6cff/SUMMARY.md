# a3086dea6cff — aligned exact-pair connectors

A black 8–13 by 10–15 grid contains 2–4 active colors. Each active color occurs
exactly twice and its two cells share either a row or a column, with enough
separation to make the filled segment visible. The output fills the inclusive
straight segment between each aligned exact pair, in first row-major color
occurrence order; later segments overwrite earlier segments at crossings.

The three-example curriculum cycles through:

1. a canonical-scale aligned-pairs scene,
2. an otherwise valid scene with one gapped collinear color occurring three
   times, which remains unchanged, and
3. an otherwise valid scene with one non-aligned pair, which remains unchanged.

Every scene contains both horizontal and vertical active pairs. Every three
consecutive examples contain both negative witnesses and an interior crossing,
so the lesson refutes count-agnostic, L-connector, one-orientation, and fixed
crossing-precedence shortcuts.

Kind: `per_puzzle`. Selected version: `3.0.0`. Rule hash: `7563337a81ab`.
The Racket authority was not changed by this review.
