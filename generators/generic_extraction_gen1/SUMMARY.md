# generic_extraction_gen1

gen1: keep-only ONE target color, then crop-to-content.

Transform: `(crop-to-content (keep-only g TARGET))` — from a large
multi-color noisy field, erase every color except TARGET (filter), then
crop to the tight bounding box of the surviving TARGET cells
(extraction). Output is the small TARGET-shaped patch; distractor
colors are scattered everywhere else and vanish.

Kind: `generic`. Imported version: `1.1.0`.
Approval is derived by the catalog from current code and retained evidence.
