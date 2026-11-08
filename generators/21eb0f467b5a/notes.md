# Working notes: 21eb0f467b5a

## Review findings and repairs

- The inherited generator exposed several declared controls without actually
  honoring them and taught only one positive aligned pair. It now validates all
  ordinary overrides strictly, makes exact dimensions/orientation/palette
  controls real, and constructs an aligned pair with at least two blanks plus a
  separate singleton. Degenerate textures remain explicit only.
- The canonical `all_aligned` program is preserved byte-for-byte at SHA-256
  `a67351f37a49020c656adf08bd4566d328af5fe97acad3e510012b9868fe9449`.
- Added `key_match`: derive the unique color-7 key pair's orientation and
  inclusive segment length, then complete only pairs with that exact two-part
  signature. Same-orientation/different-length, opposite-orientation/same-length,
  diagonal, singleton, and multi-cell controls prevent shortcut collapse.
- Episodes support 2–6 demonstrations and exactly four distinct queries. Query
  four is a substantive 30×30 boundary/density stress case.

## Self-review and evidence

- Focused suite: 21/21 passed.
- Finite teaching audit: 36 jobs, 276 labeled pairs, 1,056 rival-demo checks,
  zero survivors among eight named shortcuts.
- Protected authoring preflight: both settings at seeds 0 and 17, 40 Racket
  evaluations, original labels and ordinary draws included.
- Source-bound wrong-intermediate witness changes the key length and final grid.
- Public projection: 16 single-query views; first-turn check: 24 invariance
  checks and four positive controls.

Owner source review, native qualification/acceptance, and training admission are
separate downstream gates and are not claimed here.
