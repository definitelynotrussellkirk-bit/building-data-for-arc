# Findings-only audit: 3374854ed70d

**Disposition:** concrete override and validation defects reproduced; no audited source was edited. This is a bounded audit, not an approval or a completed generator repair.

## Source and evidence

- Audited generator: `repo/generators/3374854ed70d/generator.py`.
- Generator SHA-256: `09f4b9207c186222dc7545facfcbd40c1de94c553ac864c37976e3ea5aa0ecae`.
- Current notes read: `repo/generators/3374854ed70d/notes.md`, SHA-256 `96e2dbdc5e8cb8562118d86707edb8e9b589a489008fdb85adf4fc5feb6d40da`.
- The current `evidence/review_index.json` is absent. No historical review is represented as a current admission result.
- Canonical row reviewed: task `3374854ed70d`, including its rule, three training examples, and one test example. The rule fills the full down-right diagonal containing each seed; row-minus-column identifies a diagonal.
- Catalog and publicly executed rule hash: `1af28fc8f46c`. Public execution's rule-text SHA-256: `c6274f1955bc6ca161c0b4980cc3fb1a483ca75053c0387cdbda8e131d0b3b2a`.

`probe.py` is the standalone reproducible probe. `probe.json` contains all paired measurements and witnesses. `public_racket_label.json` is the public canonical Racket receipt. `receipt.json`, `stdout.txt`, and `stderr.txt` preserve the exact invocation, both working directories, environment overrides, exit code, and timing.

## Findings

### 1. Medium: advertised palette and color-count controls are inert

The generator advertises `palette_size`, `n_distinct_colors`, `palette_kind`, and helpful `texture` values, but its ordinary generation path never consumes these controls. Colors are chosen solely using `seed_count` and the `colors` draw. The only `texture` handling selects three explicit degenerate examples.

The probe tested seeds 0 through 7, with sample indices 0 and 3. In all 16 cases per axis, both advertised alternative values produced exactly the default input grid:

| Axis | Compared values | Identical to the default |
|---|---|---:|
| `palette_size` | 1 and 8 | 16/16 paired cases |
| `n_distinct_colors` | 1 and 8 | 16/16 paired cases |
| `palette_kind` | `warm` and `cool` | 16/16 paired cases |
| `texture` | `warm` and `cool` | 16/16 paired cases |

The smallest retained control witness is `generate(0, 0, n_distinct_colors=1)`: it returns **two** distinct nonzero colors, and the input is identical to the unmodified call. Public canonical Racket execution returned a valid output and the generator's domain checker accepted the input. Input SHA-256: `a1fe409ba396d98d3b50fae2654e18ec5fb51e2acdd70233d0f77a2b3d749dda`; output SHA-256: `374ea320c3db48536e86a5b1f421d6a051ee57249d8b912fe3d67aa0ed57fec8`.

**Consequence:** a caller requesting a palette or color-count intervention gets neither an implemented intervention nor an error. The declared diversity surface substantially overstates the generator's effective controls. This finding concerns the generator contract; the retained ordinary-grid witness has a valid canonical label.

**Suggested repair:** implement and validate these controls, or remove unsupported declarations. Bind actual colors and palette counts to the controls and preserve their realized values in generation metadata.

### 2. Medium: declared valid ranges exceed accepted override ranges

With no difficulty argument, the published `valid` ranges say `grid_h` and `grid_w` accept 5 through 14 and `seed_count` accepts 1 through 8. All six boundary requests below were rejected:

| Requested override | Actual error |
|---|---|
| `grid_h=5` or `grid_h=14` | Outside `[7, 10]` |
| `grid_w=5` or `grid_w=14` | Outside `[7, 10]` |
| `seed_count=1` or `seed_count=8` | Outside `[2, 4]` |

The source passes default sampling bounds to `ctx.draw_int`; that helper also uses those same bounds to validate explicit overrides. This conflates the default distribution with the advertised valid domain.

**Consequence:** reproducible coverage of the declared boundary shapes and seed counts is unavailable through the generator's advertised interface.

**Suggested repair:** separate explicit override validation from default sampling, or truthfully narrow `AXES`. Keep `self_check` and any metadata-aware domain validation aligned with the chosen override contract.

### 3. Medium: `self_check` accepts Boolean colors and raises on malformed later rows

A 7×7 grid containing `True` at row 1, column 2 and integer color 2 at row 4, column 1 returns an empty error list from `self_check`. The public `validate_grid` rejects the same value with `ValueError: grid cells must be integers 0..9`. The cause is `isinstance(v, int)`, which accepts Boolean values.

Separately, replacing the second row of an ordinary generated grid with `None` raises `TypeError: object of type 'NoneType' has no len()` instead of returning a schema error. The checker validates the first row's type but calls `len(row)` on later rows without checking their type.

**Consequence:** self-check success does not imply admission to the packet's public grid schema, and malformed data can crash the checker.

**Suggested repair:** validate every row before accessing it and require `type(cell) is int`. Return explicit schema errors before evaluating domain invariants.

## Execution and scope

The exact executed command was:

```text
/dev/shm/arcpuzzles_review_15a8b14353eb3e0a/WORK/.venv/bin/python /dev/shm/arcpuzzles_review_15a8b14353eb3e0a/WORK/run_with_racket.py /dev/shm/arcpuzzles_review_15a8b14353eb3e0a/WORK/.venv/bin/python ../checks/audit/3374854ed70d/probe.py
```

Launch cwd: `/dev/shm/arcpuzzles_review_15a8b14353eb3e0a/WORK`. Effective payload cwd: the same path with `/repo` appended. Environment overrides were `TMPDIR=/dev/shm/arcpuzzles_audit_tmp_15a8b14353eb3e0a` and `PYTHONDONTWRITEBYTECODE=1`.

Exit code: **0**. Wall time: **10.572 seconds**; probe time: **8.457 seconds**. Exit zero means the recorded findings were successfully reproduced, not that the audited generator passed review. Source bytes were checked unchanged at completion. The one Racket-labelled witness has matching catalog and executed rule hashes, `valid_output=true`, and no generator-domain errors; its receipt explicitly retains `approved=false` and `train_safety=unverified`.

No full battery, broad curriculum census, or source repair was attempted for this audit target. The probes establish the concrete contract defects above and do not establish an error in ordinary canonical rule execution or certify shortcut resistance.
