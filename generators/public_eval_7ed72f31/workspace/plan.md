# Marker-relative copying implementation plan
Goal: reproduce every original label, then build matched mirror/half-turn lessons.
Architecture: recover background and 8-connected multicolor marker/source groups;
extract each group's red marker bounding box and source-colored cells; use that
input-dependent geometry to reflect or half-turn each source into empty canvas.
Canonical: red singleton means 180-degree rotation; red horizontal/vertical line
means reflection in its axis. Alternative: a line means 180-degree rotation
about its midpoint. Both use the same group extraction and source offsets.

- [x] Fail tests for all four original pairs, independent point/line examples,
  unequal marker lengths, repeated colors, 8-neighbor-only attachment, strict
  inputs/counts, prefix stability, 30×30 stress, and private projection.
- [x] Implement canonical/alternative Racket, Python mirror and constructive
  sampler, native contract and portable ordinary generator.
- [x] Execute protected original labels, correct concrete findings, attack
  meaningful shortcut rules with 2-demo lessons and retain regressions.
- [x] Run source-pinned preflight, extra Racket parity, causal replay, export
  checks, and author self-review; package only scoped sources and compact proof.

Constraints: 2–6 demos and four distinct queries; parameter fixed per episode;
randomized query order is private and independent of source ordinal; explicit
30×30 scenes with spatially distributed content. Original reference is general,
not a mapping from known input grids or official task IDs to stored answers.
Review focus: diagonal association vs 4-neighbor, marker segment vs infinite
axis, line midpoint half-integer coordinates, source colors shared across
different groups, bounding-box centers vs actual marker centers, clipping and
collisions, malformed marker geometries and unknown controls.
