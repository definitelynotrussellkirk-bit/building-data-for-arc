# ZIP resource preflight proposal

`packet_resource_preflight.py` uses only Python's standard library. It reads ZIP
member metadata and the chosen destination's filesystem capacity. It does not
extract files, open member contents, delete data, or choose a destination.

```bash
python3 packet_resource_preflight.py packet.zip chosen-directory --json
python3 -m unittest -v test_packet_resource_preflight.py
```

Exit status is 0 when the measured byte/inode budgets suffice, 1 when a known
budget is insufficient, and 2 for invalid archives, unsafe members, duplicates,
or other errors. Unknown inode capacity is explicitly reported, and a status of
0 does not establish it. Archive CRCs and payload integrity are outside this
metadata preflight.

The estimate counts distinct regular files and all implicit/explicit directories,
rounds each file to the destination allocation unit, and budgets one allocation
unit per directory. Directory indexes, filesystem metadata, generated evidence,
and additional installation work require a reserve. Use `--extra-bytes` and
`--extra-inodes` for that reserve and for an embedded runtime installation.

Portable runtime snapshots and replay evidence can be budgeted separately:

```bash
python3 packet_resource_preflight.py packet.zip chosen-directory --json \
  --runtime-copies 2 --runtime-bytes 90000000 --runtime-files 260 --runtime-directories 40 \
  --replay-copies 1 --replay-bytes 90000000 --replay-files 260 --replay-directories 40 \
  --extra-bytes 200000000 --extra-inodes 2500
```

The numbers above illustrate the interface; callers must measure their actual
workflow. Per-copy byte estimates represent allocated file bytes, with directory
allocation added by the tool. Runtime/replay defaults are zero so they must be
supplied for a workflow that creates those copies. Zero-length files still need
inodes. Compression ratios do not indicate extraction inode requirements.

The report includes the nearest existing destination ancestor, filesystem
identity, and Linux mount namespace when available. In execution environments
with per-command mount namespaces, a path such as `/dev` may be a transient
tmpfs. Verify persistence or keep one execution session alive for the entire
workflow, then copy final artifacts to persistent storage before it exits. The
tool never recommends root device locations automatically. tmpfs also shares
process/cgroup memory limits; its reported free bytes do not guarantee enough
memory. Cgroup memory values are reported when readable, without assuming that
all currently used memory is unreclaimable.

For the submitted packet, metadata-only inspection found 54,592 files and
34,585 directories: 89,177 inodes before runtime installation or evidence. The
payload is 743,606,679 bytes; rounding each file to 4 KiB produces 877,780,992
bytes, and the directory estimate adds 141,660,160 bytes. The offline Racket
installation adds 1,998 files, 142 directories, and 134,164,480 rounded file
bytes. Selected generation snapshots copy 251–255 mapped files with about
83.8–84.3 MB of payload, before allocation rounding and receipts. These figures
explain why a byte-only check could miss the extraction failure.

This is an optional shared tooling proposal. It can be retained under the
selected task's workspace in a return without changing locked shared harnesses.
