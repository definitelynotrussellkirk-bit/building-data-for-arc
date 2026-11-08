# Review tools and handoff

The selected implementation is `../generator.py`; drafts here are not selected.
The generator owns input sampling and rival declarations. Racket remains the
label authority. Do not use these authoring tools during a visible-only solve.

- `semantic_probe.py` obtains official Racket labels through the public apply
  command, independently checks predictions, discovers rival declarations,
  and measures linear lessons and all cyclic query rotations.
- `code_mapping_audit.py` checks the twelve single-code substitutions against
  retained official labels. It found a real gap beyond the original six rivals.
- `replay_baseline.py` re-scores retained baseline inputs/labels with the current
  declared rivals, keeping input-generator and rival-generator hashes separate.
- `REVIEW_REGRESSIONS.md` explains the tests-first failures, final tests and the
  official portable runtime's importlib requirement.

For the next agent, start with the packet-level REVIEW.md and RESULTS.json, then
use the final source hash to select evidence. Earlier directories labelled
`after`, `stable-final-*`, or `regressions-final` are retained intermediate runs;
the final version is 2.1.0 and its final evidence paths contain `v21` or are the
explicit fresh-replay receipt. Do not treat an old filename as a final-source claim.

After editing the generator, run the public full battery and explicit task_tests
stage, re-run the source-bound lesson census, and prepare a new solve episode.
Preserve prior failures and solve records. The task's own tests must be invoked
explicitly; the general repository test suite does not discover them.

## Compressed evidence

`restore_evidence.py` is a standalone Python standard-library CLI. It preserves
large JSON reports byte-for-byte in gzip archives and records original and
compressed paths, sizes, and SHA-256 hashes in
`checks/COMPRESSED-EVIDENCE.json`. The return includes an identical standalone
copy at `checks/evidence-tool/restore_evidence.py`, usable before applying the
source patch. From the freshly extracted return root, verify the archives:

```bash
python3 checks/evidence-tool/restore_evidence.py verify --packet-root .
```

Restore the original JSON reports with:

```bash
python3 checks/evidence-tool/restore_evidence.py restore --packet-root .
```

Restore is also the default action when only `--packet-root .` is supplied.
Verify never writes reports. Restore validates compressed and decompressed
hashes, bounds decompression by the declared original size, rejects unsafe
paths and symlinks, and refuses to overwrite different existing bytes. It
keeps the archives and manifest, so verification and restoration are repeatable.

For the reviewer, from the full packet root, explicitly archive reports before
packaging with:

```bash
python3 repo/generators/531e65dffc0a/workspace/restore_evidence.py pack --packet-root .
```

Pack selects regular `checks/**/*.json` reports at least 131072 bytes; change
that threshold with `--threshold-bytes`. It excludes the manifest, preserves
existing manifest entries, and removes an original only after verifying the
stored gzip round-trip and recording its mapping. Restored JSON may expand the
working tree beyond the 25 MiB transport budget; that budget applies to the
packaged members, whose large reports remain gzip files. Restore after extracting
the return. If packaging again after restoration, run pack again first.

The synthetic verification receipt is `checks/evidence-tool/synthetic-check.json`.
It covers round-trips, repeat pack/restore, standalone restoration, corrupt
hashes, bounded decompression, unsafe paths, symlinks, and differing existing
files. It does not claim that actual packet evidence was packed during the tool
verification.


### Earlier version

See history/v2.0.0/ for exact predecessor source, notes and version-specific
tests. Older inherited probes may describe v2.0.0; current v2.1.0 evidence
uses code_mapping_audit.py and semantic_probe.py from this return.
