# Beam-axis episode prototype — 0b8ba9bb3c63

**Status: prototype, proposed and unapproved.** This is a separate authoring
experiment for the original `training:6ffe8f07` family. It does not change the
selected `generate(...)` API, its canonical Racket authority, or any approval
record. Canonical generator repairs have their own tests and review scope.

## Rule and parameter

The sole rule parameter is `beam_axes`, fixed for the entire episode:

| Setting | Executed transformation |
|---|---|
| `both` (original/default) | Emit horizontal and vertical yellow beams from the cyan rectangle. |
| `horizontal` | Emit only the cyan rectangle's horizontal row bands. |
| `vertical` | Emit only the cyan rectangle's vertical column bands. |

All settings preserve the cyan emitter (8), yellow beam color (4), transparent
red rectangles (2), black background (0), per-ray blocker clipping, and final
restoration of the emitter and blockers. Blockers keep their original colors.
Red cells are overwritten only where an active, unobstructed beam reaches them.
Objects and pixels outside the active beam remain unchanged.

`both.rkt` is the **exact selected canonical source**, including whitespace,
read from the canonical ledger. Its byte SHA-256 is
`e73f49035ca5d73e3c73948c0b15e2b6f1985366674de313cbf978463088d977`;
its normalized rule SHA-256 is
`757441c9ab4aa17070a3826de76e0b0f74e66636398f3f3aaa4392e47af17bcb`.
`horizontal.rkt` replaces only `(range cc1 (+ cc2 1))` with `'()`;
`vertical.rkt` replaces only `(range cr1 (+ cr2 1))` with `'()`.
This disables one traversal while leaving every clipping and restoration
expression intact. The original program is not rewritten or relabeled.

The `.rkt` files use the repository's `(rule! ...)` form. `apply_rule` uses the
shared `strip_rule_wrapper` helper to expose their explicit, self-contained
lambdas, then executes them in the **included `RacketBridge`**. All example and
rival outputs are real Racket results. The independent Python ray walk exists
only in the test file as a semantic cross-check; it never labels an episode.

## Deterministic episode API

```python
# Load this task-local prototype.py with importlib.util, or run its CLI below.
episode = build_episode(11)                        # canonical default: both
episode = build_episode(11, beam_axes="vertical")   # explicitly fixed rule
episode = build_episode(11, beam_axes=None)         # one seed-derived rule draw
public_challenge = episode["public"]
private_metadata_and_answers = episode["private"]
```

Seeds are literal integers in `0..2**64-1`; Boolean and coercible string/float
seeds are rejected. Rule selection and layout use separate SHA-256 seed
domains. Construction never changes the global Python RNG. `beam_axes=None`
selects one setting once, and that same program labels all three demonstrations
and the query. Omitting the parameter retains the canonical `both` default.

Inputs do not depend on `beam_axes`. For the same seed, all three settings have
identical input grids, so the settings cannot be read from an input-only cue.
Every episode contains three demonstrations followed by one query. Demonstration
dimensions are independently sampled in 23..27; the final query is **30 × 30**.
Each scene has one 3..5 by 3..5 cyan rectangle, four 2 × 2 blockers, and five red
rectangles. Four red objects intersect the beam bands; one sits beyond a
blocker and stays red. Each side has a partially clipping blocker, with visible
beam space before it. The constructor applies a deterministic reflection and
quarter-turn rotation and checks every input with the selected generator's
canonical `self_check`.

These input constraints are the same for all settings. Both axes are visible
in every input deliberately: each individual labeled pair distinguishes all
three settings. Every production lesson and every choice of one of its four
pairs as the query is checked against **all other declared settings**. The
private receipt records the rival, refuting demonstration indices, differing
cell witnesses, and whether that rival changes the query answer. The episode
fails closed if any declared rival survives all demonstrations.

## Run and reproduce

From the **outer extracted packet directory**, with the packet's prepared
Python 3.12+ environment (NumPy, Pillow and pytest installed):

```bash
PARAMETRIC_PY="$(pwd)/WORK/.venv/bin/python"
"$PARAMETRIC_PY" review.py run "$PARAMETRIC_PY" \
  -m pytest -q generators/0b8ba9bb3c63/tests/test_parametric_0b8ba9bb3c63.py

"$PARAMETRIC_PY" review.py run "$PARAMETRIC_PY" \
  generators/0b8ba9bb3c63/workspace/parametric/prototype.py \
  --seeds 11 29 47 --beam-axes all --out ../checks/parametric/replay
```

The wrapper verifies/selects the bundled offline Racket runtime and sets the
payload working directory to `WORK/repo/`. Use a new output directory on every
run; an existing directory is refused. The commands above produce nine complete
episodes (three seeds × three settings), 108 episode rule applications, and 12
official-pair applications for the canonical default. They check nine ordered
production lessons (18 rival comparisons) and all 36 query rotations (72 rival
comparisons). These are finite measured counts, not all-seed coverage.

To draw the hidden parameter from each seed, replace `--beam-axes all` with
`--beam-axes seeded`. To materialize only one setting, pass `both`, `horizontal`,
or `vertical`. The API default is canonical `both`; the evidence CLI defaults
to `all` so the author reviews the whole declared finite parameter family.

## Public/private boundary and retained evidence

Give a solver only files ending in `.challenge.json`. Each contains exactly
ARC `train` pairs (input and output) and a `test` input. It omits seeds, hidden
parameters, reference programs, hashes, provenance, and all query answers.
Episode filenames are neutral sequence numbers, without the setting or seed.

The corresponding `.private.json` files contain the fixed parameter, seed,
query answer, exact chosen Racket program, text/normalized hashes, prototype
source hashes, selected generator hash, all Racket rival outputs, and complete
production/rotation checks. `verification.json` records the Racket executable,
bridge and prelude identities plus final counts and limitations. These are
controller/author records, not model-visible challenges.

The retained run is under `WORK/checks/parametric/evidence-final/`. Its exact executed
argument arrays, outer/payload working directories, exit statuses, source
hashes and logs are in `WORK/checks/parametric/commands.json`. A genuinely
missing-feature test run was retained before implementation. The first
implementation then exposed a byte-level formatting mismatch between archived
and selected canonical rule text; that failure is retained too. The final
prototype copies the selected canonical text exactly.
The initial export also caught a property-versus-method error while recording
the bridge identity. Its log and a failing export regression are retained;
the corrected export uses the bridge's identity property.

## Scope and limitations

This prototype deliberately uses a small constructed scene family. It does
not cover arbitrary object counts, degenerate emitters, every rectangle size,
all seeds, or every explanation a solver could invent. In particular, the
four-blocker/five-red template is narrower than canonical generator sampling.
Rotation identifiability here is against the two declared parameter rivals,
not an assertion about all semantic shortcuts. Demonstrations always carry
both-axis evidence; sparse, ambiguous episodes are rejected rather than
silently assigned an unidentifiable hidden rule.

The focused tests verify canonical source identity and all 12 official pair
occurrences, construction lawfulness, exact variant output against an independent
ray oracle, blocker/emitter preservation, transparent and occluded red behavior,
all declared rivals/rotations, public/private separation, deterministic seeded
episodes, and rejection of invalid controls. Passing them does not approve the
extension, change production rule selection, or admit any data to training.
