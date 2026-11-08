# Tooling feedback

## F1: Biggest avoidable friction: witness output-path semantics

`review_witness template --out PATH` writes `PATH` as a JSON file, while `review_witness build --out PATH` creates `PATH/` as a directory containing `witness.json` and `replay.json`.  The successful template message also labels the file simply as `recipe`, which made it easy to treat it as a directory.  Use distinct flags such as `--recipe-out FILE` and `--bundle-out DIR`, or print the exact created member path and artifact type.
