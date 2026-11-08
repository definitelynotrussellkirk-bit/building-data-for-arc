# Supplementary tool-request reproduction

Ticket: `ticket-4d1d2f2f60a1092c`  
Request: `review-012cfa1a42bc531d:v0001:F3`

## Historical executed evidence

`probe.py` preserves the exact script bytes used for the single targeted probe. Its host-specific paths and start timestamp make it a historical artifact. The observed results in `probe.json`, `before_replay.json`, and `after_replay.json` are authoritative: before exited **0/WARN**; after exited **1/FAIL**, with easy and hard below the per-band floor. The historical script contained a prose typo saying exit 2. `outcome.json` corrects that wording without another policy execution. `command.json` records the actual command, inherited working directory, exit code, script hash, and this correction.

The single probe replayed synthetic morphology grids that reproduce every count in the pinned retained report. The asset contains aggregate counts, not the historical sample grids. No historical generator census or full battery was run.

## Portable replay

`replay.py` reads `retained_profile_floor.json` beside the script and validates the pinned request, manifest, generator, and retained asset. It reads the selected current policy from `WORK/repo`, measures the current invocation, and writes only a fresh output directory. It does not require the uploaded ZIP or the original host paths.

From the packet's `WORK/repo` directory, run:

```bash
python3 -B ../checks/tickets/ticket-4d1d2f2f60a1092c/replay.py --work .. --out ../checks/tickets/ticket-4d1d2f2f60a1092c/replay-run-001
```

Choose a different `--out` path if that directory already exists. `--work` may be omitted when this script remains in its original ticket directory; it then derives WORK from `__file__.parents[3]`. If a copy of the helper is moved elsewhere, pass `--work` explicitly. To check inputs and output-path handling without running the policy, append `--check-paths`. For usage, pass `--help`.

## Verification scope

The portable helper was **not** used to run a second targeted policy probe. Verification was limited to syntax compilation, `--help`, a read-only `--check-paths` invocation, and rejection of an existing output directory. No output directory was created by those checks. `portable_verification.json` retains their commands and results. The ticket's targeted-probe count remains **one**.
