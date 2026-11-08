from reviewer_support import canonical_pairs, find_root
import json
pairs=canonical_pairs('017f1406edaf', root=find_root(__file__), labeled_only=True)
print(json.dumps(pairs, indent=2))
