# Verify an ARCpuzzles packet directly in its ZIP

`verify_packet_zip.py` checks a full ARCpuzzles review packet without extracting it,
importing packet code, creating an assignment, or changing any file. It requires
Python 3.10 or later and only the standard library.

The review packet that motivated this tool contains 75,893 files, 48,797 implicit
directories, and 1,079,070,494 expanded bytes. Ordinary extraction exhausted the
available inodes. Content deduplication would still require approximately 106,840
inodes: 58,040 distinct manifest file hashes, 48,797 directories, and three files
outside the manifest inventory. The original archive can still be verified before
a suitable complete workspace is available.

## Run

```bash
python3 verify_packet_zip.py /path/to/issued-packet.zip \
  --expected-manifest-sha256 TRUSTED_MANIFEST_SHA256
```

The manifest pin must be the SHA-256 of the exact issued canonical manifest bytes,
obtained from a trusted packet receipt or an earlier trusted verification. For the
packet used in this review, it is:

```text
ee4f8b4d8c16ed2c32ba3bd263250cdbc91eeee2ce3bb06a6a5a29416523b8d3
```

Without a pin, the tool verifies the ZIP's internal consistency with its embedded
manifest. A party that changes both the sources and the manifest can produce a
different internally consistent archive. A trusted pin binds verification to the
issued manifest. The report also includes the SHA-256 of the entire archive.

The command prints JSON to standard output. Redirect that output if a retained
report is wanted. Exit status is `0` for verified content, `1` for a verification
or file-access failure, and `2` for command-line usage errors.

## What is checked

- The manifest uses the exact `arcpuzzles-full-packet-v2` schema identifier and the
  packet's canonical JSON encoding: UTF-8, sorted keys, no whitespace separators,
  preserved Unicode, and no trailing newline.
- Both supported layouts are recognized: `WORK/PACKET-MANIFEST.json` with the
  exact two outer entry files, or `PACKET-MANIFEST.json` at a flat packet root.
- Every manifest-listed source exists exactly once and has the declared SHA-256.
  In the WORK layout, both outer entry files are checked against their own hashes.
- Missing and unlisted members, duplicate ZIP names, absolute paths, traversal,
  nonnormalized paths, backslashes, Windows drive prefixes, truncated NUL names,
  symlinks, other nonregular members, and encrypted members are rejected. Issued
  packets contain file members only; explicit directory members are rejected.
- ZIP decompression/CRC failures, file-size mismatches, truncated or trailing
  DEFLATE data, malformed UTF-8 filenames, and detected changes to the input
  archive during verification fail the check. The complete compressed extent is
  decoded, so an understated size cannot hide bytes beyond a matching prefix.

Source files are hashed in 1 MiB chunks. Only the central directory and parsed
manifest are retained in memory; the expanded repository is not materialized.
STORED and DEFLATE members are supported, matching the issued packet builder;
other compression methods are rejected explicitly.
The default declared expansion limit is 4 GiB and can be changed with
`--max-expanded-bytes`. The manifest has a fixed 64 MiB parser limit.

The report stops at the first failure. `verified_file_count` counts successfully
hashed source and outer-entry members before that point; it excludes the manifest
itself. `member_count` and `expanded_bytes` include the manifest. A successful
report covers the entire inventory, including canonical data, all generators,
shared tools, and the bundled runtime archive. No source text or puzzle answer is
printed.

This is a file-integrity check. It does not approve generator semantics or replace
the packet's assignment, solve, check, or return-validation commands. The original
packager still requires a complete materialized repository. This tool changes no
manifest, packet source, validation rule, or packaging behavior.

## Tests and recorded verification

Run the complete standalone test suite from this directory:

```bash
python3 -B -m unittest discover -v
```

The suite contains 20 test methods covering 37 fixture scenarios. It uses real
synthetic ZIP files and subprocesses, including a payload that would fail if its
Python source were executed. It verifies that a valid check leaves the containing
directory and archive unchanged. The tests need no package installation.
Four cases specifically attempt to hide extra source or manifest bytes behind a
shorter declared size and forged prefix CRC, in both supported compression modes.

`test_results.txt` records the suite result. `issued_packet_verification.json`
records the check of the complete original packet. `verification_runs.json`
records the exact commands, working directories, exit statuses, timings, and tool
source hashes for those runs.
