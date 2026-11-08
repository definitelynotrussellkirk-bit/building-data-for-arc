# Public parent 136b0064 — current design and verification plan

Unapproved authoring work. Parent linkage in workspace/public-parent.json is immutable.
Canonical: read the 3x3 colored glyphs column-major left of the yellow divider;
start from the gray marker on the right; 1 draws three rightward cells, 2 two
leftward cells, 3 four leftward cells, and 6 two downward cells. Each instruction
starts one row below the previous endpoint and advances that endpoint.
Alternative: read the same glyph grid row-major. The ordered glyph stream is
input-dependent and its stateful fold cannot be replaced by independent stamps.

Implementation plan (this home only):
1. Write tests against all supplied train and test gold plus a literal cursor case;
   run them red, implement independent Python and general Racket interpreters.
2. Add a thin native adapter and matched-input sampler: 2–6 demos, shuffled bank
   of four novel queries; stress 30x30. Test prefix stability, strict arguments,
   rival rejection, legal paths and public/private boundaries before implementation.
3. Self-review with finite executable rivals and broaden seeds; retain failures,
   repair real defects, then protected-Racket authoring preflight and causal replay.
4. Return source-bound evidence, not owner approval or a training-admission claim.

Design choice: keep glyph/color semantics faithful and vary reading order rather
than introduce an unrelated transformation. Geometry, instruction counts, start
position and sequence vary. Invalid glyphs and out-of-bounds correct paths are
not admitted by the sampler. Rival paths are clipped so execution errors cannot
count as teaching evidence. Self-review is bounded, not a uniqueness proof.

## Current verification and limits

- Direct complete task suite: 42 passed. All 3 train labels and the supplied
  official test gold match both independent Python and protected-Racket rules.
- Bounded audit: seeds 0–63, 128 full episodes, all 2–6/1–4 count prefixes;
  9 named rivals per setting. 256 protected-Racket evaluations on seeds 0 and 1.
- Authoring preflight: seeds 17 and 43, both settings, 2 demos + 4 queries.
  All original labels and all finite identification/query checks passed.
- Wrong-order witness: selected row-major stream [2,3,1,2,1,6]; changing only
  the read order changes the final grid. Construction and second-process replay
  use protected Racket and remain reviewer evidence, never owner acceptance.
- Sequential public exports use one query only; identities and disk order depend
  only on their own visible bytes. Stress query: 30x30 input, 28 glyphs, trace
  reaches the bottom row. Its output is the lawful 30x14 right-hand canvas.
- The native task-tests staging command cannot resolve this unregistered task
  (Unknown puzzle). The direct task suite passed; the catalogue was not edited
  to bypass registration. Owner registration/native qualification remain pending.
- Self-review found no further failure in the named finite space. Fixed glyph
  semantics are the admitted grammar; arbitrary new/recolored symbols, clipped
  correct paths, and universal inferential uniqueness are not claimed.
