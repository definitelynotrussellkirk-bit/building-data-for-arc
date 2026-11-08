# Working notes: db95939a5dd0

## Final review state

- Final generator SHA-256: `7bf7cef69b27cf6507efc9239c4575a0b940d867eb0462e622cc0450bcf825b1`.
- Canonical `RULE_HASH`: `a742202e03fb` (unchanged).
- Focused tests: 94 passed.
- Final battery: 12/12 stages green with required query rotations and period enumeration.
- Production lesson policy: 3 demos + 1 query, ordered period-2 support schedule.
- Production semantic result: 12/12 identifiable; rotations 48/48 identifiable.
- Larger source-bound census: 300 lessons / 1,200 rotations, zero ambiguity, warnings, or errors.

## Design decisions

The key rival is a global direction assignment per color. It survives whenever a reused color keeps the same component role. The schedule therefore forces the shared canonical archetype on even default sample indices, where one color is bottom in one compound and top in another. Period 2 was selected because it leaves a witness in the demonstrations no matter which of the four pairs becomes the query.

Explicit overrides skip the teaching schedule. The rival is a lesson competitor, not a canonical shortcut, because it does not fit every canonical pair.

## Authority

Two selected `target_code` records were synchronized to canonical exact text. Archival `raw_code` remained unchanged. The normalized rule and execution behavior did not change.

## Parametric prototype

`workspace/parametric/` proposes a separate `shift_distance ∈ {1,2}` episode family. It is not part of the production repair or catalog approval. Evidence lives at `checks/parametric/manifest.json`.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.


## Current public prototype identifiers

Public filenames now derive only from visible demonstrations and query inputs. The original source/report is retained under `workspace/parametric/evidence/reviewer-original/` and `reviewer-reported/`; the corrected Racket-backed export is in `owner-current/`. The twelve focused naming/writer checks passed across six tasks. This correction does not approve the prototype or rerun its full repair battery.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-93da419de9e7b758:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `531ac6912a31e8dd594a950efc3d8dfe963578663fa846b2aad493b2de3d0603`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve request/prior leakage, unknown/None contract and global-direction teaching findings on old531ac691... source:3.2.0 validates before RNG, treats None as omission, rejects unknowns and teaches opposite-role color reuse; reviewer94 tests,15210 override draws0 findings and300 lessons/1200 rotations pass. Current source 7bf7cef69b27cf6507efc9239c4575a0b940d867eb0462e622cc0450bcf825b1. Evidence remains reviewer-reported and finite; no universal or training-admission claim.

### Assessment or prior finding

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

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-93da419de9e7b758-v0001/audit_assets.json), manifest SHA-256 `71cd5e08c7bff23fce0eb546f884565cc4bcd51d5acfcd29d0046734d0f8e7d3`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `7bf7cef69b27cf6507efc9239c4575a0b940d867eb0462e622cc0450bcf825b1`.

# Decisions — db95939a5dd0

## D1 / R1 — fail closed before RNG construction

**Choice.** Validate exact request types, ranges, enum values, difficulty, and unknown keys before calling `gen_ctx`; normalize explicit `None` to omission.

**Why.** The baseline allowed request syntax to change RNG/provenance despite meaning “use the default,” and accepted malformed extension keys. That makes equivalent training recipes produce different examples and hides authoring mistakes.

**Alternatives rejected.** Preserving unknown keys for future extensions was rejected because undeclared controls silently enter provenance and can perturb deterministic draws. Treating `None` as an active value was rejected because the public axis contract already uses omission for default behavior.

**Probe.** `test_explicit_none_is_exactly_omission_equivalent`, invalid-scalar tests, and the final 15,210-draw override matrix.

**Limit.** A future API that intentionally assigns semantic meaning to `None` must declare a different contract rather than inherit this one.

## D2 / R1 — classify named diagnostic layouts as lawful

**Choice.** Keep the existing `DEGENERATE_TEXTURES` API but also declare `LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES`.

**Why.** All three layouts are positive, `self_check`-clean fixtures; the previous name caused the shared defect linter to treat them as expected negative mutations.

**Alternative rejected.** Renaming/removing the public texture values would create avoidable compatibility churn.

## D3 / R2 — teach local role, not color identity

**Choice.** Declare `one_direction_per_color` as the query-changing lesson competitor and `opposite_role_color_reuse` as its witness.

**Why.** The canonical rule assigns direction from each component's top/bottom role. When a reused color keeps the same role, a global color-direction learner is observationally equivalent. Reusing one color in opposite roles creates the smallest direct distinction.

**Probe.** The retained seed-2 lesson, 60/60 Racket witness claims, and the post-repair visible example with role reversal.

**Alternative rejected.** Merely increasing color or shape diversity does not force the distinction.

## D4 / R2 — period 2 instead of period 3

**Choice.** Set `LESSON_SCHEDULE_PERIOD=2` and force a witness-bearing archetype on one residue.

**Why.** A lesson contains four pairs (three demonstrations and one query). A period-3 schedule can place only one guaranteed witness in a four-pair window; if that pair becomes the query, the demos remain ambiguous. Period 2 guarantees two witness pairs in every window, so any cyclic holdout leaves at least one witness.

**Cost.** Half of default draws use the shared canonical archetype rather than one third. Odd indices retain the generalized distribution, and active overrides bypass the schedule.

**Alternatives rejected.** Period 4 with three forced residues would reduce entropy further. A random witness probability gives no per-lesson guarantee.

## D5 / R2 — do not mislabel the rival as a canonical shortcut

**Choice.** Keep `one_direction_per_color` in `SEMANTIC_RIVALS` / `LESSON_COMPETITORS`, not `CANONICAL_SHORTCUTS`.

**Why.** `CANONICAL_SHORTCUTS` asserts a candidate fits every usable canonical pair. Retained evidence shows this rival is already refuted by a canonical pair.

**Failure mode avoided.** A false shortcut declaration would make the semantic checker reject valid evidence or report a dishonest canonical ambiguity.

## D6 / R3 — synchronize selected `target_code` only

**Choice.** Apply the reviewed exact-text proposal to two selected `/racket_target/target_code` pointers; preserve `raw_code` byte-for-byte.

**Why.** The selected execution authority had formatting-only drift from canonical exact text. Archival `raw_code` is provenance, not the selected executable record.

**Probe.** Token comparison before apply, then `authority_sync` and `rule_smoke` after apply.

**Alternative rejected.** Rewriting archival fields would destroy evidence without changing behavior.

## D7 / R2 — split authority proof from large census

**Choice.** Use the shared Racket-backed semantic gate for 12 lessons / 48 rotations and a source-bound Python-mirror tool for the larger 300-lesson / 1,200-rotation census.

**Why.** The shared 1,200-call Racket census exceeded 30 minutes. The smaller gate independently establishes canonical Racket parity and validates the declared rival; the larger tool then tests schedule coverage cheaply against the same selected source.

**Cost.** Not every one of the 1,200 large-census labels is separately executed by Racket. This limitation is explicit in the census report.

**Alternative rejected.** Calling a fresh Racket runtime per pair was prohibitively slow and added no new structural coverage.

## D8 / P1 — one bounded parametric axis

**Choice.** Prototype `shift_distance ∈ {1,2}`, fixed once per episode.

**Why.** It is a meaningful rule parameter, keeps all other semantics unchanged, and can be identified from three demonstrations with clearance-aware inputs. Distance 1 exactly reproduces canonical authority.

**Alternatives rejected.** Varying direction assignment or component grouping would create a different concept family, not a controlled parameter. More than two distances would enlarge the input-clearance envelope and lesson burden without evidence of added value.

**Execution choice.** Reuse one pure Racket bridge per distance. Repeated process startup reproducibly hung on the fifteenth launch; persistent bridges completed 18 labels and every result was checked against an independent Python mirror.

**Limit.** Prototype only; no production/catalog approval is implied.

## D9 — solve-lane isolation

The blind solve occurred before repair/source inspection. The post-repair solve began only after the final generator hash was fixed and consulted visible examples only; earlier rule exposure was declared. Hidden query labels remained unavailable in both lanes.

## D10 — audit targets remain unchanged

The audit assignment was findings-only. `cf60523d1603` and `59ccf6f5cc65` were probed and reported but not patched, so their exact assigned hashes remain intact.
