# Scan-order serialization with optional run-length encoding

`mode=scan_only` is the selected canonical Racket program byte for byte: collect
all nonzero input cells in row-major order into one output row.

`mode=scan_then_rle` is a genuine two-stage rule. Step A produces that ordered
one-dimensional sequence. Step B consumes the sequence and run-length encodes it
into two aligned rows: run colors above, run lengths below. The ordering and run
boundaries are properties of Step A's intermediate. Reversing that intermediate
before Step B changes the final grid on every admitted pair.

The sampler first chooses an explicit run sequence, then scatters its values over
well-separated positions while preserving row-major order. Inputs are identical
across settings and every pair distinguishes them. It supports 2–6 demonstrations
and 1–4 queries independently. The last query is 30×30, touches all four input
boundaries, and contains 24 marks with bounded run lengths.

## Bounded audit

`audit.py` replays both programs with protected Racket at four seeds and then
checks matched inputs, distinct pairs, setting separation, and five plausible
rivals over a configurable seed range. The retained 256-seed run checked 512
full episodes and 5,120 setting-paired examples. Early review found that unique
run colors let a global histogram imitate RLE; every scene now repeats one color
in separated runs, and the regression verifies that the histogram disagrees.
Finite screening is not a proof of unique induction.
