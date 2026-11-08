# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Review tools and next-agent handoff

Candidate: 2.1.0, generator SHA256
`0a0ce25730d714988a25b3df83fc8505fd6b8c25278b2f3cf0ba22824b3383f1`.
Assignment: `review-daf200e5ef4d0689`; keep its draw unchanged.
The returned ZIP is a source-bound delta for the original packet, not a full
repository or an approval receipt. Apply/intake it against its matching source.

### Recheck the repaired task

From the extracted original packet root, after intake/applying the selected
task patch, use new output directories:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 53ffc8bc9584 --battery --timeout 4000 --phase after --out ../checks/recheck-final
python3 run_with_racket.py python3 generators/53ffc8bc9584/workspace/run_task_tests.py --out ../checks/recheck-task-tests
python3 run_with_racket.py python3 generators/53ffc8bc9584/workspace/probe_lessons.py --phase final --out ../checks/recheck-lessons
```

`run_task_tests.py` copies the current task tests into a fresh portable runtime,
clears source-tree Python path overrides, runs pytest, and saves logs, source
hashes, test hashes, and the actual temporary working directory. Requirements
are the packet's Python 3.12+, NumPy, Pillow, pytest, and Racket runtime.

`probe_lessons.py` prepares a fresh portable runtime unless `--runtime` selects
an existing, hash-verified snapshot. Defaults: seeds 53000–53099, 400 cyclic
four-demo lessons/band, plus 100 four-demo/default-index lessons/band. It records
overlap and unique inputs separately, iterates both actual rival declarations,
compares an independent local-rule implementation with public Racket episodes,
and runs supported `arcpuzzles apply` on decisive/canonical inputs. Query-family
coverage is a gate when at least four seed groups are requested. Every failure
has a replay record and lossless input/output references.

The large retained census used an earlier probe revision before query-family
coverage became blocking. Its exact `probe_sampled.py` is included beside the
reports. The final tool's additional gate was checked with four-seed before/final
runs. The generator bytes are identical across both final probe runs.

### Audit reproducers

`audit_58f520283ae2.py` reproduces ignored palette-count controls.
`audit_31e0316dace3.py` retains its prepare/finish workflow for the default hard
canonical-profile gap. Read each script's CLI before using a new output folder.
Their targets are findings-only and were not modified by this return.

### What to do next

Verify the source-bound delta and these commands before selecting integration
components. Retain the failed baseline and intermediate evidence. If generating
training episodes directly, pass `--train 4`: bare generate defaults to 3 demos and bypasses this task's four-demo
teaching requirement. Do not promote approval or infer Qwen training gains from
these checks. Broader mixed-color corners, large arbitrary connected shapes,
and arbitrary-grid induction remain outside this bounded motif distribution.

If the generator changes again, prepare a new post-repair solve and retain the
old source-bound solve record, following DUTIES.md. Query correctness is reserved
for independent maintainer scoring.

## Restoring bundled evidence

The return stores checks/ in EVIDENCE-BUNDLE.tar.gz to fit the member limit.
EVIDENCE-BUNDLE.json records every original path, byte size, and SHA256. Intake
verifies this bundle automatically. To restore the original checks/ paths for
manual reading, run `tar -xzf EVIDENCE-BUNDLE.tar.gz` from the extracted return
directory. Keep the manifest and archive with the return.
