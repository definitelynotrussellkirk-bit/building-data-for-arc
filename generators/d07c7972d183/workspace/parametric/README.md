# Proposed periodic-continuation prototype

This opt-in authoring tool extends the original ARC family `training:017c7c7b`
(`d07c7972d183`). It leaves the canonical generator and rule unchanged. It is
a **proposed prototype**, with no variant acceptance or training admission.

## Rule and bounded parameters

Find the least finite period of the **complete rows** in a binary grid.
Continue that row pattern to `h + floor(h / extension_divisor)` rows, replacing
every input color 1 by `output_color` throughout the output.

| Parameter | Allowed exact integers | Original setting |
|---|---|---|
| `extension_divisor` | 2, 3 | 2 |
| `output_color` | 2, 3 | 2 |

Period inference, continuation phase, width, and the zero background remain
invariant. The divisor changes the extrapolation extent, and the color changes
the executed recoloring. The original `(2, 2)` setting returns the exact
canonical ledger program bytes. Other programs change only the corresponding
two literals; every private record retains its complete program and SHA-256.

The input grammar is unchanged and independent of settings: height 4..18,
width 3..12, whole-row period 2..6, at least two visible repeated-row cues,
and the canonical binary palette/motif constraints. Outputs have at most
27 rows. Demonstration count is **2..8**, independently of query count **1..8**.
Every accepted input is distinct within an episode. After two teaching draws,
the sampler allows at most 256 additional candidates; exhaustion raises instead
of duplicating inputs or returning fewer pairs.

## Run from WORK

Use a fresh output path. This exact command produces four complete paired
episodes, each with three demonstrations and four distinct query inputs:

```bash
python3 run_with_racket.py python3 generators/d07c7972d183/workspace/parametric/prototype.py --seed 17 --input-seed 17 --all-settings --demos 3 --queries 4 --out ../checks/parametric/paired
```

To choose one setting explicitly:

```bash
python3 run_with_racket.py python3 generators/d07c7972d183/workspace/parametric/prototype.py --seed 41 --settings '{"extension_divisor":3,"output_color":2}' --demos 2 --queries 4 --out ../checks/parametric/single
```

Omit `--settings` and `--all-settings` to choose one rule deterministically
from the episode seed. The choice is fixed for all demonstrations and queries.
An explicit `--input-seed` makes comparisons share inputs and ordering across
different settings or episode seeds. Seeds are exact integers in 0..2^63-1.
Boolean, floating, string-valued, incomplete, unknown, and out-of-range API
controls reject. CLI `--settings null` rejects rather than silently drawing.

## Labels, teaching, and exports

The protected Racket bridge supplies all labels. The first demonstration is
the canonical sampler's height-9/period-6 witness; the second has height 7 and
period 4. Together they identify all four declared settings and refute seven
parameter-aware Racket shortcuts: force the corner to zero, take the first
row recurrence, continue columns independently, output height nine, append
three rows, use ceiling extension, or repeat the full input. ARC Racket's
`/` performs integer division; the ceiling rival therefore uses the exact
integer formula `quotient(h + d - 1, d)`.

The certificate fits all candidate programs using demonstration labels only.
Its interface accepts query inputs without query labels. An execution error
does not count as teaching evidence. Each query gets a fresh surviving-rule
prediction. The writer re-executes labels and checks program, hash, source,
runtime, and certificate consistency before publication.

Give models only `public.jsonl` or files under `public/`. Their payloads use
`reviewer_support.public_challenge_bytes` exactly, including its final newline;
names are full SHA-256 content IDs from `public_challenge_id`. The batch is
unique and sorted by ID. Public payloads contain demonstration input/output
pairs and query inputs only. Private metadata and query answers cannot change
a public name.

`private.jsonl` contains seeds, settings, answers, source identities and
certificates. Exact program files are under `private/programs/`; `manifest.json`
binds all serialized files and the protected runtime. Duplicate public
episodes, existing output directories, stale private records, non-JSON metadata,
and nonfinite private numbers reject. All serialization completes before
directory creation; a final manifest marks a completed write.

## Focused checks and limits

```bash
python3 run_with_racket.py python3 generators/d07c7972d183/tests/test_parametric_prototype.py
```

These stdlib checks cover original labels, all settings, four-query episodes,
paired inputs, the 8+8 count boundary, 24 setting/input-boundary combinations,
strict numeric types, public identities, bad labels, bounded duplicate
exhaustion, integer-ceiling arithmetic, and pre-publication serialization.
They do not assert a passing production battery.

The declared finite rivals do not exhaust possible interpretations. The
mandatory teaching scaffold has a distinct distribution; its generalization
benefit is unmeasured. Counts above the stated limits and successful sampling
for every seed are not established. Evidence is source-bound and bounded.

`adapter.py` and `promotion.json` prepare the documented owner qualification
interface. They reuse this implementation and do not register or accept it.
Qualification, acceptance, inventory updates, and training decisions remain
separate owner actions.

