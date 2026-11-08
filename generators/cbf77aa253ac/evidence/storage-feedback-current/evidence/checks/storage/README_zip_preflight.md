# Optional ZIP capacity report

Reuse the existing stdlib proposal; no duplicate executable was added.

Tool: `repo/shared/tools/proposals/f067eb92fdc48c7e/checks/tooling/resource-preflight/packet_resource_preflight.py`

Tool SHA-256: `76c6ce07b7c8e06a75ee8944b887a6fc1b153739182cc850b0492a18afc5b3c2`

From `WORK/repo` inside the retained private workspace:

```bash
python3 shared/tools/proposals/f067eb92fdc48c7e/checks/tooling/resource-preflight/packet_resource_preflight.py \
  '/workspace/scratch/8a9840429e4f/upload/SEND-THIS-ARCpuzzles-review(20261023-123116).zip' \
  /workspace/scratch/8a9840429e4f --json \
  --extra-bytes 67108864 --extra-inodes 1024
```

Both archive and destination are explicit. This command only reads archive and filesystem metadata. It does not extract, delete, download, or choose storage. The chosen safety reserves are 64 MiB and 1,024 entries; they are illustrative margins, not measured future runtime requirements. Supply different reserves or the tool's runtime/replay copy estimates for the intended work.

Exit 0 means the known budgets suffice, 1 means a known byte/inode budget is insufficient, and 2 means archive/member/input errors. `inode_check_known=false` leaves inode sufficiency unknown even if exit is 0. Unsafe absolute/parent paths, duplicates, conflicts, and nonregular member types are reported without extraction.

`zip_preflight_actual.json` and `zip_preflight_fixture.json` retain exact commands, source hash, timestamps, namespace, inventory, budgets and exits. `zip_preflight_metadata.json` adds archive file/compressed-member/uncompressed-member sizes and distinguishes f_bavail process-available bytes from f_bfree including reserved space. The statvfs observation is a nearby separate timestamp; concurrent filesystem use can change free counts.

`zip_preflight_verification.json` and `zip_preflight_tests.log` retain the existing seven focused tests plus exact-capacity, one-byte-short, one-inode-short and unknown-inode boundary checks on the two-file/two-directory fixture.

This is an optional capacity report, not guaranteed extractability. Payload CRCs, permissions, quotas, filesystem metadata/index overhead, concurrent writes and subsequent runtime copies remain outside the claim. Measurements were taken via the persistent private arc_session namespace `mnt:[4026532276]`; a normal tool session can have different mounts and capacity. No comparison with another model plan was measured.

The tiny fixture needs four entries. With zero additional reserve it returned exit 0 (`zip_preflight_fixture_no_reserve.json`); with the explicit 1,024-entry reserve it returned exit 1 because the selected filesystem had only 168 free inodes. This distinguishes fixture size from requested future headroom.
