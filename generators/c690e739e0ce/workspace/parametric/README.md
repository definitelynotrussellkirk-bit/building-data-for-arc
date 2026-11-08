# Row-scope reflection parametric family

**Status:** reviewer-proposed and source-bound; owner acceptance and training
admission remain pending.

## Settings

- `reflection_scope=all_rows` returns the exact canonical source
  `(rule! flip-lr)` byte-for-byte.
- `reflection_scope=minority_rows` derives the unique globally least-frequent
  color, forms the complete row mask containing it, then reverses exactly those
  rows. This is a real A -> input-dependent intermediate -> B dependency:
  changing the derived color changes which complete rows are reflected.

Sampling is independent of the private setting, so equal seed/count requests use
identical inputs across settings. The API supports 2–6 demonstrations and exactly
four distinct controller-side queries. The query schedule is 8x11, 13x17,
22x26, and a substantive 30x30 scene.

## Minimum teaching construction

The two-demo minimum crosses scale and nuisance features constructively:

- 10x12: 2 selected rows, selector/second-rarest counts 3/4, one deliberate
  top-left coincidence, markers on both sides.
- 14x16: 9 selected rows, counts 18/19, no top-left coincidence, markers on both
  sides, and a pure-dense unselected threshold guard.

Every row is asymmetric. Selector colors, masks, parity, halves, positions,
per-row counts, and global frequency magnitudes vary. This repaired observed
shortcuts involving one side, edges, marker parity/counts, fixed global counts,
frequency thresholds, and first/last-N caps.

## Public/private contract

`public_turn()` exposes all demonstrations and exactly one query input. It omits
settings, programs, query answers, future query inputs, query indices, and total
query-count hints. Public IDs hash only canonical visible bytes. `write_batch()`
rejects duplicate first-turn challenges and keeps all four query answers private.

## Retained checks

- `evidence/current/minimum-racket/`: both settings over four seeds at the
  two-demo minimum, all labels replayed through protected Racket.
- `evidence/current/max-demos-racket/`: both settings at six demonstrations.
- `evidence/current/adversarial.json`: 384 episodes over 64 seeds and demo counts
  2/3/6; bounded exact/threshold frequencies 1..40, first/last caps 1..8,
  color/position/statistic rules, partial intermediates, tampering, and privacy.

The causal counterfactual replaces the true least-frequent color with the
second-rarest color and must change the protected-Racket final output. Finite
rival search and author qualification do not prove universal uniqueness or grant
owner acceptance.
