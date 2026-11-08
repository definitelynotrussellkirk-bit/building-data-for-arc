# Review — `2dacb90452ce`
Assignment: `review-a5a2c76f7cf55423`; production version `3.1.0`.
Source: generator SHA-256 `b972fe9cc491907d1193818efe9a68c28202c3cb355cf31fc1b0c7dd2779d4c0`.
Missing capability → repair: no small parametric family → isolated `scale_factor ∈ {2,3}` Racket-backed prototype.
Production generator: unchanged. Canonical rule: unchanged, exact factor-2 SHA-256 `511f58f5d47190acd7307da0e87d1e6d84d787e18b14ce8c3c14de0471730050`.
Variant rule: `(upscale g 3)`, SHA-256 `2fea407be69fc4a77b9a3bd2cb1cf82d34ef69c54f82fdbee89ad3bb14815cdf`.
Focused task tests: `45 passed`; evidence: `checks/parametric/focused-tests.log`.
Episode evidence: 2 settings, 2 demonstrations + 4 distinct queries each, 24 chosen/counterfactual labels executed through Racket, 0/8 ambiguous queries.
Adversarial replay: 96 sampler cases/672 inputs, 16 episodes, 192 chosen+rival labels, 16 public projections, no finding.
Supplementary tickets: audit witness reproduced; separate parameter evidence has one-query/content-ID support gaps.
Limits: finite `{2,3}` mutual-rival evidence only; no production approval or training admission follows.
Disposition: routine proposed prototype; peer support gap needs attention, while the pre-existing peer audit remains uncleared.

## Built artifact

`generators/2dacb90452ce/workspace/parametric/prototype.py` keeps one hidden
`scale_factor` fixed per episode. Factor 2 is loaded byte-for-byte from the
canonical ledger; factor 3 is created by one guarded source substitution. Inputs
come from the approved selected generator and do not depend on the setting.
Every chosen and counterfactual label is executed through Racket. Public challenge
files use shared exact visible-byte serialization and content IDs; seeds, settings,
programs, private metadata, and query answers stay private.

The retained evidence root is `checks/parametric/scale-factor-v1/`. Its report
records 4/4 canonical factor-2 labels, both settings, 12 chosen episode labels,
12 counterfactual labels, four queries per episode, and no surviving declared
alternative. The exact public files are named by their visible-byte IDs.

`checks/parametric/adversarial_probe.py` is a reusable bounded replay for future
reviewers. It writes JSON itself, avoiding corruption by the outer runner's console
preamble. It tests count/retry boundaries, distinct and lawful inputs, numeric and
shape parity through Racket, demonstration-only rival rejection, public-field
redaction, and independence of public IDs from private metadata and query answers.

## Supplementary tickets

`ticket-607a31dc1f073427` reproduced the retained source-bound witness for
`dc155169ea57`: two disconnected color-1 components have overlapping column
projections; the constructed projection-group rival merges them, while the exact
canonical Racket output does not. This confirms only the bounded retained claim.
The audited historical source snapshot was absent and the original 3000-draw
census was not rerun, so the existing audit is not cleared.

`ticket-6a1f2ccb735751c0` verified the pinned manifest, generator, and all seven
retained evidence hashes for `27b865c5f43a`. Public bodies omit hidden settings
and query answers, but each of the three settings has one query rather than four;
filenames expose the setting and the stored bytes are not shared-helper
content-addressed challenge bytes. This is a support observation, not a safety
audit or variant-approval decision.

## Scope and stopping

The broad production battery and full repository suite were not run: production
behavior and canonical authority were not edited, and packet instructions bound
verification to the prototype/tests/notes scope. The evidence is finite and checks
only factors 2 and 3 against each other. The prototype remains opt-in and proposed.
