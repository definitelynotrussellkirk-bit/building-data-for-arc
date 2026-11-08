## 0d03b427c121

**Findings-only audit: two reproduced findings; target source, rules and tests unchanged.**
Audited `repo/generators/0d03b427c121/generator.py`, version `3.0.1`, SHA-256
`838e2b3d5f65bd60b99386f95fc9938a6036c9409aa7f3ae4bfc7c33f0b5f151`.
Selected canonical Racket rule identity: `171521fb1804`.
Exact source/rule bindings, inputs, outputs and command records are retained in
`checks/audit/0d03b427c121/assessment.json`,
`checks/audit/0d03b427c121/racket.json`, and
`checks/audit/0d03b427c121/commands.json`.

| Finding | Classification | Reproducer and result |
|---|---|---|
| AUD-0d03-V1 | Reproduced validator defect | `seed=0, sample_index=0, difficulty="medium", texture="no_match"`: validator accepts, selected Racket rule fails because no matching object exists. |
| AUD-0d03-L1 | Reproduced lesson shortcut ambiguity | Real export at `seed=9, sample_index=0, difficulty="medium", train=3, test=1`: an area-only rival fits all demonstrations and all canonical pairs but predicts a different query output. |

### AUD-0d03-V1 — validator accepts an undefined reference input

The advertised invariant requires exactly one body component whose area and
boundary-cell count match the two marker counts. `self_check` checks only marker
presence and the existence of body cells. The generator's declared `no_match`
texture creates a 4-by-16 grid with eight color-1 and eight color-2 header markers,
but only a two-cell body object. Its `self_check` returns `[]`.

The public `arcpuzzles apply --check-generator-domain` receipt independently
records `generator_domain.status="valid"`, then `valid_output=false`, with a
Racket `hash-ref` contract error on `#f`. This is a declared adversarial texture,
**outside the intended ordinary unique-match domain**, that the validator fails
to reject. It is not evidence that the ordinary default sampler emits this grid.
The sibling `multiple_matches` texture is also accepted despite two matching
objects. Both objects have the same crop, so that secondary witness establishes
the missing uniqueness check, not a wrong or ambiguous output.

Minimal retained witness:
`checks/audit/0d03b427c121/counterexample-validator.json`.
The full Racket batch and case-index mapping are
`checks/audit/0d03b427c121/racket.json` and
`checks/audit/0d03b427c121/probe.json`.
Suggested repair: validate body components and require exactly one area/boundary
match before declaring an input valid.

### AUD-0d03-L1 — three demonstrations do not teach the boundary test

The retained rival reads only the number of color-1 header cells, selects the
first body component of that area, and crops/recolors it to 8. It ignores every
color-2 marker. This rival matches **3/3 usable canonical pairs**.

The public generation command successfully materialized one ordered lesson with
**3 demonstrations and 1 final query**, seed 9, medium difficulty. Its actual
accepted sample indices are `[0,1,2,3]`, with no rejected draws. The rival agrees
with the selected Racket outputs on **3/3 demonstrations**, then disagrees on the
**1/1 query**. The query specifies area 5 and boundary count 4. Two objects have
area 5, and only the correct cross has boundary count 4; the area-only rival
chooses the other shape. The query passes `self_check` and the reference returns
a valid output. The exported receipt reports `lesson_check.status="not_declared"`.

**Production verdict:** ambiguity reproduced in 1/1 materialized lesson against
this rival. **Query-rotation diagnostic:** ambiguity in 1/4 holdouts of these same
four Racket-labeled pairs; the other holdouts expose the original distinguishing
query as a demonstration and reject this rival. This is finite evidence for one
explicit rival, not a claim about all hypotheses or arbitrary seeds.

The exact export is `checks/audit/0d03b427c121/lesson.jsonl`; the source-bound
query, rival output, reference output, all pair comparisons and rotation details
are in `checks/audit/0d03b427c121/counterexample-lesson.json`.
Suggested repair: declare the area-only competitor and ensure a same-area,
different-boundary demonstration appears in each exported lesson before a query
requiring the boundary test. Such a repair also needs an explicit ordering policy.

### Scope and retained checks

Read the selected implementation, summary, current notes, associated-note file,
and exact canonical row. No current review index or task-local tests exist in
this target's home; no target-ID test was found in the shared/public test trees.
The reusable probe is `checks/audit/0d03b427c121/probe.py`; the independent
retained-output assessment is `checks/audit/0d03b427c121/assess.py`.

An exploratory Python scan covered seeds 0–99, indices 0–3, in easy/medium/hard:
1,200/1,200 generated inputs passed the validator and had one feature match under
the probe's component model. The area-only rival agreed on 1,171/1,200 and left
5/300 grouped candidate lessons ambiguous. These are **Python exploration
counts**, not a Racket census or 300 verified production lessons. Only the one
reported lesson was subsequently materialized through the real export path.

The focused Racket batch checked ten exact inputs: eight valid outputs and two
errors (the expected rejected `no_markers` control and the incorrectly accepted
`no_match` witness). All seven ordinary generated control/lesson inputs produced
valid outputs matching the exploratory model. The apply command therefore exited
1, retained honestly in `commands.json`; generation and evidence assessment
exited 0. No full battery, all-seed correctness claim, target repair or approval
is made. The original source is retained at
`checks/audit/0d03b427c121/generator.snapshot.py`, and the exact canonical row at
`checks/audit/0d03b427c121/canonical-row.json`.
