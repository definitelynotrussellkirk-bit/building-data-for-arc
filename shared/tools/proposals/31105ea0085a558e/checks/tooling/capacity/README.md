# Inspect packet extraction capacity

`inspect_packet_capacity.py` is a standalone, standard-library preflight for an
existing ZIP and a proposed extraction directory. It reads ZIP central-directory
names, sizes and attributes, and filesystem capacity metadata. It never opens a
member payload, extracts files, creates the destination, modifies a manifest,
chooses an assignment, or reads puzzle content.

```bash
python3 inspect_packet_capacity.py /absolute/path/request.zip /absolute/path/destination
python3 -m unittest -v
```

The JSON counts regular files, explicit and implied directories, and the new
destination directories that would be needed. The nearest existing destination
ancestor supplies the filesystem capacity snapshot. The inspector rejects
absolute/traversal/noncanonical names, duplicate members, symlinks and other
special files, inconsistent directory metadata, and file/directory conflicts.
This is lexical POSIX validation, not a complete extraction security audit.

Exit codes:

| Code | JSON `capacity_status` | Meaning |
| --- | --- | --- |
| 0 | `lower_bounds_fit` | The recorded lower bounds fit the available resources. This does not guarantee success. |
| 1 | `insufficient` | At least one known bound exceeds current availability. |
| 2 | `invalid_input` | The ZIP, destination, or member inventory is invalid. |
| 3 | `unknown` | No known shortfall, but one or more availability measures are unknown. |

Zero **total** inodes means inode availability is unknown, represented by JSON
`null`; zero **available** inodes with a known positive total means exhaustion.
Headroom is finite integer subtraction, or `null`, never infinity or NaN.

File-data allocation is a lower bound **under the ordinary dense-file model**:
round each file up to the `statvfs` allocation unit before summing. Zero-byte
files need inodes but contribute zero file-data bytes. Compression, sparse files,
deduplication, directory storage, filesystem metadata, quotas, permissions,
baseline/runtime copies and concurrent usage are not modeled. Existing destination
contents and filesystem-specific name equivalence are not inspected. The ZIP's
payload CRCs, local headers and content hashes are not verified. Use an empty
destination with additional headroom and verify the extracted packet separately.

`verification.json` records the exact test and real-packet inspection commands,
exit codes, source/tool hashes and retained evidence hashes. `unittest.log`
contains the focused test run. `receipt-scratch.json` and `receipt-dev-shm.json`
are point-in-time observations, not persistent capacity reservations.

The module and tests can be copied together to `checks/tooling/capacity/` as
optional shared-tool feedback. They do not replace or patch any issued reviewer
tool, and they make no generator, rule, solve, or assignment decision.
