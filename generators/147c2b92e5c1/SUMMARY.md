# 147c2b92e5c1 — select the unique holed object, transform it, and scale 2×

The input uses background `0` and has two regions:

1. **Header:** row 0 contains exactly one nonzero transform code; row 1 is blank.
2. **Body:** exactly three separated monochrome 4-connected objects. Exactly one object has one enclosed hole; the two distractors are holeless.

The transform code is:

- `1`: identity
- `2`: rotate 90° clockwise
- `3`: rotate 180°
- `4`: rotate 90° counter-clockwise
- `5`: flip left-right
- `6`: flip up-down

Select the unique one-hole body object, crop it tightly, apply the coded transform, and upscale it by a factor of 2 (each input cell becomes a 2×2 block). The distractors do not appear in the output.

The generated curriculum uses asymmetric one-hole shapes whose six coded outputs are distinct. It deterministically cycles all six codes, alternates whether the target is left/right and largest/middle-sized, spans the full declared dimension ranges, and inserts all five exact canonical dimension/palette profiles into every cyclic 20-draw window. These choices prevent fixed-transform, fixed-position, and fixed-size shortcuts from surviving ordinary lesson windows while retaining canonical-profile support.
