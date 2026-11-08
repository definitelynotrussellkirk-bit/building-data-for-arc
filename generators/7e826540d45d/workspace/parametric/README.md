# One-ring halo plus selected two-step expansion

The default `halo_mode=one_ring` returns the exact canonical Racket program.
The alternate first replaces every object by its orthogonal one-ring halo (A),
selects the most frequent nonzero color in that intermediate, and expands only
that selected halo one more orthogonal step (B). Teaching scenes pair a compact
3×3 or 4×4 square with a six-cell line, a bent six-cell L, or an eight-cell
line. The compact object is larger in the input, but the selected object has
the larger first halo, so skipping A changes B's selector.

Every three-demonstration lesson varies selected-object orientation, topology
(straight and bent), source size (6 and 8), raw source-size rank (second and
third), vertical half, and opposite-corner placement. Consequently,
widest-input-object, bottommost-object, longest-straight-object, fixed-rank-two,
and fixed-rank-three shortcuts all fail in a 200-seed / 600-pair audit.
Inputs remain shared across settings; 3–6 demonstrations and 1–4 queries are
supported, with a distributed 30×30 fourth query.

This remains reviewer-authored prototype evidence pending owner source review,
native qualification/acceptance, and any separate training decision.
