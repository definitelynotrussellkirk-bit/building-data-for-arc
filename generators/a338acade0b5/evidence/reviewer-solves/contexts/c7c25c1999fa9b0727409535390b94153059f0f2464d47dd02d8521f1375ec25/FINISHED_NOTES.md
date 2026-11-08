# Blind solve notes — a338acade0b5

- Visible examples contain exactly two equal-colored non-background markers.
- Example 0: markers at (1,1) and (1,5), inclusive horizontal span 5; output is a 1×5 strip.
- Example 1: markers at (2,8) and (8,8), inclusive vertical span 7; output is a 1×7 strip.
- Example 2: markers at (0,6) and (4,2), a 45-degree diagonal with inclusive span 5; output is a 1×5 strip.
- Hypothesis: output length is the inclusive Chebyshev distance, `max(|dr|, |dc|)+1`, representing the number of cells on an axis-aligned or 45-degree segment.
- Training uses red (2) markers and azure (8) output. Query 0 deliberately uses azure markers, suggesting the colors swap rather than output always being azure. I therefore map 2↔8 and retain any other marker color unchanged as a conservative fallback.
- No generator, canonical rule, reference solution, private label, or audit evidence was consulted.
