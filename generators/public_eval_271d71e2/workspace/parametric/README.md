# Fuel-limited sliding family

`motion_policy=all_moves` is byte-identical to the general public reference.
`longest_move` executes those same motions and highlights the black border of
the uniquely farthest-traveling box cyan. A computes fuel-capped motion toward
fixed rails; the intermediate associates each moved box with its actual distance;
B ranks those distances and paints the corresponding translated border.

The native folder is relocatable and contains all resources. The sampler uses
independent geometry and presentation RNG streams, supports demos 2..6 and
queries 1..4, shuffles the complete four-query bank before taking a prefix, and
returns only demonstrations plus the selected query from `public_turn`.
Never provide the episode's `private` field, directory listing, programs, answers
or future inputs to the model. Source schedule index nine is a substantive 30x30
scene, not necessarily the fourth presented query.

Geometry: three/four complete black frames in separated lanes; magenta background,
maroon attached and fixed rails, gray/orange interiors. Quarter turns give all
four directions. Boxes can stop at a rail or exhaust fuel, with previously spent
fuel and zero-fuel stationary cases. Original parent labels include broader
layouts and were checked separately. No claim of unrestricted ARC coverage.
Two demos are constructed to reject the alternate declared setting and eight
explicit selector rivals: rail gap, starting fuel, remaining fuel, final orange
count, rectangle size, first, last, and shortest actual travel. Finite testing is
not universal identifiability or learning benefit.

Run from the packet outer directory with its configured protected runtime:

    python3 review.py run python3 generators/public_eval_271d71e2/workspace/parametric/audit.py --out ../checks/public_eval_271d71e2/audit-new --seeds 20

Output must be new. Audit counts include repeated prefix requests, and report
separately the number of distinct scene inputs. The public writer sorts exact
visible SHA-256 IDs; controller metadata is separate. Racket programs all execute;
parse/runtime errors cannot count as elimination evidence. Audit is reviewer
work, not owner registration, native acceptance or training admission.
