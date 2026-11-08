# Feedback to Codex

## F1: Biggest avoidable friction: isolated task staging can silently escape to the original checkout

**Symptom:** A task-local prototype that used the repository's generic root finder passed in the working checkout but imported the original packet checkout when run by `review.py task-tests`, because the staged snapshot omitted the canonical ledger used as the root sentinel.

**Evidence:** The first isolated `public_eval_e12f9a14` run failed 17 tests while direct tests passed. Tracing module origins showed the staged adapter loading a generator/runtime outside the stage. Binding the exact adjacent `generator.py` and the runtime under the same staged snapshot made the final isolated runs pass 29/29 and 28/28.

**Suggested change:** Provide a supported `find_task_snapshot_root(__file__)` helper for relocated task tests, or copy the minimal root sentinel into the staged snapshot and assert that every dynamically loaded module remains beneath that snapshot.

## F2: Authoring preflight lacks an official one-query public-preview path

**Symptom:** `preview_public.py` accepts native qualification evidence but not source-bound public-creation preflight evidence, forcing reviewers to build a parallel exporter before they can test sequential one-query visibility.

**Evidence:** The reusable `checks/tools/public_creation_exports.py` had to bind the preflight source/program map, emit 32 content-addressed public files, verify hidden-metadata invariance, and reject visible-byte tampering. The packet's independent checker then confirmed the same 32 files.

**Suggested change:** Add an official `preview-public --preflight <preflight.json>` mode that writes one-query views while preserving `owner_accepted=false`, `verification_status=authoring_preflight_not_owner_qualification`, and exact source/content hashes.
