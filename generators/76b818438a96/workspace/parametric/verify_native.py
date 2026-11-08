"""Bounded native-family evidence with replayable protected-Racket rivals."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("_76b818438a96_verify_prototype", HERE / "prototype.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    episodes = [p.build_episode(seed=17, parameter=value, n_train=3, n_test=4) for value in p.VALUES]
    assert [pair["input"] for pair in episodes[0]["pairs"]] == [pair["input"] for pair in episodes[1]["pairs"]]
    identifiers = [p.public_challenge_id(e["public_challenge"]) for e in episodes]
    assert len(set(identifiers)) == 2
    summaries = []
    generator = p.load_generator()
    for episode in sorted(episodes, key=lambda e: p.public_challenge_id(e["public_challenge"])):
        identifier = p.public_challenge_id(episode["public_challenge"])
        paths = p.write_episode(episode, args.out / "episodes" / identifier)
        sizes, path_lengths, extension_counts, occupied, spans, bend_crossings = [], [], [], [], [], 0
        for pair in episode["pairs"]:
            assert not p.scene_issues(pair["input"])
            scene = generator._scene_info(pair["input"])
            sizes.append([scene["height"], scene["width"]])
            points = [(r, c) for r, row in enumerate(pair["input"]) for c, value in enumerate(row) if value]
            occupied.append(len(points))
            spans.append([max(r for r, c in points)-min(r for r, c in points)+1,
                          max(c for r, c in points)-min(c for r, c in points)+1])
            for link in scene["links"]:
                path_lengths.append(len(link["path"]["cells"]))
                extension_counts.append(link["extension_count"])
                start = link["other_endpoint"] if episode["parameter"] == "opposite" else link["aligned_endpoint"]
                walked = generator._walk_from(link["path"], start)[:link["extension_count"]]
                directions = {(b[0]-a[0], b[1]-a[1]) for a, b in zip(walked, walked[1:])}
                bend_crossings += len(directions) > 1
        assert bend_crossings and episode["teaching"]["all_rivals_refuted_by_demos"]
        short_inputs = p.sample_inputs(17, 3, 1)
        first_turn = {"train": episode["public_challenge"]["train"],
                      "test": episode["public_challenge"]["test"][:1]}
        assert [pair["input"] for pair in first_turn["train"]] == short_inputs[0]
        assert first_turn["test"][0]["input"] == short_inputs[1][0]
        assert set(first_turn) == {"train", "test"} and set(first_turn["test"][0]) == {"input"}
        changed = deepcopy(episode)
        changed.update(seed=12345, parameter="private-value", programs={"hidden": "different"})
        changed["test"][0]["selected_output"][0][0] = (changed["test"][0]["selected_output"][0][0]+1) % 10
        assert p.public_challenge_bytes(changed["public_challenge"]) == p.public_challenge_bytes(episode["public_challenge"])
        summaries.append({"setting": episode["parameter"], "seed":17, "demos":3, "queries":4,
                          "public_id":identifier, "sizes":sizes, "occupied_cells":occupied,
                          "foreground_spans":spans, "path_length_range":[min(path_lengths),max(path_lengths)],
                          "extension_count_range":[min(extension_counts),max(extension_counts)],
                          "recolorings_crossing_bends":bend_crossings, "sampling":episode["sampling"],
                          "teaching":episode["teaching"], "racket":episode["racket"],
                          "public_path":str(Path(paths["challenge"]).relative_to(args.out)),
                          "private_path":str(Path(paths["evidence"]).relative_to(args.out)),
                          "first_turn_sha256":hashlib.sha256(p.public_challenge_bytes(first_turn)).hexdigest()})
    # Two small demonstrations fail to teach uncapped long traversal.
    inputs = [p._scaled_scene(seed,14,teaching=True) for seed in (1,2)] + [p._scaled_scene(3,30,teaching=True)]
    correct = p.load_programs()["opposite"]
    capped = correct.replace("(ext-count (length ext-cells))", "(ext-count (min 6 (length ext-cells)))")
    outputs, runtime = p.execute_programs(inputs,[correct,capped])
    assert outputs[0][:2] == outputs[1][:2] and outputs[0][2] != outputs[1][2]
    pairs = [{"input":grid,"output":output} for grid,output in zip(inputs,outputs[0])]
    weak = p.teaching_check(pairs[:2],pairs[2:],"opposite")
    repaired = p.teaching_check([pairs[0],pairs[2]],[pairs[1]],"opposite")
    assert "cap_6" in weak["unsafe_rivals"] and not repaired["unsafe_rivals"]
    mismatch = [[r,c] for r,row in enumerate(outputs[0][2]) for c,value in enumerate(row) if value != outputs[1][2][r][c]]
    save(args.out / "teaching-counterexample.json", {"racket":runtime, "program":correct,"rival_program":capped,
        "demonstrations":pairs[:2], "query":pairs[2], "rival_query_output":outputs[1][2],
        "different_query_cells":mismatch, "before":weak,"after_same_demo_count":repaired,
        "repair":"replace the second small demonstration with a long traversal example"})
    native_guard = p.scene_issues(generator.generate(987076,76,difficulty="hard"))
    assert any("ray" in reason for reason in native_guard)
    summary = {"schema":"76b818438a96-native-verification-v1", "status":"passed",
        "requested_episodes":2,"successful_episodes":2,"failed_episodes":0,
        "canonical_generator_sha256":hashlib.sha256((p.ROOT/f"generators/{p.TASK}/generator.py").read_bytes()).hexdigest(),
        "program_sha256":episodes[0]["program_sha256"], "episodes":summaries,
        "capped_rival_query_differences":len(mismatch),"confirmed_canonical_case_rejected":native_guard,
        "limits":["two materialized episodes; native qualification and count-boundary tests are separate",
                  "11 explicit rivals do not prove universal identifiability",
                  "sequential reveal checks cover first-turn projection, not a downstream trainer implementation",
                  "canonical sampler retains the separately recorded blocked-ray defect; native filter excludes it"]}
    save(args.out / "summary.json",summary)
    print(json.dumps({"status":"passed","episodes":2,"labels":14,
                      "capped_rival_query_differences":len(mismatch),"summary":str(args.out/"summary.json")},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
