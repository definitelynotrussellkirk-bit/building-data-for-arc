# ffe1da16c912

Match a transformed query support to one of three prototype panels.

Kind: `per_puzzle`. Selected version: `3.0.0`.

The generator uses a fixed four-panel 3×15 grammar. Three equal-area, pairwise D4-distinct prototypes form the library; the fourth panel is a rotated/reflected and recolored copy of exactly one family. The answer restores the matched prototype's displayed orientation, crops it tightly, and uses the query color.

Natural curriculum:

- easy / medium / hard: 4 / 5 / 6 cells per prototype;
- match position cycles through all three panels every three examples;
- all eight D4 transforms occur in every 24-example joint schedule;
- the matched family has eight distinct D4 images, so transform overrides are observable;
- all prototypes have equal area, ruling out count-only family selection.

Rule hash: `c4020b613ba0`. The selected Racket rule is unchanged. The review after battery is 12/12 green; focused tests are 80/80 green. Approval remains catalog-derived from current code and retained evidence.
