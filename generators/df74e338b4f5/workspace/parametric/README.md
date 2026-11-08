# Native parametric family: recoloring scope

The canonical `all_markers` setting is the selected rule byte-for-byte: detect
all hollow color-9 rectangles and recolor every marker by strict containment
depth.

The `rarest_positive_depth` setting retains that depth inference as step A,
builds the positive-depth histogram, selects the least frequent positive class
(ties choose the deepest), and then recolors only markers in that class. This is
a real causal dependency: step B cannot know which cells are eligible before
step A produces the input-dependent histogram and selected depth.

All settings use matched inputs. Episodes support 2–6 demonstrations and 1–4
private queries; the four-query curriculum ends with substantive 30×30 nested
frames. Public projections contain demonstration input/output pairs and query
inputs only. Settings, programs, future query inputs, and query outputs remain
private.

## Reusable bounded audit

From `WORK/repo/`, create the finite learnability report and the matching
protected-worker request:

```bash
python3 generators/df74e338b4f5/workspace/parametric/audit.py \
  --seed 0 --seed 17 --seed 97 \
  --demos 2 --demos 3 --demos 6 --queries 4 \
  --out generators/df74e338b4f5/workspace/parametric/evidence/current/authoring_audit.json \
  --worker-request ../checks/df74e338b4f5/authoring-worker-request.json
```

Then, from the outer packet directory, execute every label through protected
Racket:

```bash
python3 review.py run --receipt checks/df74e338b4f5/authoring-racket-command.json \
  python3 -m arcpuzzles.parametric_worker \
  ../checks/df74e338b4f5/authoring-worker-request.json \
  > WORK/checks/df74e338b4f5/authoring-racket.json
```

The audit covers only its declared finite rival set. It does not accept the
variant family or admit it to training.
