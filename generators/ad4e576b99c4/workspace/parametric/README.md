# Proposed parametric opposite-side shear

**Status: proposed/unapproved. `training_admitted: false`.** This task-local prototype does not change the canonical generator, canonical Racket authority, global approvals, or training admission.

The hidden parameter `shear_start_rows` has exactly three integer settings: **2, 3, 4**, with canonical default **3**. At source-relative row `dr`, displacement inward from the opposite horizontal edge is `max(0, dr - (shear_start_rows - 1))`. The exact source rectangle, including color-1 holes, moves without reflection. The source clears to color 1. The split and lower color-6 field remain fixed. The first color-6 row receives the canonical color-9 border using the new final displacement; its endpoint convention is preserved.

The input domain remains the unchanged production generator's domain: grid dimensions 16–22, patch width 3–7, patch height 4–10, bottom field height 3–6, and either horizontal side. The largest displacement is 8, so even the smallest width accommodates the widest patch (`8 + 7 <= 16`). Inputs are sampled by the source-bound production generator with lawful exact overrides for side and height. Parameter changes do not affect the inputs.

## Run

From the packet's outer directory, the supplied wrapper selects the protected
Racket runtime and runs the payload from `WORK/repo`:

```bash
python3 review.py setup
python3 review.py run python generators/ad4e576b99c4/workspace/parametric/prototype.py \
  --seed 42042 --settings 2 3 4 --demos 2 --queries 4 \
  --out ../checks/my-new-parametric-batch
```

From the repository root, with its Python dependencies and protected Racket runtime available:

```bash
python generators/ad4e576b99c4/workspace/parametric/prototype.py \
  --seed 42042 --settings 2 3 4 --demos 2 --queries 4 \
  --out /tmp/ad4e576b99c4-paired-batch

python -m pytest -q generators/ad4e576b99c4/tests/test_parametric_shear.py
```

`--out` must identify a new directory. Omitting `--settings` runs all three settings. The CLI uses the same input seed for every setting, yielding paired inputs with different demonstrated and query outputs. Repeating a setting in the same CLI batch is an error. Racket startup, execution, or timeout errors are surfaced; there is no label fallback.

Python API:

```python
# Load this task-local module by its file path, or use it in an existing task harness.
validate_parameter(3)
program = program_for(2)
a = make_episode(17, shear_start_rows=2, input_seed=42042)
b = make_episode(17, shear_start_rows=4, input_seed=42042)
public_ids = write_batch([a, b], '/tmp/a-new-paired-batch')
```

`make_episode(seed, *, shear_start_rows=3, n_demo=2, n_query=4, input_seed=None, timeout_ms=4000)` accepts exact Python integers only. Booleans, floats, and strings are rejected for numeric API inputs. Seeds must be nonnegative; `n_demo` is 1–8, `n_query` is 1–32, and `timeout_ms` is 1–60000. Omitting `input_seed` uses `seed`. Request validation precedes source loading and Racket startup.

## Sampling and bounded evidence

Each requested input is distinct across demonstrations and queries. Sampling permits at most 64 attempts per slot and raises a diagnostic on exhaustion. The first demonstration has a noncanonical source mask. With at least two demonstrations, both horizontal sides appear. Default queries cover heights 4, 10, 6, and 8 and both sides. These schedules are public, lawful, and independent of the hidden setting.

Every accepted demonstration and query output comes from the packet's actual protected `arc_repl.racket_bridge.RacketBridge`. This is the packet's persistent Racket session class; the packet does not expose a class named `RacketSession`. Standalone program text is read from the source-bound canonical ledger. Setting 3 uses the exact canonical text. Alternatives substitute only the three validated delay literals: two final-foot expressions and one row-shift expression. The canonical generator rule pin remains `6de9bdaa4c45`; the exact canonical program SHA-256 is checked independently.

The private certificate checks **14 explicitly named candidates**: all three legal settings executed in Racket; fixed-public-comb, same-side, and border-off-by-one rivals at each setting; identity; and no-shear. Supplementary Python code predicts only the declared wrong-rule rivals. The border rival extends the color-9 region by one cell toward the foot.

Candidate fitting sees demonstration inputs and outputs only. After fitting, candidate predictions on query inputs are compared against one another. A batch is rejected if no candidate fits, or if any surviving candidate gives a different query answer. Query gold and the hidden setting do not select survivors. The certificate reports the family, survivors, eliminated candidates, and per-query disagreements. This is finite candidate evidence, not a claim of universal identifiability.

## Output and verification

The writer regenerates each entire episode before writing, including deterministic source inputs, exact counts, real-Racket labels, program text and hashes, source and prototype identity, and the certificate. Caller-supplied certificates or flags are never trusted. Comparison uses full serialized private data so Python's equality between booleans and integers cannot conceal type tampering. Reverification deliberately incurs another bounded Racket run.

```text
batch/
  public/
    <visible-sha256>.json
  private/
    manifest.json
    episodes/
      <visible-sha256>.json
```

Public files use the shared `public_challenge_bytes` projection and `public_challenge_id`. Their exact written bytes define the filename SHA-256. They contain only demonstrations (`input`, `output`) and query `input` grids. They contain no query labels, parameter values, seeds, programs, hashes, certificates, or setting map. Public entries and the private manifest's ID list are sorted by visible ID.

Private episode records include all query labels, exact standalone programs and their hashes for each setting, generator and prototype hashes, canonical parent identity, sampling bounds, hidden setting, and finite certificate. The private manifest stores the visible-ID-to-setting mapping. Duplicate visible payloads are rejected before a batch is committed. Files are prepared in a sibling staging directory, then the completed directory is renamed into place; verification failures leave no advertised public output.

Focused tests cover canonical equivalence on canonical and newly sampled examples; paired alternative settings; distinct inputs and requested counts; strict numeric gates; finite demo-only evidence; public byte identity and privacy; duplicate rejection; bounded sampling exhaustion; and query-label, certificate, program, count, input, and provenance tampering.

## Retained example and reusable checks

`evidence/paired-batch-v1/` retains three verified episodes made with seed 42042:
two demonstrations and four queries for each setting, using the same six inputs
across settings. Its public challenges are ready for visible-only use; answers
and the setting map stay under `private/`. `evidence/manifest.json` binds this
example, code, tests, and independent boundary evidence to the exact source.

The delta also includes `checks/record_check.py`. From the packet's outer
directory, after activating its Python dependencies and Racket environment, run
`python WORK/checks/record_check.py --timeout 180 new-check-name -- COMMAND ...`.
It runs one command from `WORK/repo`, enforces a timeout, saves stdout/stderr and
source hashes in a new check directory, and appends the exact result to
`WORK/RESULTS.json`. Use a new name after edits. `checks/independent_check.py`
retains the separate point-transport oracle used for the 24 Racket boundary
comparisons; its expected results do not use the prototype's rival renderer.
