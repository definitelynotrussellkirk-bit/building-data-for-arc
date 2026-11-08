# Source-bound generic mutation-gate calibration evidence

**Finding: reproduced false positive. Optional shared-tool patch is proposed only
and has not been applied.** The selected rotation validator should continue to
accept lawful rectangular rotation inputs.

The first canonical training input is:

```json
[[0,0,9],[0,0,9],[9,9,9]]
```

The modal background is 9; minority color 0 occupies exactly the top-left 2×2
block. The unchanged detector's `_minimal_impostors` produces this exact grid as
`solid_2x2`. Calling `probe_selfcheck_minimal_impostors` on this canonical input,
with all four canonical training pairs supplied for calibration, flags its
accepted block. This is a direct canonical false positive: the real reference
`(rule! rotate-ccw)` produces its recorded output
`[[9,9,9],[0,0,9],[0,0,9]]`, and the current validator accepts it.

The current `_canonical_minimal_kinds` recognizes canonical minority singletons
only. It does not recognize the literal canonical block, leaving its calibration
set empty on this task. This is a calibration gap rather than evidence that the
validator should reject the task's own canonical input.

## Reference and detector reproduction

`reproduce.py` reads the four original training pairs and original labeled query
from the canonical ledger, plus three explicit 3×3 witnesses: center singleton,
top-left 2×2 minority block, and middle horizontal short line. All eight inputs
are accepted by the selected validator. All five canonical outputs match actual
Racket execution. All eight grids and executed outputs are retained in
`evidence.json`, along with exact rule text/hash, reference support hashes,
selected generator hash, and detector dependency hashes.

The program executes through the supplied `RacketBridge`, with the narrowly
scoped callable adapter `(define (rule! f) f)` and exact installation
`(define calibration-rule (rule! rotate-ccw))`. This executes the declared
reference primitive; the adapter does not implement general REPL rule syntax.
There is no Python output mirror or fallback.

`original/scripts/` retains the full unmodified detector and its full
`generator_module_loader.py` dependency, byte-for-byte hash matched against
`repo/shared/tools/`. The two called probe paths require only those modules and
stdlib; no functions or imports are stubbed. Importing this complete source in
its expected `scripts` layout avoids drawing conclusions from extracted function
fragments or from a broken direct import of the repository-layout tool.

On the five original inputs the unchanged tool reports:

- `short_line 5/5`, `singleton 5/5`, and `solid_2x2 5/5` accepted by the named probe.
- `selfcheck-power`: only **10/40** mutations rejected, below its fixed 30% cutoff.

This is a focused exact-source probe invocation on the canonical input sample,
not a rerun or replacement for the inherited gate's generated-input sample.
The inherited baseline's 12/44 count remains distinct.

The power heuristic assumes its mutations destroy a required structure.
Rotation applies to lawful asymmetric singleton/block/line inputs as well as
many shuffled, transposed, or recolored grids. Those changes do not generally
produce invalid rotation inputs. Racket execution proves the transformation and
canonical label agreement; the generic rectangular rotation contract supplies
the task-domain reason to accept these witnesses. Executability alone would not
establish task-domain lawfulness for an arbitrary ARC rule.

## Optional minimal generic proposal

`proposal.patch` changes only `_canonical_minimal_kinds`: additionally recognize
`solid_2x2` or `short_line` when `_minimal_impostors(canonical_input)` returns a
probe byte-equal to that canonical input. It preserves existing singleton
calibration, thresholds, all other mutations, and the aggregate power probe.
There are no task IDs or broad rotation exemptions in the patch.

The exact-copy candidate lives under `proposed/scripts/` and is never installed
into `repo/shared/tools/`. Six focused tests were written first. The original
module fails the three expected new-calibration assertions; the proposed module
passes all six. Tests include nonmatching block geometry, singleton preservation,
remaining warnings with a permissive checker, and preservation of the power
warning.

`proposal-comparison.json` records the actual task comparison:

| Observation | Unchanged tool | Isolated proposal |
|---|---|---|
| Canonical minimal kinds | none | `solid_2x2` |
| Named accepted probes | short line, singleton, solid 2×2: each 5/5 | short line and singleton: each 5/5 |
| Aggregate power | rejects 10/40; warning remains | rejects 10/40; identical warning remains |

The three-cell named short-line shape and center singleton are lawful under the
rotation rule, but this small proposal does not invent canonical evidence for
those exact additional probe types. The actual fourth canonical training input
has two top-row minority cells; it is not byte-equal to the detector's middle
three-cell line probe. Remaining named and power warnings are therefore retained
honestly. A broader generic task-domain calibration mechanism requires separate
design and review.

## Exact commands

From the outer packet directory:

```bash
python3 review.py run python3 ../checks/gate-calibration/reproduce.py
```

The following pure stdlib candidate tests/comparison were actually run from
`WORK/`:

```bash
python3 checks/gate-calibration/test_proposed_calibration.py checks/gate-calibration/original/scripts/generator_defect_lint.py
python3 checks/gate-calibration/test_proposed_calibration.py checks/gate-calibration/proposed/scripts/generator_defect_lint.py
python3 checks/gate-calibration/compare_proposal.py
```

Exit codes and logs are recorded in `commands.json`. No shared patch, validator
restriction, canonical authority change, or whole battery was applied. No
post-repair solve directory or private solve answers were read.
