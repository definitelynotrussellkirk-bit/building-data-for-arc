"""Make a small public/private example batch only after protected Racket checks."""
import argparse
import importlib.util
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demos", type=int, choices=range(2, 7), default=3)
    parser.add_argument("--queries", type=int, choices=range(1, 5), default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Choose a new output directory")
    here = Path(__file__).resolve().parent
    root = here.parents[3]
    from arcpuzzles.parametric_worker import evaluate_contract
    spec = importlib.util.spec_from_file_location("f47990415137_export", here / "export.py")
    writer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(writer)
    contract = json.loads((here / "promotion.json").read_text())
    jobs = [{"seed": args.seed, "settings": {"reference": reference},
             "demos": args.demos, "queries": args.queries}
            for reference in contract["parameters"]["reference"]]
    result = evaluate_contract(root, "f47990415137", contract, jobs)
    for episode in result["episodes"]:
        episode["reference"] = "reviewer_protected_racket"
        episode["owner_acceptance"] = "pending"
    files = writer.write_batch(result["episodes"], args.out)
    proof = {"racket": result["racket"], "checks": result["checks"],
             "racket_evaluations": result["racket_evaluations"],
             "owner_acceptance": "pending", "training_admitted": False}
    (args.out / "private" / "verification.json").write_text(json.dumps(proof, indent=2) + "\n")
    print(json.dumps({"status": "verified_examples", "episodes": len(result["episodes"]),
                      "queries_per_episode": args.queries, **files}, sort_keys=True))


if __name__ == "__main__":
    main()
