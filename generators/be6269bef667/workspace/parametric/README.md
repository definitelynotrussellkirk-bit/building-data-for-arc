# Native parametric family: be6269bef667

`weighting=unit` is the exact canonical program: every emitter contributes one
along its ray until a color-5 wall or the boundary.

`weighting=plurality_double` first counts direction-coded emitters and binds the
unique plurality direction. It then traces every ray, adding two for emitters in
that selected direction and one for all other directions. Step B therefore
cannot choose ray weights until step A supplies the input-dependent direction.

Inputs are matched across settings. The minimum two demonstrations use different
plurality directions. Every scene contains all four direction symbols, disjoint
long horizontal and vertical ray lines, overlap, selected-direction wall stops,
and distractor walls. Four queries cover transfer, larger geometry, a substantive
30×30 cross-hatch, and a wide boundary scene. `public_turn()` reveals one query
input at a time and keeps settings, programs, answers, and future queries private.

From the packet's outer directory:

```sh
python3 review.py run python3 -m pytest -q \
  generators/be6269bef667/tests/test_parametric_plurality_weight.py
python3 review.py run python3 \
  generators/be6269bef667/workspace/parametric/audit.py \
  --out generators/be6269bef667/workspace/parametric/evidence/current/self-audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify be6269bef667 \
  --demos 3 --queries 4 --out ../checks/be6269bef667/qualification --summary
```

These are reviewer-side source-bound checks only. Owner acceptance and training
admission remain separate.
