# Working notes: fa2e57ec3fa2

Current decision: keep `stop` byte-for-byte canonical and add `mirror_turn`.
Each emitter first binds its first-hit mirror; color 6 supplies an upward
direction and color 8 a downward direction, then a second vertical trace consumes
that input-derived intermediate.

The base generator's inert wall/palette controls were removed. `palette_kind`
now changes actual obstacle regimes, unknown axes are rejected, and ordinary
size/count boundaries are explicit. The family supports 2–6 demonstrations,
four setting-independent queries, and a 30×30 eight-emitter stress query.

The immutable canonical record stores its sole `test` pair as an object rather
than a list, exposing a shared authoring-preflight container-shape bug. The
source-bound task-local `base_preflight_compat.py` normalizes only that legacy
shape; canonical bytes, labels, and shared runtime remain unchanged.

Finite adversarial review tested five seeds, every supported demo/query count,
and 70 plausible shortcut episodes; all declared rivals were refuted by the
minimum two demonstrations. Protected Racket qualification and the skip-A
counterfactual are retained under `checks/fa2e57ec3fa2/`. This is reviewer-ready,
not owner-accepted or training-admitted.
