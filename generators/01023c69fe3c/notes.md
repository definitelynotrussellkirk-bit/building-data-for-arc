# Working notes: 01023c69fe3c

## 2026-10-26 reviewer build

- Current base source is `generator.py` version `1.2.3`, SHA-256 `4d216376a0448e4d81452e93d753e8d7324bcc4c7de055b3d583f56956ba3d47`. Canonical authority and canonical program were not edited; rule hash remains `a403765e8e23`.
- Repaired two base-source defects. First, `near_corners` could collapse to same-row anchors on a legal 5×6 edge-avoiding scene. Second, the declared `n_decor=0..6` axis rejected explicit values 4–6 because the 0–3 default draw was evaluated eagerly. Both have focused regressions; explicit decor overrides now use strict 0–6 validation while the default sampler remains 0–3.
- Built native settings `canonical` and `interior_cue`. `canonical` returns the canonical program byte-for-byte. `interior_cue` computes the canonical crosshair/interior grid, uses the derived blue interior to select a unique input cue color, then paints only remote same-color cells in intermediate-zero positions azure.
- The sampler is setting-neutral, supports 2–6 demonstrations and 1–4 queries, and always has a four-query bank containing 8×12, 15×15, 24×27, and substantive 30×30 cases. The first two demos use different cue colors and cross semantic roles across all six decor colors.
- Adversarial reversals retained in `workspace/parametric/evidence/adversarial.json`: replaced a non-causal global color swap with a selector-cell-only control; crossed demo colors to defeat fixed-color shortcuts; excluded payloads from the complete expanded selector zone; and excluded cue-colored crosshair nuisances from that zone.
- The protected causal witness changes only step A's selector from the exact canonical interior to a one-cell-expanded rectangle. The expanded selector reads an earlier ring decoy of another color and therefore changes the final remote payload.
- Reviewer evidence is source-bound and ready for owner review, but it is not owner qualification, owner acceptance, or training admission. Next action: integrate the delta, perform owner source review, refresh native qualification from integrated source, and run fresh acceptance before any training use.
