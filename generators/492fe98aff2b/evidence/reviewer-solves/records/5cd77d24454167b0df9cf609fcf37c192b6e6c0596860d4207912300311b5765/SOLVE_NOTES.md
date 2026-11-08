# Solve work log

## Exposure declaration before solving

I had not opened the generator, Racket rule, task notes, reference solutions, private query labels, or any prior explanation for task `492fe98aff2b`. I used only `solve-blind/challenge.json`, the provided solution template, and my own visible-example probe.

## Observation and hypothesis

Each training output is exactly the minimal axis-aligned bounding rectangle around all nonzero input cells. Empty rows and columns *inside* that rectangle are preserved; only the all-zero margin outside the extremal colored cells is removed.

Concrete checks:

- Train 0: nonzero rows 1–3 and columns 2–6 produce the shown 3×5 output, including the zero middle row.
- Train 1: nonzero rows 3–6 and columns 5–10 produce the shown 4×6 output.
- Train 2: nonzero rows 1–5 and columns 3–7 produce the shown 5×5 output.

Rejected alternatives were deleting every empty row/column or extracting each colored run separately; both would remove internal spacing that the outputs retain.

## Revision 1

Hypothesis: crop the input to the smallest rectangle containing every cell whose value is not background color 0.

Probe: `cd solve-blind && python3 probe_visible_examples.py`. Before implementation, the probe failed at the template's `NotImplementedError`, establishing the red test. After implementation it should match all three visible examples. The all-zero fallback returns a copy of the input; this case is not demonstrated by the challenge and does not affect the observed rule.
