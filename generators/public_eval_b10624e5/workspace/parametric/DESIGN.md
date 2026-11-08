# Panel-relative reflected scaling

Infer the faithful b10624e5 rule: a blue cross separates four yellow panels, each containing a solid red square. The one decorated square supplies a multicolor template. Copy its decoration to other red anchors, scaled by target/source red-square side. Reflect horizontally when changing panel columns and vertically when changing panel rows. Preserve the source and dividers; clip copies to their destination panel.

Add episode parameter orientation=panel_reflections|preserve_orientation. Both settings must recover the source, anchor size and pixels; the alternative uses no panel-relative reflections but still scales. Pure recoloring would be cosmetic; changing scaling to an unrelated size would break the anchor correspondence. Preserve-or-reflect is the selected meaningful alternative. This is an implementer choice under the autonomous-build request.

A: identify the uniquely decorated panel and recover its anchor bbox/native side plus colored offsets. B: transform offsets relative to each destination anchor using input-dependent size ratios and panel differences. The causal ablation substitutes native source side one.

Scope only this home. Native resources adjacent in parametric/. Exact canonical default copy. Independent demos 2..6 and queries 1..4, private four-query bank with independent presentation permutation. Stress input 30x30 uses multiple anchor sizes and meaningful clipping at outer and divider boundaries.

Grammar: single-cell full blue cross; yellow background; one solid square red anchor per panel; exactly one panel has other pixels. Source can be in any quadrant. Sampler uses commensurate fine-pixel or macrocell patterns for fractional scales. General reference uses anchor-relative nearest-neighbor floor sampling; behavior on unobserved noncommensurate shrinking is an authored extension, not uniquely established by original gold.

Verify supplied two demos and test gold in protected Racket, independent hand fixtures, strict malformed/count validation, boundary clipping, numerical floors, source-color blue/black handling, finite executable rivals and hidden metadata/future query invariance. Owner registration and acceptance remain pending.
