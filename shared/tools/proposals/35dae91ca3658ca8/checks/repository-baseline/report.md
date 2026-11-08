# Pristine original-packet verification of three repository failures

All three observed working-packet failures reproduce on the original supplied ZIP in an isolated fresh extraction, with a newly created local venv and independently unpacked offline-bundle Racket runtime. Only the three exact test nodes were run; the full suite was not rerun. No repository or packet-control source was edited.

| Failure | Pristine result | Classification |
|---|---|---|
| Historical archival pair identity for `defba1ab4f90` | Same expected `8b35cf5d019d…` versus actual `b4ba8572d697…`; fails | Preexisting supplied-source regression/assertion mismatch |
| Unsupported-platform system Racket probe diagnostic | Same stale regex versus richer returncode/stdout/stderr message; fails | Preexisting supplied test/diagnostic mismatch |
| Isolated-test interpreter preflight | Prerequisite probe passes; child test fails exact `sys.executable` spelling; fails with relative interpreter | Invocation-sensitive preexisting test/runtime issue |

The third failure is explained by interpreter spelling: the parent is launched with `WORK/repo/../.venv/bin/python3`; the fixture writes that exact string as its expectation. The isolated child reports the normalized `WORK/.venv/bin/python3`. User-site isolation and all three dependencies pass their probe. Running only this same test node through the same outer wrapper with the absolute normalized baseline-owned interpreter passes (1 passed in0.40s), verifying the path-spelling diagnosis. It is not a missing-dependency failure. This does not claim that the unrecoverable original working-run child record had identical details; it establishes the reproduced failure's cause and matching symptom.

The successful fixture setup run reports 3 failed in4.16s, exit1. An initial attempt retained separately failed one archival test and had two fixture errors because the chosen basetemp parent directory was absent; after creating only `WORK/checks`, the same three nodes ran and reproduced all three assertion failures. Both attempts are retained honestly.

`extraction.json` records the original ZIP identity and extraction location. `source_hashes.json` records 15 relevant source identities, all byte-identical to the supplied ZIP and corresponding working files, checked again after tests. `command_receipt.json` records exact commands, exits, classification, source ZIP/runtime identities, and evidence hashes. `three-tests.log` and `junit.xml` retain the failures; prerequisite child results/XML preserve details, and `normalized-interpreter.log`/JUnit record the passing focused follow-up. `dependencies.txt` records independently installed packages. The original `/tmp/pytest-of-root/pytest-71/test_preflight_matches_isolate0/ok` was already absent and could not be inspected.

No shared fixes were attempted. This verification establishes preexistence and the third test's invocation sensitivity, rather than declaring the repository suite green.
