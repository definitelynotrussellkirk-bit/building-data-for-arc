# Original-source classification of repository test failures

All **14** failing nodes from the changed-tree full-suite log reproduced on the untouched original extraction: **14 failed, 0 passed, 0 skipped**, pytest exit code **1**. The selected run took 9.53 seconds (11.54 seconds including the packet wrapper). Only these 14 nodes were run; the original full suite was not rerun.

Each failure has the same assertion or exception lines as the corresponding changed-tree failure. Comparison ignored only incidental Python object addresses. The exact node list, failures, and line comparisons are retained in `classification.json` and the selected pytest XML/log.

| Group | Nodes | Reproduced behavior |
|---|---:|---|
| Archival-reference expectations | 2 | `defba1ab4f90` historical pair hash differs from its test constant; `d982cffd80f8` draw contains no self-check rejection where the test expects one. |
| Check audit/jobs/resume/signals | 11 | Managed liveness, checkpoint resumability, and stage-child termination expectations fail identically; results include `liveness_unknown`, a denied resume, and child-liveness assertions. |
| Packet Racket setup | 1 | Expected error regex `Racket probe failed: unusable runtime` does not match the detailed return-code/stdout/stderr message. |

## Independence and source binding

The run used a newly created `.venv-shared-baseline` under the original extraction, independently installed with Python 3.12.14, pytest 9.1.1, NumPy 2.5.4, and Pillow 12.3.0. Its package paths are recorded in `environment.json`. It used the original packet's own verified offline Racket archive; no main-workspace environment or runtime was borrowed. The archive SHA-256 is `2c5fdc02787ba569f03d89cad6086a5c3be49045d58281e2db7fe31b43650eb7`.

All **1,913** selected relevant test, public API, runtime, tool, data, and archival-generator files matched the original packet manifest and the changed tree. Their original hashes remained unchanged after the tests. The exact inventory and hashes are retained in `source-bindings.json`.

The original packet-manifest SHA-256 is `23675c976262aebd13f7ec6a8c0910f04da692747f0d653db14737d1a2fcdab1`.

## Classification and limits

These 14 failures are **inherited and reproduced in this host environment**, with no evidence that this generator repair introduced them. This result does not certify their cross-platform cause or claim that every original repository test behaves identically. No shared code fix or repository-source modification was made. The fresh repository remains available for patch replay.

`commands.json` records exact argv, working directories, dependency setup, environment settings, exit codes, and evidence paths. `selected.log` and `selected.xml` retain the actual failures. Copies of these compact receipts and logs are available in the main workspace's `WORK/checks/shared-baseline` directory; their original execution paths remain truthful.
