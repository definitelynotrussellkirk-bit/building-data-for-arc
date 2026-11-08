# Proposed zero-line parameter prototype

**Status: proposed, task-local prototype.** The approved production generator,
canonical ledger, original rule pin and runtime interfaces are unchanged.
Nothing here establishes variant approval or training admission.

## Rule and parameters

Compute the rows and columns containing **original input zeros**, once. Clear
the selected lines to zero while preserving the episode's protected nonzero
color. Zero remains the cue and erase color; preserving a color does not stop
a line from continuing beyond it.

| Parameter | Domain | Canonical setting |
| --- | --- | --- |
| mode | both, rows, columns | both |
| protected_color | exact integers 1 through 9 | 2 |

The explicit setting both plus 2 has exactly the canonical transformation.
The function materialize_program() also defaults to that setting. By
contrast, **omitting settings from the episode API or CLI chooses a setting
deterministically from the seed**. It chooses one member of the finite 27-setting
table once per episode, then retains that same setting across every pair.
If only one parameter is supplied, the other comes from that seeded choice.

The original reasoning is retained: recognize zero cues, collect their row
and/or column indices, preserve a special color, and transform simultaneously.
The new inferences concern which axes apply and which color is protected.
There is no sequential state claim: newly written zeros do not create new
active lines.

## Runnable commands

Run from the outer extracted packet directory. The review.py run wrapper selects
the included Racket runtime and executes payload paths relative to WORK/repo.
Use a Python installation with pytest for the test command. In an environment
using a virtual environment, replace both python3 entries with its absolute
Python executable.

Create **two complete episodes**, canonical both+2 and alternative
columns+7, each with **three demonstrations and four distinct queries**:

~~~bash
python3 review.py run python3 generators/09636f05e06e/workspace/parametric/prototype.py --examples --seed 17 --train 3 --test 4 --out ../checks/parametric/examples
~~~

Create one explicit row-only, color-9 episode:

~~~bash
python3 review.py run python3 generators/09636f05e06e/workspace/parametric/prototype.py --seed 29 --mode rows --protected-color 9 --train 2 --test 4 --out ../checks/parametric/rows-example
~~~

Create a deterministic batch whose settings are selected once per seed:

~~~bash
python3 review.py run python3 generators/09636f05e06e/workspace/parametric/prototype.py --seed 41 --count 2 --train 3 --test 4 --out ../checks/parametric/seeded-batch
~~~

Run only the authored prototype regressions:

~~~bash
python3 review.py run python3 -m pytest -q generators/09636f05e06e/tests/test_parametric_prototype.py
~~~

Each output destination must be new. Existing files, directories and symlinks
are refused, including an existing empty directory. Duplicate visible payloads
are rejected before the destination is created. Public files are named by
their visible-payload SHA-256, and the public index sorts those IDs.

## API, finite bounds and input source

build_episode(seed, *, n_train=3, n_test=4, mode=None,
protected_color=None, max_attempts=256, labeler=None) returns the private
authoring episode, including all labels. write_batch(episodes, output_dir)
writes the public/private projection. RacketLabeler may be shared as a context
manager across episodes; otherwise build_episode opens and closes its own
bridge.

The seed must be an exact integer in 0 through 2**32-1. Demonstration and query
counts are independent exact integers, each 1 through 32. The CLI's --count
is 1 through 16; consecutive batch seeds must stay in the seed domain.
--examples is a separate two-episode convenience mode and rejects explicit
settings or --count other than 1. The per-input retry limit is 1 through 256;
the CLI uses 256. A duplicate input, exhausted witness budget or failed
candidate agreement raises an explicit error. No shorter batch is returned,
and no query or demonstration is cloned. These finite bounds define supported
requests, not a claim that every seed/count combination will succeed.

Inputs come directly from the unchanged selected generator.py, with no cell
editing. Dimensions are drawn in 12 through 22, actual zero-bearing row and
column counts in 2 through 4, and palette size is exactly 10. A deterministic
input-index schedule alternates:

- Scatter: equal row/column counts, disconnected zero cues and gaps in both
  support sets.
- Rectangle: independently chosen row/column support counts.
- Thin rectangle: support counts 2-by-4 or 4-by-2.

The canonical generator chooses its existing placement biases and fill
densities. These distributions are constrained authoring profiles, not IID
canonical inputs and not a promise of uniform accepted dimensions. A bounded
rejection predicate requires all nine nonzero colors on both row-only and
column-only arms, untouched cells, and a protected-then-ordinary ray contrast
for **each** possible protected color in each axis. Every retained grid passes
GEN.self_check. No zeros or last palette representatives are overwritten,
because the prototype never writes to a generated input grid.

Input seeds, controls and witness rejection are independent of mode and
protected color. In particular the two --examples episodes use the same
inputs, so their output differences are attributable to the rule setting.
The first demonstration is a gapped scatter scene even when only one
demonstration is requested.

## Label authority and teaching checks

materialize_program(mode, protected_color) produces exact executable Racket
lambda text for each of the 27 settings. RacketLabeler evaluates that lambda
through the supplied arc_repl.racket_bridge.RacketBridge. **Every retained
demonstration and query answer comes from Racket.** The focused tests
independently compare all 27 materialized programs with the marked Python
countermodel evaluator on scatter, rectangle and thin representative inputs,
and compare the explicit canonical setting with the canonical labeled pairs.

assess_teaching(demos, query_inputs) takes no query answers. It enumerates
all 27 parameter hypotheses against demonstration labels only. It also checks
six structural forms for every setting: global support hull, global clearing,
ignoring the protected color, iteration from fresh zeros, intersection-only
clearing, and rays stopping at the protected color. This is 27 parameter
hypotheses plus 162 structural hypotheses, with equivalent hypotheses allowed
to survive. For a one-axis rule, the fresh-zero interpretation is already at
its fixed point and is observationally equivalent. The fresh-zero rival
literally repeats the base transformation to convergence, bounded by the
number of cells plus one equality check; protected-only barriers may prevent
global propagation in both-axis mode. A focused barrier regression independently
checks that fixed point by repeated execution of the one-round Racket program.

For each query input, all surviving hypotheses must produce one common
prediction. Disagreement rejects the entire episode; queries are not filtered
against their answers and demonstrations are not resampled to fit queries.
Racket executes the query labels only after this check. All-nine-color
contrasts on both exclusive arms identify the chosen parameter setting.
Gapped scatter and untouched cells expose hull/global shortcuts, while
protected-then-ordinary rays expose barrier shortcuts.

This is a finite, declared hypothesis check. It is not a proof of unique
induction over arbitrary programs, all seeds or all possible ARC grids.
Unlisted structural shortcuts may remain.

## Public/private boundary and evidence

The returned API object is **private authoring data**. Write it through
write_batch before sharing a challenge. The writer uses
reviewer_support.public_challenge_bytes and public_challenge_id; the exact
helper bytes are written unchanged and hashed again.

The public directory contains only demonstration input/output grids, query
input grids and a sorted index of their content IDs. Query answers, seeds,
settings, source hashes, Racket programs and input receipts live under
private/, keyed separately by the public ID. Public directory entries and
IDs depend exclusively on visible data. Changing private metadata or query
answers cannot change their bytes or names. The tests exercise that invariant,
visible-output/input mutation, exact-byte hashing, duplicate rejection,
fail-closed destinations and batch-order independence.

Each private episode retains exact program text and its SHA-256, selected
generator source SHA-256, prototype source SHA-256, public helper source SHA-256,
seed/setting, accepted input receipts, surviving hypotheses and per-query
agreement. The private summary hashes each exact public/private episode file.
Program and source bindings report identity, not approval.

Keep retained authoring command outputs and independent probes under
WORK/checks/parametric/. The focused test matrix is bounded evidence;
unchanged production coverage is reported separately.
