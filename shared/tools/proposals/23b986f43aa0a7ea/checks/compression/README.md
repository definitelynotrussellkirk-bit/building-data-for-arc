# Evidence archive utility

## Design and implementation scope

The parent request specifies per-file deterministic gzip, a complete original-path/hash mapping, bounded verification/restoration, no source deletion and no overwrite. The selected implementation is the small standard-library CLI `repo/generators/7944933e200f/workspace/evidence_archive.py`. It writes only explicit `checks/` evidence and generated payload/index paths. A generic tar/ZIP evidence bundle would still count expanded member bytes against the official 25 MiB return budget, so this utility compresses the JSON evidence files themselves instead. It uses the existing `review-large-evidence-v1` index schema, whose `compressed_path` field is the gzip path. The unchanged native retention reader independently recognizes and verifies this schema.

Plan executed: write CLI integration tests and observe missing-feature failures; implement pack/verify/restore and strict path/hash/byte checks; run seven synthetic tests; exercise native retention compatibility; preserve all actual original evidence. The tests and documentation remain under `checks/compression/`; the only reusable source added is the assigned task workspace utility. No generator execution behavior changes.

## Commands

Run from `WORK/`, selecting real evidence files explicitly (replace the example names):

```sh
.venv/bin/python repo/generators/7944933e200f/workspace/evidence_archive.py pack --work . --manifest checks/compressed/MANIFEST.json --path checks/first-report.json --path checks/second-report.json
.venv/bin/python repo/generators/7944933e200f/workspace/evidence_archive.py verify --work . --manifest checks/compressed/MANIFEST.json
.venv/bin/python repo/generators/7944933e200f/workspace/evidence_archive.py restore --work . --manifest checks/compressed/MANIFEST.json --destination /absolute/new-work-root
```

Restoration recreates each original `checks/...` path beneath the chosen destination root. It permits matching existing bytes and rejects different content without replacing it. It verifies every compressed and expanded size/SHA-256 before beginning restore, then repeats verification while writing each temporary output. Failed/interrupted writes may leave earlier correctly restored files; rerunning preserves them. Only its own unpublished temporary files are cleaned up.

The manifest maps `original_path`, `original_bytes`, `original_sha256`, `compressed_path`, `compressed_bytes`, and `compressed_sha256` per file, plus exact totals and restoration instructions. Payload paths mirror original paths under `checks/compressed/payloads/`. Gzip uses compression level 9, zero timestamp and no embedded source filename. The same bytes produce identical payload bytes in separate runs on the same Python/zlib runtime. Cross-runtime compression identity is not promised; verification always uses the recorded hashes.

The default expanded aggregate limit is 128 MiB, adjustable explicitly with `--max-bytes BYTES`. Every decompression read is bounded by remaining declared expansion plus one detecting byte. The reader also bounds manifest bytes (4 MiB), entry count (4,096), and aggregate compressed bytes. It rejects absolute/noncanonical/traversing paths, duplicate or colliding paths, symlink source/payload/destination components, nonregular files, incorrect totals, corrupt gzip/CRC, and compressed or expanded hash/size changes. Use a private workspace without concurrent filesystem mutation; it does not defend against a separate hostile process racing directory replacements.

`pack` never removes originals. Before excluding/moving any source evidence from the return, verify the archive and preserve its manifest/payloads, update `RESULTS.json` evidence paths to existing compressed evidence, and explain the original restorable paths. Keep actual failed iterations. This tool makes no check verdict or approval claim.

## Verification

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python checks/compression/test_evidence_archive.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python checks/compression/native_compat.py
```

`tests-before.log` retains the six expected missing-feature failures. `tests-after.log` records the initial six-test green run. `tests-final.log` records seven focused CLI tests, including exact roundtrip, deterministic payloads across independent runs, original preservation, same/different destination behavior, corruption with a forged compressed hash, traversal/absolute paths, symlinks, bounded expansion/aggregate limits and conflicting manifest/payload preservation. The synthetic fixtures are removed after testing. `native_compat.json` records actual unchanged native retention-reader verification of a synthetic manifest/payload closure; no production evidence is modified by those checks. The repository-wide suite was not run for this isolated utility; no such pass is claimed.
