# 39fd645f21c6

Version `4.0.0`; canonical `RULE_HASH = 36a57f0bfc36`.

Find the unique blue (1) 4-connected component and compute its feature triple:

1. cell area,
2. number of enclosed background holes in its bounding box,
3. reflection-symmetry class (`0=none`, `1=row`, `2=column`, `3=both`).

Recolor every non-blue component with exactly the same triple to cyan (8); leave every other cell unchanged.

The v4 teaching distribution fixes the former exact-shape shortcut. Every generated scene contains one or two **different-shape** feature twins plus three one-coordinate decoys: one differs only in area, one only in hole count, and one only in symmetry class. Inputs use the exact canonical profiles `11x16/5 colors`, `12x16/5 colors`, and `12x17/5 colors`. A deterministic six-step lesson schedule exposes all five target families and alternates one- and two-match scenes, allowing every cyclic query rotation to refute the declared rivals.

Exact public axes are `scene_profile`, `target_family`, and `match_count`; `observe_overrides` recovers each from the returned grid. `strict_canonical_like` accepts all canonical examples and generated inputs. The Racket authority and canonical data are unchanged.
