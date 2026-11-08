# Passive proposal: preserve an interrupted main draw

This directory contains a working prototype and a passive patch. Nothing here
has been installed into the supplied repository, and no live assignment,
baseline, generator, blind labels, or audit draw was used by the tests.

## Failure and cause

The real `review.py start` invocation in this round selected task
`274345a1792c`, then raised `ENOSPC` while copying its baseline. The exact
recovery account is retained at `../../draw-recovery.json`. The original random
seed was not saved; recovery retained the selected task using a newly recorded
seed constrained to that same selection. The prototype cannot recover that lost
seed retroactively.

In `repo/src/arcpuzzles/review_full_draw.py`, `draw_main` selects the seed, task,
question and source-bound contract before copying, but writes `ASSIGNMENT.json`
only after all baseline copies. A failed copy therefore leaves no committed
draw identity. The old code also returns immediately when `ASSIGNMENT.json`
exists, even if a preceding attempt failed before writing the required blind
assignment or duties.

The supplied source hash is
`026dc776c6195ea39dd5fe48aca8cb889266e5bfb9b45058d11b6a76e89c6358`.
The candidate hash is recorded separately in `source-binding.json`.

## Proposed behavior

An OS advisory lock serializes cooperating main-draw invocations. After source
verification, the exact proposed contract is written to
`.review/pending-main-draw.json` using a temporary file, file `fsync`, atomic
rename and directory `fsync`. This happens before the first baseline copy.

Retries read that journal and reuse its exact seed, task, question, assignment
ID, packet identity and baseline hashes. A conflicting explicit seed, changed
packet manifest, damaged journal or changed source binding causes a visible
error. No fallback chooses fresh entropy after a committed pending draw.

Baseline copies use a dedicated staging directory and are verified against the
bound digest before publication. Completed matching copies are reused; a
partial destination is replaced atomically. Read-only files from earlier
completed copies therefore do not require writing through their permissions.
The assignment and required auxiliary files are finalized idempotently, and the
journal is removed only after finalization and staging cleanup. Existing
`RESULTS.json` content is preserved.

Completed draws without a pending journal keep their existing behavior,
including reuse after a reviewer legitimately edits the selected source.
An old partial baseline without a journal instead requires explicit recovery;
the tool refuses to infer a lost seed or quietly start another draw.

## Files and reproduction

| File | Purpose |
| --- | --- |
| `proposal.patch` | Passive unified diff for one shared source file. |
| `candidate_review_full_draw.py` | Executable candidate, used only against synthetic fixtures. |
| `build_proposal.py` | Rebuilds the candidate and patch from exact source contexts; writes only here. |
| `test_draw_journal.py` | Twelve focused behavior and fault-injection tests. |
| `verify_proposal.py` | Runs the legacy failure cases and the complete prototype suite; saves commands, logs, JUnit and hashes. |
| `evidence-final-v2/verification.json` | Exact interpreter, commands, working directories, overrides, exit codes, counts and source hashes. |
| `evidence-final-v2/fault-witnesses.json` | Original and retried seed/task/assignment identities from the synthetic failure cases. |
| `feedback.md` | Concise feedback suitable for the round's general tooling report. |

From this directory, using the round's existing Python environment:

```bash
/workspace/scratch/6da8da487eb0/round2-venv/bin/python -B verify_proposal.py --out evidence-replay
```

Use a new output directory each time. For a relocated proposal, pass
`--repo /absolute/path/to/ARCpuzzles`; the verification runner supplies that path
to the tests. Python 3.12+, pytest and the ordinary ARCpuzzles source package are
required. The prototype uses the repository's existing POSIX `fcntl` locking
approach and directory `fsync`; Windows is not verified.

`build_proposal.py --repo /absolute/path/to/ARCpuzzles` regenerates the passive
candidate and patch only inside this proposal directory. It fails if the
expected source contexts are missing or repeated. Review a regenerated diff
when its source binding changes.

## Measured verification

The final source-bound run in `evidence-final-v2/` records **five expected legacy
failures and twelve prototype passes**, with zero test errors or skips. The
legacy failures demonstrate loss of the pending seed/task, a retry selecting a
different task, incomplete finalization after assignment publication, lack of a
journal publication boundary, and acceptance of bytes changed during copying.

The prototype suite exercises:

- `ENOSPC` after a real partial baseline write, followed by retry with different
  available entropy while retaining the original draw.
- Conflicting explicit seeds, altered packet identity, corrupt journals, and
  pre-journal partial baselines.
- A subprocess calling `os._exit(73)` during copying, then a fresh subprocess
  resuming the original draw. This also verifies lock release on process death.
- Interruption after assignment publication, verified baseline digests and
  read-only modes, source changes during copying, failure to publish the
  journal, preservation of existing results, and completed-draw idempotence.

The first test-harness invocation used a nonexistent parent for `--basetemp`
and produced three setup errors. `setup-error.log` and its command receipt retain
that result. The parent was created, the genuine legacy failures were then
reproduced, and `verify_proposal.py` now creates its evidence parent before pytest.
The initial three-failure reproduction and first nine-test passing run are also
retained separately; the twelve-test final run is the current verification.

## Integration instructions and limits

The public outer `review.py start` already calls `draw_main(WORK)` on every
invocation, so it reaches the proposed resume path without an entry-point change.
The legacy `assignment.py` entry uses the same function through its `main`.

To adopt this proposal, review `proposal.patch` in a maintainer checkout, check
its source binding, and use `git apply --check` before applying it. Move the
behavioral tests into the repository test suite and replace the proposal loader
with the installed module under test. Re-run the shared suite and supported
platform checks, then rebuild source-bound packets. Do not apply this patch to
the immutable executables in an already-issued review packet.

Before production adoption, also decide how other commands expose a pending
transaction. The prototype resumes correctly through `start`, but standalone
`status`, `duties`, `audit` and packaging do not yet inspect its journal. They
should refuse incomplete setup or report that `start` must finish; alternatively,
publish `ASSIGNMENT.json` last as the externally visible readiness marker. This
prototype retains the existing assignment-first finalization order.

The tests inject I/O errors and process termination; they do not simulate a
kernel crash, power loss, filesystem corruption, uncooperative writers or network
filesystem locking. `fsync` durability relies on the filesystem. In particular,
a journal under `/dev/shm` survives process failure but cannot survive loss of
the memory-backed filesystem itself. The journal is not a signature or a new
approval authority. The patch addresses main draws only; audit-draw journaling
would be a separate, explicitly reviewed extension. No full shared-repository
battery, real large-packet failure run, or Windows test was performed.
