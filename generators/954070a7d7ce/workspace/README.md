# Review tools and next-agent handoff

**YOUR TASK ID IS: 954070a7d7ce.** Assignment `review-39ca466c1586c929` is already
drawn. Do not reroll it. The returned `patches/source.patch` is rooted at
`repo/`; apply it to the matching original packet root with `git apply` after
checking the immutable assignment. No shared source or audit-target edits belong
to this patch.

Selected implementation: `../generator.py`, version **2.0.2**, SHA-256
`a2288e64d15c0773254b2a42696a8ef58dd1b24148c4b0ab6f2c23ca94c0c25d`.
Canonical program hash starts `285c825480d1` and is unchanged. The top-level
review reports and `RESULTS.json` carry measured evidence and actual commands.
Do not mistake local review success for catalog approval or training admission.

## Reproduce from the extracted packet root

```bash
python3 setup_racket.py
python3 run_with_racket.py python3 -m arcpuzzles check 954070a7d7ce \
  --battery --timeout 4000 --phase after --out ../checks/replay-battery
python3 run_with_racket.py python3 generators/954070a7d7ce/workspace/review_probe.py \
  --per-band 200 --matrix --out ../checks/replay-probe
python3 run_with_racket.py python3 generators/954070a7d7ce/workspace/run_repository_tests.py \
  --out ../checks/replay-tests
python3 run_with_racket.py python3 generators/954070a7d7ce/workspace/audit_probe.py \
  --per-band 200 --out ../checks/replay-audits
```

Output directories must be new; never overwrite earlier failure evidence.
The wrapper changes directory into `repo`, which explains the `../checks` paths.
All tools are offline and use the packet's verified Racket runtime. The probes
record actual temporary runtime paths, source hashes, and exact counterexamples;
the temporary runtime copies are deliberately removed when each probe exits.

`review_probe.py` additionally accepts `--generator` to compare the frozen
original, e.g. `../.review/baseline/repo/generators/954070a7d7ce/generator.py`.
It independently inventories frames and requests actual Racket outputs. Its
`--matrix` flag exhausts supported axis combinations at two seeds across all
three bands, not every possible random scene.

`audit_probe.py` reads the two drawn targets only for findings. Its structural
600-case censuses are separate from the smaller canonical/witness Racket checks.
The audit IDs are intentionally fixed to this review's immutable assignment.

`run_repository_tests.py` uses a disposable venv and explicit `.pth` entries for
the repo source and already-installed caller dependencies. This survives child
processes stripping `PYTHONPATH`; it downloads and installs nothing globally.
It retains unfiltered repository logs, selected-task logs, exit codes, elapsed
times, and actual environment paths. It is a test-environment workaround, not a
patch that relaxes runtime isolation. Pytest and runtime dependencies must
already exist in the calling environment.

`verify_return.py RETURN.zip --out checks/replay-return.json` validates the
archive contract and applies its patch to a disposable copy of the original
changed files, then compares the result with the live reviewed source. Invoke it
with `python3 repo/generators/954070a7d7ce/workspace/verify_return.py` from the
packet root; it does not edit the working repository or rerun scientific checks.
It requires the matching immutable packet baseline and git on PATH.

## What to inspect next

Start with `REVIEW.md`, then replay the final source rather than repeating the
baseline investigation. Useful follow-on work is a larger independently seeded
profile-floor stability check and any additional plausible semantic competitors.
Do not generalize to nested/touching frames, change Racket, or silently expand the
override interface without a task-specific reason and new regression evidence.
The next packet should carry this decision summary, the immutable assignment,
latest source hash, all newly executed commands, and concise new findings; it
need not repeat raw conversation history.

## Solve separation

These are **authoring tools**, not solve tools. Do not read or run the generator,
probes, root answer explanation, or Racket source during an independent solve.
Use the visible challenge, standalone Python, and visible checker feedback only.
The review's completed solve declares prior exposure **yes** and masked scoring
**unknown**. Preserve every actual revision and do not relabel it a blind solve.
