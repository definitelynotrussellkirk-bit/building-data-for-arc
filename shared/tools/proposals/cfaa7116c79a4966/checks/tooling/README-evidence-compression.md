# Compress large evidence without losing original bytes

Run the helper from the extracted packet root. The default minimum size is
1,048,576 bytes; change it with --threshold-bytes. Only JSON and JSONL files
beneath checks/ are eligible. checks/tooling/ and checks/compressed/ are excluded.
Stop all evidence writers before packing.

List candidates or perform a dry run:

    python3 checks/tooling/pack_large_evidence.py list --threshold-bytes 1048576
    python3 checks/tooling/pack_large_evidence.py pack --dry-run --threshold-bytes 1048576

Pack after reviewing that list:

    python3 checks/tooling/pack_large_evidence.py pack --threshold-bytes 1048576 --raw-backup /absolute/path/to/raw-evidence-backup

Replace the absolute path example with a scratch location outside the packet.
Paths containing '..' are deliberately rejected. Existing backup files are
never overwritten. The tool creates deterministic gzip bytes, verifies the
stored gzip against the complete original, writes and verifies the independent
raw backup, and commits checks/compressed/MANIFEST.json before removing any
original. Every original path is packet-relative. JSON/JSONL contents are not
parsed, filtered, reformatted, or shortened; failures remain byte-for-byte intact.

The readable manifest records original and compressed paths, sizes, SHA-256
hashes, and totals. checks/compressed/RESTORE.md travels with it. An additional
pack can add newly produced evidence to the same manifest. A previous original
still present after an interrupted run requires inspection; do not delete it
without checking the manifest, gzip, and backup.

Verify or restore:

    python3 checks/tooling/pack_large_evidence.py verify
    python3 checks/tooling/pack_large_evidence.py restore --destination /absolute/path/to/restored-evidence

Restore requires a new or empty destination and verifies all compressed inputs
before creating output. It rejects traversal, symlinks, case-insensitive path
collisions, existing files, invalid manifests, and corrupt/truncated gzip data.
Restored paths appear beneath the destination's checks/ directory. It uses only
the Python standard library and makes no network calls.

To operate on a different extraction, place the global option before the command:

    python3 checks/tooling/pack_large_evidence.py --packet-root /path/to/packet verify

For RESULTS.json, retain paths to the gzip files, the compression manifest, and
readable summaries. An original path existing only after restoration is not a
direct return member. Do not alter source-bound reports to rewrite their
original evidence hashes. The automatic return evidence bundle preserves the
gzip files and this manifest as stored.

Run the fixture-only acceptance suite:

    python3 checks/tooling/test_pack_large_evidence.py --report checks/tooling/evidence-tool-test.json

The suite uses temporary packets and raw backups, never production evidence.
