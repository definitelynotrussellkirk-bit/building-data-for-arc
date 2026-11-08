# Solve notes

Human-visible-example work log. This is an exposed post-repair solve: I had already seen the rule during generator review, but during this solve phase I did not consult the generator, Racket source, reference solutions, private labels, or the retained prior solve.

Each input is a uniform field plus one singleton. Output shape is unchanged. The singleton keeps its own color and equal Manhattan distances from it receive equal colors, producing diamond rings.

Train 0 has seed color 6. Reading outward gives `6,1,3,4,0,5,2,8,9` and then repeats. Train 1 (seed 3) and train 2 (seed 3) confirm the same phase and Manhattan metric. Thus the full cycle can be written `(0,5,2,8,9,6,1,3,4)`: find the unique non-modal seed and advance through this cycle by Manhattan distance modulo 9.
