## Findings-only audit: 0727bca3d518

**Disposition: reproduced training-distribution and override-contract defects; no source edits.** Generator version `2.1.1`, SHA-256 `0c26f5935d057f8f3b77c603b6a5dd930444625eba6758364915be246007e325`. Selected rule hash `e89facdfd983`, exact rule-text SHA-256 `465fd6913c5f5c0882ac8e3074b1f1674b624e15b875ee464512af6a7b2a3632`. The selected canonical rule and all three labeled canonical pairs were inspected. Current `notes.md` is a placeholder, `evidence/associated_notes.jsonl` is empty, and `evidence/review_index.json` is absent.

### Reproduced, high priority: rectangle-based sampling teaches a wrong square-core shortcut

A natural rival merges all nonzero/non9 colors, finds the largest completely filled axis-aligned square in each of the first two panels, and returns `ceil(square_side/2)` per panel. Actual selected Racket execution confirms this rival matches **all 60 generated inputs tested** (24 defaults and 36 helpful-texture/depth overrides), while failing **all 3 canonical pairs**:

| Canonical pair | Actual Racket output | Square-core rival |
|---|---|---|
| train 0 | `[[3,4]]` | `[[3,2]]` |
| train 1 | `[[1,3]]` | `[[1,2]]` |
| test 0 | `[[4,2]]` | `[[3,2]]` |

This is a generator-supported shortcut refuted by canonical demonstrations, **not** a canonical-fitting rival. Its significance is that generated teaching examples can reward the wrong geometric feature while withholding the canonical distinction. Canonical diamonds have greater Manhattan onion depth than their largest filled square indicates.

The mechanism is explicit in `_depth_shape` (generator lines 108–130): for target depth `d>=2`, every shape begins with a solid rectangle whose sides are at least `2*d-1`; only extra cells are added. The fallback is also a solid square. Generated depth 1 bodies have at most 5 cells, so cannot contain a 3x3 square. `_fill_panel` may add a separated shallow component, and `generate` verifies the final first-two-panel mirror depths exactly equal the targets (lines 228–229).

For a filled square of side `s`, actual onion depth is at least `ceil(s/2)`. The guaranteed `(2*d-1)` square gives the rival value at least `d`; the exact-depth check bounds it above by `d`. Therefore the source construction forces equality between this shortcut and the Python depth mirror for successful declared depth 1..3 outputs. This structural argument is distinct from the finite **63 actual-Racket executions** (all mirrors matched), and is not presented as exhaustive Racket validation.

The default sampler also caps both depths at 3 in every difficulty, including hard (lines 199–212). Thus it has **no default support for output value 4**, although value 4 appears in canonical train 0 and test 0. The undeclared override `depth1=4,panel_h=7` happens to be accepted; that does not supply default depth 4 coverage or diamond-shaped examples.

Minimal follow-up: sample diamond/Manhattan cores and other lawful nonrectangular masks, retain exact oracle labels, include depth 4 where geometrically feasible, and require generated lessons to contain counterexamples to the square-core rival. Add regression witnesses using the existing canonical diamonds. No authority change is warranted.

### Reproduced, medium priority: advertised overrides are inconsistent and invalid controls are accepted

At `seed=0,sample_index=0,difficulty=None`:

- `panel_h=4`, `9`, and `10` are declared valid by `AXES` (`4..10`) but each raises `ValueError` because the active draw range is `5..8`.
- `depth1=4,panel_h=7` is accepted although the advertised depth range is `1..3`.
- `depth1=True` and `depth1=1.5` are silently accepted as target depth 1.
- `texture="not_a_texture"` and `unknown_axis=1` are silently accepted.
- Control `depth1=0` correctly raises `ValueError`; the report does not claim all invalid values are accepted.

These are direct API execution results, independent of an input-output interpretation. Exact calls, exception messages, and observed mirror depths are retained in `report.json` under `controls`. Minimal follow-up: explicitly validate scalar types, exact legal axes, texture names and unknown keys, then reconcile declared height support with difficulty-dependent ranges. Preserve depth 4 support intentionally if adding it, rather than relying on the current bypass.

### Verification, exact scope and reproduction

All files are in `WORK/checks/audit/0727bca3d518/`. The executable command was:

```sh
# cwd: /workspace/scratch/b1624dafaa34/arc-review
WORK/.venv/bin/python review.py run ../.venv/bin/python ../checks/audit/0727bca3d518/audit_probe.py > WORK/checks/audit/0727bca3d518/probe.log 2>&1
```

**Exit code: 0.** The wrapper's payload cwd was `/workspace/scratch/b1624dafaa34/arc-review/WORK/repo`. The script uses `Catalog.apply(reference="canonical",check_generator_domain=True)` with actual included Racket, not the Python mirror as label authority.

Population: 3 canonical pairs; 24 default generated pairs at seeds 0..7, sample_index 0, each of easy/medium/hard; 36 override pairs at seed 0, index 0, unspecified difficulty, `panel_h=7`, all 9 ordered `depth1,depth2` combinations 1..3 crossed with all 4 helpful textures. The 9 override-controls are separate direct generator calls. All 63 actual outputs equal the independent stored canonical labels where present and the generator mirror; no generated label mismatch or execution error was found in this bounded cohort. No full battery was run or claimed.

The exact first canonical square-shortcut counterexample input hash is `a16f12a388d599e57ba4dbe8c23374abcf3fb01633c84a4598d84e243bda035d`. Full input/output arrays and rival predictions for every case are in `report.json`; authoritative outputs and rule/source hashes are in `racket_receipt.json`. `probe.log` retains stdout and wrapper context. The source remained unchanged throughout this audit.

Artifacts:

- `audit_probe.py`: SHA-256 `44fb932d01eb6f7344d2db84a93b2c6e300fb54ebd47e13e3b0792b82d60ef2c`.
- `report.json`: SHA-256 `faf1166df3da974ec46e2f43f0ad38a5a7dddd3674811665645a7ba4c89775b4`.
- `racket_receipt.json`: SHA-256 `98442eeb67cc114ad9b1dbdd40cb180eb5aaeefb5a3572e0fd09ec278b993616`.

This is source-bound findings-only evidence; it does not approve, repair, or change the target's status.
