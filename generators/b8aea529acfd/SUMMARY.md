# b8aea529acfd

A black canvas contains one padded, completely filled rectangular body using exactly two foreground colors. One color is the strict majority; the minority color forms a sparse horizontally asymmetric motif. The output crops the nonzero bounding rectangle and flips that crop left-to-right.

Kind: `per_puzzle`. Reviewed version: `2.1.0`.

Ordinary draws alternate one of twelve preserved anchor profiles with a dense edge-accent witness. These witnesses distinguish majority-color cropping and modal-background inference from the selected rule. Three demonstrations and one query support holding out any one of the four ordinary pairs. Explicit profile overrides retain their exact requested profile and bypass this coverage schedule.

Task tests enforce filled bodies, ordered palette roles, actual canonical-shortcut fit, all eight schedule starts, and the seed-370 duplicate-rejection regression. The reusable source-bound crop probe is in `workspace/probe_crop_contract.py`; exact counterexamples and Racket labels are in `counterexamples/`.

Approval is derived by the catalog from current code and retained evidence.

Owner acceptance: current repaired source is retained with reviewer-reported checks; audits of the other two targets remain unresolved. No model trajectory is training-admitted.
