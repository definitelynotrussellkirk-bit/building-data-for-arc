# Next-agent handoff — 98a65dc7fcb1

## Start here

The main work is complete for assignment `review-0a0a7f531c095e30`; **do not
reroll the assignment or audits**. Read root REVIEW.md, then RESULTS.json and
AUDIT.md. Main generator source is `29c6a2f1df57fcddb81e12cde94dbbb1fa793848c5acf46eb4e4b91ca09645eb`. This is a delta ZIP: its
`patches/source.patch` must be applied from the original packet root. Use the
same frozen baseline; inspect and check the patch first.

```sh
# In a pristine extracted ORIGINAL packet, with the returned patch available:
git apply --check /path/to/returned/patches/source.patch
git apply /path/to/returned/patches/source.patch
```

Root return docs, checks, and solve records stay available in the return ZIP.
A maintainer should apply/intake the patch through the repository's normal
review mechanism rather than treating this report as automatic approval.

## Commands (all start at packet_root)

Use new output directories on replay so failures and earlier evidence survive.
The bundled wrapper runs the inner command from `repo` with local verified
Racket. No cloud services, GPU, network, or extra model installation is needed.

```sh
python3 setup_racket.py
python3 -m pytest -q repo/generators/98a65dc7fcb1/tests/test_review_98a65dc7fcb1.py
python3 run_with_racket.py python3 -m arcpuzzles check 98a65dc7fcb1 --battery --timeout 4000 --phase after --out ../checks/replay_after
python3 run_with_racket.py python3 generators/98a65dc7fcb1/workspace/probe_distribution.py --seeds 100 --indices 8 --exhaustive-local --out ../checks/replay_probe
python3 run_with_racket.py python3 generators/98a65dc7fcb1/workspace/audit_assigned.py --seeds 20 --out ../checks/replay_audits
python3 run_with_racket.py python3 generators/98a65dc7fcb1/workspace/run_portable_tests.py --task a16cf9241d71 --test generators/a16cf9241d71/tests/test_generator_a16cf9241d71.py --out ../checks/replay_a16_tests
```

Baseline probe: add `--source ../.review/baseline/repo/generators/98a65dc7fcb1/generator.py
--phase before` to the distribution command, with a new output directory.
The original baseline remains in the full packet; it is intentionally not
repacked as another repository tree.

`probe_distribution.py`: final/baseline source-bound Racket parity, four
independent rivals, overlapping-window survival, input uniqueness, exact
counterexamples, optional ternary exhaustive check and arbitrary-grid stress.
The local Python predicate checks Racket output; it never supplies its label.

`audit_assigned.py`: read-only ordinary/boundary/fixture probes for the two
assigned tasks, including actual Racket labels, typed findings, unchanged
source hashes, literal typo calls, and actual runtime directory. Exit0 means
report produced; inspect `failures`, unknown-key acceptance, and texture warnings.

`run_portable_tests.py`: stage a selected task with the project's official
runtime mapping; copy a runtime-native task test; launch pytest in that exact
layout and preserve exit status, stdout/stderr and source/manifest identities.
It is not a universal test-data packager: tests needing extra fixture files
would need those dependencies explicitly staged. The main review test is
library-native and should use the direct pytest command above.

## Boundaries to preserve

Do not touch the two audit sources. The full repository suite currently has
one unrelated miniature-packet import failure (F1), not a main-task regression.
The after battery is12/12, main tests59/59, audit-A existing tests8/8.

The completed solve is **not blind**. Earlier rule exposure=yes, reference
consulted during solve=no, visible3/3, hidden label unknown. Do not rerun prepare
over the completed episode or read its private labels for reviewer scoring.
Independent intake must score the frozen candidate. A new generator revision
needs newly source-bound checks and a separate honestly recorded solve episode.

Keep counts honest: final2,400 draws mean1,586 globally unique inputs;
1,500 lesson windows overlap. Ternary exhaustive3x3 is19,683 inputs, not all
10-color grids. Four rivals are a finite diagnostic family. Normal guarantees
exclude arbitrary override combinations or a reordered teaching schedule.

## Next useful owner work

Address F1's incomplete shared test fixture; reject unknown keys and migrate
lawful fixture metadata for audit db95939a5dd0 in its own assignment. For this
task, prefer a held-out model experiment and cross-band deduplication over
adding more decorative knobs. Extend adjacent-object sampling only if it adds
measured value without losing canonical coverage. Diagnostic palettes remain
fixed; irrelevant negative-fixture controls should eventually reject explicitly.

## Verify a returned delta without trusting this working copy

`verify_delta.py --packet ORIGINAL_PACKET.zip --delta RETURN.zip --out NEW_DIR`
uses the official static validator, safely extracts the original packet into a
new temporary directory, checks/applies the patch with git, runs the restored
task-local tests, and compares its generator to the returned solve snapshot.
It records the actual replay directory and patch/source identities. It does
not execute a new complete Racket battery or read private solve labels.
