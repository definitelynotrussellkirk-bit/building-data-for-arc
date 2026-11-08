# Working notes: 40b155c46f6e

Review `review-fd6b371d37a717d6` repairs R1 (fixed row subset and lesson support),
R2 (non-observable/clipped overrides) and R3 (validator and semantic declarations).
Original generator `693d6775ec4dc7994e3d81d4442dec00db41467a9f5a4a1e8fd5bfa35f56ce9f`; final `ba2ed8f163990a4fca514bb9913e447be8d3e96a541dbad13402a7366161144d`.
No Racket, canonical example, archival solution or random audit source changed.

The choice is a compact bounded distribution with a three-phase default
curriculum, not an unrestricted sampling of everything the reference accepts.
Explicit axis requests are exact; removed controls now fail loudly. The core
phase maintains original-size/palette support without replaying original grids.
The left/right phases provide witnesses against seven canonical-perfect rivals.
Mixed per-row lengths, no-change nonzero rows and independently assembled short
lessons remain useful future stress cases, not verified teaching guarantees.

Measured review evidence lives in the retained return ZIP: all 12 after battery
stages green, 60 task tests, 178 repository tests, and 360 source-bound lessons
(120 per band, 720 unique inputs, overlapping windows). All seven rivals are
contradicted by every measured final lesson's demonstrations. Finite evidence
must not be summarized as universal induction or training approval.

`workspace/README.md` gives tooling commands; `workspace/HANDOFF.md` compresses
next steps. Full distribution decisions, audit findings, exact commands, failures
and solve notes are retained in the return's `DECISIONS.md`, `AUDIT.md`,
`RESULTS.json` and `checks/`. Existing imported evidence remains unchanged.
## Current reviewer considerations

Source SHA-256: `ba2ed8f163990a4fca514bb9913e447be8d3e96a541dbad13402a7366161144d`.

# Decisions and boundaries: 40b155c46f6e

Assignment is unchanged. Main generator `693d6775ec4dc7994e3d81d4442dec00db41467a9f5a4a1e8fd5bfa35f56ce9f` -> `ba2ed8f163990a4fca514bb9913e447be8d3e96a541dbad13402a7366161144d`;
canonical program `d149383b47c7695dcc8d454ef06c29aa1ea7cbec4fde114203dd3c9274ece203` unchanged. R1/R2/R3 refer to `REVIEW.md`.

## Preserve the transformation, repair the input distribution

The reference performs a row-local singleton-to-majority recoloring, preserving
zero background. Its canonical outputs match all three usable original pairs.
The previous generator's comment says it aims to match compact canonical rows;
no source evidence justifies a semantic odd-row restriction. We therefore changed
positions and teaching support, not the canonical Racket rule. An alternative
patch to make the reference skip even rows would encode the sampler defect and
was rejected. No archival bank or shared helper was edited.

## Keep a bounded compact-row domain

Retained 5..7 by 7..12 grids, zero background, 1..3 active rows, compact lengths
3..6, one singleton and one repeated nonzero color. Added an explicit blank-row
separator requirement, already implied by the old intended layout and satisfied
by every canonical pair. Canonical examples, all tested defaults and every
exact-axis corner pass the final validator. Malformed/ragged grids, booleans,
noninteger colors and values outside 0..9 now return errors rather than crash or
silently pass.

We did not expand to every input the Racket rule can process. Adjacent active
rows, disconnected runs, ties, already-uniform nonzero rows and multi-color
unchanged rows remain out of the normal sampler domain. Those are possible
future domain decisions, not automatically missing obligations. In particular,
rejecting an intentionally malformed frame in A2 would improve validator
honesty; it would not require training on broken frames.

## Enumerate lawful row placements rather than shuffle a fixed subset (R1)

The old code slices `[1,3,5]`, then shuffles and sorts that subset. Every default
sample in the recorded 720-input baseline misses a positive even active row.
The replacement enumerates separated subsets of `range(height)` and samples a
set. Core and right-witness phases allow every feasible set. The left-witness
phase requires at least one positive even row so each three-demo lesson has a
counterexample to the retained audit's restricted-row rival.

A shifted canonical input, from active rows `[1,3]` to `[0,2]`, passes both
validators, stays compact/separated and gives a concrete Racket/rival
counterexample. It is not an out-of-domain malformed probe. See R1's case files.
Purely uniform placement would improve average coverage but could still omit the
witness from a short lesson; deterministic, cyclic witness scheduling was chosen
to make the short-lesson contract testable.

## Three phases, with all cyclic starts checked

`sample_index % 3` selects `core`, `left_witness`, `right_witness`. Seeds still
randomize colors, placements and dimensions inside each phase; no original grid
is replayed. `EXAMPLES_NEEDED=3` is retained and now supported by an executable
finite-competitor contract.

Core uses height 5, width 8/9, two rows, run length 4/5 and four distinct nonzero
colors. This guarantees one original-size/palette-profile draw per three default
samples without pretending to reproduce every canonical structural detail.
Its odd cells are interior; boundary phases deliberately supply first/last odds.
The left phase has three rows, length 3 or 6, and cyclic color roles across rows.
The right phase supplies a last-position odd and varies row count and length.
Left also supplies a positive even active row. Together these break the seven
canonical-perfect rivals on demonstrations, not just on a masked query.

Rejected alternatives: a larger `EXAMPLES_NEEDED` would spend more context on an
avoidable support defect; independent low-probability witness flags have no
three-demo guarantee; a post-hoc acceptance filter can bias distributions or loop
and obscure exact sample provenance. The chosen schedule is simpler to replay.

**Cost/limit:** schedule phases correlate shape, run length, row count, odd-cell
position and color-role reuse. This is not independent-axis sampling. Defaults
also use a single common run length per grid, although the validator accepts
lawful canonical grids with mixed lengths. Those correlations remain worth
stress-testing with undeclared rivals. No finite rival battery proves universal
identifiability. Reordered, independently resampled, overridden or shorter demo
sets do not inherit the contiguous-window guarantee.

## Honest exact controls (R2)

Kept only `grid_h`, `grid_w`, `n_active_rows`, `run_len`. Every accepted integer
value is observable in pixels and feasible in every band. Their full Cartesian
product fits: even height 5 accommodates three rows `[0,2,4]`, and width 7 fits a
length-6 run. Thus no incompatible-pair exception is needed. `None` means default.
Explicit values are validated before use; no clipping or difficulty-specific
narrowing of valid overrides remains. `observe_overrides` returns a tuple for
mixed canonical lengths instead of falsely reporting one length.

Removed palette/texture/anchor/asymmetry/position-bias axes rather than preserve
false promises or invent new semantics merely to retain a name. Their original
rationale is not documented; several were accepted without affecting pixels,
and degenerate textures generated self-check-invalid examples. Unsupported and
misspelled keys now raise `ValueError`. This is an intentional API break for
callers of retired controls; it is not backward-compatible silent emulation.
Canonical-like palette support is maintained by the core phase, not by a fake
palette override. Final override report and tests exercise accepted and rejected
values, type errors and all boundary combinations.

## Separate input validity, profile support and lesson evidence (R3)

`strict_canonical_like` delegates to the documented semantic manifold validator,
with `MIN_STRICT_FRAC=1.0`. It is not a claim that every sample has canonical
height/width/palette. The existing profile-floor gate separately verifies
canonical-size/palette support. Six executable witnesses map to seven executable
rivals. Each named witness is checked against actual output disagreement; each
canonical shortcut is checked against every original pair. Rival code generates
diagnostics only; canonical Racket remains the training-label authority.

## Reproducible evidence rather than self-certified labels

The final probe uses actual `runner.run_one` episode assembly, three demos plus
one query, 40 seeds per band and starts 0/1/2 (120 lessons per band). It records
input hashes, rejections, unique counts and source identities. Each worker runs
in a copied temporary runtime under `python -I` with `PYTHONPATH` removed and
canonical authority explicitly selected. The Python oracle is independent test
code, checked against Racket; there is no fallback label path.

The first audit worker failed because isolated Python removes the script
directory. Only the copied runtime's own directory is added before the sibling
import. Original failure logs and its worker source are retained; the repaired
execution successfully obtains both audit counterexamples from Racket. No
shared runtime code was changed to accommodate the tool.

## Audit and solve boundaries

A1/A2 (`79fa065ed7aa`) and A3 (`d1e7fb6c23d0`) are findings only; their original
source hashes are unchanged. A1 is an exact override defect, A2 a validator
weakness on a deliberately malformed input, A3 a semantic support gap that
leaves a canonical-perfect shortcut alive. Do not conflate these categories.

After generator edits were frozen, the Python solve used only visible examples
and newly authored Python probes. Earlier rule exposure is declared yes. One
actual solve revision passed the visible checker; no failed solution was
manufactured. Final notes are frozen, and query correctness is unobserved.
Changing generator bytes later requires a new solve episode, not relabeling this
one as belonging to the new source.

## Next measurement, not a performance claim

Before broadening the normal domain, test undeclared rivals against randomized
lesson ordering, independently sampled indices, mixed per-row lengths and
alternative color-role assignments, while distinguishing supported default
contracts from stress cases. Use a separately held-out small-model experiment to
measure any transfer effect. No such model experiment was performed here.
