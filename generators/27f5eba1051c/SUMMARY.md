# 27f5eba1051c

Read the one-based rank at `(0,0)`, clear that marker, sort the three disconnected monochrome objects by occupied-cell count descending, leftmost column ascending, then color ascending, and crop the selected object's inclusive bounding box.

Kind: `per_puzzle`. Generator version: `5.0.0`.

The default sampler uses a four-example cyclic teaching schedule: a canonical-linked profile, an occupied-area tie resolved by column, an equal-area/equal-column tie resolved by color, and a semantic stress profile. The stress profile includes disconnected objects sharing a color and conflicts occupied-cell ranking with bounding-box area and position, so every four consecutive default examples refute the declared plausible shortcuts.

Approval is derived by the catalog from current code and retained evidence; this file does not grant approval.
