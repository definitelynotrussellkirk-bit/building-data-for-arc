# 85e65da9fb15

A 0-background grid contains two hollow rectangular frames and two to four loose 4-connected shapes. Process loose shapes in top-left order. For each shape, choose the unused frame it fits most tightly by bbox area, breaking ties by frame top-left position; keep the original orientation when it fits, otherwise rotate 90 degrees clockwise if that fits. Center the shape in the chosen frame. Output only the frames and successfully filed shapes; unmatched shapes disappear.

The generator cycles three teaching profiles over consecutive sample indices: centered placement with slack, order-sensitive frame competition, and required rotation with unmatched distractors. Only exact grid dimensions are advertised as overrides; all other variation is deterministic keyed sampling.

Kind: `per_puzzle`. Reviewed version: `3.0.0`.
