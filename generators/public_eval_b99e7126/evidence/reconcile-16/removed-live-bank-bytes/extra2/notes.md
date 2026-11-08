# Current family: self-similar tiled completion

Status: authoring-preflight passed, reviewer-ready. This is not native owner
qualification, acceptance or model-training admission. All four supplied labels
match the general reference under protected Racket execution.

## Canonical interpretation

Recover the framed regular tile lattice from homogeneous separator bands. The
normal tile is the unique majority pattern; the other tile is special. Exactly
one color in the special tile is absent from the normal tile and separator.
Its occupied micro-cells encode the desired macro arrangement of special tiles.
Find the unique translated mask containing all observed special tiles, and copy
the complete special tile into missing macro positions. No original-grid lookup
or fixed palette table is used. Separator bands may be wider than one pixel.

The authored domain requires two tile patterns, a unique normal majority, one
novel color, and a unique placement. Ambiguous placements are rejected rather
than silently resolved. These grammar restrictions go beyond what four examples
can prove about every possible input; owner semantic review remains necessary.

## Sequential variant and counterfactual

`completion=fill_holes` first completes the macro template. It then floods the
macro complement from its boundary with four-neighbor connectivity and fills
all enclosed macro cells with the special tile. The completed occupied set is
the intermediate, not a preselected output region. `fill_before` is the retained
wrong-order program: it measures holes on the original partial arrangement.
The 30x30 ring witness is open before completion and contains one hole afterward;
the wrong order changes eight final cells.

## Sampler and lessons

Ten construction profiles cover ring, tail, diagonal gap, concave/open shapes,
multiple rotations/reflections, variable tile/background/novel colors (including
zero), varied macro-grid sizes, and partial masks. A closed-ring-with-missing-tail
lesson contrasts with an initially open lesson. Four-neighbor cavity topology
is distinguished from eight-neighbor leakage. The largest profile uses a 7x7
macro lattice of 3x3 tiles with thick outer bands, exactly 30x30.

An initial test exposed a normal/special frequency tie on a small lattice. The
sampler now enlarges that profile or limits the observed set, preserving a strict
normal majority. Tests also reject genuinely ambiguous template placements.

Both settings share inputs. Independently requested 2–6 demonstrations and 1–4
queries use a complete, independently shuffled four-query bank before slicing;
only one current query is projected publicly. No global RNG mutation or shared
mutable metadata is used.

## Evidence and portability

71 task tests pass. The final 64-seed audit spans both settings and demo counts
2, 3 and 6: 384 episodes, 4,224 named-policy checks and 640 distinct inputs. No
declared policy both fits the demonstrations and changes a query in that scope.
The audit performs 42 protected Racket evaluations plus two causal replay calls,
checks 16 public views, and rejects seven deliberate malformed exports.
These are bounded author checks, not a universal uniqueness proof.

Evidence is under WORK/checks/public_eval_b99e7126/preflight-final, audit-final,
and tests-release. The native folder is resource-closed. build_generator.py
creates the standalone ordinary generator and --check detects drift. No catalog,
shared runtime, approval, immutable parent or original gold data was changed.
