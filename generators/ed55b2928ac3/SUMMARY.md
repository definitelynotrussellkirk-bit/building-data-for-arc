# ed55b2928ac3

Read the key at `(0,0)`, clear it, crop the remaining nonzero content, and apply the keyed transform: `1=rotate-cw`, `2=rotate-180`, `3=flip-lr`, `4=flip-ud`, `5/6/7=identity`.

The native generator now uses honest exact controls over the full declared 6–12 grid bounds, every key, and 3–6 connected non-rectangular content cells. `self_check` validates the broader canonical domain: canonical shapes need not be fully asymmetric and may reuse the key color.
