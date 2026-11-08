F1: Persist the exact main-draw identity before copying the baseline.

This round's initial `review.py start` selected `274345a1792c` but failed with
`ENOSPC` before `ASSIGNMENT.json` was written. The selected task was recoverable
from the failing destination path, but the original random seed was lost; the
explicit same-task recovery is recorded in `checks/draw-recovery.json`.

`checks/tooling/draw-journal/` contains a passive, source-bound proposal that
writes and fsyncs a pending contract before copying, resumes its exact seed/task
under an OS lock, atomically verifies/publishes baseline copies, and retains the
journal through required-output finalization. The unchanged source reproduces
five expected regression failures; the candidate passes twelve focused tests,
including an actual subprocess exit during copying and retry from a new process.
Exact commands, exit codes, hashes, JUnit and synthetic draw witnesses are in
`checks/tooling/draw-journal/evidence-final-v2/`.

No supplied shared executable or live assignment was changed. The proposal's
README identifies the production integration work still needed, including
pending-state handling in other commands, platform checks, and the limits of
process-failure tests versus power-loss durability.
