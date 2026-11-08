# Passive review receipt checker

`receipt_check.py` checks the structure and path references in a supplied
`WORK/RESULTS.json`. It uses only Python's standard library. It does not execute
recorded commands, edit the input, import a generator, parse evidence contents,
scan private solve data, or obtain reference answers. It is an optional reviewer
helper, not an additional maintainer acceptance gate.

## Run it

From the outer extracted packet directory:

```bash
python3 WORK/checks/receipt-helper/receipt_check.py --work-root WORK
```

The default results file is `<work-root>/RESULTS.json`. A positional results
filename is also supported; a relative positional filename is relative to the
caller's actual working directory. `--work-root` is likewise relative to the
caller. For example:

```bash
python3 WORK/checks/receipt-helper/receipt_check.py \
  WORK/RESULTS.json --work-root WORK --legacy-wrapper-policy error
```

When the helper lives beneath `WORK/` and that ancestor contains `repo/`, it can
discover the work root from its own location regardless of the caller's cwd:

```bash
python3 /path/to/extracted/WORK/checks/receipt-helper/receipt_check.py
```

Use `--work-root /path/to/fresh-replay/WORK` when checking a fresh replay or a
renamed workspace. The helper is a single-file executable script and does not
need an installed ARCpuzzles package, pytest, Racket, or access to a catalog.

### Optional expected source hash

Supply both flags to compare the current selected generator's **file bytes**
against an explicitly known final SHA-256:

```bash
python3 WORK/checks/receipt-helper/receipt_check.py --work-root WORK \
  --task-id YOUR_TASK_ID \
  --expected-final-generator-sha256 YOUR_ACTUAL_64_HEX_SHA256
```

The only extra file read by this option is
`WORK/repo/generators/<task-id>/generator.py`; it is hashed without importing or
executing it. Task IDs must be single safe directory names. Paths that escape
WORK through symlinks are rejected. A missing file or hash mismatch is an
error. Omitting both flags leaves the source check explicitly unknown; the
helper does not invent an expected hash from an unrelated receipt or assignment.

A `matched` result means only that the current generator bytes match the
caller's supplied hash. It does **not** establish that each cited report,
replayed patch, solve episode, or rule used those bytes. Evidence contents and
private solve/reference labels remain unopened. The source hash should come
from the final completed check the reviewer intends to cite.

## What is checked

- The input is a JSON object without duplicate keys or non-JSON numeric values.
  `completion_state` and `stopping_reason` are nonempty strings;
  `remaining_failures` and `verification_commands` are explicit arrays. The
  checker reports these as reviewer claims and does not approve a completion
  state or interpret the contents of a remaining-failure entry.
- Each command has a nonempty `argv` array of strings and a nonempty executable.
  Empty later arguments are allowed; NUL characters are rejected. The helper
  does not check executable availability, interpret shell code, validate every
  program's options, or reconstruct the historical environment.
- `cwd: "packet_root"` maps to the outer directory containing WORK. Other
  relative cwd values resolve inside WORK. An escaping relative path, missing
  relative directory, or file used as a directory is an error. Actual absolute
  cwd values are accepted, including ones outside WORK. An unavailable old or
  foreign-platform absolute cwd is reported as **unknown**, not rewritten or
  treated as proof that the original record was false.
- Each command has a nonempty `evidence_paths` array. Paths must be relative to
  WORK, resolve inside it after symlink resolution, and exist. Absolute paths,
  escapes, broken references, and non-regular special files are errors. A
  directory can be cited, but its contents and package membership are explicitly
  **not inventoried**. Files are checked for existence only; their contents,
  authenticity, nonemptiness, hashes, and semantic outcomes are not assessed.
- An actual integer `exit_code` is preserved, including a nonzero result. `null`
  remains unknown. A missing, string, float, or boolean exit code is malformed;
  in particular, JSON `false` is not accepted as exit code zero.

### Legacy wrapper diagnostic

`WORK/RETURN-GUIDE.md` places `run_with_racket.py` in WORK, but its reproduction
example combines outer `cwd: "packet_root"` with the bare script filename.
When a recognizable direct/Python script invocation would look for that missing
script at the outer root, the helper emits `legacy_wrapper_wrong_cwd`.

The default is a warning. `--legacy-wrapper-policy error` makes it an error.
The diagnostic also recognizes an actual absolute cwd that names the current
outer root. It does not flag `WORK/run_with_racket.py`, an absolute script path,
`review.py`, or arbitrary text passed to `echo`/Python `-c`. It does not unwrap
`env`, shells, or other launchers. Correct a record only to reflect what actually
ran; do not silently substitute a suggested command for its history.

## JSON output and exit status

Validation output is JSON on stdout. `--help` prints ordinary text help. The JSON
uses `arcpuzzles-passive-receipt-check-v1` and separates `errors`, `warnings`, and
`unknowns`. Each issue carries a stable code, field location, and explanation.
Per-command rows retain the reported cwd, resolved location, evidence existence,
exit code, and `recorded_zero` / `recorded_nonzero` / `unknown` outcome.

| Helper exit | Meaning |
|---|---|
| `0` | No receipt-validation errors. There can still be warnings, unknowns, reported failures, or recorded nonzero command exits. |
| `1` | Malformed or unavailable results, invalid command/path evidence, missing cited evidence, or an optional source-hash failure. |
| `2` | Invalid CLI arguments; the diagnostic is JSON. |

`validation_status` is `invalid`, `valid_with_unknowns`, or `valid`. The helper
always states `verification_status: "not_reexecuted"` and
`semantic_verdict: "not_assessed"`; it never emits a generator `passed` verdict.
An empty command array is explicitly unknown. No missing field is interpreted
as a successful check. A nonzero recorded test result does not by itself make
an honest, well-formed receipt invalid.

The checker writes no output files itself. If retaining stdout, choose a new
filename under `checks/`; shell redirection creates that file on the caller's
behalf. This helper cannot prove return-ZIP inclusion or substitute for the
required fresh-packet patch replay and focused test execution.

## Tests and retained evidence

From this directory:

```bash
python3 -m unittest -v test_receipt_check
```

The tests create temporary synthetic WORK trees inside this helper directory
and remove them afterward. They exercise actual CLI behavior, including a
sentinel command that would create a file if accidentally executed and a
generator that would raise if accidentally imported. No assigned task,
canonical data, solve record, or private reference label is read. The foreign
absolute-cwd regression also exercises Windows path syntax on the current host;
this is not a claim that the full test suite ran on Windows.

`verification.json` records the exact final test command, cwd, exit status,
counts, helper/test source hashes, and retained log path. Development failures
are described separately as expected preimplementation checks, not generator
or solve failures. Cite **`checks/receipt-helper/`** as a whole in feedback to
retain the helper, README, tests, and verification evidence together.
