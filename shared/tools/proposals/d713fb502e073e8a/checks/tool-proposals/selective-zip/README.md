# Selective ZIP review helper

`selective_zip.py` is a dependency-free Python CLI for inspecting a large review
packet and extracting an explicitly selected subset into a **new** directory.
It was tested with Python 3.12 and uses only the standard library.

The helper does not execute archive contents. Listing and preflight inspect the
ZIP central directory without opening member payloads. Extraction streams only
selected files, checks their ZIP CRCs, and reports a SHA-256 hash for each file.
It never modifies the source ZIP.

## Quick start

```bash
ARC_ZIP='/path/to/SEND-THIS-ARCpuzzles-review(20261020-130326).zip'

# Counts and byte sizes by subtree; no extraction.
python selective_zip.py list "$ARC_ZIP" --depth 3

# Inspect exact member names under a selected subtree.
python selective_zip.py list "$ARC_ZIP" \
  --include 'WORK/repo/src/' --members --json

# Check an explicit selection and a fresh destination before writing.
python selective_zip.py preflight "$ARC_ZIP" ./review-bootstrap \
  --include 'review.py' \
  --include 'START-HERE.md' \
  --include 'WORK/repo/src/' \
  --include 'WORK/repo/shared/runtime/'

# Run the same selection as an extraction; save its hash report separately.
python selective_zip.py extract "$ARC_ZIP" ./review-bootstrap \
  --include 'review.py' \
  --include 'START-HERE.md' \
  --include 'WORK/repo/src/' \
  --include 'WORK/repo/shared/runtime/' \
  --json > review-bootstrap-extraction.json
```

The destination's parent must already exist. The destination itself must not
exist, even if empty. Use a separate fresh destination for each extraction.
The tool does not merge into an existing working tree.

### Selection semantics

| Selector | Meaning |
| --- | --- |
| `--include 'review.py'` | The exact member `review.py` |
| `--include 'WORK/repo/src/'` | Every member whose name begins with that literal prefix |
| `--exclude 'WORK/repo/shared/tools/proposals/'` | Omit that subtree from any included selection |
| `--all` | Explicitly include all members before exclusions |

Repeat `--include` and `--exclude` as needed. Selectors are **literal**; shell
wildcards and glob syntax are not interpreted. Directory selectors must end in
`/`. Include and exclude selectors are case-sensitive, matching ZIP member
names. Exclusions take precedence. An include selector that matches nothing is
an error, and a selection with no remaining members is an error. Unmatched
exclusions produce a note.

`list` and `preflight` inspect the whole archive if no include is supplied.
`extract` requires at least one `--include` or explicit `--all`; it will never
extract the full archive accidentally because a selector was omitted.

### Budgets and reports

Preflight and extraction use these defaults:

| Setting | Default |
| --- | ---: |
| `--max-bytes` | 536,870,912 uncompressed bytes (512 MiB) |
| `--max-members` | 20,000 selected ZIP entries |
| `--reserve-bytes` | 67,108,864 disk bytes (64 MiB) left free |
| `--reserve-inodes` | 128 filesystem inodes left free, when measurable |

All budget arguments are nonnegative integer counts. Set different values only
after reviewing the selection and available space. Raising budgets does not
disable path or collision checks.

The disk estimate rounds file sizes to filesystem allocation blocks and adds a
block for each output directory. The inode estimate includes files, explicit
and implied directories, and the destination root. These are estimates, not a
reservation: filesystem quotas, metadata, unusual allocation rules, and other
processes can still cause extraction to fail.

`--json` returns counts, selected and omitted byte totals, selectors, errors,
warnings, and available storage. Successful extraction additionally returns a
`files` array containing each selected file's original archive path, byte count,
and SHA-256 digest. No report file is inserted into the extracted tree.

Exit status is `0` for success and `2` for a rejected request or extraction
failure. Argument syntax errors also use `2`. `list` is an inventory operation,
not a safety check; its `paths_validated` field remains false. Preflight does
not check member CRCs or decompress content, and its
`selected_contents_verified` field remains false.

## Safety behavior

Before any output is created, the selected members are checked for:

- Absolute paths, traversal components, empty or dot path components,
  backslashes, NUL truncation, control characters, Windows device names and
  ambiguous punctuation, and trailing periods or spaces.
- Duplicate member paths, case-folded or Unicode-normalization aliases, and
  file/directory conflicts, including implied parent directories.
- Symlinks, special filesystem types, inconsistent directory types,
  directories with payload data, encrypted or compressed-patch members, and unsupported
  compression methods.
- Excessive path depth or size: at most 128 components, 4,096 UTF-8 bytes in a
  member name, and 255 UTF-8 bytes in a component.
- Existing destinations and symlinked or missing destination ancestors.

Extraction creates the destination exclusively, uses exclusive file creation,
and streams in 1 MiB chunks. It also checks actual uncompressed lengths against
declared lengths and the byte budget. CRC, I/O, and other handled failures
remove the newly created partial directory. Forced termination or an inability
to remove files can leave a partial directory; cleanup failure is reported.

The output contains the original selected file bytes and archive-relative
paths. It does not preserve timestamps, ownership, ZIP container metadata,
setuid bits, or group/world permissions. Output directories are private, files
are private, and the owner's executable bit is retained when present.

Use a trusted destination parent that other processes are not concurrently
renaming or replacing. This tool protects against hostile archive member
paths; it does not provide an OS sandbox or defend against a hostile local
process with the same filesystem privileges. Python's ZIP parser still needs
memory proportional to the central directory. Nothing is executed, and the
helper does not decide which source code or puzzle content is appropriate to
read at a particular review phase.

## Observed packet size and bootstrap example

The supplied packet has **87,941 members and 1,297,397,589 uncompressed bytes**.
The following measurements came only from filenames and sizes in its central
directory; no puzzle, generator, rule, answer, or note contents were opened.

| Subtree | Entries | Uncompressed bytes |
| --- | ---: | ---: |
| `WORK/repo/generators/` | 70,610 | 723,801,834 |
| `WORK/repo/shared/` | 15,982 | 503,917,377 |
| `WORK/repo/shared/tools/proposals/` (within shared) | 11,381 | 248,153,519 |
| `WORK/repo/REVIEW/` | 1,158 | 9,205,889 |
| `WORK/repo/catalog/` | 4 | 7,663,446 |
| `WORK/repo/src/` | 59 | 1,970,834 |
| `WORK/repo/shared/runtime/` (within shared) | 142 | 3,593,921 |
| `WORK/repo/tests/` | 92 | 672,327 |
| Bundled Racket tarball | 1 | 34,026,024 |
| `WORK/PACKET-MANIFEST.json` | 1 | 15,861,675 |

The source archive also contains two distinct members with these paths:

```text
WORK/repo/generators/4fd85612056f/workspace/reviewer-tools/second-pass-d91c405b/MANIFEST.json
WORK/repo/generators/4fd85612056f/workspace/reviewer-tools/second-pass-d91c405b/manifest.json
```

Their sizes are 2,552 and 3,967 bytes. They collide on a case-insensitive
filesystem, so this helper's conservative policy rejects a full extraction.
It also reports that the full archive exceeds the default byte and entry
budgets. The original ZIP retains both members; the helper does not silently
rename or discard either one.

A broader bootstrap-only example preflights successfully:

```bash
python selective_zip.py preflight "$ARC_ZIP" ./review-bootstrap \
  --include 'review.py' \
  --include 'START-HERE.md' \
  --include 'WORK/setup_racket.py' \
  --include 'WORK/run_with_racket.py' \
  --include 'WORK/solve_episode.py' \
  --include 'WORK/package_return.py' \
  --include 'WORK/assignment.py' \
  --include 'WORK/repo/setup.py' \
  --include 'WORK/repo/pyproject.toml' \
  --include 'WORK/repo/src/' \
  --include 'WORK/repo/shared/runtime/' \
  --include 'WORK/repo/shared/tools/' \
  --exclude 'WORK/repo/shared/tools/proposals/' \
  --exclude 'WORK/repo/shared/tools/evidence/' \
  --json
```

That selection contains **266 entries and 6,994,191 uncompressed bytes** and
omits **87,675 entries**. On the checked filesystem it estimates 7,843,840 disk
bytes and 326 inodes. It was preflighted, not extracted or executed. The saved
`core_preflight.json` records the observation; available space can change.

This is only a starting selection for a working tree. It omits the assignment's
generator, puzzle assets, canonical data, most evidence and histories, review
handoff material, the packet manifest, and the bundled Racket distribution.
Add the exact assets required by the task at the allowed review phase. A sparse
copy is **not** equivalent to the original packet, does not demonstrate that a
runtime is complete, and must not be used to claim full packet verification or
archival preservation. The original ZIP remains the authoritative complete
container.

## Tests

From this directory:

```bash
python -m unittest discover -v
```

These tests exercise real temporary-file I/O and the extractor's real capacity
checks. Successful extraction cases need the temporary filesystem to report
more than **64 MiB of available space**, plus the small synthetic files and
directory allocations, and more than the default 128-inode reserve where
inodes are reported. The suite also creates symlinks and checks POSIX file
permissions; it was exercised on Linux. An exhausted or quota-constrained
default temporary directory can therefore prevent success-path tests from
reaching the behavior they intend to check.

Select a writable temporary filesystem with enough reported available space:

```bash
TMPDIR=/path/to/private-temp-directory python -B -m unittest discover -v
```

On Linux, a private directory under `/dev/shm` is another option when permitted
and when it has sufficient free capacity. In an execution environment with
separate filesystem namespaces, create the private directory and run the suite
in the same namespace. This changes only where test scratch files are created;
it does not lower the extractor's reserve or replace its disk checks with mocks.

The synthetic-archive tests cover byte preservation, selective omissions,
path attacks, aliases and duplicates, file/parent conflicts, symlinks and
special entries, destination protection, budgets and storage reserves,
corrupted CRC cleanup, encryption and compression rejection, SHA-256 reports,
permission handling, and the distinction between preflight and content
verification. `test_results.txt` records the initial successful run. A later
run with `/tmp` reporting zero available bytes produced 8 failures among 24
tests because preflight rejected the success paths. A fresh reproduction is
preserved in `test_results_constrained_tmp.txt`. The identical, unmodified
24-test suite then passed with a private `/dev/shm` temporary directory and
approximately 2.00 GB available; see `test_results_shm.txt`. The private
temporary directory was removed afterward. `test_environment_verification.json`
records both outcomes and the unchanged code/test hashes.
