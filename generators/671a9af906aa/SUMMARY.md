# 671a9af906aa

Find the shortest orthogonal route from start 2 to goal 3 in a color-8 maze while tracking whether key 4 has been collected; door 5 is passable only after collection. Paint traversed zero cells 7, preserve all markers, and return the input unchanged when no lawful route exists.

Version `2.0.1` preserves the constructive perfect mazes and five-scene route cycle (`key_detour`, `key_bypass`, `key_detour`, `key_bypass`, `unreachable`). A rotating 25-scene size schedule gives every route profile 80% canonical-size and 20% enlarged support, removing the previous perfect relationship between height and reachability. Any six-scene window retains at least two-thirds canonical-size support. Exact `grid_h`, `grid_w`, and `route_mode` controls and canonical rule hash `09280085884a` are unchanged. Lesson output validation rejects Boolean/float color aliases before comparing labels.

Focused verification: 37 task tests pass; all three difficulty bands cover all six size/profile combinations over one schedule cycle; 18 generated examples and all four canonical pairs match executed Racket labels. The full inherited battery and large census were not rerun for this revision.

Kind: `per_puzzle`. Current generator SHA-256: `d8f73a03d424429172711492b4c6251cc82ac2adecc6f8fa28f81e004392095a`.
Approval remains a catalog decision derived from current code and retained evidence.
