# ZIP-backed packet source overlay

This helper supports a sparse, physically relocated review packet when the original
issued ZIP cannot be fully extracted. It executes the original reviewer tools and
keeps the standard full-return format.

## Commands

Run from the outer packet directory containing `review.py` and `WORK/`.
Use a new receipt filename on each invocation.

```bash
.venv-review/bin/python -I -B WORK/checks/tooling/zip_packet_overlay.py verify \
  --packet-root . \
  --archive /absolute/path/to/original-issued.zip \
  --archive-sha256 TRUSTED_ORIGINAL_SHA256 \
  --receipt WORK/checks/tooling/source-scan-001.json \
  --progress
```

This calls the unmodified `review.py` `main(["verify"])`. Exit 0 means its
verification passed. Exit 1 means real files differ from the original packet,
which is expected after an authorized repair. An integrity rejection exits 2.

```bash
.venv-review/bin/python -I -B WORK/checks/tooling/zip_packet_overlay.py package \
  --packet-root . \
  --archive /absolute/path/to/original-issued.zip \
  --archive-sha256 TRUSTED_ORIGINAL_SHA256 \
  --receipt sparse-package-receipt-001.json
```

This imports the authenticated original `build_full_return`, which creates the
patch, `INTAKE.json`, artifact hashes, and final ZIP. The helper never writes
those structures itself. After normal filesystem methods have been restored,
it independently calls the unchanged standard `validate_full_return` on the
built archive. The original builder's default output naming is preserved.
`--out PATH` and `--bundle-evidence` are passed to the original builder.

A package receipt must be a new file directly in the outer packet directory.
It cannot be inside the evidence it is reporting on. A verify receipt may also
be under `WORK/checks/tooling/`, so it can be included in the eventual return.
Receipts cannot be written into the repository, baseline, or solve directories.

## Required physical state and trust boundary

1. The issued ZIP is immutable. Record its SHA-256 at intake and supply that same
   fingerprint on every invocation. The helper checks the entire ZIP before the
   scan and again after the original operation.
2. `.hydrated-source-paths.json` is a JSON array of archive-relative names, such
   as `"WORK/repo/src/arcpuzzles/review_full_return.py"`. Every original file
   ever materialized must be recorded **before materialization**. Keep this
   inventory monotonic: never remove a name, including after file deletion.
   Never reconstruct it by listing only files that still exist. A ledger
   omission would lose the historical information needed to distinguish a
   deletion from a file that was never extracted.
3. All currently real manifest source files must be in that ledger. A missing
   previously hydrated file, an unrecorded real source, a symlink, or a
   nonregular source causes preflight rejection.
4. Materialize the original entry files and manifest, the runtime under
   `WORK/repo/src/`, the entire selected generator home, all required rules and
   data, the frozen baseline, and the ordinary assignment/report/solve files.
   This helper does not implement virtual imports, directory enumeration,
   `open()`, or `read_text()`; normal runtime operations still need real files.
5. Use one process with no concurrent hydration, control-file replacement, or
   source edits during a scan or build. The archive, manifest, and ledger are
   checked for identity/content changes during the operation. The helper
   temporarily adapts class methods globally within that process and is not a
   thread-safe general-purpose filesystem.

The ledger is a trusted extraction-history input, not a cryptographic proof that
a file was never materialized. Its exact hash is retained in each receipt. This
explicit dependency is necessary for honest deletion semantics in a sparse
representation. If the complete materialization history is unavailable, do not
use the helper; extract a complete packet on adequate storage instead.

## Integrity checks retained

The helper first verifies the archive inventory exactly matches the source
manifest plus the two outer entry files and the manifest itself. It checks:

- The supplied archive SHA-256, normal ZIP CRC/decompression checks, and every
  original source SHA-256 in the manifest.
- The real manifest is byte-identical to the archived manifest and canonical.
- Both real outer entry files match the manifest and original archived bytes.
- Runtime Python source is physically present and unchanged before packaging.
- The archive, manifest, and ledger remain regular files with unchanged identity
  and content during the operation.

Only `Path.is_file` and `Path.read_bytes` are adapted, and only for an exact
manifest source name that is currently absent and has never been materialized.
Such a read returns the original ZIP bytes. Every real source read uses the real
filesystem. A real file observed during the operation is also permanently
ineligible for fallback for that operation.

`Path.is_symlink`, `exists`, `stat`, imports, directory iteration, baseline,
assignment, evidence, and public solve paths are untouched. Symlink ancestors are
rejected. Unlisted paths never receive fallback. The original builder retains
its shared-source checks, task scope checks, frozen-baseline checks, assignment
checks, patch construction, artifact hashes, intake derivation, and standard
return validation. Allowed selected-task edits are still packaged by that
builder; shared-source edits remain rejected.

Each receipt contains the archive, manifest, and ledger SHA-256 values, the
number and expanded bytes of original source entries actually verified, physical
versus absent source counts, exact per-method real/streamed read counts and byte
counts, distinct source counts for each kind of read, and measured peak RSS.
The `reads` section counts calls through the two adapted methods; it does not
claim to count all interpreter/import I/O. The source inventory records the
preflight state. The overall status and exit code describe the original
operation, so a repaired packet may have a successful archive-source scan but
an original `verify` status of `rejected`.

## Memory and supported ZIPs

The standard library's ZIP decompressor is retained. A streamed central-directory
reader stores compact offsets instead of retaining more than 100,000 `ZipInfo`
objects. On this issued archive, metadata-only peak RSS measured 37,680 KiB for
105,835 entries, compared with 96,572 KiB for an ordinary `ZipFile` metadata load.

The first full real-packet verification also passed all 105,832 source files and
both outer entry files. It checked 1,733,830,994 expanded source bytes, served
5,010 real files and 100,822 absent files, and measured 146,576 KiB peak RSS
(about 143.1 MiB). The retained evidence is
`zip-overlay-source-scan-receipt.json`.

The helper accepts ordered, single-disk, regular-file ZIP entries using stored
or deflate compression, including ZIP64 directory member counts. It rejects
duplicate/unsafe names, overlaps/unordered local headers, encrypted or unsupported
entries, source members larger than 64 MiB, more than 200,000 members, and central
directories larger than 128 MiB. Unsupported inputs fail closed rather than
weakening validation. It uses CPython's ZIP metadata helpers and should be
retested when changing the Python runtime.

The original builder retains its normal in-memory evidence/return behavior.
Therefore the helper's compact source index does not impose a universal 200 MiB
process cap on arbitrary large evidence. Check the measured per-run receipt.
No repository bytecode caches are written or reused during the package import.

## Regression suite

```bash
PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.tmp" \
  .venv-review/bin/python -I -B WORK/checks/tooling/test_zip_packet_overlay.py
```

The suite uses synthetic puzzle/source bytes and the original review entrypoint,
builder, and validator. It covers:

- An absent, never-hydrated source and exact real/streamed counts.
- A real shared edit; deletion before and after preflight; a newly observed real
  file later deleted; symlink, symlink-ancestor, and nonregular substitutions.
- Wrong archive hashes, archived bytes inconsistent with the manifest, altered
  real manifests, duplicate/extra archive entries, and no wildcard fallback.
- Frozen-baseline tampering and undeclared source files rejected by the original
  builder.
- A legitimate selected-task patch and intake emitted by the original builder,
  followed by the unmodified standard validator.
- Both CLI workflows, safe receipt destinations, control-file replacement,
  cache-free operation, and restoration of filesystem methods after errors.

The suite does not run unrelated repository task tests or inspect real puzzle
evidence. Real task validation and blind/post-repair solves remain separate
duties carried out through their original public entrypoints.
