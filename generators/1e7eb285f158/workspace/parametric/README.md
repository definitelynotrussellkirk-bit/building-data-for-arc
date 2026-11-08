# Largest zero rectangle: inset depth and tie order

**Status: proposed task-local prototype.** This adds a runnable authoring family
and qualification adapter; it does not change the selected production generator,
approve variants, clear inherited findings, or admit training data.

The reasoning remains: discover all-zero rectangles with height and width at
least three, maximize area, choose among equal maxima, and paint a cyan inset.

| Parameter | Allowed values | Canonical default |
|---|---|---|
| `inset_depth` | `1`, `2` | `1` |
| `tie_policy` | `row_major_first`, `row_major_last` | `row_major_first` |

The complete tie key is `(top, left, bottom, right)`. `row_major_last` reverses
that full key **after** maximizing area; it does not select the smallest area
or rank by the rectangle's bottom-right corner. The default `program(settings)`
returns the selected canonical Racket text byte-for-byte from `canonical.rkt`.
Alternative rules change only inset bounds and tie ordering. Rules remain total
on strict 1..30 integer grids: no eligible rectangle returns a copy, and depth
two paints nothing when the chosen rectangle is too thin for that inset.

## Run a four-query export

From the outer extracted packet directory:

```bash
python3 review.py setup
python3 review.py run python3 generators/1e7eb285f158/workspace/parametric/export.py \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/parametric/new-episodes
python3 WORK/check_public_exports.py WORK/checks/parametric/new-episodes/public \
  --demos 3 --queries 4
```

Use a new output directory. This command emits all four settings for each seed:
eight episodes, 24 demonstrations and 32 queries. Each episode fixes its setting
once. `--seed` is repeatable; omission uses seeds 0 and 17. `--demos` supports
3..12 and `--queries` supports 1..12 independently; unsupported counts fail.
The CLI uses the existing local protected Racket bridge and requires no extra
third-party package beyond the packet runtime.

The Python API `generate(seed, settings, demos=3, queries=4)` produces **Python
label claims** for the qualification worker. The CLI separately executes every
label through Racket, checks agreement, and retains those executed answers.
It also fits all four Racket candidate programs to demonstration labels only;
the intended setting must be the sole survivor before publication. Exact
program/input evaluations are cached within that export, including across
labeling and candidate fitting. A failed execution is never a rejected rival.

`public/<sha256>.json` contains only demonstration inputs/outputs and query
inputs. Its filename hashes the exact written bytes using the existing public
projection helpers. Seeds, settings, reference programs, query answers and
certificates are in `private/`. Files and records are ordered by public hash;
duplicate visible episodes and duplicate inputs within an episode are rejected
before creating the destination. Existing destinations are refused.

`write_export(episodes, out, report=None)` is a separate packaging helper. It
checks structure and projection, **not labels or rule execution**. Its default
report says Racket verification was not run. Use the CLI for verified exports.

## Why these demonstrations

The production distribution has a unique planted maximum or equal-size ties;
it does not teach area ranking against a smaller eligible competitor. The new
sampler makes the first demonstration select a 6x6 rectangle (area 36) over
7x5 and 5x7 rectangles (area 35). The winner is neither first nor last in scan
order, tallest nor widest. The next two demonstrations show a horizontal tie
and a cross-diagonal tie, separating column direction and row priority. The
first query adds a vertical tie. Other query inputs vary independently.

Every setting uses the same inputs and ordering for a fixed seed/count request.
The sampler's hashed local RNG streams include seed, split, pair index and retry
number; they exclude hidden settings and labels. Demonstrations and queries use
separate streams. All input grids in an episode are distinct. Every pair has a
32-attempt limit, with accepted attempts recorded; exhaustion fails explicitly.

The Python demonstration-only certificate eliminates the other three parameter
settings and ten declared shortcuts: paint the whole rectangle, paint every
maximum, choose the first/last eligible maximal rectangle, choose the tallest/
widest rectangle, use column-major ordering, reverse only the secondary tie
direction, echo the modal foreground, or do nothing. It receives no queries.
This is a conservative finite-family teaching check, not uniqueness among all
programs. The CLI's independent Racket fit covers the four parameter hypotheses;
the ten additional shortcut checks are Python evidence.

## Scope and tested limits

Sampled grids are 19..23 in each dimension, with selected rectangles 5..7 in each
dimension so both inset depths act. Smaller 3x4 competitors appear in tie scenes.
Nonzero guard rings separate planted rectangles; randomized outside-zero texture
is rejected if it creates another eligible rectangle. This avoids relying on the
production lattice, but the guard/slot geometry is still synthetic and limited.
This is not evidence of unrestricted canonical texture coverage or improved
model generalization. The 22/23 grid sizes extend the production 12..21 envelope.

Focused tests use only `unittest`, so reviewers can run them without installing
pytest (the inherited production tests still use pytest):

```bash
python3 review.py run python3 -m unittest discover \
  -s generators/1e7eb285f158/tests -p 'test_parametric_*.py' -v
```

Retained checks cover all four settings on seeds 0 and 17 with 3 demos/4 queries,
the maximum 12/12 request in Python, exact numeric-type rejection, deterministic
replay and RNG isolation, finite retries, literal inset/area/tie cases, all four
canonical examples, protected Racket parity and public/private export invariance.
The maximum-count case has not been re-executed through Racket in these authoring
checks. Final source-bound receipts live in `evidence/current/`; generated
episode evidence is delivered in the return's `checks/parametric/episodes-v2/`.

## Owner-side qualification

`adapter.py` loads the exact adjacent prototype, avoiding a cached module named
`prototype`; `promotion.json` declares all four settings and independent limits.
The source/evidence inventory is `evidence/manifest.json`. Building that inventory
does not run qualification or grant approval. The production source in this
packet is not approved; owner assessment and fresh native qualification remain
separate from this proposal.

After the owner has reviewed the selected production source and these variants,
the native qualification command is:

```bash
arcpuzzles parametric qualify 1e7eb285f158 --seed 0 --seed 17 \
  --demos 3 --queries 4 --out var/review/qualification-1e7eb285f158
```

Do not treat the authoring export, a passing test, or this proposed adapter as
an acceptance record or as authorization to change a training mixture.
