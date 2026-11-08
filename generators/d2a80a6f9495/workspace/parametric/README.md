# Swap-scope parametric family

This task-local native family exposes one episode-fixed setting:

| `swap_scope` | Rule |
| --- | --- |
| `all_two_color` | Exact canonical program: swap the two colors in every 8-connected object that contains exactly two colors. |
| `repeated_pair` | Count unordered color pairs across eligible objects, then swap only objects whose pair occurs more than once. |

The canonical setting returns the selected authority bytes exactly. The alternate
retains the canonical object extraction and cellwise color swap; only the
input-derived eligibility set changes.

## Sequential dependency

1. **A:** extract every multicolor object, retain exactly-two-color objects, and count their unordered color pairs.
2. **Intermediate:** the global pair-multiplicity map and repeated-pair set.
3. **B:** swap colors only in objects selected by the episode setting.

For `repeated_pair`, B cannot decide eligibility from one object in isolation.
The retained protected-Racket counterfactual replaces every multiplicity with one;
that changes the final output on the qualified 30×30 case.

## Sampling and public projection

`generate(seed, settings, demos, queries)` supports 2–6 demonstrations and 1–4
queries independently. Inputs are matched across settings and prefix-stable as
counts change. Every scene contains two repeated pair classes, at least one
unique pair, one-color controls, and three-color controls. The four query sizes
are 14×16, 20×22, 26×28, and a substantive 30×30 boundary case.

`public_turn(episode, index)` returns all demonstrations and exactly one unlabeled
query. It exposes no setting, program, query answer, future query, query index,
or total-count hint; turn zero is identical to single-query generation.

`audit.py` checks the supported count boundary against eleven executable finite
rivals. This is a bounded learnability audit, not a universal uniqueness proof.
Native qualification and the causal witness execute labels through protected
Racket; owner acceptance and training admission remain separate.
