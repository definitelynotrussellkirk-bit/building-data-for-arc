# dd038eb3d459

A canonical-scale black grid contains exactly one blue control in a corner, one connected red polyomino, and one connected green polyomino. The control maps TL/TR/BR/BL to 0/1/2/3 clockwise quarter-turns. Normalize red, rotate and normalize green, take their symmetric XOR, normalize the result, and emit its tight cyan(8) crop.

Version `3.0.0` uses a four-example corner curriculum. Every four consecutive default samples include all four corner codes, and the TL example is constructed so 0° and 180° produce different answers; this refutes the strongest key-map shortcut left by the canonical pairs. Five exact canonical canvas profiles and connected 3–5-cell polyomino banks provide shape and placement diversity without advertising dead controls.

Kind: `per_puzzle`. Rule hash: `624c38e915df`.
Approval is derived by the catalog from current code and retained evidence.
