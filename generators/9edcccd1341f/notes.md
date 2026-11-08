# Working notes: 9edcccd1341f

## Intended rule

Preserve the nonzero key row. Inside the framed scene, select the unique
most-frequent non-border color; recolor the outer frame with that winner; draw a
hollow winner-colored frame around all winner cells' bounding box; clear the
remaining interior.

## Domain assumptions

- Grid height and width are 10–14.
- Row 0 is a nonzero key containing all active colors.
- Rows 1 and `h-1` and columns 0 and `w-1` form one uniform nonzero frame.
- The interior has at least two non-frame colors and one unique frequency winner.
- The winner bounding box spans at least two rows and columns.
- Valid public calls use literal integer `seed`/`sample_index`, nonnegative
  `sample_index`, and known difficulty/override keys.

## Review findings and repairs (2026-10-23)

- G9-1: strict defect lint found 33 accepted malformed scalar probes. Added exact
  integer checks for seed/index and a nonnegative index check.
- G9-2: all five prior `CANONICAL_SHORTCUTS` mismatched all 10 canonical pairs.
  Reversed the earlier registry choice: `CANONICAL_SHORTCUTS` is empty; the same
  five functions remain `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`.
- Kept `VERSION = "3.0.0"` because valid generation is unchanged. A 300-call
  easy/medium/hard parity probe found 0 baseline mismatches.
- No canonical Racket authority or rule hash changed.

## Verification

- Before battery: 10/12 green; defect lint and semantic declaration gate failed.
- Final battery: 12/12 green.
- Portable task tests: 34/34 passed.
- Lesson census: 300 lessons (3 demos + 1 query), 0 ambiguous; 1,200/1,200 cyclic
  query rotations identifiable.
- Profile support: canonical 10/10 accepted; 9/20 exact draws in each band.

## Proposed parametric prototype

`workspace/parametric/prototype.py` proposes episode-level
`frequency_target={most_frequent,least_frequent}`. The default materializes exact
canonical Racket (`d1ac07400a65`); the alternate changes only `pick-max` to
`pick-min`. Shared inputs have one unique maximum and one unique minimum and pass
production `self_check`. At seed 173, both four-demo episodes reject the opposite
setting and the queries disagree; default parity is 10/10 canonical pairs.

Status: proposed only. Limits: two settings, one retained episode per setting,
a strict-minimum two-candidate subset, and only the opposite setting as a rival.

## Open findings

No open blocker for the canonical repair. Broader parametric approval would need
a multi-seed/band census and a wider rival family.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.


## Current public prototype identifiers

Public filenames now derive only from visible demonstrations and query inputs. The original source/report is retained under `workspace/parametric/evidence/reviewer-original/` and `reviewer-reported/`; the corrected Racket-backed export is in `owner-current/`. Focused naming/writer checks passed; the source-bound owner receipt records the exact group count. This correction does not approve the prototype or rerun its full repair battery.
## Current reviewer considerations

Source SHA-256: `81702249939144274a4725186695d52ee99c28a4e12fd1bb1283537c429644eb`.

# Decisions for `9edcccd1341f`

## D1 — Repair the public scalar contract at the source

The baseline strict lint accepted 33 malformed scalar probes. I added validation
at the start of `generate`, before `gen_ctx` can normalize or accidentally accept
them. `seed` and `sample_index` must be literal Python integers; booleans are
rejected despite being `int` subclasses, and `sample_index` must be nonnegative.
I did not prohibit negative integer seeds because neither the declared API nor
the linter identified them as invalid.

## D2 — Reclassify, do not delete, the five wrong hypotheses

All five entries formerly copied into `CANONICAL_SHORTCUTS` mismatched all 10
canonical labels, so the declaration was false. I set `CANONICAL_SHORTCUTS` to an
empty typed dictionary and retained the exact same callables in
`SEMANTIC_RIVALS` and `LESSON_COMPETITORS`. This preserves their training-value
role while restoring the stronger meaning of “canonical shortcut.”

Reversal from the prior implementation: copying `SEMANTIC_RIVALS` into
`CANONICAL_SHORTCUTS` was convenient but semantically wrong. The strict gate's
instruction—partial/noncanonical heuristics belong in `LESSON_COMPETITORS`—is
now reflected directly in source.

## D3 — Keep `VERSION = "3.0.0"`

The repair changes rejection of invalid calls and metadata, not outputs for valid
calls. Bumping the version would feed a different version token into keyed
sampling and unnecessarily change the generated distribution. A source-bound
comparison of 300 valid calls found 0 differences, so the existing version is the
least disruptive and most honest choice.

## D4 — Do not edit canonical Racket authority

The selected Racket rule already matched the intended transformation and passed
execution parity. No canonical row, training/augmented rule record, rule hash, or
catalog pin was changed. Authority-set SHA-256 remains
`2af47aa3604bea7b59b91636b8ab6b20409ce26f9e6f905e525b5caaee5dccbc` and the
declared rule hash remains `d1ac07400a65`.

## D5 — Do not rewrite the production distribution

The existing generator already supports 10–14 rows and columns, all three named
difficulty bands, a 20.7% strict-canonical-like rate, 9/20 exact-profile draws per
band, and strong lesson witnesses. A new size branch or larger grid cap would add
risk without addressing either reproduced defect. The 300-call parity check also
shows the repair introduced no hidden distribution restriction.

## D6 — Use frequency extremum as the parametric rule dimension

The proposed parameter is `frequency_target` with values `most_frequent` and
`least_frequent`. It changes one meaningful reasoning choice while preserving
the key row, frame recoloring, selected-color bounding box, output shape, and
canonical default exactly.

Rejected alternatives:

- Changing only an output color would be cosmetic and teach less transferable
  reasoning.
- Switching hollow versus filled bounding boxes would alter more of the output
  grammar and overlap existing lesson rivals.
- Parameterizing frame retention would conflate two independent rule clauses.

The alternate frequency rule needs a unique minimum. The prototype therefore
uses a documented, setting-independent lawful subset: deterministic 12×12 draws
with one canonical winner and all distractors collapsed to one keyed distractor
color. Both candidate color sets must span two axes, the production `self_check`
must pass, and both settings receive identical inputs.

The extension remains proposed because evidence covers two settings, one retained
five-pair episode per setting at seed 173, and only the opposite setting as a
rival. That is enough for a runnable falsifiable prototype, not for approval.

## D7 — Preserve solve-lane truthfulness

The blind task was solved before generator inspection and records `earlier
exposure: no`. The assigned task's post-repair solve occurred after reviewing its
rule and records `earlier exposure: yes`. Neither solve consulted hidden labels or
reference source during solving.

## D8 — Audit without changing unassigned targets

For `306332da48b4`, I retained a concrete source-bound override defect instead of
editing the target. For `dafb4f819b93`, I retained the portable-test and missing
semantic-contract failures while separately probing core behavior. This keeps the
assigned patch limited to `9edcccd1341f`.

## D9 — Preserve failed and interrupted evidence

The baseline failures remain under `checks/before/`. One intermediate semantic
run was interrupted by the foreground execution limit and is retained as
`checks/intermediate-semantic-gate-command.log`; the complete final battery on
the same final source supersedes it. I did not rewrite or delete either record.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-1e5bbd7c27fe6e1c:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `5b6f00adc3e1565253dbd69d0f5b9f9b295559777a1ca4c60eaff92de32f62bf`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Auditedsource repo/generators/9edcccd1341f/generator.py SHA256 5b6f00adc3e1565253dbd69d0f5b9f9b295559777a1ca4c60eaff92de32f62bf. 9edcccd1341f

**Classification: reproduced defect (invalid recipe scalars accepted).** Source SHA-256 from the audit assignment: .

The generator validates overrides but does not strictly validate  or . Defect lint records 33 warnings: booleans, floats, numeric strings, and negative sample indices are accepted across easy/default/hard probes. This permits invalid recipes to alias or perturb valid random streams instead of failing loudly. The retained task suit. Reviewerreported boundedfinding;noautomaticpeerapproval. Exactevidence: `checks/.audit-9edcccd1341f-defect_lint.check.lock` `checks/.audit-9edcccd1341f-lint.check.lock` `checks/.audit-9edcccd1341f-task-tests.check.lock` `checks/audit-9edcccd1341f-defect_lint/checks/9edcccd1341f_audit_battery_summary.json` `checks/audit-9edcccd1341f-defect_lint/checks/9edcccd1341f_audit_commands.jsonl` `checks/audit-9edcccd1341f-defect_lint/checks/9edcccd1341f_audit_defect_lint.log` `checks/audit-9edcccd1341f-defect_lint/checks/9edcccd1341f_audit_defect_lint.receipt` `checks/audit-9edcccd1341f-defect_lint/progress.log` `checks/audit-9edcccd1341f-defect_lint/result.json` `checks/audit-9edcccd1341f-lint/checks/9edcccd1341f_audit_battery_summary.json` `checks/audit-9edcccd1341f-lint/checks/9edcccd1341f_audit_commands.jsonl` `checks/audit-9edcccd1341f-lint/checks/9edcccd1341f_audit_lint.log` `checks/audit-9edcccd1341f-lint/checks/9edcccd1341f_audit_lint.ok` `checks/audit-9edcccd1341f-lint/checks/9edcccd1341f_audit_lint.receipt` `checks/audit-9edcccd1341f-lint/progress.log` `checks/audit-9edcccd1341f-lint/result.json` `checks/audit-9edcccd1341f-task-tests/checks/task_tests.xml` `checks/audit-9edcccd1341f-task-tests/progress.log` `checks/audit-9edcccd1341f-task-tests/result.json` Currentselected81702249939144274a4725186695d52ee99c28a4e12fd1bb1283537c429644eb alreadyrejectsallspecifiedscalarcases; ownerfocused11regressions passed in generators/9edcccd1341f/tests/test_review_repairs.py. Thisold5b6sourcefindingisexplicitlyresolved forcurrentbytes,notrecordedasnewcurrentdefect.

### Assessment or prior finding

## 9edcccd1341f

**Classification: reproduced defect (invalid recipe scalars accepted).** Source SHA-256 from the audit assignment: `5b6f00adc3e1565253dbd69d0f5b9f9b295559777a1ca4c60eaff92de32f62bf`.

The generator validates overrides but does not strictly validate `seed` or `sample_index`. Defect lint records 33 warnings: booleans, floats, numeric strings, and negative sample indices are accepted across easy/default/hard probes. This permits invalid recipes to alias or perturb valid random streams instead of failing loudly. The retained task suite passes 7/7, showing this boundary is currently untested rather than intentional.

Reproducers from `WORK/`:

```sh
python3 run_with_racket.py python3 -m arcpuzzles check 9edcccd1341f --stage task_tests --timeout 180 --phase audit --out ../checks/audit-9edcccd1341f-task-tests
python3 run_with_racket.py python3 -m arcpuzzles check 9edcccd1341f --stage defect_lint --timeout 240 --phase audit --out ../checks/audit-9edcccd1341f-defect_lint
```

Task tests: exit 0, 7 passed. Defect-lint controller status: interrupted after writing the complete scan log; the retained log reports `0 issue(s), 33 warning(s)` and `FLAGGED 1`. Evidence: `checks/audit-9edcccd1341f-task-tests/result.json` and `checks/audit-9edcccd1341f-defect_lint/checks/9edcccd1341f_audit_defect_lint.log`.

Checked scope: public call validation, override boundaries, input validator, canonical pairs/rule mirror, named semantic rivals/witnesses, retained tests, and lint. Audit target was not modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
