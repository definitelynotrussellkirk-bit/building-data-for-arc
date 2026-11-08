# Adversarial-witness ticket report

Ticket: `ticket-39b2589aa4b0c084`  
Consumer: `target_current_audit`  
Pinned target: `5f6fdf4f9900` / generator `569fc64005104d307d54d9b451c1b7f2ac9397f52f6e986ee2d7b7f46009bd83` / rule `9c543a96623c`

## Shortcut inspected

The canonical rule checks eligible diagonal neighbours in `NW, NE, SW, SE` order and uses the **first** eligible direction. The bounded rival uses the same concave-corner condition and rendering, but chooses the **last** eligible direction. It is plausible because all eight canonical occurrences (four unique inputs duplicated across training and augmented rows) produce the same output under both priority rules.

## Retained lawful witness

Using ticket-derived generation seed `6478827037103426384`, the fifth ordinary draw (`sample_index = 4`, profile `n4_sparse`) is a lawful current-source counterexample.

At input cell `(row=1, col=0)`, both `NE=(-1,+1)` and `SE=(+1,+1)` satisfy the concave-corner condition. The selected authority uses NE because it is first; the shortcut uses SE because it is last. Those directions have opposite diagonal orientation, producing eight differing output cells in the corresponding 4×4 expanded block.

- `self_check` returned `[]`.
- One protected Racket execution matched the Python first-eligible mirror.
- The Racket output differed from the last-eligible shortcut at all eight retained cells.
- The probe found the witness after five draws and completed in 3.625 seconds.

This completes the ticket as a current-source coverage witness. It is **not** a peer safety finding: the current generator can produce a lawful counterexample to the canonical-fitting shortcut. The bounded probe did not test production lesson windows, so it does not establish that every episode contains such a counterexample.

## Files

- `probe.py` — exact bounded shortcut search.
- `probe.log` — actual wrapper output.
- `probe-result.json` — source-bound result and limits.
- `witness.json` — input, protected label, rival output, ambiguous corner, and differing cells.
- `racket-receipt.json` — protected authority receipt.
