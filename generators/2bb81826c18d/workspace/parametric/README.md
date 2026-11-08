# Periodic interior erasure — proposed prototype

This is a separate, runnable **parametric prototype** for task `2bb81826c18d`.
It does not register a production generator, edit the canonical Racket rule,
refresh approval, or grant training admission.

## Rule and fixed episode semantics

Preserve the zero background and every solid rectangle's border. For an
interior cell, let `ir` and `ic` be zero-based row and column offsets from that
rectangle's top-left **interior** cell. Erase it to zero exactly when
`(ir + ic) % period == phase`; keep its original color otherwise.

| Parameter | Allowed values | Canonical setting |
|---|---|---|
| `period` | `2`, `3` | `2` |
| `phase` | integer `0 <= phase < period` | `0` |

The complete setting set is `(2,0)`, `(2,1)`, `(3,0)`, `(3,1)`, `(3,2)`.
Booleans, strings, floats and out-of-range values are rejected. The canonical
setting reproduces the original checkerboard rule: its original backward
scans yield one-based interior coordinates, and subtracting one more from
each coordinate changes their sum by two, leaving parity unchanged.

Object detection, per-object coordinate anchoring, border preservation,
spatial relationships, composition over rectangles, and color roles stay the
same. Period three changes the diagonal spacing of erased cells; phase moves
the erasure pattern within the fixed border. These are executed rule changes,
not changes only to palette or scene sampling.

`choose_setting(seed)` chooses one of the five settings once, using a local
SHA-256-derived value independent of scene drawing and pair count. The same
instantiated Racket lambda labels all demonstrations and queries. Explicit
settings are available only as an authoring control for exercising every
alternative; they are recorded as `explicit_for_authoring` in private episodes.
All input random draws use a separate local seeded `random.Random` instance.

## Domain and teaching construction

The lawful input domain is a `10..24` by `10..24` integer grid with background
zero and one to four solid, monochromatic, distinct-color rectangles, each at
least `3x3`, with no orthogonal contact. The prototype sampler uses `14..24`
canvases so up to four separate construction zones always fit. Colors, sizes,
positions, aspect ratios, object counts and boundary contact may vary. The
sampler is independent of the canonical generator's implementation.

All settings share this domain. A rectangle at least `5x5` has interior local
coordinate sums `0..4`; the five settings select five distinct subsets of
those sums. The first demonstration always contains such a rectangle. Every
episode executes each of the four alternative Racket settings and requires
each to disagree with a visible demonstration. Other pairs may contain `3x3`
rectangles, including cases where an alternative phase erases no cell.

The episode order is intentional. No claim is made that every query rotation
retains an identifying demonstration. The rival checker preserves
`ambiguous_query` and `survived_all` outcomes for externally supplied lessons;
the focused tests include a genuinely ambiguous `3x3` demonstration.

## Files and run commands

- `prototype.py`: parameter validation, exact Racket expressions, scene draws,
  episode construction, rival execution, and the public challenge projection.
- `probe.py`: bounded evidence runner, canonical equality, executed witness,
  independent geometry checks, deterministic replay, and public/private files.
- `../../tests/test_parametric.py`: portable prototype-only regressions, using
  `reviewer_support.find_root`, `load_selected_generator`, and `canonical_pairs`.

From the outer extracted packet, with a Python 3.12+ interpreter containing the
declared runtime dependencies and pytest:

```bash
python3 review.py run python3 -m pytest generators/2bb81826c18d/tests/test_parametric.py -q
python3 review.py run python3 generators/2bb81826c18d/workspace/parametric/probe.py --out ../checks/parametric/probe --seed-count 20
```

The wrapper selects the included Racket runtime and runs the payload from
`WORK/repo/`. Use a new `--out` directory for each probe; existing destinations
are refused. Both wrapper and payload must use the same prepared interpreter.
The retained command receipts contain the exact interpreter paths actually run.

For direct Python authoring, call `generate_episode(seed)` or
`generate_episode(seed, setting=(3, 1))`. The result is **private**. Pass it to
`public_challenge(episode)` before showing a solver the puzzle. The public
dictionary contains only training input/output pairs and query inputs; no
seed, parameters, reference code, rule hash, or query outputs are exported.
The projection returns independent copies of the grids.

## Execution and evidence

Labels come from the included public `RacketBridge.define_grid` and
`RacketBridge.eval_text` APIs. The bridge evaluates the exact materialized
lambda on each input and is always closed with its context manager. The
canonical source's `rule!` registration wrapper is explicitly removed for
direct lambda application; both the original text and executed expression
are retained with separate SHA-256 hashes. Prototype expressions need no
wrapper and are executed as emitted. A Python bounding-box calculation checks
the resulting labels in the probe; it never supplies them.

`WORK/checks/parametric/` retains the test-first failure, test results and exact
command receipts. `WORK/checks/parametric/probe/` contains:

- `programs.private.json`: all five exact Racket programs and hashes, plus the
  original canonical source and executed expression.
- `canonical-equality.private.json`: every labeled canonical pair, original
  Racket output, and canonical-setting prototype output.
- `witness.private.json`: a lawful `5x5` rectangle input and the five pairwise
  different executed outputs.
- `episodes.private.jsonl`: complete seed-bound episodes, chosen parameters,
  exact programs, query labels, and all four rival results.
- `challenges.public.jsonl`: solver-visible projections only.
- `report.json`: source/runtime hashes, the exact payload command, per-episode
  replay and rival results, artifact hashes, counts, and explicit limitations.

The bounded probe exercises each explicit setting at seeds `0`, `7`, and `19`,
plus seed-selected episodes at seeds `0..19`: 35 complete episodes, 140 labeled
pairs, 140 declared-rival checks, and 35 exact deterministic episode replays.
Canonical equality covers eight labeled records across both supplied canonical
variants, representing four unique inputs. Counts of duplicate canonical
records and deterministic replays are reported separately from unique cases.

This is finite evidence for the five declared settings and sampled seeds. It
does not prove uniqueness against other rule families, universal identifiability,
exhaustive random support, rotation-safe teaching, or canonical repair coverage.
