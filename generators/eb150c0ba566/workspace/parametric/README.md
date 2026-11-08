# Native prototype-policy family

`prototype_policy` is either `matching` (the byte-exact canonical rule) or
`opposite_shape`. Each seed still paints with its own color, but the alternative
selects the other header prototype's 3x3 mask before stamping. Inputs are shared
across settings, support 2–6 demonstrations and four query prefixes, and include
an occupied 30x30 stress scene.

Sequential dependency: step A reads each seed and selects a 3x3 prototype mask;
the intermediate is that input-derived mask; step B stamps its occupied offsets
at the seed using the seed color. The stamp footprint cannot be determined until
step A selects the mask.
