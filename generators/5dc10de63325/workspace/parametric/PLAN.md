# Native count/component family: implementation plan

Goal: promote the existing three exact fill-order programs and add a largest-cyan-component count rule without changing production semantics.

Design: A segments monochromatic cardinal cyan components and measures the largest. B applies the canonical quarter-count glyph renderer to that measured count. This is a derived-mask/count dependency, not iterative simulation. All settings share input grids. The new native API is separate from the legacy prototype API; legacy exports are not the new native public-turn format.

Constraints: exact canonical bytes; Python 3.12+; native 4–6 demos / 1–4 queries, all four sampled before projection. The fourth demo is necessary because the first three establish q1/q2/q3 glyphs but do not distinguish global from component counting. Production and legacy APIs remain unchanged. Source counts 4–19 bound signal density; large stress adds semantically ignored noncyan distractors and distributes signal to all borders instead of claiming dense cyan is lawful.

Tasks:
- [x] Write native contract tests; retain a failing run.
- [x] Implement adjacent-path legacy reuse, strict request validation, connected components, constructive sampler, finite teaching audit, one-query projection.
- [x] Test the complete scoped suite; inspect two surfaces: minimum teaching lesson and 30x30/control/privacy boundaries.
- [x] Build a reusable bounded audit with independently executed protected-Racket labels.
- [x] Inventory exact source, qualify all settings, export through the existing shuffled preview helper and replay a source-bound wrong-intermediate witness.

Review focus: no min/max clamping; diagonal versus cardinal connectivity; all-nonzero distractor shortcut; max-count overflow; private fields anywhere in pairs; single-query prefix independent of requested demo count. No fresh reviewer is available; final review is author self-review. A native qualification is not acceptance or training admission.

Self-review: no remaining functional finding on the bounded scope. Native qualification 8 jobs / 160 protected evaluations, 32 public turns checked, causal witness reviewer_replayed. Owner acceptance not performed.
