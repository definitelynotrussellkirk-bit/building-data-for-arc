# Restore losslessly compressed evidence

MANIFEST.json maps every original packet-relative path to its gzip file, exact
byte count, and SHA-256. Compressed bytes have independent size and hash checks.
The original JSON and JSONL bytes, including every failure, are preserved.

From the extracted packet root:

    python3 checks/tooling/pack_large_evidence.py verify
    python3 checks/tooling/pack_large_evidence.py restore --destination /absolute/path/to/restored-evidence

The destination must be new or empty. The helper rejects symlinks, traversal,
file collisions, overwrites, and corrupt or truncated gzip data. It verifies all
archives before creating restored output. Restored files appear beneath
DESTINATION/checks/ at their original relative paths. Replace the absolute
destination example with your desired location. Paths containing '..' are
deliberately rejected; use an explicit absolute backup or restore location.

If the return's checks/ files were put into EVIDENCE-BUNDLE.tar.gz, first unpack
that verified bundle using the packet's public review evidence-extract command.
The compression helper and this manifest are themselves ordinary checks/ files.

Source-bound reports may still name original evidence paths and hashes. After
restoration those bytes and names match exactly. Do not edit an original report
to make its references point at compressed files. RESULTS.json evidence_paths
must instead name retained compressed paths and this manifest.

Pack keeps a second original copy beneath the explicitly selected --raw-backup
directory, using the same packet-relative paths. That scratch copy is not
needed for restoration from the returned archive. Pack never overwrites a raw
backup. On interruption inspect the manifest and retained originals; do not
delete unexplained partial files merely to force a retry.
