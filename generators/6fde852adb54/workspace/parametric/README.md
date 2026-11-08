# Native landing-metric family for `6fde852adb54`

This workspace promotes a two-setting family that preserves the selected
falling-column puzzle and changes one input-derived decision only: how a
bottom-connected obstacle component is scored by column before a body-only
slice chooses its destination.

| `landing_metric` | Column score |
|---|---|
| `total_cells` | Number of component cells in the column. This is the exact canonical rule and exact canonical Racket text. |
| `longest_vertical_run` | Longest contiguous vertical run of component cells in the column. |

Every other branch is shared: each of the three mover columns falls
independently; tip-ending columns stop before their first obstacle; body-only
columns inspect a near-floor component; equal best scores use nearest column,
then lower column index; pure one-cell-per-column shelves retain the canonical
clearing branch.

## Real sequential dependency

**A — component analysis and metric scoring.** For each body-only source column
that reaches a bottom-connected obstacle component, discover that component and
compute the episode setting's score for every occupied component column.

**Intermediate.** The input-dependent score map, maximum-score candidate set,
and nearest-then-lower winning landing column.

**B — placement.** Move the three body cells into the winning column and use
that same winning column when deciding which adjacent cells of a horizontal
shelf are cleared.

B cannot be chosen before A: changing or skipping the score map changes the
winning column, destination cells, and sometimes shelf edits. The retained
`counterfactual_skip_assignment.rkt` performs the tip branch but leaves every
body slice in its source column. The protected causal witness uses the first
constructive count-versus-run example and records different final grids.

## Episode construction

`adapter.py` delegates to `prototype.py` by exact adjacent path. Inputs are
identical across settings for the same seed and requested counts. Supported
requests are:

- exact integer seed `0..2^63-1`;
- 2–6 demonstrations;
- exactly four queries.

The first three demonstrations are constructive rather than filtered draws:

1. A connected gapped component where total count and longest run select
different non-source columns.
2. A bottom horizontal shelf plus a stopped tip, exposing tie handling, shelf
clearing, and the tip-obstacle branch.
3. A component whose best total/run column does not touch the bottom, exposing
a bottom-touching-run shortcut.

Additional demonstrations reverse direction or vary the same meaningful
branches. Queries are fixed at 14×14, 18×20, 24×24, and 30×30. The 30×30 query
has boundary contacts, at least eight components, at least 35 obstacle cells,
and a substantive multi-column component. Inputs remain distinct across the
whole episode.

## Learnability and export checks

`rivals.py` exposes eight finite hypotheses: the two declared settings,
stay-in-source, leftmost-best, rightmost-best, no-shelf-clearing,
tips-ignore-obstacles, and bottom-touching-run. `teaching_report` fits these
rules to demonstrations only and labels a survivor harmful only when it changes
a recomputed query prediction. The three-demo schedule leaves only the selected
setting among declared rules and no harmful named shortcut. This is a bounded
finite audit, not universal uniqueness.

`public_turn()` exposes all visible demonstrations plus exactly one query input.
Settings, programs, seed, query answers, later query inputs, and total-count
hints are excluded. IDs are SHA-256 of exact `public_challenge_bytes`; changing
private fields or future query content does not change the first-turn bytes.

## Files

- `prototype.py` — generator, Python oracle, traces, finite-rival audit, public projection.
- `adapter.py` — native promotion entrypoint.
- `promotion.json` — finite parameter/count contract.
- `canonical.rkt` — exact selected canonical source.
- `longest_vertical_run.rkt` — alternate setting source.
- `counterfactual_skip_assignment.rkt` — causal ablation used by the witness.
- `rivals.py` — reusable named-rival registry.
- `audit.py` — bounded Python preflight, protected-Racket parity audit, and sequential public exporter.
- `evidence/landing-metric-v1/` — source-bound authoring receipt, private examples, execution hashes, and public-turn files.

The older `focus_catalog.py`/`focus_challenge.json` evaluation-inspired proposal
is retained as historical task-local work. It is not part of this native
landing-metric parameter's semantics.

## Reproduce

From the packet outer directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/6fde852adb54/tests/test_parametric_landing_metric.py

python3 review.py run python3 \
  generators/6fde852adb54/workspace/parametric/audit.py \
  --out generators/6fde852adb54/workspace/parametric/evidence/landing-metric-v1

python3 review.py run python3 -m arcpuzzles parametric qualify 6fde852adb54 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/6fde852adb54/qualification --summary
```

The evidence and qualification are reviewer preparation only. Owner exact-source
acceptance and any training admission remain separate downstream decisions.
