# Proposed final assembled episode export gate

This stdlib prototype provides **one additional automated data-quality gate**:
stop final export if an explicitly declared input-output rival fits every final
demonstration but disagrees with a labelled held-out query. It checks the actual
assembled episode immediately before reference labels are removed for public
export. That placement catches an assembler dropping, replacing, or reordering
the informative witness after a generator's schedule census has passed.

The gate is proposed only; no production export hook is changed. It imports no
main generator or reference runtime. It cannot establish reference label
correctness, general identifiability, or measured Qwen3.5-9B improvement.

## Use

Add this directory to your module search path and call:

```python
from final_episode_gate import screen_episode

result = screen_episode(
    final_labelled_episode,
    rivals={"only_three_by_three": candidate_shortcut},
    rationale={
        "only_three_by_three": (
            "This export teaches extended full-grid rotation; a hypothesis "
            "that rotates only 3x3 inputs is a relevant shortcut."
        )
    },
    query_rotation=False,
)
if not result["allowed"]:
    raise ValueError(result)
# Only now strip private labels and emit the final public challenge.
```

Malformed inputs or an absent allowlist/rationale raise `ValueError`; exporters
must also stop on these exceptions. Candidate callables receive independent
input copies. Exceptions, observed input mutation, invalid output grids, or
observed nondeterminism return `allowed=False` with exact example indices.

Rivals must be **explicitly selected for the intended export domain**. A 3x3-only
rotation rival is relevant when the export deliberately teaches an extended
rotation domain. Automatically applying a full-rotation-vs-2x2 shortcut screen to
an intentionally restricted 2x2 domain could reject a perfectly adequate lesson.
The caller's rationale makes this domain decision reviewable; the prototype does
not infer a correct allowlist from the canonical examples alone.

## Indices and query rotation

Indices are zero-based flattened positions: all final `train` examples followed
by all final `test` examples. The returned `examples` list maps each to its
original split/index. Each check reports demo/query indices, surviving rival
names, matching demonstration indices, disagreeing query indices, violations,
and evaluation errors.

Default behavior screens all currently supplied test queries against the actual
train examples. It does not rotate demonstrations into queries. Only explicit
`query_rotation=True` tests every final example as the sole held-out query with
all other labelled examples as demonstrations. This is leave-one-out checking;
it is not a statement about arbitrary subset sizes or alternative assemblers.

A passing result has `reference_labels_verified=False`. The export pipeline must
independently execute/check the authoritative Racket program. The Python rival
functions are competing hypotheses only and never generate authoritative labels.

## Run tests and small reference-backed evidence

From the outer packet directory:

```bash
python3 review.py run python3 generators/864eaaac6503/tests/test_final_episode_export_gate.py
python3 review.py run python3 generators/864eaaac6503/workspace/export_gate/materialize_evidence.py --out ../checks/export-gate/witnesses
```

Use a new output directory for each materialization. Evidence is source-bound and
existing directories are not overwritten. The materializer loads the selected
main generator only inside its explicit `main()` authoring path, snapshots those
exact bytes, and generates two distinct extended inputs at seed 731, sample
indices 1 and 3, easy difficulty. A single provided Racket bridge labels both;
no full runtime is staged or copied. It uses exact `(rule! rotate-ccw)` through
the narrow bare-callable adapter `(define (rule! f) f)`. General REPL syntax is
outside that adapter's scope.

`checks/export-gate/witnesses/evidence.json` retains two constructed diagnostics:

| Diagnostic | Final demonstrations | Final query | Current partition | All four query rotations |
|---|---|---|---|---|
| `teaching_negative` | Three original canonical 3x3 pairs | Second extended pair | Reject | Reject |
| `teaching_positive` | Two original canonical pairs plus first extended pair | Distinct second extended pair | Pass | All pass |

The negative intentionally models final assembly losing the first extended
witness and substituting a third canonical pair. Its rival rotates 3x3 inputs and
returns identity otherwise. The rival fits all three canonical demos, then
disagrees at flattened query index 3. The positive supplies two distinct extended
reference-labelled pairs; holding either out still leaves an informative demo.
Both artifacts are explicitly labelled teaching diagnostics, not accidental
solve attempts or model-visible challenges.

## Retained verification

Eight focused tests cover ambiguous final assembly, witness replacement, explicit
query rotation, preservation by two informative examples, multiple current query
positions, fail-closed rival errors/mutation, missing metadata/labels, and the
separation between finite-rival screening and reference-label validation.
Expected preimplementation failures, passing tests, actual reference execution,
commands/exit codes, source hashes, snapshots, outputs, and verdicts are retained
under `WORK/checks/export-gate/`. The tests' small literal labels are fixtures;
the materialized extended witness labels are independently executed by Racket.

This remains a finite caller-declared-rival screen. It does not certify all
hypotheses, prove a generator schedule, integrate a production exporter, admit
training data, or measure downstream model gains.
