# Repeated-shape class policy

The native family preserves the exact canonical `most_frequent` Racket program
and adds `least_repeated`. Every input has exactly two repeated normalized-shape
classes with distinct frequencies, plus optional singleton distractors. Inputs
are identical across settings; demonstrations teach which repeated class is
selected.

The rule is sequential: **A** groups objects and selects a repeated class;
the intermediate is that class's normalized shape and measured frequency;
**B** scales the selected shape by that frequency and paints it cyan. Replacing
the selected shape/frequency pair changes the protected-Racket result.

The adapter supports 2–6 demonstrations and 1–4 queries independently. The
first two demonstrations deliberately reverse area/mass and top-left cues while
using different frequencies. The fourth query is a distributed 30×30 scene with
nine objects and 76 foreground cells. `rival_audit.py` checks named selection,
fixed-scale, and constant-output shortcuts over bounded seeds.
