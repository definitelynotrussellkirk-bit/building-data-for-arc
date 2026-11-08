# Working notes: 72b99d3a9be8

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 base repair and native parametric reviewer build

- Baseline defect: ordinary generation exercised only a horizontal-wall shape,
  and early extra color-2 bars could intercept the beam before the sampled wall,
  so `wall_orientation` did not reliably control the observed branch.
- Repaired the base to version `4.0.0`: strict fail-closed overrides, genuine
  horizontal and vertical selected color-2 reflectors, an oppositely oriented
  color-3 pass-through decoy, and only color-3 extra bars. `self_check` now checks
  the canonical rule domain rather than rejecting lawful canonical boundary/no-wall
  inputs. The repaired generator SHA-256 is
  `8606ad55de7e4cb48657589b1aa557c93e034d8ad00ee325b368e787a9b44fb5`.
- Preserved the exact canonical default program at SHA-256
  `baea714b401fca9469e37e6c4e79617dd0f320eceb42cb42b963ea2fe4f04353`.
  Added `reflector_color = 2 | 3`; only the selected input color's semantic role
  changes, while wall orientation remains measured from the selected cells.
- Step A derives an ordered sequence of selected-color bounce events (hit,
  orientation, incoming/outgoing direction); step B consumes those directions to
  continue and paint the beam. Substituting the other color's event sequence
  changes the protected-Racket output.
- Retained source-bound evidence: 6/6 repaired-base tests, 12/12 full task tests,
  72 protected-Racket audit evaluations, 256 prefix-stability episodes (2,560
  pairs), authoring preflight, protected causal replay, and 16 verified one-query
  public views with 24 private-field invariance checks.
- Minimum two-example lessons reject the other setting, identity, straight-line,
  stop-at-reflector, wrong-axis, forward-only, and backward-only shortcuts. The
  fourth query is a substantive 30x30 stress case with at least 45 foreground
  cells and at least 20 changed cells under either setting.
- Limit: the declared rival family is finite. Reviewer work is ready; owner
  exact-source native qualification and fresh acceptance remain the next action.
