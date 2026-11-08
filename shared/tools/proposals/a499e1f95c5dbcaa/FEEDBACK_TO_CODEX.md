# Feedback for future ARCpuzzles agents

## F1: Recover extraction before invoking the assignment draw

**Symptom:** the normal extraction failed with ENOSPC before creating its destination. A later resumable extraction saved 6,256 files and then hit the same resource failure.

**Evidence:** `evidence/extraction-final.json`, `evidence/final-workspace-state.json`, and `SOURCE_FINDINGS.md`. The source orders seed selection and baseline verification before pending-draw publication; running `start` on missing sources can fail before that draw is journaled.

**Built change:** `arc_packet_recover.py` verifies the archive without extraction, binds a destination to its exact identity, resumes complete files, refuses changed files, and never invokes the draw. Its output explicitly separates archive verification from generator review.

**Suggested maintainer action:** make a small, standalone recovery helper available alongside future packets, or incorporate this code through a separately reviewed tooling change. Preserve the full source-integrity gates and keep assignment execution explicit. A possible future change to journal draw intent earlier needs its own transaction/recovery design and tests; this deliverable does not change draw semantics.

## F2: Keep receipts available when storage or compressed-data handling fails

**Symptom:** writing only a local receipt is unreliable under ENOSPC. During review of the new helper, malformed compressed members and report-path symlink loops also initially suppressed structured stdout.

**Evidence:** `evidence/regressions-expanded-red.log` records the reproduced defects; `evidence/tests-final.log` records the complete passing suite after repair.

**Built change:** handled errors reach JSON stdout; optional report failure is reported separately on stderr; archive corruption is distinguished from genuine filesystem errors. Tests cover DEFLATE, BZIP2, LZMA, report symlink loops, and source symlink loops.

## F3: Release unneeded manifest metadata before streaming the library

**Symptom:** the first complete verification attempt ended with signal 9. The runtime memory snapshot was near its cgroup limit and contained OOM-kill counts. The individual signal's cause was not conclusively attributed.

**Evidence:** `evidence/archive-verification-attempt1-command.json`, `evidence/runtime-storage-and-memory.json`, and the successful subsequent `evidence/archive-verification.json`.

**Built change:** canonical JSON is compared in fragments instead of constructing another full serialized copy; ZIP path strings are reused; unrelated parsed generator metadata is released before streaming member payloads. The complete subsequent verification passed. Inventory memory remains proportional to archive size.

No linter or generator-quality finding is claimed: generator source inspection and the assigned checks were not reached.
