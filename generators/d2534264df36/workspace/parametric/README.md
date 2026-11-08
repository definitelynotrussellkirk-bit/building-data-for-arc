# Ring-completion cross-stop family

This task-local family preserves the exact canonical default and adds two
input-dependent composed settings:

- `complete_only`: exact canonical `d2534264df36` Racket source.
- `nearest_hit`: complete every source ring, then select the nearest nonzero
  completed side on the north hub ray and use its row/color to fill blank cells
  of the interior orthogonal cross.
- `farthest_hit`: the same composition, selecting the farthest completed side.

The input grammar deliberately repairs the retained `paired_only` teaching hole.
The two minimum demonstrations are both 19×19 and each includes a singleton-row,
singleton-column, and paired side witness. Thus a learner must infer that each
non-corner source acts independently rather than treating a matched pair as the
activation cue. Queries include 23×23, 27×27, 30×30, and a second 19×19 case.
Inputs are identical across settings for the same seed/counts.

The sequential dependency is substantive. Step A completes rings. Its ordered
north-ray hits are the intermediate. Step B cannot choose either cross extent or
color until that intermediate exists. `evidence_tools.py witness` constructs a
protected-Racket skip-A counterfactual; the raw source has a blank hub ray, so
skipping completion changes the final output.

Supported requests are 2–6 demonstrations and 4–8 queries. Public challenge
projection uses the repository helper, which retains demonstration outputs and
query inputs while hiding the setting, reference program, and query answers.

Focused checks:

```bash
python3 review.py run python3 -m pytest \
  generators/d2534264df36/tests/test_parametric_cross_stop.py -q
```

After native qualification, compact evidence can be rebuilt with:

```bash
python3 generators/d2534264df36/workspace/parametric/evidence_tools.py audit \
  --execution ../checks/d2534264df36/qualification/execution.json \
  --out ../checks/d2534264df36/self-audit.json
python3 generators/d2534264df36/workspace/parametric/evidence_tools.py witness \
  --qualification ../checks/d2534264df36/qualification/qualification.json \
  --execution ../checks/d2534264df36/qualification/execution.json \
  --out ../checks/d2534264df36/sequential-dependency.json \
  --replay-out ../checks/d2534264df36/dependency-build-replay.json
```

This is reviewer-ready source only. Owner integration, fresh qualification,
protected witness replay, and native acceptance remain required; training is not
admitted by this prototype.
