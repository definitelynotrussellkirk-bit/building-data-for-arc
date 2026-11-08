# Working notes: 9b2cd53e36fb

## 2026-10-24 repair

The core `3.4.0` sampler and canonical rule behavior were already heavily audited, so this repair deliberately avoids algorithmic changes. Version `3.4.1` rejects unknown axes/textures, keeps degenerate fixtures out of the advertised ordinary texture domain, and replaces a checkout-specific test import with `reviewer_support` so all 180 floating-hole regressions execute in the packet runtime.

Evidence: `checks/9b2cd53e36fb-task-tests-final/`, `checks/9b2cd53e36fb-lint-after-v3/`, and `checks/final-adversarial/`. The final task suite passed 6 tests plus 180 subtests; lint passed against the identical final generator SHA-256 `3e0191b04ca7e9426dda8e183dee21ce42f46ce4add9cf8682554e04af6fd80d`.

## 2026-10-24 native parametric family

Added a task-local native promotion adapter without changing the approved
production generator. The default `selection=all_holes` rule is the exact
2,571-byte canonical Racket program. The alternate `selection=largest_axis`
first identifies the unique largest edge hole, derives its row/column mirror
axis, then mirrors and sweeps every edge hole on that axis. Inputs are matched
across settings, support 2–6 demonstrations and exactly four queries, and include
both axes, floating distractors, 24x30 coverage, and a substantive 30x30 case.

Focused tests passed 44/44. A protected-Racket finite-rival audit passed 16/16
two-demo episodes over eight seeds (160 evaluations), native qualification
passed four setting/seed jobs (40 evaluations), and a source-bound
wrong-intermediate witness changed the final 18x14 output when `rows` was replaced
with `cols`. This return reports the family as reviewer `ready`; owner acceptance
and any training admission remain pending.
