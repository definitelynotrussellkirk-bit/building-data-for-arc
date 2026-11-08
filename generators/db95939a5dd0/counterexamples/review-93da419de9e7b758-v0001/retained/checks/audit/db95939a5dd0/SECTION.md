## db95939a5dd0

**Reproduced production teaching defect and the existing override defect;
no sampled label mismatch.** This is a findings-only audit. The target source,
rule and shared code were not edited.

Generator version `3.1.0`, source SHA-256
`531ac6912a31e8dd594a950efc3d8dfe963578663fa846b2aad493b2de3d0603`.
Executed canonical rule hash `a742202e03fb`; exact Racket text SHA-256
`bf377d1387cb0c955f8ab424dcbf673ddb8e25c1793b4a9cab78f09bf519fb08`.
Every count below is bound to these source/rule bytes in
`checks/audit/db95939a5dd0/run-v1/audit.json` and
`checks/audit/db95939a5dd0/run-v1/racket-applied.json`.

### A-db-1 — One color's displacement is not taught as compound-dependent

The intended rule moves each compound's upper color left and its lower color
right. A plausible rival keeps **one displacement per color for the whole
grid**: inspect compounds in row-major order, assign each color the direction
required by its first compound, and reuse that direction when the color occurs
again. The rival agrees with the intended rule whenever a reused color retains
the same role. It fails when one color is lower in one compound and upper in
another. Its executable implementation is `one_direction_per_color` in
`checks/audit/db95939a5dd0/probe.py`.

The rival fits all **3/3 original variant-0 canonical demonstrations**. It is
refuted by that variant's canonical test and by the duplicate of that same pair
used as a demonstration in the other retained variant. Across the full retained
corpus it fits **6/8 pair records**, representing **3/4 unique input/output
pairs**; it is not claimed to fit every canonical record.

An actual production episode reproduces the teaching failure:

```python
Catalog(root=ROOT).generate(
    "db95939a5dd0", seed=2, count=1, difficulty="medium",
    n_train=3, n_test=1, sample_index=0,
    allow_unapproved=True, timeout=120,
)
```

The selected public materializer accepted sample indices **[0,1,2,3]**, with
**0 rejected pairs** and no overrides. The rival fits **3/3 demonstrations**
but fails the **1/1 query**. The complete native episode and source provenance
are retained at `checks/audit/db95939a5dd0/run-v1/native-episode.json`.
Its query input SHA-256 is
`b41b83f7f4cada0f83042d30d8af2dcefb8780c216f0a01ad0ccde0f14ca37fd`.
The query is 14 rows × 13 columns, and its output has the same dimensions.

The query is input index **39** of the separately retained public Racket apply.
At zero-based output cells **(10,5), (10,6), (10,9), (10,10)**, actual Racket
values are **[3,3,2,2]** while the rival gives **[2,2,3,3]**. Complete input,
actual output and rival output are retained in `audit.json` under
`rival_witnesses`. All four episode inputs pass the target's `self_check`,
and native generation labels match the independent public Racket apply.

A smaller lawful witness is also retained at reference input index **35**:
a 12×12 background-1 grid containing color 2 at row 2, columns 3–4; color 3 at
row 3, columns 3–4; color 3 at row 7, columns 7–8; and color 4 at row 8,
columns 7–8. Coordinates are zero-based and all unlisted cells are 1. Color 3
must move right in the first compound and left in the second. The rival instead
moves it right in both, causing four wrong output cells in row 7. This manual
witness passes `self_check` and actual Racket execution; its exact emission is
not claimed. The native seed-2 query establishes generated support separately.

The source explains why the distinguishing event can be missed: generalized
two-compound draws share a lower color with another lower role, while the
canonical shared-color archetype supplies the opposite-role reuse. That
archetype is selected probabilistically; no teaching schedule or executable
lesson rival contract guarantees its appearance among demonstrations. Native
provenance explicitly reports `lesson_check.status="not_declared"`.

Suggested owner repair: declare the global per-color rival and a witness for
opposite-role color reuse, then ensure demonstrations refute it before a query
requires that distinction. Retain the present per-compound Racket rule. Merely
increasing the rare archetype probability does not guarantee a teachable lesson.

The candidate search examined **three source-generated four-pair candidates**
(seeds 0–2, indices 0–3, medium) and stopped at the first independent-Python
mirror candidate. Only the selected seed-2 episode was materialized through
the public production API. The measured production failure is therefore
**1/1 deliberately selected materialized episode**, not an estimated failure
rate. Broader lesson frequency and query-rotation policy were not assessed.

### A-db-2 — Unknown controls and explicit omission change the prior

The existing unresolved unknown-key finding remains reproducible. For seeds
**0–2**, index **0**, in easy, medium and hard (**9 paired coordinates**),
`generate(..., typo_axis=123)` accepts the undeclared key in **9/9 calls**.
The output changes versus the identical coordinate without that key in **3/9**.
For example, `generate(2,0,difficulty="easy",typo_axis=123)` returns a different
lawful grid rather than rejecting the unknown axis. Its base/unknown records
are reference input indices **14/15**.

The recognized omission `grid_h=None` also changes the output in **3/9** paired
coordinates; all **9/9** such calls are accepted. The first changed example is
`generate(2,0,difficulty="easy",grid_h=None)`, reference input index **16**.
GenCtx treats `None` as omitted, but this source selects its canonical-archetype
branch only under `if not overrides`. Both an ignored unknown key and a known
key set to `None` make that raw mapping nonempty, disabling the prior.

All **27/27** base/unknown/None draw records in this bounded comparison pass
`self_check` and match actual Racket. This is an API/distribution defect, not a
bad-label claim. `control_records` in the retained `audit.json` contains every
coordinate, acceptance result, changed-grid result and reference input index.

The prior leads were the unresolved audit entries from
`review-0a0a7f531c095e30:v0001`, `review-b0bc4d5df8dac99b:v0001`, and
`review-ef42e4cc11a0332d:v0001`. Their historical counts were not reused. The
unknown-key result is an independent confirmation; the explicit-None case
shows a related failure of the shared omission convention.

Suggested owner repair: reject keys outside `AXES`, then decide archetype-prior
eligibility from recognized non-None overrides. No fix is included in this
audit-only return.

### Commands, checked behavior and limits

Run from `WORK/`; the wrapper payload executes from `WORK/repo/`:

```bash
python3 run_with_racket.py /workspace/scratch/2f38d6086605/arc_review/WORK/.venv/bin/python ../checks/audit/db95939a5dd0/probe.py --out ../checks/audit/db95939a5dd0/run-v1
```

The probe exited **1**, deliberately reporting reproduced audit findings;
its report records `completed=true` and no execution failure. It preserves
the failure evidence rather than treating these contracts as passing.
Use a new output directory to rerun. The exact interpreter, command, cwd,
source/probe hashes, native generation options, Racket command and return code
are recorded in `audit.json`.

The probe invokes public `python -m arcpuzzles apply db95939a5dd0` with
`--check-generator-domain --timeout 120`; this Racket apply exited **0**.
Retained files are `checks/audit/db95939a5dd0/run-v1/racket-inputs.json`,
`checks/audit/db95939a5dd0/run-v1/racket-applied.json`, and
`checks/audit/db95939a5dd0/run-v1/racket-apply.log`.

All **40/40 reference input records** were accepted, self-check-clean and
matched an independently implemented per-compound transform. They contain
**17 unique grids**: eight canonical records, 27 control records, one manual
witness, and four native episode records. All **8/8 canonical labels** match
actual Racket, representing only **four unique input/output pairs** across
two retained variants. No task-local test directory or lesson rivals were
declared in the inspected source. No full battery, general frequency census,
or unrelated source review was run. Other ambiguity remains unknown.
