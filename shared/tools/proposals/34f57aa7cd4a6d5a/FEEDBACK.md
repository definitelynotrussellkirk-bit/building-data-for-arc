Portable task-test warnings should name the replacement import in the first line

**Symptom.** The audit target `f7672a367745` has retained tests importing the legacy `scripts.canonical_profile_gate` namespace. A direct repository pytest invocation failed to collect, while the portable task-test stage passed 14/14 and emitted a helpful multiline warning. Evidence: `checks/audit/f7672a367745/task-tests.log` and `checks/audit/f7672a367745/task-tests-portable-command.log`.

**Suggested shared change.** Make the first warning line say: “Use `reviewer_support.canonical_pairs` (portable) or run `arcpuzzles check TASK --stage task_tests` (legacy replay).” This would turn an import failure into an immediate actionable choice.
