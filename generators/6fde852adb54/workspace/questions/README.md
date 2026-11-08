# Proposed question probe and finite-rival lesson gate

This workspace answers the two supplied review questions for `6fde852adb54`.
It does not replace `generator.py`, change the canonical rule, hook into normal
production generation, or grant training approval.

`question_gate.py` provides:

- `rival_predict(grid)`: uses the longest contiguous vertical obstacle run when
  choosing a body slice's destination in a near-floor component. The canonical
  rule instead uses the total obstacle count per column.
- `make_witness(...)` and `sample_witness(seed, sample_index)`: lawful gapped
  obstacle components which separate those rules. Supported dimensions are
  14 through 24; palettes have four distinct ARC colors. This sampler is a
  proposed witness source, separate from current `generate()`.
- `lesson_gate(demos, query, canonical_predict=...)`: verifies demo labels,
  then rejects only when this declared rival fits every demo and changes the
  query answer. It reads query input only. The caller must supply the pinned
  Racket predictor or a cache already verified by that exact rule.

## Run the retained probe

From the packet's `WORK/` directory, using its Racket setup/wrapper:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 run_with_racket.py python3   generators/6fde852adb54/workspace/questions/probe_questions.py   --out ../checks/questions/probe.json
```

This executes Racket on the official examples, all eight public geometries,
one generated control, the exact 14×14 counterexample, and four distinct
proposed sampler queries. It writes the full counterexample with both outputs,
six differing coordinates, source/rule hashes, and three reusable lesson files.
No census or model inference is performed. Add `--expected-generator-sha HASH`
to reject source drift before the run; sources are also checked after execution.

## Check another lesson

The input is a JSON object with a nonempty `demos` array of `input`/`output`
pairs and a single `query` object containing `input`. A query `output`, if
present, is ignored. There is no hidden-label requirement.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 run_with_racket.py python3   generators/6fde852adb54/workspace/questions/probe_questions.py   --lesson ../checks/questions/ambiguous_lesson.json   --out ../checks/questions/my_gate_report.json
```

Exit 2 is the expected rejection for this ambiguous lesson. Replace the lesson
with `repaired_lesson.json` or `answer_equivalent_lesson.json` to obtain exit 0.
The latter deliberately permits a surviving rival whose query answer is equal.
Malformed data and reference errors cannot produce a passing report. A failed
reference is reported as `reference_error`; invalid data as `invalid`.

The cheap local regression suite uses the Python mirror, without claiming new
Racket verification. Run it from `WORK/repo/`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3   generators/6fde852adb54/tests/test_question_gate.py
```

## Scope and false positives

This is one finite, named hypothesis test, not proof of universal
identifiability. The current production generator does not separate this rival:
its eight public geometries agree and its generalized active bar/L components
have contiguous columns. The workspace sampler supplies the missing cases;
production sampling is unchanged.

For a self-contained episode, add a discriminating demonstration before asking
for a query which requires that distinction. The gate may be too strict for a
training protocol that intentionally relies on prior episodes or an explicitly
provided rule. A rival used outside its lawful domain can also cause false
rejections. Keep the scene validator, declared hypothesis scope, and actual
query comparison; do not reject merely because a rival survives the demos.
No Qwen3.5-9B inference, training, or measured performance improvement is claimed.
