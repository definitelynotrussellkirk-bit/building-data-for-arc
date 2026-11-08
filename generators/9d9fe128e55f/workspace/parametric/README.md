# Proposed parametric family: `9d9fe128e55f`

`rank_policy` is fixed for an episode:

- `all_by_size` is the exact canonical program: sort every color-8 component by occupied area and repaint it with the legend in that order.
- `right_anchor_threshold` first selects the color-8 component whose rightmost cell is closest to the separator, binds its occupied area, then keeps and size-ranks only components whose area is at least that threshold. Smaller components disappear and surviving components consume the legend from its first color.

The alternative is genuinely sequential: selecting the anchor produces an input-dependent size threshold, and that threshold changes both eligibility and palette assignment. Inputs are matched across settings. The deterministic bank supports 2–6 demonstrations, defaults to 3, qualifies the adversarially checked two-demo minimum, and always stores exactly four distinct queries for sequential reveal. The final query is a substantive 30×30 scene.

The first two demonstrations use crossed controls and include a guaranteed diagonal-only contact that distinguishes 4-connectivity from a plausible 8-connected shortcut. `adversarial_probe.py` is the bounded replay tool for seed/count/settings rivals plus protected Racket checks of canonical, base-generator, and parametric labels.

Python labels are claims only. Native preflight re-executes retained labels through protected Racket. This family is proposed and unapproved; owner source review, native qualification, exact-source acceptance, and any training admission remain separate.
