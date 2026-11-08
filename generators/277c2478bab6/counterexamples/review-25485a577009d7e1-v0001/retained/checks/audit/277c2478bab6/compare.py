import json, pathlib
root=pathlib.Path(__file__).resolve().parent
p=json.loads((root/'probe_results.json').read_text())
r=json.loads((root/'racket.json').read_text())
rivals=json.loads((root/'rival.json').read_text())
matches=[entry['output']==rival for entry,rival in zip(r['results'],rivals)]
print(json.dumps({'canonical_matches':sum(p['canonical_rival_fit']),'canonical_denominator':len(p['canonical_rival_fit']),'generated_matches':sum(matches[:12]),'generated_denominator':12,'manual_match':matches[12],'manual_difference_cells':sum(a!=b for ra,rb in zip(r['results'][12]['output'],rivals[12]) for a,b in zip(ra,rb)),'racket_errors':[e['error'] for e in r['results']],'boundary_exception_messages':[x['message'] for x in p['boundary_probes']]}))
assert len(r['results'])==13
assert all(e['error'] is None for e in r['results'])
assert all(p['canonical_rival_fit']) and all(matches[:12]) and not matches[12]
assert all(x['result']=='exception' for x in p['boundary_probes'])
