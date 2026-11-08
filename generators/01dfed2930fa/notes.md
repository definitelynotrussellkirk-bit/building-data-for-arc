# Working notes: 01dfed2930fa

## 2026-10-26 base repair, parametric build, and adversarial hardening

The ordinary generator repair remains Version 2.1.0: every sliding three-sample
window contains a mixed-color room that must stay unfilled and a same-color
multi-seed room that must fill. Explicit texture overrides and the exact
canonical rule remain unchanged.

The parametric default `unique_color` is byte-exact canonical. The alternative
`strict_majority` counts every seed color in each color-8-bounded room, then
fills zeros only when one count is strictly greater than half of all seeds.

A second adversarial pass found two count-specific rules that matched the entire
old generated bank across 1,000 seeds:

- `seed_count_lookup.rkt` implemented the canonical outputs by recognizing only
  the old positive seed totals.
- `three_of_four_only.rkt` implemented the majority outputs by handling only the
  old 3:1 mixed case plus monochrome rooms.

Both are retained as executable regressions. Every scene now has eight roles:
3:1 and 3:2 minority-first majorities, monochrome totals 2 and 5, a 1:1 tie,
a 2:2:1 no-majority room, a one-seed room, and an empty room. Seed total 5
therefore realizes all three action pairs `(neither, majority-only, both)`, and
seed total 2 realizes both fill and no-fill. Two demonstrations reject both new
shortcuts plus first-seed, plurality, identity, and exactly-one-seed-cell rules.

Inputs remain setting-independent and prefix-stable for 2–6 demonstrations and
1–4 seed-shuffled queries. Query dimensions remain 14×18, 19×23, 25×27, and
30×30. The returned evidence includes a reproducible before/after 1,000-seed
shortcut audit, protected-Racket tests and probe, task tests, base authoring
preflight, public projection/privacy checks, and a fresh sequential witness.

This is reviewer authoring evidence only. Owner source review, exact native
acceptance, and training admission remain pending. The finite rival family and
bounded seed census do not prove universal program uniqueness or training gain.
