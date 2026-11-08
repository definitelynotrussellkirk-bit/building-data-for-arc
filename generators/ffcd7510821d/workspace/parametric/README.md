# Direction-parametric marker-count rotation

This native-ready prototype preserves the reviewed `ffcd7510821d` grammar and
exact canonical default. The private episode parameter is `direction`:

- `clockwise` is the byte-for-byte canonical Racket program.
- `counterclockwise` counts the same row-0 maroon markers, clears only those
  markers, crops the same complete scene, and reverses the count-selected turn.

The causal chain is explicit: **A** counts row-0 markers and constructs the clean
cropped object; the intermediate is `(turns mod 4, cropped object)`; **B** cannot
choose or execute the direction-specific rotation without that intermediate.
Protected-Racket evidence uses a fixed wrong-turn program on the same input to
show that corrupting the marker-count intermediate changes the final output.

Inputs are setting-independent. Episodes support 2–6 demonstrations and exactly
four distinct queries. Demonstration prefixes begin with marker counts 1 and 3,
so either direction is distinguishable with two examples. Queries include a
substantive 30×30 four-quadrant scene whose four colored connected blobs touch
the body boundaries. Public projection contains demonstration labels and masked
query inputs only.

From the packet root:

```bash
python3 review.py task-tests ffcd7510821d --phase after \
  --out ../checks/ffcd7510821d-tests-final
python3 review.py run python3 -m arcpuzzles parametric manifest ffcd7510821d \
  --evidence generators/ffcd7510821d/workspace/parametric/evidence/current \
  --include generators/ffcd7510821d/tests/test_parametric_direction.py \
  --reported-checks 'Focused staged tests, protected Racket parity, finite shortcut audit, public masking, causal wrong-intermediate witness, and 30x30 stress.'
python3 review.py run python3 -m arcpuzzles parametric qualify ffcd7510821d \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/ffcd7510821d/qualification --summary
python3 review.py run python3 \
  generators/ffcd7510821d/workspace/parametric/build_evidence.py \
  --qualification ../checks/ffcd7510821d/qualification/qualification.json \
  --out ../checks/ffcd7510821d/review-evidence
python3 WORK/check_public_exports.py \
  WORK/checks/ffcd7510821d/review-evidence/public --demos 3 --queries 4
```

Reviewer qualification is not owner acceptance. The owner must integrate and
replay these exact bytes before this family becomes live; training admission
remains false.
