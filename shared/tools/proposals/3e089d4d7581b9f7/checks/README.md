# Evidence map and restoration

Paths here are relative to `WORK/`. In `RESULTS.json`, `.` means WORK and `packet_root` means the outer directory containing review.py and WORK. Each command also records its actual absolute working directory. Official controller reports retain their own exact temporary runtime locations and copied-file hashes. The original, fuller authoring metadata is `checks/handoff/author-results.json`; the supplied packager emits the normalized root RESULTS.json.

## Decisive final evidence

- `checks/after-final/result.json` and `checks/after-final/checks/1b2b9283b4ab_after_battery_summary.json`: completed 12-stage final battery, including required query rotations.
- `checks/task-tests/result.json` and `checks/task-tests/checks/task_tests.xml`: portable selected-task tests, 34 methods plus 214 passing subtests (248 JUnit cases), no failures/errors/skips.
- `checks/lesson-census-final.json`: 300 lessons, 1,200 materialized pair occurrences and query rotations, 1,198 unique inputs, no ambiguity against the declared rivals.
- `checks/schedule-census-final.json`: all four start residues at seed 0 across three difficulty bands; 12 overlapping lessons, 48 pair occurrences/rotations, 17 unique inputs.
- `checks/room-graph/final/report.json`: actual-cell graph probe, eight witnessed orientations and 44 joint-control checks. Exact input/output/rival fixtures accompany it.
- `checks/regressions/final-2.json` and `checks/regressions/call-contract-final.log`: focused room-graph and call-validation regression receipts.
- `checks/parametric/final/report.json` and `checks/parametric/final-tests.json`: proposed two-setting tie-marker prototype. This evidence is separate from canonical repair approval.
- `checks/audit/9cea0e6444f1/report.json` and `checks/audit/3642ceca5803/audit-report.json`: the two findings-only peer audits, including exact reference execution receipts.
- `checks/handoff/candidate-replay.json`, `checks/handoff/fresh-tests.json`, `checks/handoff/fresh-probe.json`, and `checks/handoff/tested-source-binding.json`: fresh dependency-closure replay, all 34 focused methods passing in that checkout's own environment, the relocated CLI probe, and exact tested-patch identity.

## Retained history

`checks/before/` binds the original version 3.0.2 (`43a5059c…`). `checks/after/`, `checks/lint-initial/`, `checks/schedule-census.json`, and the compressed intermediate large census bind the first version 4.0.0 implementation (`cd5e04fa…`). The first after battery failed defect lint because call arguments were still coercible. `checks/regressions/call-contract-red.log` reproduces those invalid calls; the final generator (`b7e78b1e…`) fixes them. Intermediate passes are not reported as final-source passes.

Development failures in `checks/parametric/` and both audit command receipts remain retained. These are implementation/tool-authoring history, not fabricated solver failures. The blind and exposed solver records each contain their one actual attempted revision, visible-only feedback and frozen finish notes.

## Restore the intermediate census

Only the all-green intermediate `checks/lesson-census.json` was replaced by its lossless gzip representation. Its companion summary is still directly readable. `checks/compressed-evidence.json` uses the supplied retention reader's `arc-review-evidence-archive-v1` contract, with full original-path/size/SHA mappings. No failed evidence was removed.

From `WORK/`, the following verifies both representations and restores only a missing original:

```bash
python3 - <<'PY'
from pathlib import Path
import gzip, hashlib, json
manifest = json.loads(Path('checks/compressed-evidence.json').read_text())
for entry in manifest['entries']:
    packed = Path(entry['compressed_path']).read_bytes()
    assert len(packed) == entry['compressed_bytes']
    assert hashlib.sha256(packed).hexdigest() == entry['compressed_sha256']
    raw = gzip.decompress(packed)
    assert len(raw) == entry['original_bytes']
    assert hashlib.sha256(raw).hexdigest() == entry['original_sha256']
    target = Path(entry['original_path'])
    if target.exists():
        assert target.read_bytes() == raw
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
    print(target, len(raw), entry['original_sha256'])
PY
```

If the supplied packager bundles `checks/` to meet its member limit, first use the restoration instructions it places beside that bundle. The inner gzip mapping above then restores the intermediate census. Neither operation retrieves any private solve labels.
