# 2f58238f8bb6

Row 0 holds transform-key cells (1=identity, 2=rotate-CW, 3=rotate-180, 4=flip-LR). Crop the single monochrome template below the key row and render one transformed copy per key cell, in order, top-aligned with one-column gaps. Repeated touching key cells are separate commands.

Kind: `per_puzzle`. Version: `3.0.0`. Canonical Racket rule pin: `6da56985f4bc` (unchanged).

Default draws alternate asymmetric, repeated-command teaching examples with broader connected shapes. Three demonstrations from any four default accepted pairs retain a complete key-map witness. Exact controls are `grid_h`, `grid_w`, `n`, and `template_color`; all advertised combinations are supported in every difficulty. Explicit overrides can remove teaching support, so check the resulting lesson.

`workspace/check_lesson.py` checks a saved visible lesson's transform-map sufficiency without consulting query labels. The semantic gate and source-bound census additionally exercise the declared command/gallery rivals. These are finite hypothesis checks, not universal identifiability or training admission.
Approval is derived by the catalog from current code and retained evidence.
