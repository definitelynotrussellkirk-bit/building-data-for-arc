# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Lesson-output leakage probe

`probe_lesson_output_leak.py` samples consecutive five-demo lessons and reports
whether the query answer is an exact copy of any demonstration output, while
retaining a separate first-demonstration count for the original period-five
defect. It also reruns the task's `lesson_identifiable` hook on each window. The optional
`--generator` argument can compare an earlier source snapshot with the selected
implementation.

From the repository root:

```sh
python3 generators/7aee010af40d/workspace/probe_lesson_output_leak.py \
  --seeds 20 --starts 10 --fail-on-finding
```
