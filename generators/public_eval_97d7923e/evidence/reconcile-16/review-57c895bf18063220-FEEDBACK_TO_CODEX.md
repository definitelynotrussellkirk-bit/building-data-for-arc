# Feedback to Codex

## F1: Make interrupted reviewer launchers resume from completed child evidence

**Symptom:** a high-level `review.py task-tests` invocation can be interrupted by the host command window after its pytest child has already produced JUnit/source-binding files, leaving no final `result.json`. The exact payload then has to be rerun even though most work completed.

**Evidence:** the final successful receipts are `checks/public_eval_4c416de3-tests/result.json` and `checks/public_eval_97d7923e-tests/result.json`; each was obtained by invoking the documented payload directly after an earlier high-level launch left only partial files. The same packet also produced complete preflight payload JSON before some outer receipt invocations returned cleanly.

**Suggested change:** make `review.py` persist a small in-progress command identity before spawning, then atomically finalize or resume from valid child outputs after interruption. Ensure the launcher owns and reaps the whole process group, and distinguish “payload completed but wrapper receipt missing” from a semantic test failure.

## F2: Promote the bounded public-family audit pattern into a shared command

**Symptom:** `review_public_creation preflight` correctly verifies official labels and finite setting identification at the qualification demo count, but public-family authors still need task-local code for the required 2–6-demo sweep, shortcut rivals, public/private leakage, prefix stability, stress metrics, and hash-named one-query exports.

**Evidence:** the byte-identical task-local tools at `repo/generators/public_eval_4c416de3/workspace/parametric/audit.py` and `repo/generators/public_eval_97d7923e/workspace/parametric/audit.py` implement the same reusable harness. Their outputs are `checks/public_eval_4c416de3/adversarial/audit.json` and `checks/public_eval_97d7923e/adversarial/audit.json`.

**Suggested change:** add a shared `arcpuzzles.review_public_creation audit` command with plugin hooks for task-specific rival predictors. Standardize counts, protected-rival receipts, presentation manifests, public-byte hashing, and leakage controls so future agents only supply the semantic rival set rather than copying the harness.
