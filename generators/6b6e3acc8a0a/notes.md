# Working notes: 6b6e3acc8a0a

## Delivered family

The exact canonical default remains `translation_mode=canonical_all`: derive the vector from the unique color-1 source anchor to the unique color-2 destination anchor, translate every non-background/non-anchor cell on a fresh canvas, and discard out-of-bounds destinations.

The nearby setting `translation_mode=pointer_select_color` adds a genuine sequential dependency without changing episode inputs. Step A translates a unique color-8 pointer by the anchor vector. The intermediate is the input color at that landing cell. Step B translates every color-9 cargo cell by the same vector and paints surviving destinations with the selected color. The selector varies over colors 3, 4, 6, and 7 across the bounded episode bank.

The adapter is deterministic, count-prefix stable, setting-neutral on inputs, and supports 2–6 demonstrations plus 1–4 queries. The four-query bank includes compact, boundary, dense, and substantive 30×30 cases. The first two visible demonstrations reject the named alternatives tested in `test_visible_demos_reject_named_shortcuts`: opposite vector, copying, retaining cargo color 9, fixed recolor, reading the pointer origin, and recoloring without translation.

## Base/preflight repair

The canonical record uses the legacy shape where `test` is one pair object rather than a list. The packet's base-preflight loop iterated that object as strings and raised `TypeError`. `workspace/parametric/preflight_compat.py` is a task-local compatibility runner that normalizes only this container boundary (`dict -> [dict]`) and delegates all source binding, protected-Racket execution, ordinary generation checks, parametric checks, receipt construction, and source-change guards to the official preflight. Its normalizer is covered by a task-local regression test. Labels and canonical program bytes are not changed.

## Retained evidence and limits

- Direct and copied-runtime tests: 14/14 passed.
- Structural self-audit: both settings × seeds 0 and 17; 24 pair claims; selector colors {3,4,6,7}; sizes through 30×30.
- Authoring preflight: four jobs (two settings × two seeds), 2 demonstrations + 4 queries each, 32 protected-Racket label evaluations, all passed.
- Causal witness: protected Racket replayed the qualified setting and a wrong selected-color intermediate; the final output changed.
- Public projection: 16 one-query views; source-bound projection verification passed. The combined first-turn check covered this task's four episodes with 24 private-field invariance mutations and four positive controls.

This is reviewer-ready source, not owner acceptance. The finite checks do not prove universal identifiability, and no training admission is claimed.
