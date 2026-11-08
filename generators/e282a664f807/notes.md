# Working notes: e282a664f807

## 2026-10-25 base review and native family

- Replaced stale, mostly fixed metadata with strict observable controls for grid size, rectangle height/width, corner slope and distractor count. The canonical rule itself is unchanged.
- Ordinary generation now alternates positive- and negative-slope corner pairs, so every two-example window exercises both orientations. Canonical labels are replayed by an independent Python mirror and the protected Racket source.
- Added native `completion_policy` settings: `single_box` is the exact canonical program; `largest_completed` completes every two-cell candidate into a rectangle and then recolors the unique largest completed rectangle to 9.
- Retained an executable wrong-order program that chooses the smallest raw pair before completion. All raw candidates initially have count two, so only the completed intermediate exposes the input-dependent areas needed by the second stage.
- Generation supports 2–6 demonstrations, four stable private queries, a substantive 30x30 case, strict settings/count validation, and one-query public projection.
- Bounded self-review covered 64 seeds and 896 labelled pairs. No named rival survived, but this finite audit does not prove unrestricted uniqueness or learning benefit.
- Authoring preflight, protected causal replay and public-view checks passed for these exact sources. Owner source review, native owner qualification, fresh acceptance and any training admission remain pending.
