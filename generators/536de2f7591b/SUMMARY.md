# 536de2f7591b

**Version 3.0.1 — input-only generator; canonical rule hash `02c227b9b2a6`.**
On each active row, a contiguous green-3 block slides left to just after the
nearest original cyan-8 cell to its left, or to column zero. Its length is
preserved. Cyan cells and nonmarker distractors stay fixed; distractors never
occupy either initial or final green footprints.

Default four-example cycle: canonical suffix blocks (width 1–2), moving interior
blocks, inert path distractors, and a width-three block. Canonical and width-three
profiles retain observed canonical shape pairs; other profiles vary by band.
`EXAMPLES_NEEDED=4`. Default lessons are tested against three canonical-fitting
rivals; this is a finite contract, not universal identifiability.

Exact observable controls: `grid_h` 5–18, `grid_w` 6–20, `n_green_rows` 1–6,
`max_block_width` 1–3, `n_distractors` 0–3. More requested green rows than an
explicit height is incompatible. Unknown/legacy controls and noninteger values
are rejected. V2 override names are not silently supported.

Selected base Racket target text is synchronized to canonical authority;
canonical source is unchanged. Approval remains derived by catalog and retained
independent evidence, not by this summary or reviewer-local passing checks.
See `notes.md`, `tests/`, and `workspace/README.md`.
