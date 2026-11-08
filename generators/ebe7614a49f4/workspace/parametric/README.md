# `ebe7614a49f4` point/ray family

`render=points` is the exact canonical row/column activation program.
`render=rays` first derives the canonical active-row × active-column
intersection coordinates, then reads direction codes at only those coordinates
and traces green rays until color-8 obstacles or the grid boundary. Direction
codes away from the intersection set are decoys, making the first-stage selector
causally necessary.

The sampler is setting-independent, supports 2–6 demonstrations, and always
stores four distinct private queries. `adversarial_probe.py` checks the minimum
lesson, matched inputs, count corners, 30×30 stress, crossed controls, tamper
rejection, public first-turn privacy, and optional protected-Racket parity.
Owner qualification/acceptance and training admission remain separate.
