# Optional shared-tool proposal: score declared lesson rivals without a hook

This proposal is separate from the selected generator repair. The actual files
under `repo/shared/` remain unchanged. `semantic_gate_declared_rivals.patch`
applies from the repository root and changes only:

- `shared/tools/generator_semantic_gate.py`
- `shared/tests/test_generator_semantic_gate.py`

## Reproduced defect and proposed behavior

The original gate returns `NO_CONTRACT` for a module that declares lesson rivals
but none of the three primary hooks. When another hook is present, it can report
`PASS` while leaving `lessons` null: lesson scoring is guarded solely by the
presence of `lesson_identifiable`. Thus declaring `LESSON_COMPETITORS` or
`CANONICAL_SHORTCUTS` does not ensure those rules are tested on lessons.

The patch lets either nonempty, validated declaration trigger the existing
materializer and competitor evaluator. With no author lesson hook, a rival is
an ambiguity only when it fits every demonstration and changes the query answer.
Answer-equivalent survivors remain counted without becoming ambiguity failures.
The report retains `hooks_declared.lesson_identifiable = false`, adds lesson
`hook_declared` and `assessment_basis` fields, and limits the headline to
“without detected declared-rival ambiguity.” An explicit note states the limited
assessment basis. Materialization failures still fail; competitor exceptions are
counted warnings, which fail the existing strict gate. Legacy `identifiable`
counts retain their established schema and should be read with status/error
counts: an errored rival is not proof of complete assessment.

Modules without a primary hook or a valid lesson-rival declaration retain the
legacy no-contract advisory, or fail under `--require-contract`. Malformed
declarations remain errors. Existing hook scoring and shortcut merge precedence
are unchanged. The new cases are appended to the already mapped shared test
module, so ordinary runtime preparation includes them without a mapping edit.

## Verification

Actual command, run from the packet root (exit 0):

```sh
python3 -B repo/generators/547c45a21db1/workspace/tooling_proposal/verify_proposal.py --run run-002
```

For another replay, choose a new `--run` name. The driver copies the shared
sources into a temporary tree beneath `checks/tooling-proposal/`, runs the
regressions against the original source, checks/applies the exact optional patch
there, then tests the candidate. It removes only its own temporary runtime copies
after saving hashes, commands, return codes, logs, and JUnit reports.

Final evidence is `checks/tooling-proposal/run-002/verification.json`:

| Check | Result |
| --- | --- |
| Original source against the 13 new regressions | 7 failed, 6 passed; expected exit 1 |
| `git apply --check` in disposable repository layout | Exit 0 |
| Exact optional patch applied in that layout | Exit 0 |
| Patched source against the 13 new regressions | 13 passed; 0 failures/errors/skips |
| Entire existing and extended semantic test module | 106 passed; 0 failures/errors/skips |
| Original shared tool and test files | Hashes unchanged |

The new tests cover both declarations with and without a strict-membership hook,
query-changing rivals, answer-equivalent and demo-refuted rivals, raising rivals,
zero materialized lessons, empty declarations, malformed declarations, and the
existing `SEMANTIC_RIVALS`-only legacy case. The synthetic task doubles nonzero
cell values; four distinct demonstrations containing 1s are ambiguous against
“add one,” which changes the query containing a 2. These are transparent fixture
labels for testing gate control flow and scoring. This optional proposal does
not claim a new real-Racket integration run or a census of the generator corpus.

## Source identity and retained intermediate evidence

- Original tool SHA-256:
  `e6213a5bde35eaecf5f97eaa070604398bbe0af0be9c7f0fef9a2227b8dbd569`
- Final proposed tool SHA-256:
  `e6bbaf38c0d1bbc68a0035126c8a938e953fa2c8a936eef908907fd2162f1d59`
- Final optional patch SHA-256:
  `6357b5cdded6ac0b6ba9697c1323870b38219f8b2077a93783c2c549b3c6cce7`

`run-002/verification.json` contains the complete copied-source manifests,
including hashes for dependencies and the one retained canonical row needed by
the established reader test. Exact nested commands and their actual temporary
working directories are recorded there; the driver reconstructs that layout.

`run-001/` retains an earlier successful proposal test, before the new cases were
folded into the mapped test module and the headline wording was refined. Its
exact patch, test fixture, and driver are archived in
`run-001/proposal_snapshot/`; the original recorded patch path in that run now
refers to the final proposal, so use the archived snapshot to reproduce that
intermediate hash. The final acceptance evidence is run-002.
