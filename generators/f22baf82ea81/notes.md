# Working notes: f22baf82ea81

## Review decision

The retained sampler was semantically faithful but too narrow: ordinary draws
used only centered solid inner rectangles, so a centered-solid-inner shortcut
fit the generated curriculum even though the canonical rule only requires a
content-dependent crop and color swap. The production generator is repaired at
version `2.2.0` with four ordinary inner topologies: centered rectangle,
off-center rectangle, connected non-solid mask, and hollow ring. The canonical
Racket program and canonical default semantics are unchanged.

## Native family

The episode-fixed parameter is `post_transform={as_is,rotate_cw}` with canonical
`as_is`. Step A crops the nonzero bounding box and swaps its two colors. Step B
applies the selected orientation to that input-derived intermediate. The full
six-demo/four-query input bank is generated before slicing, giving matched inputs
across settings and prefix stability for 2–6 demonstrations and 1–4 queries.
The fourth query is a substantive 30×30 case.

The first two demonstrations refute crop-only, full-grid, orientation, and
solid-inner-bbox rivals. The protected-Racket counterfactual rotates the
unswapped crop; it differs from rotating the correct swapped intermediate.

## Verification and limits

Focused tests: 23 passed. The 32-seed audit covered 192 episodes, 160 protected-
Racket evaluations, 32 counterfactual checks, 318 distinct inputs, and all four
inner topologies with no observed failure. Authoring preflight, causal replay,
16 sequential public projections, and first-turn privacy checks passed. These
are finite authoring checks, not owner acceptance or training admission. The
next owner action is source review followed by fresh native qualification and
acceptance on the exact integrated bytes.
