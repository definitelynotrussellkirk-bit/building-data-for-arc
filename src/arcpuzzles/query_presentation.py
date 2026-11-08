"""Private deterministic query ordering and single-turn public projection.

Source query banks and presentation records belong to the controller. A yielded
turn contains only demonstrations and the current query input.
"""
from copy import deepcopy
import json
import random

SCHEMA = 'arcpuzzles-query-presentation-v1'


def query_order(total, seed):
    if type(total) is not int or total < 1 or type(seed) is not int:
        raise ValueError('Query presentation needs a positive count and integer seed')
    order = list(range(total))
    # Domain separation keeps presentation independent of generator RNG state.
    random.Random(f'{SCHEMA}:{seed}').shuffle(order)
    return order


def present_queries(episode, *, seed, count):
    """Copy a complete source bank, shuffle pairs, and then select a prefix."""
    bank = deepcopy(episode['test'])
    if type(count) is not int or not 1 <= count <= len(bank):
        raise ValueError('Presentation count must select a nonempty bank prefix')
    order = query_order(len(bank), seed)
    result = deepcopy(episode)
    result['query_presentation'] = {
        'schema': SCHEMA, 'seed': seed, 'source_indices': order,
        'source_queries': bank, 'source_episode_id': episode.get('episode_id'),
        'selected_count': count,
    }
    result['test'] = [deepcopy(bank[i]) for i in order[:count]]
    return result


def verify_presentation(episode):
    """Check private projection consistency; legacy source order remains readable."""
    record = episode.get('query_presentation')
    if record is None:
        return episode['test']
    fields = {'schema', 'seed', 'source_indices', 'source_queries',
              'source_episode_id', 'selected_count'}
    if (type(record) is not dict or set(record) != fields or record['schema'] != SCHEMA
            or type(record['source_queries']) is not list
            or type(record['selected_count']) is not int
            or not 1 <= record['selected_count'] <= len(record['source_queries'])
            or type(record['seed']) is not int or record['seed'] != episode['seed']):
        raise ValueError('Invalid private query presentation')
    order = query_order(len(record['source_queries']), record['seed'])
    # JSON comparison distinguishes booleans from integer source indices/cells.
    encode = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    if (encode(record['source_indices']) != encode(order)
            or encode(episode['test']) != encode([record['source_queries'][i]
                                                  for i in order[:record['selected_count']]])):
        raise ValueError('Query presentation permutation or paired answers differ')
    return record['source_queries']


def iter_public_turns(episode, *, limit=None):
    """Yield the stored presentation order, one bare model-visible turn at a time.

    Call next only after obtaining the current answer. Never pass the source
    episode, iterator state, bundle directory or private labels to the actor.
    """
    if limit is not None and (type(limit) is not int or not 1 <= limit <= len(episode['test'])):
        raise ValueError('Turn limit must select a nonempty presentation prefix')
    for pair in episode['test'][:limit]:
        yield {'train': [{'input': deepcopy(p['input']), 'output': deepcopy(p['output'])}
                         for p in episode['train']],
               'test': [{'input': deepcopy(pair['input'])}]}
