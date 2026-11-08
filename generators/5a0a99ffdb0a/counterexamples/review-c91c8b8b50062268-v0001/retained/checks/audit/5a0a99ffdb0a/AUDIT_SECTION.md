## 5a0a99ffdb0a

**Reproduced defects; audited source unchanged.** Target v2.0.0, generator SHA-256
`569741a2236e8da7ae9888a05a27d3a29c7b398710d858397fce143556bb387b`.
This is a bounded read-only source/Python audit. No Racket labels, broad battery,
lesson census, canonical authority, approval or training status were changed.

### A2-5A-CANONICAL-SEP — canonical inputs rejected by the validator

All **3/3 authoritative labeled inputs** (train[0], train[1], test[0]) have
full-height separator columns colored 5 at columns 3, 7 and 11. The target's
`self_check` rejects every one, emitting `separator column C must be full-height
color 9` for each separator. Changing **only those separator cells from 5 to 9**
makes all **3/3 controls pass**; the panels and their shapes/colors are untouched.
The canonical-rule splitter uses panel geometry and does not read separator
values. `_build` always emits 9, so this discrepancy also identifies excluded
canonical separator support; it does not show incorrect generated query labels.

The shared required gate `shared/tools/generator_selfcheck.py::check_canonical_inputs`
explicitly requires `self_check` to accept every authoritative canonical input.
The probe supplies the same canonical metadata fields as that gate. Retained
`probe.json` contains all three exact original inputs, original error lists,
separator-only controls and source/rule bindings. This is a canonical-domain
validation defect, independent of intentionally adversarial texture modes.
Recommended follow-up: align the validator's separator policy with the retained
canonical authority/examples and add canonical acceptance regressions.

### A2-5A-COLOR-CONTROL — advertised exact count is silently ignored

`AXES["n_distinct_colors"]` declares default 4 and valid range `3..4`, but
`generate` never consumes that override. At seed 17, sample index 0, easy,
requests `n_distinct_colors=3` and `=4` both succeed and return the **exact same
grid as the no-override call**. Each result has four distinct panel foreground
colors, plus background 0 and separator 9 (six grid colors in total). Thus the
request for three is neither honored nor rejected as incompatible. The exact
inputs, hashes, feature counts and empty self-check results are retained in
`probe.json` under `exact_control_cases`.
Recommended follow-up: implement the advertised feasible count or narrow the
contract and explicitly reject incompatible requests.

### Ordinary-draw control and limits

The audit separately inspected **12 ordinary draws**, seed 17, indices 0..3,
in each of easy/medium/hard. All **12/12 passed self_check**, and an independent
coordinate-based D8 normalization found three inequivalent prototypes and
exactly one query match in all **12/12**. This finite control does not establish
reference-output correctness or lesson identifiability. The declared
`single_cell`, `duplicate_protos` and `max_panel` adversarial textures were not
invoked and are not counted as default-distribution defects.

### Reproduction and evidence

Actual invocation, from `/dev/shm/arc_review_071004/extracted` (the outer packet
root), exit **0**:

```bash
/dev/shm/arc_review_071004/extracted/WORK/.venv/bin/python review.py run /dev/shm/arc_review_071004/extracted/WORK/.venv/bin/python ../checks/audit/5a0a99ffdb0a/probe.py --out ../checks/audit/5a0a99ffdb0a/probe.json
```

The wrapper reports effective payload cwd
`/dev/shm/arc_review_071004/extracted/WORK/repo`. Environment:
`PYTHONDONTWRITEBYTECODE=1`,
`TMPDIR=/dev/shm/arc_review_071004/extracted/WORK/.review/tmp`.
Exact command/cwd/exit and elapsed time: `checks/audit/5a0a99ffdb0a/command.json`.
Full stdout/stderr: `checks/audit/5a0a99ffdb0a/probe.log`.
Runnable probe: `checks/audit/5a0a99ffdb0a/probe.py`.
Source-bound cases and counts: `checks/audit/5a0a99ffdb0a/probe.json`.
Results remain **reviewer-reported**. No full runtime snapshot or Racket reference execution
was requested for this audit.
