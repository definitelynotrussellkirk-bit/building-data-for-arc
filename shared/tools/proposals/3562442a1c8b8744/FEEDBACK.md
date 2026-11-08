Prioritize — make interrupted battery process cleanup explicit

**Symptom.** The first after-battery controller invocation was terminated by the outer execution timeout after two completed stages, while its child process continued far enough to leave a live lock/running aggregate. The documented `--resume` path recovered correctly without source changes, but a reviewer can easily mistake the retained running aggregate for a finished result. Evidence: `checks/after/attempts/0001/result.json`, `checks/after-command.log`, and the final resumed summary under `checks/after/checks/`.

**Suggested shared change.** In the battery controller/CLI, install SIGTERM/SIGINT handlers that terminate the child process group, atomically mark the active stage and aggregate `interrupted`, and print the exact resume command. Also make `result.json` distinguish “controller gone but child PID still alive” from a legitimate active run. This is the shared-tool change that most needs attention.
