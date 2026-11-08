# Working notes: 67c14e0f76b1

## 2026-10-25 base review and native family

- Preserved the exact canonical local rule: mark a zero cell with color 2 only when its immediate horizontal neighbors are both blue.
- Adversarial review found a concrete base-teaching defect: one four-example window repeated the same irrelevant palette. The palette schedule now cycles by seed and sample index, and a regression checks every four-example window over 64 seeds.
- Added native `postprocess` settings on identical inputs: `mark_only` is canonical; `largest_marked` applies the canonical rule first, then recolors the unique largest newly marked four-connected component to 8.
- A three-demo prefix initially permitted a “recolor the first marked component” shortcut. The repaired prefix places the largest stack at right, middle and left, with a retained 64-seed regression.
- Retained an executable wrong-order program that selects/recolors a raw blue component before marking. This destroys one side of corresponding gaps, demonstrating that Stage B must consume Stage A’s intermediate.
- Generation supports 2–6 demonstrations, four stable private queries, a substantive 30x30 boundary case, strict settings/count validation and one-query public projection.
- Bounded self-review covered 64 seeds, 256 base lesson windows and 896 labelled pairs. No named rival survived, but this finite audit does not prove unrestricted uniqueness or learning benefit.
- Authoring preflight, protected causal replay and public-view checks passed for these exact sources. Owner source review, native owner qualification, fresh acceptance and any training admission remain pending.
