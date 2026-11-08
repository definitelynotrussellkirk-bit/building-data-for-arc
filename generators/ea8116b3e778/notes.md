# Working notes: ea8116b3e778

## Current decision

Keep the approved `generator.py` and canonical Racket authority unchanged. The
missing work is represented as a task-local, unapproved prototype under
`workspace/parametric/` with one episode-fixed parameter:

- `horizontal`: row reflection only.
- `vertical`: column reflection only.
- `half_turn`: center reflection only.
- `both`: all three images; exact canonical default.

All settings reuse the same lawful production `single_quadrant` inputs. This
isolates the rule parameter from sampler changes and makes every retained pair
distinguish the selected program from all three declared rivals. Demonstration
and query counts are independent; retained evidence uses two demonstrations and
four distinct queries per setting.

## Retained evidence

`WORK/checks/parametric/ea8116b3e778-symmetry-mode.json` records four episodes,
24 selected labels, and 96 exact Racket program/pair checks. Every Racket result
matches the Python mirror, all 24 demonstration/rival comparisons disagree, all
48 query/rival comparisons disagree, and canonical `both` exactly matches the
selected generator mirror and normalized rule hash `4e2d4d62614f...`.

Public challenges omit settings, seeds, programs, and query answers. Their
filenames are SHA-256 of the exact visible bytes; private episodes and exact
programs are retained separately in `workspace/parametric/materialized/`.

The legacy task test was also made source-packet portable by using
`reviewer_support.find_root`, `canonical_path`, and `load_selected_generator`
instead of unavailable monorepo `scripts`/`per_puzzle` imports and task-relative
data paths. No production behavior changed.

## Limits / next useful action

This validates one six-pair episode per setting and all declared pairwise rivals,
not every seed or every conceivable rule. The prototype is not selected for
production or training; a maintainer should review the parameter semantics and
retained lessons before any admission decision.
