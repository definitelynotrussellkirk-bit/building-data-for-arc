# Proposed stack-side parameterization

Status: **proposed prototype**, separate from the canonical generator repair.
This extension does not edit the selected generator, its canonical authority,
production interface, approvals, sampling schedule, or training boundaries.

## Rule and parameter

The parameter stack_side has exactly two values:

| Value | Executed behavior |
|---|---|
| toward_main | Canonical/default setting: cyan occupies the short-axis edge on the cyan picture's side of the small pictures. |
| toward_small | Alternate setting: invert that short-axis stack direction. |

Both settings preserve object roles, complete hollow 3x3 rings on stride four,
cyan's seven long-axis slices, two aligned small pictures, per-slice ring
counts, small-picture colors, alignment, maximum stack extent, and long-axis
slice order. The alternate reflects each row of a tall output, or the row order
of a wide output. It preserves the seven-slice order.

The blue edge marker is retained to stay within lawful source inputs. Placement
is computed from cyan/small relative geometry. This prototype makes no causal
claim about the marker. The exact canonical Racket text, including its
inconsistent historical marker comments, is preserved in rules/toward_main.rkt.
The alternate in rules/toward_small.rkt changes only the final
(if main-at-end ...) condition to (if (not main-at-end) ...).
The executable checks both materialized files against that exact derivation.

With --stack-side auto, a seed chooses the setting **once per episode**,
independently of demo/query counts. Explicit settings support controlled
comparisons. --stack-side both produces a complete episode for each setting
using the same sequence of lawful inputs.

## Exact runnable commands

From the outer packet directory (the one containing review.py):

    python3 review.py run python3 generators/48fee61713bb/workspace/parametric/prototype.py --seed 17 --stack-side both --demos 3 --queries 4 --out ../checks/parametric
    python3 review.py run python3 -m pytest generators/48fee61713bb/tests/test_parametric_block_stack.py -q

The wrapper selects the included offline Racket runtime and executes payloads
from WORK/repo. The caller may set PYTHONDONTWRITEBYTECODE=1 and a writable
TMPDIR. Python uses the supplied runtime dependencies; pytest is needed for
tests.

Demo and query counts are independent literal integers in 1..32, with defaults
of **3 demos and 4 queries**. Booleans, floats, zero, negative counts, and
out-of-range values are rejected. A seed is an integer in 0..2**63-1.
The default sampling budget is 256 attempts (configurable in 1..10000).
Failure to obtain every requested unique input raises an explicit error;
queries are never duplicated or silently omitted.

## Labels, teaching checks, and exports

Every retained label executes the matching Racket program. A second oracle in
oracle.py independently extracts eight-cell connected ring components, counts
their aligned origins, and reconstructs the output. It uses neither the
generator's lattice reader nor its Python mirror. The writer re-executes every
label before exporting. The exact source-bound rules are simple lambda bodies;
existing strip_line_comments and strip_rule_wrapper helpers remove only the
registration wrapper/comments before direct bridge execution. No broader
source compiler or legacy scripts compatibility alias is required.

For **each query**, identify_query(demonstrations, query_input, engine=...)
first fits both settings using only demonstration inputs and outputs. Its
signature accepts neither the selected setting nor any query answer. It then
compares both rules' query predictions and reports the surviving settings,
mismatching demonstration indices, and prediction hashes. An empty demonstration
context remains ambiguous. These are finite declared-rival checks, not proof
that demonstrations distinguish every imaginable rule.

Only files under the output's public/ directory are public challenges. Their
payload contains exactly train input/output pairs and test inputs.
The filename is the full SHA-256 of that compact, sorted JSON payload; no
setting, seed, answer, ordinal, or private provenance enters the name. Private
episodes, query labels, settings, exact rules, provenance, and execution logs
are under private/. The top-level summary.json is reviewer evidence and is
also private; it must not be served as a challenge.

For a batch, `write_episodes` projects every public payload first, rejects any
duplicate visible payload before creating public or private output, sorts the
batch by full visible-content SHA-256, validates every label, and only then
writes in that public-ID order. Thus caller setting order and private metadata
cannot determine public enumeration. `write_episode` delegates to the same
batch path. `write_public_challenge` remains a low-level projection helper and
does not replace label verification.

## Evidence and limits

WORK/checks/parametric/summary.json binds the recorded source/rule bytes,
complete episodes, uniqueness, every label check, per-query rivals, and the
parameter witness. private/racket-executions.json records every actual rule
evaluation. The focused batch-order fixture is retained under
WORK/checks/parametric-batch-order/: it supplied settings in reverse private
order, wrote the two public challenges in ascending visible-content hash order,
and completed 142 Racket executions across three demonstrations and four
queries per setting. The baseline probe deliberately fails because the
unchanged canonical rule cannot implement the alternate behavior. Its
corrected-adapter log is
WORK/checks/commands/parametric-baseline-alternate-gap-fixed-adapter.log. The
initial failed adapter probe is retained separately at
WORK/checks/commands/parametric-baseline-alternate-gap.log.

The current domain is the original generator's fixed 30x30 calibrated layouts,
512 cyan patterns, 290 small patterns, and 42 ordered small-color palettes.
Larger grids and arbitrary ring pictures are not claimed. Only the recorded
seeds and fixtures have been exercised. Successful prototype checks and
canonical repair acceptance do not approve these proposed variants or admit
them to training.
