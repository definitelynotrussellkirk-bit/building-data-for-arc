"""A2: bounded reproduction of a source-implied narrow-frame shortcut."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = "d4ea5a7deae6"
SOURCE = REPO / "generators" / TASK / "generator.py"
SOURCE_SHA = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert SOURCE_SHA == "de9ab54c1aadf474c7571ee30545bbd8054b3598c98bbcfbf70588246006e73d"
spec = importlib.util.spec_from_file_location("audited_generator", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def rival(grid):
    """Use the token kernel but snap width-4 seeds to the nearest middle row."""
    out = [[1 if value == 1 else 0 for value in row] for row in grid]
    for frame in gen._frame_records(grid):
        r0, c0, r1, c1 = frame["bbox"]
        token = frame["tokens"][-1][2]
        sr, sc, color = frame["seeds"][-1]
        if c1 - c0 + 1 == 4:
            middle_rows = sorted({(r0 + r1) // 2, (r0 + r1 + 1) // 2})
            sr = min(middle_rows, key=lambda row: (abs(row - sr), row))
        for dr, dc in gen._kernel(token):
            r, c = sr + dr, sc + dc
            if r0 < r < r1 and c0 < c < c1:
                out[r][c] = color
    return out


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def prepare():
    catalog = Catalog(REPO)
    task = catalog.get(TASK)
    pairs = canonical_pairs(TASK, root=find_root(SOURCE), labeled_only=True)
    canonical_results = []
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        matches = rival(pair["input"]) == pair["output"]
        assert matches
        canonical_results.append({
            **{key: pair[key] for key in ("variant", "split", "pair_index")},
            "input_sha256": digest(pair["input"]),
            "output_sha256": digest(pair["output"]),
            "rival_matches_canonical_label": matches,
        })
    write("canonical_fit.json", canonical_results)

    # Canonical train 0 has a 5x4 right frame and a seed at (3, 9).
    # Relocate only that seed one row upward; the token at (2, 10) stays put.
    base = next(pair for pair in pairs if pair["variant"] == 0
                and pair["split"] == "train" and pair["pair_index"] == 0)
    witness = [row[:] for row in base["input"]]
    assert witness[3][9] == 5 and witness[2][9] == 0
    witness[3][9] = 0
    witness[2][9] = 5
    assert gen.self_check(witness) == []
    assert rival(witness) != gen.rule_mirror(witness)
    write("input.json", {"inputs": [witness]})
    write("rival.json", {"outputs": [rival(witness)]})
    write("mirror.json", {"outputs": [gen.rule_mirror(witness)]})

    # Supplementary bounded checks. These use the disclosed Python mirror;
    # actual authority output for the witness is obtained separately by CLI.
    cases = [(seed, 0, None, {}) for seed in range(12)]
    cases += [(0, 0, None, {"n_frames": n, "texture": texture})
              for n in (1, 2) for texture in ("centered", "clipped")]
    sample_results = []
    for seed, index, difficulty, overrides in cases:
        grid = gen.generate(seed, index, difficulty=difficulty, **overrides)
        matches = rival(grid) == gen.rule_mirror(grid)
        assert matches
        sample_results.append({
            "seed": seed, "sample_index": index, "difficulty": difficulty,
            "overrides": overrides, "input_sha256": digest(grid),
            "self_check": gen.self_check(grid),
            "narrow_frame_count": sum(frame["bbox"][3] - frame["bbox"][1] + 1 == 4
                                       for frame in gen._frame_records(grid)),
            "rival_matches_python_mirror": matches,
        })
    write("generated_probe.json", sample_results)
    canonical_narrow_specs = [list(frame) for _, _, frames in gen._PROFILE_SPECS
                             for frame in frames if frame[3] == 4]
    assert all(frame[5] in {(frame[2] - 1) // 2, frame[2] // 2}
               for frame in canonical_narrow_specs)
    rule = task["variants"][0]["program_solution"]
    write("binding.json", {
        "finding_id": "A2", "task_id": TASK,
        "classification": "new canonical-fitting shortcut / advertised-domain coverage gap",
        "generator_sha256": SOURCE_SHA, "generator_version": gen.VERSION,
        "canonical_rule_hash": task["rule_hash"],
        "canonical_rule_text_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "constructed": True, "seed": None, "sample_index": None, "overrides": None,
        "construction": {"from_canonical": {"variant": 0, "split": "train", "pair_index": 0},
                         "move_seed": {"from": [3, 9], "to": [2, 9], "color": 5}},
        "documented_domain": True,
        "documented_domain_reason": "11x13 grid; two separated complete frames 5x5 and 5x4; distinct tokens 2/4 and seed colors 6/5; exactly one token and seed per interior",
        "generated_domain": False,
        "generated_domain_reason": "General branch chooses widths 5..6; every width-4 canonical profile seed is on one of the central rows, preserved by reflection. This witness has narrow-frame seed at top interior row.",
        "self_check": gen.self_check(witness),
        "canonical_profile": gen.is_canonical_profile(witness),
        "canonical_narrow_specs": canonical_narrow_specs,
        "canonical_pair_count": len(pairs),
        "canonical_rival_match_count": sum(row["rival_matches_canonical_label"] for row in canonical_results),
        "bounded_generated_probe_count": len(sample_results),
        "bounded_generated_probe_authority": "Python rule_mirror, not Racket; supplementary source-check only",
        "racket_evidence": "racket.json (public apply command; generated separately)",
        "rival_evidence": "rival.json", "input_evidence": "input.json",
        "advertised_metadata": {"SUMMARY": gen.SUMMARY, "INVARIANTS": gen.INVARIANTS,
                                "AXES": gen.AXES},
    })
    print(json.dumps({"canonical_rival_matches": len(pairs),
                      "bounded_generated_rival_matches": len(sample_results),
                      "self_check": gen.self_check(witness),
                      "generator_sha256": SOURCE_SHA, "rule_hash": task["rule_hash"]}))


if __name__ == "__main__":
    prepare()
