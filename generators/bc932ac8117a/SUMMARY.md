# bc932ac8117a

A 0-background grid contains two different-colored, same-size monochromatic objects: one hollow framed template and one solid twin. Transfer **every** 4-connected zero region enclosed by the hollow object's bounding box into the solid twin at the same local coordinates, carving those solid cells to 0 and preserving everything else.

The 3.0.0 sampler uses 4×4 or 5×5 twins with a connected interior divider. Every ordinary input therefore has multiple enclosed holes while retaining colored interior cells, refuting both “hollow the whole interior” and “copy only the largest hole.” Object roles alternate left/right, and the three-demonstration lesson floor makes every one-query rotation include both orientations, refuting a rightmost-target shortcut.

Kind: `per_puzzle`. Current version: `3.0.0`. Canonical Racket rule hash: `bcafd3a4dd95` (unchanged).
