# Optional minimal-probe lint proposal

## Maintainer decision requested

Decide whether the generic defect linter should support a **named, justified,
current-rule-bound, live-reference-validated semantic declaration** for lawful
minimal probes. The unified patch in this directory is a proposal against
`shared/tools/generator_defect_lint.py`. It has **not** been applied to that
authoritative file. Production `generator.py`, canonical data, assignment
contracts, and task tests were not edited by this proposal.

Until maintainers adopt a supported mechanism, retain and report the stock
`selfcheck-minimal-impostor` warning. Do not remove lawful 3/4-cell shape support
solely to silence a heuristic, and do not describe the stock battery as passing
because the disposable patched test passed.

## Root cause and existing mechanisms

`_minimal_impostors` constructs five exact named kinds on an accepted source
grid's modal background. `probe_selfcheck_minimal_impostors` treats every
accepted kind as suspicious unless `_canonical_minimal_kinds` calibrates it.
That calibration currently recognizes only a literal canonical singleton.
The selected task's canonical training population contains no singleton, 2x2,
or short line, so it provides no exemption.

The existing `LAWFUL_DEGENERATE_TEXTURES` mechanism concerns named texture
overrides and texture/domain overlap, not these minimal probes.
`SOLID_OUTPUT_JUSTIFICATION` concerns the solid-output detector, not these
probes. No existing evidence-bound named minimal-probe exemption was found in
the current tool. This conclusion comes from the selected linter source; no
unrelated corpus scan was used.

The old generator advertised area 3..9 while its checker also accepted empty
and singleton inputs. The baseline direct reproduction therefore reports four
accepted kinds: all-background, singleton, short-line, and solid-2x2. Those
baseline findings are retained in `WORK/checks/lint-proposal/stock-repro.json`.
The focused fixture rejects area below three, isolating the two lawful
four-cell kinds without pretending the old checker's other accepts were sound.

## Actual canonical execution

`arcpuzzles apply 12ace26107fd --reference canonical` was used on two handmade
7x7 zero-background inputs: a corner 2x2 block and a horizontal four-cell line
starting at column zero in the middle row, matching the linter's constructors.
Both produce `[[4]]`, with valid digit-grid outputs. The unchanged onion rule
counts four cells removed in the first erosion and then stops.

The first receipt, `tiny-apply.json`, binds baseline generator SHA-256
`825a4892e8a9d663536c3ec745e3f486aab761084b9fc6e14bde4bc4f66ee619`.
The later receipt, `tiny-apply-current.json`, binds the repaired version-4
snapshot SHA-256
`17d8d9f77b69029cfdffecd1a855ddf88ba346fdf73ac2bbf2932a3d3d96301e`.
Both receipts report both probes accepted by their respective selected
`self_check`, independently of Racket validity. These are snapshot claims;
later generator changes require new evidence.

The executed wrapped callable has SHA-256
`62885b9352674d96c2dcf46a2749b01c344b6965377ac4471bec96d659e49317`.
This is the apply receipt's `rule_text_sha256`, which hashes
`bundle.rule_callable_text`. The selected normalized program has SHA-256
`3e24db6285e1c9e31be97d01f1dacfcb6985e88dc280c6fce4ecc72f5f4f7b45`.
The normalized rule-source identity is `3e24db6285e1`. These full hashes refer
to different representations of that rule: its selected program and its
executable wrapped callable. Their difference is not a rule-identity mismatch.

## Proposed contract

The optional mapping is exact and kind-specific:

```python
LAWFUL_MINIMAL_PROBES = {
    "solid_2x2": {
        "justification": (
            "The selected onion rule accepts connected solid shapes; a "
            "2x2 block has one four-cell shell, yielding [[4]]."
        ),
        "rule_hash": RULE_HASH,
        "expected_output": [[4]],
    },
    "short_line": {
        "justification": (
            "The selected onion rule accepts connected solid shapes; a "
            "four-cell line has one four-cell shell, yielding [[4]]."
        ),
        "rule_hash": RULE_HASH,
        "expected_output": [[4]],
    },
}
```

This snippet is documentation, not an applied production declaration. Only
disposable candidate files under `WORK/checks/lint-proposal` append it during
the integration test.

Each declaration must name one of the five built-in probe kinds, contain
exactly the three documented fields, provide a string justification of at
least 30 non-padding characters, match the current canonical rule hash, and
provide a valid ARC expected-output grid. A live canonical reference callback
must exist. For every accepted source draw used by the bounded probe, the
canonical rule must produce a valid output; every accepted mutation of a
declared kind must also produce a valid output equal to that kind's declared
expected output. One failed validation keeps that entire kind's finding.

The patch adds optional keyword parameters to the existing probe and a narrow
adapter in `lint_one` using the existing canonical bridge and rule body. No
declaration means stock behavior and no extra reference calls. Successful
validation produces an explicit note listing names, counts, and current rule
hash. Malformed declarations, unsupported names, stale bindings, missing
reference execution, invalid source outputs, probe errors, and mismatched
expected outputs fail closed with findings/warnings. Existing literal
canonical calibration remains unchanged.

## Scope and extra risk

**A successful reference output does not establish task-domain membership.**
Many reference rules return outputs for malformed inputs. This proposal is
therefore a maintainer-reviewed semantic declaration with live checks of its
claimed outputs, not a proof that the declared grammar or checker is correct.
A superficial 30-character justification can still be wrong. Maintainers must
review the task-specific explanation and examples.

The mechanism does not permit a wildcard or blanket waiver. It exempts only
the declared accepted kind after all checked occurrences validate. Undeclared
singleton/all-background findings remain active in the permissive-checker
regression. Missing-self-check checks, aggregate `selfcheck-power`, explicit
must-reject mutation fixtures, other detectors, and other tasks are unchanged.
The mechanism could still weaken the heuristic if reviewers accept a false
semantic declaration, so adoption belongs to the shared-tool maintainer.

Live validation adds reference work only for opted-in modules: at most six
accepted sources plus their accepted declared mutations per lint invocation.
There is no persistent exemption cache to become stale. A single expected
output per kind deliberately cannot express every possible lawful task; this
keeps this proposal narrow rather than introducing arbitrary validation hooks.

## Source-bound patch identity

| Artifact | Full SHA-256 |
|---|---|
| Stock shared linter | `84eee63069f85e7309d0e8bdc534a72f63aa4bc7abb8f756a3bc66d78381dd7e` |
| Proposed patched linter | `091d2e59a311f920fef062d8c4c126dadf6c820f4f761fb5be645251fe1be38f` |
| Unified patch | `021df866d06a72515b1d95f3a7d2bdbfcea93434c0ec1b200c7549512b9d9205` |

`source-hashes.json` repeats these machine-readable identities.
`build_patch.py` deterministically derives the patch from the stock source
without editing that source. A shared-source change requires a new review;
do not assume the current proposal or evidence covers new bytes.

## Tests and exact commands

Commands below run from the outer review directory
`/workspace/scratch/df43994906e4/arcpuzzles_review`. Every Python payload uses
the WORK virtual environment. Wrapper payload paths resolve from `WORK/repo`.

Build the patch without applying it:

```bash
WORK/.venv/bin/python review.py run /workspace/scratch/df43994906e4/arcpuzzles_review/WORK/.venv/bin/python generators/12ace26107fd/workspace/lint_proposal/build_patch.py
```

Run the test-first stock reproduction (expected exit 1, one assertion failure):

```bash
WORK/.venv/bin/python review.py run /workspace/scratch/df43994906e4/arcpuzzles_review/WORK/.venv/bin/python generators/12ace26107fd/workspace/lint_proposal/run_tests.py --mode stock
```

Run the disposable patched tests and `lint_one` integration (expected exit 0):

```bash
WORK/.venv/bin/python review.py run /workspace/scratch/df43994906e4/arcpuzzles_review/WORK/.venv/bin/python generators/12ace26107fd/workspace/lint_proposal/run_tests.py --mode patched
WORK/.venv/bin/python review.py run /workspace/scratch/df43994906e4/arcpuzzles_review/WORK/.venv/bin/python generators/12ace26107fd/workspace/lint_proposal/run_tests.py --mode patched --tag current
```

Each mode copies a self-contained selected runtime into the scratch cache
`/workspace/scratch/df43994906e4/lint-proposal-runtime-cache/runtime-<mode>[-<tag>]`
on its first run, and reuses that snapshot on subsequent runs. The portable
default resolves two levels above WORK; `--runtime-cache` can select another
scratch directory, and explicitly refuses any destination within WORK. These
large reproducible trees must not be bundled with review returns. Initial test
runtimes were moved to this cache after their standalone JSON/text receipts
were retained; `runtime-cache-relocation.json` records the move. No unique
failure evidence lived only in those trees. Use a new alphanumeric tag for new
generator bytes. The runner applies the actual unified patch to the disposable module,
translating only diff headers from `shared/tools/` to the runtime's `scripts/`
mapping. It never patches authoritative shared source.

The exact later canonical apply command was:

```bash
WORK/.venv/bin/python review.py run /workspace/scratch/df43994906e4/arcpuzzles_review/WORK/.venv/bin/python -m arcpuzzles apply 12ace26107fd --input /workspace/scratch/df43994906e4/arcpuzzles_review/WORK/checks/lint-proposal/tiny-inputs.json --check-generator-domain --out /workspace/scratch/df43994906e4/arcpuzzles_review/WORK/checks/lint-proposal/tiny-apply-current.json
```

Apply refuses overwrite; choose a new output name when rerunning.

Observed results:

| Run | Result |
|---|---|
| Stock test-first | 11 tests, 1 expected failure, 0 errors; lawful 2x2/line still warned |
| Patched baseline snapshot | 11 tests pass; real canonical bridge adapter integration passes |
| Patched version-4 snapshot | 11 tests pass; real canonical bridge adapter integration passes |
| Actual apply, baseline and version-4 snapshots | Both inputs yield valid `[[4]]`; both selected self-checks accept |

Guard cases cover absent declarations, missing reference execution, stale hash,
wrong labels, unknown names, blank justifications, malformed containers,
invalid expected grids, invalid generated-source outputs, reference exceptions,
and undeclared permissive-checker accepts. The success path and integration use
the actual Racket bridge. Invalid-output/exception injection is confined to
tests that exercise those failure branches.

The version-4 integration validates both named kinds 2/2 and has zero
error-level findings. It is **not globally clean**: its retained report also
contains a `palette_roles` structural advisory and strict-scalar argument
warnings. These unrelated findings were not suppressed or repaired by this
proposal. Raw reports, red/green logs, source-bound identities, handmade inputs,
and apply receipts live under `WORK/checks/lint-proposal/`.

Only these focused tests and the bounded selected-task integration were run;
this optional proposal was not applied to or tested against the entire corpus.
