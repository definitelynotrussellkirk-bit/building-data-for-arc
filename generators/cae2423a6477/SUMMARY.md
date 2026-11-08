# cae2423a6477 — Ring Selector

A black grid contains isolated green (`3`) objects. Recolor an object orange
(`7`) **only** when its cells are exactly the complete border of its own
rectangular bounding box. Large open outlines, small solid or bent objects,
non-rectangular simple loops, and branched objects that merely enclose a
rectangular hole remain green.

Generator version: `3.1.0`. Rule hash: `1f6f97325987`.

The default three-example schedule cycles through three exact, observable
profiles:

1. `canonical_small` — canonical-sized rectangular frames plus one short
   negative object.
2. `large_open` — a true frame plus a large one-gap border, refuting size and
   bounding-box shortcuts.
3. `hollow_irregular` — a true frame plus **two complementary hollow decoys**:
   a stepped, non-rectangular simple loop and a rectangular ring with one
   outward nub. These jointly refute “recolor every object with a hole,”
   “recolor every closed unbranched loop,” and “recolor every object with a
   rectangular hole.”

The sole override axis is `scene_profile`; it is exact, validated, and
recoverable from every emitted grid. The generator declares semantic witnesses,
rival rules, lesson-identifiability checks, a Python rule mirror, and a strict
canonical-profile predicate.

`workspace/rival_probe.py` independently mines a small grammar of plausible
object-level shortcuts. It checks canonical fit and then measures whether each
rival survives complete generated lessons; it exits nonzero if a sampled lesson
remains ambiguous.
