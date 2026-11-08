# Lossless retention of the three large census reports

The three original census JSON files each contain 32,458,807 bytes. All three
are retained, including two intermediate source versions. They are compressed
individually under `checks/census-gzip/`, with an original-path/size/SHA-256 and
compressed-path/size/SHA-256 mapping in its `MANIFEST.json`. Compression reduced
97,376,421 original bytes to 2,873,317 gzip bytes. No report fields, labels,
instances, failures or source bindings were filtered.

`evidence_compression.py` is copied unchanged from the supplied retained
proposal `repo/shared/tools/proposals/f703d78e6ce3facb/checks/transport/`.
Its SHA-256 is
`de870fd2a915b3bda09a8625c495fc401010189b16e9fc5ef7e1abebde52748d`.
It uses only the Python standard library. The original reports were removed
only after the tool verified complete gzip roundtrips and rechecked source
bytes. Separate verify and actual restoration runs also passed; exact outputs
are in `compress.log`, `verify.log`, and `restore.log`.

## Which census is final?

| Original report | Generator SHA prefix | Phase |
|---|---|---|
| `checks/lesson-census.json` | `ab8562299a2076a9` | Intermediate, before removal of the mistaken uint32 seed restriction |
| `checks/lesson-census-final.json` | `2bb8371cd4389e27` | Intermediate, before the final malformed-shape rejection |
| `checks/lesson-census-repaired.json` | `416d21b39294a0c8` | Final generator, headline counts in REVIEW.md |

Each native file keeps its own exact source, Racket and runtime hashes. Its
original `*.summary.json` companion and console log remain under `checks/`.
The summary alone does not replace the full recoverable report.

## Verify and restore

After unpacking the return's standard evidence bundle, run from its `WORK/`
directory (the directory containing `checks/`):

```bash
python3 checks/transport/evidence_compression.py verify \
  --bundle checks/census-gzip
python3 checks/transport/evidence_compression.py restore \
  --bundle checks/census-gzip --out /absolute/path/to/new-census-restoration
```

The restoration directory must not already exist. It will contain the exact
original paths, for example
`checks/lesson-census-repaired.json`, beneath that new directory. Every stream
is checked against both compressed and raw sizes/hashes, and unsafe paths or
symlinks are rejected. Do not run against concurrently modified evidence.

The supplied return builder automatically bundles `checks/` to respect the
member limit; its bundle manifest covers these gzip streams and this helper.
Bundling alone does not reduce the expanded-byte budget, which is why the
three reports were first compressed losslessly. The outer return's native
intake and bundle verification remain enabled and unchanged.
