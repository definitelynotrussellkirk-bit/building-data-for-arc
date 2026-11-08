# Review notes: 1409f5f7af2e

## Canonical source repair

The canonical rule remains unchanged (`f34e705e21f3`): a black cell becomes red
iff its immediate vertical neighbors are green. The pre-existing ordinary
sampler covered isolated target triples but never a shared-endpoint vertical
chain, so the plausible rival “only fill isolated targets” fit the generated
curriculum. The sampler now schedules `canonical_anchor`, `all_controls`, and
`shared_chain` profiles in every three-example window. The new shared-chain
profile contains independently consequential adjacent centers, and
`isolated_targets_only` is retained as an explicit rejected rival. The base
sampler's declared production minimum remains three demonstrations. Its exposed
schedule metadata now names that same three-profile cycle and is regression-tested.

## Native parametric family

The private episode-fixed parameter is `endpoint_treatment`:

- `preserve` executes the exact canonical Racket program byte-for-byte.
- `highlight_busiest` executes canonical filling as stage A, counts the newly
  red centers by column as an input-derived intermediate, selects the unique
  busiest activated column, then recolors every green cell in that column blue
  while preserving the red centers.

Inputs and ordering are matched across the two settings. The adapter supports
2–6 demonstrations and exactly four distinct private queries with prefix-stable
generation and one-query public projection. Query four is a substantive 30×30
case with content and boundary contacts across all four edges. Ties are excluded
constructively rather than resolved by a hidden rule.

## Adversarial findings repaired

The first implementation leaked the selected column through dimensions/profile
position; winner location is now seed-dependent at fixed dimensions. Minimum
lessons also allowed left/right rank and scan-order shortcuts, endpoint-only
highlighting, nonlocal vertical matching, diagonal matching, and an
all-target-columns interpretation. Crossed rank controls, an off-chain green in
the winner column, long-gap and diagonal decoys, shared-endpoint chains, and
raw-green-frequency controls now refute those finite rivals. Malformed counts,
Boolean numeric impostors, duplicate inputs, altered demonstration labels,
program/setting mismatch, extra setting keys, missing queries, and forged
embedded certificates are rejected and regressed.

## Final evidence on bound source

- 20 focused tests passed, including exact canonical preservation, sampler
  regression tests, 2–6 count boundaries, public projection, and protected
  Racket parity.
- The bounded adversarial sweep covered 64 seeds, both settings, demonstration
  counts 2/3/6, 384 episodes, and 2,944 inputs; a protected-Racket subset
  executed 144 labels at the minimum and maximum lesson sizes.
- Authoring preflight passed for both settings at the parametric two-demo
  minimum and bound the exact generator, adapter, Racket programs, contract,
  and manifest. This is not owner qualification or acceptance.
- A protected-Racket skip-A witness changes both the selected column and final
  grid, demonstrating the claimed A → count intermediate → B dependency.
- Saved public exports passed one-query projection, conformance, future/private
  mutation invariance, and visible-query positive controls.

## Finite limits

The named rivals and bounded seed sweep do not prove uniqueness against every
program or learning benefit. The canonical base generator's ordinary minimum is
three demonstrations while the separate native family is deliberately taught
at two through six. Owner source review, native owner qualification/acceptance,
and training admission remain pending; no approval flag was edited.
