# Proposed four-corner crop family

This task-local proposal preserves the canonical `upper_left` rule and varies one
episode-fixed parameter, `corner`, across the four floor-sized corners of the
nonzero-content crop. Inputs are sampled independently of the hidden setting.

Native entry points are `adapter.py:program(settings)` and
`adapter.py:generate(seed, settings, demos, queries)`. Supported counts are 2–6
demonstrations and 1–4 queries. The retained evidence always uses four queries;
a controller reveals `prototype.visible_turn(episode, i)` one at a time. Those
bytes contain all demonstrations plus only the current query input, with no
setting, program, answer, query ordinal, future input, or total-count hint.

`verify.py` executes all four programs on all retained inputs through the packet's
bundled Racket bridge, checks demonstration-only identification, checks each of
four queries against all alternate corners, and writes hash-named public turns
plus a private receipt under `evidence/current/`. This is proposed evidence, not
canonical acceptance or training admission.
