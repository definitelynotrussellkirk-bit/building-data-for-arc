# 600ed4e5d09c native parametric family

`transform_codebook=canonical` preserves the canonical program byte-for-byte.
`transform_codebook=inverse` changes only the key-to-transform codebook:

- key 1: clockwise rotation -> counter-clockwise rotation
- key 2: 180-degree rotation -> 180-degree rotation
- key 3: left/right reflection -> up/down reflection
- key 4: up/down reflection -> left/right reflection

Inputs are matched across settings. Every scene contains one hollow frame, one
selected asymmetric L tetromino with a full eight-element dihedral orbit, and
two non-outline distractors. The first two demonstrations use keys 1 and 3, so
the minimum two-demo episode identifies the declared setting. The final query
is 30x30 and includes boundary stress.

The sequential dependency is native: Step A selects, tightly crops, and
transforms the target object; Step B centers that transformed intermediate
inside the detected frame. `skip_transform.rkt` is the protected-Racket causal
ablation. `shifted_codebook.rkt` is an additional named rival.
