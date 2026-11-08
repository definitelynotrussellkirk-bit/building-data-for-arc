# Archive-backed return packaging

`package_from_archive.py` calls the original, unmodified
`arcpuzzles.review_full_return.build_full_return`. It supplies a private
`PosixPath` subclass for missing immutable repository files. No shared module or
global `pathlib` object is changed.

The helper streams and hashes every member of the original ZIP, checks the exact
original inventory and working manifest, verifies the real outer entry files and
official Python modules, and preserves the assignment. A manifest-listed source
may be read from the archive only when it is physically absent, is outside the
selected task tree and every baseline path, and has no symlink ancestor. Existing
disk bytes always take precedence, including tampered bytes: the unchanged
builder must reject those. Selected sources, frozen baselines, reports, solve
artifacts, and evidence stay on disk. The ordinary builder still generates the
patch, performs its complete immutable-source hash loop, and validates the ZIP.

## Run after the review documents and evidence are ready

From `WORK/`, use new output and receipt filenames:

```bash
python3 -B checks/support/package_from_archive.py \
  --work . \
  --source-zip "../../upload/SEND-THIS-ARCpuzzles-review(20261020-135043).zip" \
  --out review_response_archive.zip \
  --verification-report checks/support/archive-source-final.json
```

The final stdout JSON reports the official builder result, return ZIP SHA-256,
number of archive-backed source reads, and a digest of their sorted path/hash
inventory. Capture that output outside `checks/` if retaining it separately.
The optional source-verification receipt is written before packaging so it can
be included in the return. Its packaging status intentionally remains
`not_yet_run_when_this_source_receipt_was_written`; the final stdout result carries
the completed packaging result. This avoids changing packaged evidence afterward
or requiring the ZIP to contain its own hash.

`--bundle-evidence` passes through to the official builder. This helper supports
the packet's `WORK/` layout and POSIX paths. It neither executes returned tests nor
replaces the separate fresh patch replay and focused tests required by the
handoff guide. Record this wrapper's actual invocation instead of claiming the
plain `review.py package` command was used.

## Verification

```bash
python3 -B checks/support/test_package_from_archive.py
```

The 13 tests use tiny synthetic packets and the actual official builder. They
exercise absent immutable fallback, tampered disk data, missing selected source
and frozen baseline, symlink files and ancestors, existing directories, corrupt
archives, mismatched manifests, unauthorized real files, attempted writes through
the view, receipt path containment, and byte-identical ordinary/backed return
ZIPs. They import no puzzle generator and run no Racket program.

`tdd-red.txt` records the initial 12 expected failures before the helper existed.
`receipt-path-red.txt` records a subsequent failing containment check before its
fix. These are software-development tests, not failed puzzle solve attempts.
`tests-first-run.txt` retains the first 12-test pass; `tests-final.txt` records the
final 13-test pass. `source-preflight.json` records the real archive verification
and official builder import without creating a review return.

## Fresh replay test runner

`verify_fresh_tests.py` runs the task tests after the official `replay-return`
command has applied a candidate patch to a new checkout. It checks the expected
generator hash, creates a new Python environment, installs pinned pytest, sets
the import paths to the fresh checkout, and rejects task imports from elsewhere.
It retains the exact commands, dependency origins, Racket binary hash, console
logs, and JUnit results. It reuses base NumPy/Pillow packages and the verified
Racket interpreter, but no task source from the earlier review workspace.

From the outer packet root, with a new output directory:

```bash
python3 WORK/checks/support/verify_fresh_tests.py \
  --fresh-work /path/to/replay/checkout/WORK \
  --expected-generator-sha256 55208e87beb462887f5ef092e800ec95ec95dcaf2ded80b321012207424ccdf0 \
  --racket /path/to/verified/racket/bin/racket \
  --out WORK/checks/fresh-replay-tests
```

The completed run is recorded in `checks/fresh-replay-tests/result.json`:
28 tests and 744 subtests passed. `checks/fresh-replay/summary.json` binds that
result to the official replay receipt and the exact candidate source patch.
