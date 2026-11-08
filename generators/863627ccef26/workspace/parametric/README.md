# Parametric family: 863627ccef26

- `merge_mode=union_conflict_9` preserves the exact selected ARC program.
- `merge_mode=intersection_only` infers A→B, applies that transform to Q, then
  keeps only Q∩transform(Q), colored 9.

The input grammar scales square panels from 3×3 through 9×9, producing complete
three-panel inputs up to 9×29. This is the largest exact three-panel square
layout below ARC's 30-column limit. Two demonstrations distinguish the settings;
four controller-side queries vary transform and panel size.
