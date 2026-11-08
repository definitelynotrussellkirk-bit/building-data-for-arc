# 0ee26bf68bad

Extract the cropped cardinal contour of the largest monochromatic four-connected object, selected by cell count. The Racket rule is unchanged and pinned by `RULE_HASH=d66e3a1b4a29`.

Kind: `per_puzzle`. Selected version: `2.0.0`. Source SHA-256: `92caaf858ae07f4d83f9d097870d1b21b809fedc0c54478ba77c85984b790717`.

Implemented production alternates solid-rectangle scenes with joint counterexamples. Every scene has three monochromatic four-connected components and a unique largest; smaller components may tie, colors may repeat, and different colors may touch. Exact controls are height `7..14`, width `9..14`, winner color `1..9`, and rectangle/joint texture. All difficulty bands retain canonical shape support.

Reproduced evidence includes four canonical labels and 11 handcrafted Racket-labeled witnesses, including `counterexamples/joint_six_rivals.json`. Final emitted evidence in `WORK/checks/lesson-final.json` records 300 lessons and 1,200 rotations with no measured ambiguity against seven unique declared rivals; this is finite coverage, not universal identifiability.

Remaining support shortcuts can discard repeated-component colors or prefer hole-containing objects. Negative support for those alternatives is proposed, not implemented. See `notes.md` for exact source/evidence bindings, the emitted example, domain limits, and the still-retained prior audit. Catalog approval and training admission are separate from these reviewer-reported results.
