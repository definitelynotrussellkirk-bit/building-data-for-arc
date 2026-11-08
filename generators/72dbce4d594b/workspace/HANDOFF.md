# Next-agent handoff: 72dbce4d594b

Do not redraw the assignment or change its baseline. Assignment is
`review-1ebfbb9437c3e8aa`; returned production generator is version 2.1.0,
SHA-256 `a6dba3cfd52647f610cd11abab494e063f8d766dc054f70c0e9ba90ee7e67880`.
Canonical rule remains `d291f7b88b55`. No audit target or shared source was edited.

## What changed

The original 12/12-green battery missed a command-table ambiguity: seed 0,
start 0, medium, four demos allow command 1 to mean a half-turn instead of
identity, changing the query. The preserved fixture reproduces it. The repair
uses five-demo lessons with one small canonical anchor and four asymmetric
teaching slots, all commands covered, all candidate objects asymmetric. It adds
28 single-command D4 rivals and fixes the per-seed profile parity defect.

## Apply and run

Use the repository's return intake path when available. For a manual replay,
place the original extracted packet at your working directory, preserve its
immutable assignment/baseline, extract the returned reports without overwriting
original sources, and inspect/apply the delta from that packet root:

```sh
git apply --check patches/source.patch
git apply patches/source.patch
python3 -m pytest -q repo/generators/72dbce4d594b/tests/test_review_regressions.py
python3 repo/generators/72dbce4d594b/workspace/instruction_table_probe.py \
  --case repo/generators/72dbce4d594b/workspace/baseline_ambiguous_lesson.json \
  --out checks/counterexample_replay.json
```

The fixture probe intentionally exits **1** because it demonstrates ambiguity.
The focused tests should pass (51 passed in the recorded run).

```sh
python3 repo/generators/72dbce4d594b/workspace/instruction_table_probe.py \
  --generator repo/generators/72dbce4d594b/generator.py \
  --support-root repo/shared/runtime --seeds 64 --starts 12 \
  --out checks/table_probe_replay.json
python3 setup_racket.py
python3 run_with_racket.py python3 -m arcpuzzles check 72dbce4d594b \
  --battery --timeout 4000 --phase after --out ../checks/after-replay
```

The battery destination must not already exist. The retained run is 12/12 green;
the finite independent probe is 0/2,304 ambiguous revised lessons.

## Gate actual exported episodes

Pass `--train 5` or `n_train=5`, then test the actual pairs after overrides,
filtering and retries. The shared exporter does not do this automatically.
For an ARC-style mapping with `train` and `test` arrays, import the workspace
module by path and call:

```python
# probe is the imported instruction_table_probe.py module.
report = probe.analyze(episode["train"], episode["test"])
if not report["passed"]:
    raise ValueError(report)  # retain report; resample/review, never relabel
```

The query entries need only an `input`; query labels are ignored. The generic
`factorized_gate` supports other instruction-keyed families, given named
predictors. D4 consensus is not uniqueness over arbitrary possible programs.

## Portable canonical replay

Build a portable workspace via the packet wrapper, copy `reference_probe.py`,
`instruction_table_probe.py`, and `baseline_ambiguous_lesson.json` to its root,
then rename that directory. Set `RACKET_PATH` to the installed Racket executable,
unset PYTHONPATH, change into the renamed directory, and run:

```sh
python3 -I reference_probe.py --out ../checks/reference_parity_replay.json
```

Recorded working directory: `relocated-runtime`, originally `portable-stage`.
The inherited tests ran before that rename. The reference probe checked 406
cases with actual Racket, the mirror and independent matrix code; all matched.
This is a portable-path check, not OS-level isolation.

## Do not lose these limitations

The inherited root-level task test has a stale expected rule hash: 278 passed,
1 failed. The full repository suite has a synthetic-packet import failure:
165 passed, 1 failed. Preserve them until fixed by an authorized shared-code
change. See F3/F4 rather than changing Racket to satisfy the literal.

The fresh solve contains one genuine revision, five visible passes, and two
unscored masked queries. Earlier rule exposure was yes; it is not a blind solve.
Do not call execution success hidden correctness. No Qwen model was trained and
no training admission was granted. The next substantive work is post-assembly
export gating, then independent replay and model evaluation—not adding another
arbitrary heuristic to this now-repaired default schedule.

## Restore large check reports only when needed

The official return has a 25 MiB expanded ZIP limit. The two verbose override
reports are therefore retained losslessly as `.json.gz`. No cases were pruned.
`checks/EVIDENCE_COMPRESSION.json` records original paths, sizes, SHA-256 values
and compressed hashes. From the extracted return root, restore exact bytes with:

```python
import gzip, hashlib, json
from pathlib import Path

manifest = json.loads(Path("checks/EVIDENCE_COMPRESSION.json").read_text())
for item in manifest["entries"]:
    source = Path(item["stored_path"])
    target = Path(item["original_path"])
    # Paths in this supplied manifest are relative and inside checks/.
    for path in (source, target):
        if path.is_absolute() or ".." in path.parts or path.parts[0] != "checks":
            raise ValueError(f"Unsafe evidence path: {path}")
    packed = source.read_bytes()
    assert hashlib.sha256(packed).hexdigest() == item["stored_sha256"]
    raw = gzip.decompress(packed)
    assert len(raw) == item["original_bytes"]
    assert hashlib.sha256(raw).hexdigest() == item["original_sha256"]
    if target.exists():
        assert target.read_bytes() == raw
    else:
        with target.open("xb") as stream:
            stream.write(raw)
```

Only run this on the validated return; the manifest's hashes bind bytes but are
not a general trust mechanism for arbitrary archives. Restoring adds roughly
31.5 MiB of raw reports. Do not leave restored copies under `checks/` when
rebuilding a constrained return ZIP unless you reapply the compression policy.
