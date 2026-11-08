# Checkerboard phase — separate proposed prototype

This task-local prototype changes the executed rule through one bounded parameter:
`checkerboard_phase` is the literal integer `0` or `1`, with canonical default `0`.
At phase 0, the upper-left interior cell is colored and each scatter group's count
must equal `ceil(interior_area / 2)`. At phase 1, the upper-left interior cell is
empty and the count must equal `floor(interior_area / 2)`. Updating both the parity
and capacity preserves the family's count-conserving placement reasoning.

`render_program(0)` returns the exact selected canonical-ledger program, including
its trailing newline. Its SHA-256 is
`ad481460a74e96fa6032b90bfcde8b2ec3fcfd8d9214e3914fe352de71a31f52`.
Phase 1 changes only the capacity expression and parity comparison. Both complete
Racket programs are materialized in the evidence directory. The stripped-source
hash is also recorded because the catalog may normalize outer whitespace.
Canonical authority, selected generator code, runtime APIs and approval records
are unchanged. This is a **proposed prototype**, not a production rule variant or
an approved generator. It does not import the selected generator's implementation.

## Episode and input contract

A SHA-256-derived choice selects the phase exactly once per integer seed: seed 0
selects phase 1 and seed 1 selects phase 0. One phase applies to all three
training pairs and the query. Each episode contains an even-area match, an
odd-area match, an unmatched-count demonstration, and a two-frame query. Their
layouts, orientations, outline colors and scatter colors vary with the seed.
Demonstration outputs and both parameter settings' predictions are executed
through the included `RacketBridge`. The task-local executor removes only the
known outer `rule!` registration form and applies the unchanged pinned lambda.
No Python mirror supplies labels or generic DSL wrapping.

The narrow prototype domain consists of zero-background ARC grids no larger than
30 by 30, complete hollow rectangular frames with empty interiors, positive
capacity under the selected phase, distinct frame capacities, distinct singleton
color counts, and disjoint outline/scatter colors. Unmatched counts and unmatched
frames are allowed. Inputs are bounded constructive draws with explicit failure;
there is no partial-grid fallback. In phase 1 an interior of area 1 has capacity
zero and is excluded. The prototype makes no coverage claim for all seeds or
all lawful rectangles.

## Exact runnable commands

From `WORK/`, use a new output folder for every run:

```bash
python3 run_with_racket.py python3 generators/18bd3cd2985e/workspace/parametric/prototype.py --out ../checks/parametric/phase-v1 --seed 0 --seed 1
python3 run_with_racket.py python3 -m unittest discover -s generators/18bd3cd2985e/tests -p test_parametric_phase_prototype.py -v
```

The standard-library tests also support normal pytest discovery. Their scope is
this prototype's parameter behavior, canonical-default equivalence and challenge
projection. Canonical-generator repair coverage is separate.

## Retained evidence and interpretation

The first command retains full private episodes, public challenge files, every
input's stable JSON hash, prototype source hashes, exact Racket text and hashes,
actual interpreter/argv/cwd, runtime identity, alternative-parameter predictions,
refuting demonstration indices, and one common lawful phase discriminator. Public
files contain only training inputs/outputs and query inputs; parameters, seeds,
programs, query answers and rival predictions remain in private evidence.

`canonical-rival-fit.json` checks the rank-matching rival on every labeled
canonical record and re-executes canonical labels. The rival sorts frames by
checkerboard capacity and groups by scattered-pixel count, then pairs them by
rank without checking equality. `semantic-witnesses.json` retains a lawful
capacity-1/count-2 refutation, a diagonal-singleton connectivity refutation, and
two bounded canonical-rule probes: first matching equal-capacity frame and
same-count color overwrites. The latter two are outside the prototype domain;
the observed overwrite color is not a guaranteed abstract hash-key order.

A passing finite result means these episodes refute the declared alternative
phase and these witnesses establish the stated differences. It does not prove
identifiability against every possible rival. Exact retained commands, statuses,
failures and source/evidence hashes are in `WORK/checks/parametric/`.
