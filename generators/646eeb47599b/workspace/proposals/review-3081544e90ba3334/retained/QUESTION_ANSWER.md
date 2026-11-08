# Question answer

## `qwen9-data-value`

The single highest-value additional gate is a **seed-locked rival-separation gate with query rotation**. For every generated lesson, execute the canonical program and a small curated bank of plausible shortcut programs on the same demonstrations; then rotate each example into the query position. Admit the lesson only when the canonical program remains consistent and every rival is contradicted before the held-out answer is exposed.

A reproducible failure it would catch is an episode in which a coordinate shortcut or one-sided wall rule matches every demonstration but disagrees with the canonical program on the query. Such an episode supplies a correct label but ambiguous supervision: Qwen3.5-9B can minimize loss by learning the shortcut rather than the intended transformation.

A possible false positive is a rival that is syntactically different but extensionally equivalent on the generator's reachable input domain. The gate could reject a sound lesson because the sampled episode cannot distinguish two programs that never diverge on lawful scenes.

The cheapest test is entirely symbolic and model-free: keep a fixed bank of the existing retained rivals, generate roughly 32 seed-locked lessons spanning the declared profile bands, run all programs locally, and compare output hashes under every query rotation. This needs no Qwen inference and should run as a small pre-admission CI stage; only collisions require a larger search or human review.
