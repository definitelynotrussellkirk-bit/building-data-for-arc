# Restore exact large evidence files

Three complete JSON files are stored as gzip to fit the return budget: the
original override-failure report and the intermediate and final 300-lesson
censuses. No rows, grids, failures or rotations were removed.
`EVIDENCE_INDEX.json` records both paths, both byte counts and both SHA-256s.
The three originals total 54,930,095 bytes; the gzip files total 1,506,681 bytes.

From the extracted return directory, verify the retained compressed evidence:

```bash
python3 checks/evidence_archive.py verify --root .
```

Restore their exact original `.json` paths in that extracted return:

```bash
python3 checks/evidence_archive.py restore --root .
```

The helper verifies compressed and restored hashes/sizes, refuses unsafe paths
and symlinks, and does not overwrite a differing existing file. Identical
already-restored files are accepted. It leaves the gzip files and manifest in
place. Allow roughly 55 MB for restored originals. The command works with
standard-library Python; it does not require the ARC runtime or network.

If the packet builder places checks inside its native EVIDENCE-BUNDLE, extract
that bundle first. From the original packet's outer directory, run its supported
verification and extraction command, with absolute paths and a new destination:

```bash
python3 review.py run python3 -m arcpuzzles review evidence-extract /absolute/path/review_response_review-10591f5c6a4dc6fa.zip --out /absolute/path/new-evidence-directory
```

The commands above then run from that new evidence directory. To rerun the task-local generator
probe, apply `patches/source.patch` to the original packet as described in
RETURN-GUIDE.md, and run through `review.py run` from that packet's outer root.
Commands in RESULTS.json retain their actual original arguments; compressed
outputs can be inspected after restoration at the same paths.
