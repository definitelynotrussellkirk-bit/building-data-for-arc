"""Check final retained prototype files, boundaries, and current source hashes."""
import hashlib
import itertools
import json
from pathlib import Path

from reviewer_support import find_root


HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
BASE = HERE / "artifacts-final"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    report = json.loads((BASE / "report.json").read_text())
    assert report["runtime"]["protected"] is True
    assert report["runtime"]["backend"] == "racket"
    source = report["selected_generator"]
    assert digest((ROOT / source["path"]).read_bytes()) == source["sha256"]
    for path, sha in report["prototype_sources_sha256"].items():
        assert digest((ROOT / path).read_bytes()) == sha

    programs = {}
    for rule in report["rules"]:
        program = (BASE / rule["path"]).read_text()
        assert digest(program.encode()) == rule["sha256"]
        programs[rule["parameters"]["direction_scope"]] = program
    assert set(programs) == {"union", "rows", "columns"}

    demonstrations = queries = seeded = 0
    for episode in report["episodes"]:
        public = json.loads((BASE / episode["public"]).read_text())
        private = json.loads((BASE / episode["private"]).read_text())
        scope = private["parameters"]["direction_scope"]
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert len(public["test"]) == len(private["query_outputs"])
        assert digest(json.dumps(public, sort_keys=True).encode())[:16] in episode["public"]
        assert private["program"] == programs[scope]
        assert digest(private["program"].encode()) == private["program_sha256"]
        assert private["selected_generator"] == source
        assert private["parameters"] == episode["parameters"]
        assert private["parameter_selection"] == episode["parameter_selection"]
        assert private["identifiability"]["survivors"] == [scope]
        assert set(private["identifiability"]["rivals"]) == set(programs)
        for rival, result in private["identifiability"]["rivals"].items():
            assert bool(result["mismatching_demonstrations"]) == (rival != scope)
        demonstrations += len(public["train"])
        queries += len(public["test"])
        seeded += private["parameter_selection"] == "deterministic_seed"

    witness = json.loads((BASE / report["witness"]).read_text())
    assert witness["selected_generator_self_check"] == []
    assert set(witness["outputs"]) == set(programs)
    for row in witness["pairwise_differences"]:
        left, right = witness["outputs"][row["left"]], witness["outputs"][row["right"]]
        cells = [[r, c] for r, values in enumerate(left) for c, value in enumerate(values) if value != right[r][c]]
        assert cells and len(cells) == row["differing_cells"] and cells[0] == row["first_cell"]
    assert len(witness["pairwise_differences"]) == len(list(itertools.combinations(programs, 2)))

    counts = report["counts"]
    assert counts["episodes"] == len(report["episodes"])
    assert counts["distinct_public_challenges"] == len(list((BASE / "public").glob("*.json")))
    assert counts["demonstrations"] == demonstrations
    assert counts["queries"] == queries
    assert counts["seed_selected_episodes"] == seeded
    assert counts["finite_rival_demonstration_executions"] == len(programs) * demonstrations
    result = {
        "status": "pass",
        "report": "artifacts-final/report.json",
        "report_sha256": digest((BASE / "report.json").read_bytes()),
        "verifier_sha256": digest(Path(__file__).read_bytes()),
        "counts": counts,
        "selected_generator": source,
        "prototype_sources_sha256": report["prototype_sources_sha256"],
        "witness_pairwise_differences": witness["pairwise_differences"],
    }
    (HERE / "artifact-verification.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
