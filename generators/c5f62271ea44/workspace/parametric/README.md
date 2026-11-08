# Mapping direction: task-local prototype

Status: **prototype / proposed**. This extension does not change the selected
generator, canonical Racket source, approval, or production generation API.
It preserves the original task's scene grammar and object roles.

## Rule and parameter

The single parameter is `mapping_direction`, with exactly two allowed values:

| Value | Executed rule |
| --- | --- |
| `forward` (original/default) | Find the unique D4 transform taking the panel's four logical inner corners to the external key signature; apply it to the whole panel. |
| `inverse` | Infer that same transform, then apply its inverse to the whole panel. |

The external key still contains three dots. Its absent fourth bounding-box
corner means blue (1). Panel extraction, all four marker roles, key recognition,
unique D4 matching, and transporting the body motif remain invariant.
Quarter-turn clockwise and counterclockwise actions exchange under inversion.
Identity, the half turn, and the four reflections are self-inverse.

`forward.rkt` is materialized as the exact canonical program text. `inverse.rkt`
is a separate concrete program that exchanges only the two quarter-turn action
arms while retaining their original signature tests. A guard rejects changed
canonical arm text rather than attempting an unsafe general program mutation.
The original source and its hash remain separately recorded.

## Run

From the **outer extraction directory** containing `review.py`:

```bash
python3 review.py run ../.venv/bin/python -m pytest -q generators/c5f62271ea44/tests/test_parametric_direction.py
python3 review.py run /workspace/scratch/b1624dafaa34/arc-review/WORK/.venv/bin/python generators/c5f62271ea44/workspace/parametric/direction.py --seeds 0,17,71,103 --out ../checks/parametric/episodes-v3-3-final
```

The output directory must be new. The packet wrapper supplies the offline
Racket runtime and runs the payload from `WORK/repo/`. The CLI itself and
importable toolkit use Python's standard library plus included repository
helpers and the actual included `RacketBridge`; pytest is required only for
tests. No `scripts.*` compatibility aliases are installed. This task's explicit
Racket lambda needs only the shared public comment-stripper and rule-wrapper
peeler, avoiding the generic wrapper's legacy parser import.

The CLI generates a complete four-demonstration, one-query episode for each
seed **and each setting**, materializes both Racket programs, checks all eight
stored canonical rows against the default, and retains a same-input
quarter-turn intervention with different executed outputs. It runs both rules
on every episode pair and checks all five choices of held-out query. In every
rotation, the remaining four demonstrations must reject the alternative
parameter setting. `report.json` gives counts, exact program/source hashes,
and SHA-256 hashes of each emitted challenge/private file's actual bytes.
The earlier `checks/parametric/episodes/` output is intermediate evidence; its
two episode-file hash fields used canonical-object JSON digests. The corrected
`checks/parametric/episodes-final/` output is also intermediate evidence, bound
to generator 3.2.0. Final source-bound evidence is in
`checks/parametric/episodes-v3-3-final/`, with corrected byte hashes and generator
3.3.0 source hash `e71a8359f0ef77c8ca881a47703ca3265ffd0d54ddc46f6309c97316dc894f03`.
The exact final command, source identities, execution counts, and all sixteen
emitted-file hash checks are recorded in
`checks/parametric/execution-receipt-v3-3.json`.

See `WORK/REVIEW.md` for final canonical generator guarantees and verification.
This prototype's quarter-turn-only, four-demonstration curriculum remains
unchanged and is separately scoped from canonical lesson guarantees.

## Small reusable API

`RuleExecutor(root)` is a context manager owning one persistent bridge with
both concrete programs. `apply(grid, direction)` executes Racket, then checks
the result against an independent coordinate implementation. A failed check
raises; the mirror never supplies a returned label.

`generate_episode(seed, mapping_direction='forward', root=..., executor=...)`
returns `{'public': ..., 'private': ...}`. Pass `None` to select the direction
once by a SHA-256 keyed seed draw; this choice remains fixed for all five pairs.
Explicit settings allow controlled interventions without changing inputs.
Omit `executor` for a one-off episode, or reuse the context manager for a batch.
`write_suite(out, seeds=[...], root=...)` runs the retained CLI evidence workflow.

The public challenge contains exactly `train` input/output pairs and `test`
inputs. Parameter values, seed, encoded transforms, Racket text and hashes,
source provenance, query answer, and rival diagnostics occur only in private
files. A private file also records pair hashes and every holdout's rival
demonstration mismatches and query agreement.

## Sampling and limits

Each episode deliberately contains five quarter-turn scenes, with both
clockwise and counterclockwise represented. That constraint ensures the two
parameter settings differ on every pair, so the distinction remains teachable
when any pair becomes the query. All scenes are drawn through the selected
generator's public input API and checked against its canonical grammar.
The prototype's focused tests separately check all eight D4 transforms and
confirm the settings differ **only** on quarter turns.

This is bounded evidence for two declared parameter rivals and a finite seed
set. It does not prove identifiability against every possible program or
establish broad curriculum coverage. In particular, the strengthened teaching
episodes intentionally omit self-inverse transformations. Other generators
should define their own lawful parameter, instantiate matching Racket, and
choose demonstrations distinguishing their own finite rivals rather than
reuse this task's arm-text substitution. No model training or admission claim
is made.

The test-first receipt is retained under `WORK/checks/parametric/`: initial
pytest attempts exposed missing pytest; an explicit feature-existence assertion
then failed before implementation. Later execution caught the generic wrapper's
legacy `scripts` dependency and one mistaken test count (38 versus the correct
8 canonical + 20 episode-rival + 2 witness = 30). These failures are retained
separately from final passing results.

A subsequent review regression (`file-hash-red.txt`) failed because the original
episode report's `challenge_sha256` and `private_sha256` were canonical-object
digests while files were emitted as pretty JSON. The corrected implementation
hashes emitted bytes; the regression compares both reported fields directly
with `hashlib.sha256(path.read_bytes()).hexdigest()`.
