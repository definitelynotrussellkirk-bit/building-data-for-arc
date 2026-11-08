# Working notes: 6ecd6f93877b

## Final review state

- Generator version: `3.0.0`
- Final source SHA-256: `1e7aeefc5a4bc0e9178e0dcebea9d86e24f2dda7453060cbcc8effb08a8e99a0`
- Pinned rule hash: `66d1273fdbac`
- Racket authority changed: no
- Final full battery: 12 green, 0 advisory, 0 failed
- Focused tests: 50 passed
- Deep lesson census: 300 lessons, 1,200 pairs, 1,200 unique inputs, 1,200 query rotations, zero declared ambiguity

## Root cause

The imported generator used a copied multi-axis template whose controls were largely inert, aliased, or silently narrowed by difficulty. More importantly, all five labeled pairs have per-color count at most three and output length at most six. The old distribution stayed inside those ceilings, so `clip_counts_at_three` and `truncate_to_six` were indistinguishable from the authority.

## Repair decisions

The public contract was reduced to four exact controls: height, width, number of colors, and maximum count. Even indices are canonical anchors; odd indices are broad witnesses with a count of four and total output length seven through ten. A ten-column broad canvas preserves the canonical output-shrink relation discovered by the first repaired battery. Executable semantic rivals and a three-demo rotation hook bind the curriculum claim to actual lesson contents.

## Reusable tools

- `workspace/reference_probe.py`: independent rule/rival oracle and axis observer.
- `workspace/qualify.py`: deterministic replay, exact overrides, schedule support, all query rotations, shortcut witness, canonical-fit, and shape-drift checks.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `1e7aeefc5a4bc0e9178e0dcebea9d86e24f2dda7453060cbcc8effb08a8e99a0`.

# Decisions — 6ecd6f93877b

## D1: Preserve the Racket rule and repair only the sampler contract

The canonical rule is coherent and all five labeled pairs agree with it: count each nonzero color, order colors numerically, and repeat each by its full count. The defect was in generation and teaching support, not label authority. I therefore pinned `RULE_HASH = "66d1273fdbac"`, added an independent Python mirror for diagnostics, and made no canonical or archival Racket change.

Rejected alternative: changing the authority or canonical examples to manufacture broader coverage. That would alter the task rather than repair its generator.

## D2: Replace copied controls with four exact observable axes

The legacy interface exposed nine controls, many of which were aliases, inert, or accepted only in difficulty-specific subranges. The final public axes are only `grid_h`, `grid_w`, `n_colors`, and `max_count`. Each has one semantic meaning, can be observed from pixels, supports its complete declared range in every difficulty band, and composes with every other axis.

Rejected alternatives:

- retain palette/texture aliases and document their weak effect;
- silently clamp overrides to a difficulty band;
- accept unknown keys for forward compatibility.

Those choices make automated experiments irreproducible and conceal typos. The final implementation rejects invalid or unknown requests loudly.

## D3: Alternate canonical anchors and broad shortcut witnesses

The five canonical pairs admit at least two short wrong programs: cap counts at three and truncate the strip to six cells. Even sample indices stay in the canonical envelope; odd indices force a count of four and a total output length above six. This keeps approximately half of the default distribution close to retained data while making every broad example a counterexample to both shortcuts.

Rejected alternatives:

- sample broad cases only probabilistically, because a short lesson could miss them;
- abandon canonical-like examples entirely, because that would create unnecessary distribution drift;
- add only one of the two counterexamples, because each rival exploits a distinct canonical ceiling.

## D4: Use consecutive four-pair windows with three demonstrations

`EXAMPLES_NEEDED` is three. Lessons are assembled from four consecutive generated pairs, with one pair held out as query. Alternation gives every four-pair window two anchors and two witnesses; after any query rotation, at least one witness remains in the demonstrations. `lesson_identifiable` executes both competitors on the exact demonstrations and query.

This supports arbitrary query rotation rather than depending on a privileged final query position. The required-rotation semantic gate and a 300-lesson/1,200-rotation census validate that policy against the declared competitors.

Rejected alternative: declare an ordered-only curriculum and rely on witness frequency. Frequency alone does not prove that each complete lesson teaches the relevant distinction.

## D5: Preserve the canonical output-shape relation

The first repaired candidate used broad outputs of length seven through ten on narrower random canvases. Although the labels were correct, defect lint correctly identified a new transformation-shape regime: broad outputs were systematically wider than inputs. The final broad default fixes `grid_w` at ten, retaining both shortcut witnesses while preserving the canonical relation that the output strip does not exceed input width.

Rejected alternative: dismiss the shape warning as cosmetic. A solver can exploit shape regimes, so a new perfectly correlated geometry is itself a shortcut risk.

## D6: Keep semantic hypotheses executable

The generator now exposes `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`. Rival programs are executable and first checked to fit every usable canonical pair. A witness claim is then tested by disagreement with the authority-backed output.

Rejected alternative: document shortcuts only in prose. Executable competitors let future agents rerun exact lesson and rotation checks after changes.

## D7: Add a fast independent qualification path

`workspace/reference_probe.py` avoids importing generator helpers for its rule and rival calculations. `workspace/qualify.py` tests replay, exact controls, profile support, shape relation, witnesses, canonical shortcut fit, and all four query rotations across consecutive starts. It is intentionally a preflight tool, not label authority; final claims still use the Racket-backed battery and lesson census.

## Remaining limitations

- The semantic contract enumerates two strong competitors, not all possible programs.
- The valid domain is deliberately bounded to 5–10 rows/columns, 2–5 colors, and counts 1–4.
- Exact overrides can request valid combinations outside the default teaching profile; the default curriculum, not every possible override, preserves the canonical shrink relation.
- Alternation is deterministic, though the learner does not observe sample indices. Colors and positions remain independently randomized.
- Reviewer checks do not grant catalog approval or training admission.
