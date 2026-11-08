# 42a152269589

A zero-background 10×(10–13) grid contains 3–5 separated, single-colour polyomino components. The components use exactly three foreground colours and total 12 cells. The rule sorts pieces by descending area and ascending colour, then backtracks them into a 3×4 rectangle: first translation-only, then with rotations, then with rotations and reflections.

Version `3.0.0` uses a three-slot curriculum:

1. `translation_anchor` — the supplied orientations already tile 3×4.
2. `rotation_required` — translation fails but rotations solve it.
3. `reflection_and_repeat` — rotations fail, a reflection is required, and a colour is repeated across disconnected components.

The generator includes an exact Python mirror of the selected Racket rule, canonical-aware validation, exact observable overrides, declared rival solvers, counterexample witnesses, and lesson-identifiability checks.

Kind: `per_puzzle`. Approval is derived by the catalog from current code and retained evidence.
