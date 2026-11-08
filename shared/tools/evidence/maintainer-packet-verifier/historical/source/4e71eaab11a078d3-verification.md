# Verification

Version 0.5 passed **53 tests** locally and in a fresh normal-wheel installation
at `/tmp/arcpuzzles-v05-isolated-h2fhedwl`, with Landlock denying `/home` reads.
This includes native JSON/tensor exports, label/input separation, actual rule
provenance, archival research opt-in and bare-expression Racket execution.
The [v0.5 receipt](migration/v05-evidence/receipt.json) binds code, tests, wheel
and logs. The 0.4 JSON-only route was also exercised before Torch was installed;
its [separate receipt](migration/native-export-evidence/receipt.json) is retained.

The earlier v0.3 isolated library check
imported all **3,941 generators**, verified **11,736 original file hashes** and
checked **11,732 runtime mappings**. The generic path now preserves the inherited
duplicate-pair and undeclared-identity rejection checks.

Real mixed sampling, multi-query grid/code chat renders, DSL prediction/execution,
hindsight mutations and synthetic prefix traces were exercised. The relocated
mutation, prefix and mixed-challenge routes reproduced all 12 public/private
artifact projections byte-for-byte. See [the 0.3 receipt](migration/export-evidence/receipt.json)
and [dataset guide](datasets.md). The separate full v0.3 generation census is
complete: all 3,941 generators attempted, all 449 approved generators matching
the measured historical pairs. See [every exception's classification](migration/census-classification.md).
The subsequent v0.5 tests re-exercise the affected routes; no second full census
is claimed. Imports and hash checks do not establish corpus-wide semantic validity.

The public-interface tests cover filter composition, exact approval conditions,
stale generator/rule rejection, malformed requests, pagination, answer-free
challenge projection, independent runtime copies, exclusive review assignment,
failed preparation, process timeouts, ZIP contents, and HTTP/Python parity.

```bash
python -m pytest -q
arcpuzzles lint --verify-import --imports
```

The second command checks every generator home and runtime mapping, verifies
copied original hashes, and imports all generators in a separate runtime.
It does not certify the semantic quality of every generator. Current approval
is derived from existing review evidence and current source identity.

Real execution checks use the imported `6c68e1b008a5` generator for seeded,
Racket-verified episodes and the inherited lint/self-check stages. A generic
generation smoke uses `generic_dense_recolor_gen1` with explicit unapproved
research opt-in. Those checks establish the exercised routes, not all-seed or
all-generator semantic correctness.

Standalone distribution verification builds and installs a normal wheel into a
fresh environment outside the checkout. Linux Landlock denies reads to the
Desktop repositories, with the restriction inherited by Python/Racket children,
while the verification exercises queries, generation, and review preparation.
This tests the absence of an implicit predecessor/sibling source dependency.
The measured result is recorded in `verification-results.json`.

The current source-read restriction is reproducible with
`tools/deny_predecessor_reads.py`: copy it and `tests/` beside a normal installed
wheel in a fresh `/tmp` directory, then invoke the wrapper with the absolute path
to that environment's Python followed by `-m pytest -q`. Install the declared
runtime/dev/tensor dependencies there first. No editable source install is used
for relocation tests. Final receipts are written after wheel construction; the
wheel retains its build-time documentation while the source repo retains final
verification evidence.

The earlier 0.1 pass imported all **3,941** generators and verified **11,701**
copied source hashes. **22** public-interface tests passed in both the checkout
and the isolated wheel install, including a regression that deliberately changes
a disposable archival rule and verifies generation still executes the reviewed
canonical rule. **34** inherited common tests passed in a full staged runtime
under the same source-read restriction. The full 12-stage battery has been
preserved but was not run across the corpus.

No training jobs, model servers, paid calls, external reviews, notebook pushes,
or competition submissions are involved in these checks. No review status is
upgraded as a result of repository migration tests.

The full 12-stage battery also ran on `6c68e1b008a5` from the isolated v0.5
installation: seven green, two advisory and three failed stages, with no timeout
or missing dependency. Active rule texts differ despite sampled execution parity;
generated palette support misses the canonical palette, canonical profile support
was zero in 60 draws, and a semantic contract is absent. These inherited findings
remain visible and no safety label was upgraded. This establishes that all twelve
shared tools run independently; it is not a clean generator-quality result or a
full-corpus battery. See [the retained evidence](migration/battery-evidence/receipt.json).

The reusable full-library review packet has a relocated round-trip test at
`tests/test_review_full_portable.py`. It extracts a ZIP outside the owner
checkout, draws an assignment through the documented entry script, retains
before and after check receipts, packages a compact return, collects it, and
checks its candidate without editing owner source. For review-packet changes,
exercise the affected workflow tests, frozen source inventory and relocated
generation/reference path. Unchanged generator batteries, a complete repository
suite and a full-library packet build are not required. Report the actual scope;
this fixture does not establish a real packet's successful relocation.

### Maintainer cold packet check

New workspace packets have a reusable owner check. Choose an included per-puzzle
target, use a new output directory, and supply `--owner-sources` when verifying a
new release against this checkout:

```bash
PYTHONPATH=src python3 -m arcpuzzles review verify-packet \
  var/review/SEND-THIS-ARCpuzzles-review.zip --id INCLUDED_TASK \
  --owner-sources --out var/review/packet-verification
```

The command checks every ZIP member and hash, creates a fresh Python environment
under `/tmp`, installs the packet's declared runtime dependencies, and selects its
pinned bundled Racket. Linux x86_64 and Landlock ABI 2 or later are required. The
probe can read its cold tree and system runtime paths; an owner-side file must be
unreadable. It generates one episode (three demonstrations and four queries by
default), checks distinct inputs and public/private separation, then replays
every label through the canonical reference API. It runs no generator batteries
and changes no approval or training admission.

`verification.json` records the exact ZIP, tool sources, command exits, timeouts,
logs, reference hashes and tested scope. Public challenges and private labels are
retained separately under `artifacts/`. Successful scratch is removed after
evidence retention; failed scratch stays available at the recorded path.
`--keep-checkout` retains success too. `--sha256` binds an expected ZIP;
`--train`, `--test` and `--seed` select the scoped probe. Use the optional
`--accepted-family ID` only when the standard accepted-parameter export path also
needs checking; it exercises two episodes and inspects their saved export.
This is maintainer release work, not an additional external-reviewer duty.

## Portable task tests and interrupted checks

### Offline source test setup

Repository tests that spawn an installed-package child deliberately remove
`PYTHONPATH`. Running the parent with only `PYTHONPATH=src` therefore does not
provide the child's installation. In a **prepared virtual environment** with
Python 3.12+, the build backend and required runtime/dev dependencies already
available, install this checkout without network access:

```bash
env -u PYTHONPATH .venv/bin/python -m pip install \
  --no-index --no-deps --no-build-isolation -e .
env -u PYTHONPATH .venv/bin/python -m pytest -q tests/test_apply_rule.py
```

Use `-m pytest -q` without the filename when a full repository suite is needed.
These flags disable dependency downloads and isolated build provisioning; they
do **not** supply missing dependencies. Prepare them from a compatible wheelhouse
or an approved connected installation first. Missing Python packages or Racket
are setup failures, not evidence of a generator regression. An editable source
test does not establish normal-wheel isolation or corpus quality.

For an extracted reviewer packet, activate a prepared virtual environment first,
then run from the packet root:

```bash
python3 review.py run python3 -m pip install \
  --no-index --no-deps --no-build-isolation -e .
python3 review.py run python3 -m pytest -q tests/test_apply_rule.py
```

The wrapper runs in `WORK/repo/`, verifies/selects the bundled Linux x86_64
Racket runtime (or a compatible system runtime on other platforms), and passes
it to child processes. No root access is needed. The same environment's installed
package remains importable when a test child removes `PYTHONPATH`. Record actual
results from the selected source; the older test counts above are historical.

Run task-local regressions explicitly; the twelve-stage battery remains separate:

```bash
arcpuzzles check TASK --stage task_tests --phase after --timeout 600 --out var/checks/TASK-tests
```

This snapshots the selected task's tests/workspace and public API, mirrors their
library paths, and also runs matching retained frozen fixtures in the legacy
layout. Every copied file is hash-bound in `RUNTIME_MANIFEST.json`. Public API
calls from tests use the snapshot. Source symlinks are rejected. A missing test
suite produces `test_status=no_tests`, exit 5 and `passed=false`; it is not a pass.
Tests requiring third-party packages still need those declared dependencies in
the active Python environment.

The check reports `test_counts` (tests, passed, failed, errors, skipped) from its
retained `checks/task_tests.xml`; missing/interrupted XML leaves counts unknown.
Before pytest, `test_import_diagnostics` points out private `scripts.*` imports
that work in the staged legacy runtime but fail under direct packet pytest.
These are portability warnings, not automatic failures. New tests can use
`reviewer_support.canonical_pairs(..., root=find_root(__file__))` in either layout.

All `check --out` runs create a receipt before launching the child, checkpoint
stage evidence on progress, and write a terminal receipt when the process ends.
`result.json` records `status`, exact commands, copied-source hashes and evidence
hashes; `progress.log` retains the interleaved progress stream. `running` and
`interrupted` have `passed=null`, preserving completed stages without inventing
an aggregate score. Controlled Python interruption stops the process group.
A forcibly killed parent may leave its last `running` checkpoint: check process
liveness before interpreting it. Retain the interrupted output. Battery runs
support explicit checkpointed `--resume` with source/runtime/settings checks;
see [reviewer check resume](reviewer-check-resume.md). Changed generator,
runtime or settings require a fresh output directory. Resume does not turn a
running or interrupted receipt into a pass without completing its stages.

The return builder now emits standard Git EOF markers and splits records only
on LF. Regression tests run actual `git apply --check`, apply each patch and
compare exact file bytes, including CRLF and embedded separators.

## Hand-made inputs and reference identity

For generator repair or audit, use the public `Catalog.apply` route to label
hand-made inputs. Keep it closed during a blind solve: it exposes reference
answers. The review packet wrapper runs this code from `repo/` with its verified
Racket runtime. `grids.json` below is a JSON list of input grids.

The CLI uses the same staged reference runner:

```bash
arcpuzzles apply TASK --input grids.json --reference canonical \
  --timeout 120 --out var/checks/TASK-apply.json
```

It accepts one raw grid, `{"input": GRID}`, `{"inputs": [GRID, ...]}`, or a list
of grids/input objects; the Python API below always receives a list of grids.
Supply 1–64 rectangular grids of 1–30 rows and columns with integer colors 0–9.
Per-puzzle generators are supported; generic generators are rejected. Input
and output dimensions need not match. Results remain in input order, including
per-input failures. A failed reference input sets that result's output/hash to
null and makes the CLI return 1 after saving its receipt; worker startup/timeout
errors raise `ApplyFailure` through the Python API. Output files are never
overwritten. Canonical execution can be used to investigate an unapproved
generator; it does not approve it. `--reference archival` requires explicit
`--allow-unapproved` and always returns `approved=false`.

```python
import json
from pathlib import Path
from arcpuzzles import Catalog

catalog = Catalog(Path.cwd())
task_id = "d70726fd510f"
grids = json.loads(Path("grids.json").read_text())
expected_generator = catalog.describe(task_id)["generator_sha256"]
receipts = []
for start in range(0, len(grids), 64):  # Public apply accepts at most 64 inputs.
    receipt = catalog.apply(task_id, grids[start:start + 64],
                            reference="canonical", timeout=300)
    assert receipt["generator_sha256"] == expected_generator
    assert receipt["rule_hash_matches_catalog"] is True
    assert all(row["error"] is None for row in receipt["results"])
    receipts.append(receipt)
Path("apply-receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")
```

Save the inputs/settings beside these receipts. Name each hash representation:
exact canonical ledger/program text, normalized catalog rule identifier, and
`rule_text_sha256` of the executed callable. Runtime wrapping can change the
exact text hash; comparing it directly to an unwrapped program hash is invalid.
Retain `catalog_rule_hash`, `executed_rule_hash`, `rule_hash_matches_catalog`,
`generator_sha256`, actual outputs, errors, and input/output hashes. A matching
normalized identity establishes the selected authority; it does not prove
universal equivalence or a generator's training eligibility.
