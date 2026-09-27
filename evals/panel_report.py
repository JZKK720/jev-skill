"""Publish source-free derived records and regenerate result tables without API calls."""
import argparse
import json
from pathlib import Path
import statistics
from . import model_panel
from .calibration import digest
from .calibration_metrics import summarize as calibration_summary
from .run import aggregate, dump


def metrics(rows, kind):
    correct = sum('error' not in r and r.get('prediction') == r['target'] for r in rows)
    confusion = {}
    for row in rows:
        prediction = '__error__' if 'error' in row else row['prediction']
        counts = confusion.setdefault(row['target'], {})
        counts[prediction] = counts.get(prediction, 0) + 1
    labels = sorted(confusion)
    per_label = {label: dict(n=sum(confusion[label].values()), correct=confusion[label].get(label, 0)) for label in labels}
    return dict(attempted=len(rows), valid=sum('error' not in r for r in rows), correct=correct,
                accuracy=correct/len(rows), errors=sum('error' in r for r in rows),
                unknown_predictions=sum(r.get('prediction') == 'unknown' and 'error' not in r for r in rows),
                needs_review=sum(r.get('review_status') == 'needs_review' for r in rows) if kind == 'jev' else None,
                median_latency_seconds=statistics.median(r['latency_seconds'] for r in rows),
                usage=aggregate(rows), confusion=confusion, per_label=per_label,
                calibration=calibration_summary(rows) if kind == 'jev' else None)


def export_run(source, output):
    source, output = Path(source), Path(output)
    model_panel.summarize_run(source)  # Validate raw requests, predictions and completeness first.
    plan, samples = model_panel.load_run(source)
    by_id = {s['id']: s for s in samples}
    events = [json.loads(line) for line in (source/'events.jsonl').read_text().splitlines()]
    rows = []
    for event in events:
        sample = by_id[event['id']]
        row = {key: event[key] for key in ('id','model','started_at','prediction','probabilities','confidence',
                                         'review_status','error','latency_seconds') if key in event}
        row.update(task=sample['task'], target=sample['target'],
                   request_sha256=digest(json.dumps(event['request'], sort_keys=True, ensure_ascii=False).encode()))
        if 'response' in event:
            row['response_sha256'] = digest(json.dumps(event['response'], sort_keys=True, ensure_ascii=False).encode())
            row['response'] = {k:event['response'][k] for k in ('model','usage') if k in event['response']}
        rows.append(row)
    output.mkdir(parents=True, exist_ok=False)
    dump(output/'records.json', rows)
    dump(output/'index.json', dict(manifest=plan, sample_ids=[s['id'] for s in samples],
         records_sha256=digest((output/'records.json').read_bytes()),
         raw_events_sha256=digest((source/'events.jsonl').read_bytes()),
         note='Derived records omit all source questions, descriptions and raw response text. Hashes detect drift, not cryptographic authorship. Raw audit requires locally retained originals.'))
    return regenerate(output)


def regenerate(directory):
    directory = Path(directory)
    index = json.loads((directory/'index.json').read_text())
    raw = (directory/'records.json').read_bytes()
    if digest(raw) != index['records_sha256']:
        raise ValueError('Derived records changed')
    rows = json.loads(raw)
    models = index['manifest']['models']
    expected = {(i,m['id']) for i in index['sample_ids'] for m in models}
    if len(rows) != len(expected) or {(r['id'],r['model']) for r in rows} != expected:
        raise ValueError('Incomplete derived records')
    summary = {}
    table = ['| Model | Correct | Valid | Errors | Review flags | Median seconds | Reported USD |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for model in models:
        group = [r for r in rows if r['model'] == model['id']]
        result = metrics(group, model['kind'])
        result['by_task'] = {task:metrics([r for r in group if r['task']==task], model['kind']) for task in sorted({r['task'] for r in group})}
        result['resolved_models'] = sorted({r.get('response',{}).get('model','unreported') for r in group})
        summary[model['id']] = result
        cost = result['usage']['reported_cost_usd']
        cost_text = f'${cost:.6f}' if cost is not None else f"unknown ({result['usage']['cost_unknown_calls']} missing)"
        review = result['needs_review'] if result['needs_review'] is not None else '—'
        table.append(f"| `{model['id']}` | {result['correct']}/{len(group)} | {result['valid']}/{len(group)} | {result['errors']} | {review} | {result['median_latency_seconds']:.3f} | {cost_text} |")
    dump(directory/'summary.json',summary)
    (directory/'table.md').write_text('\n'.join(table)+'\n', encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--export',type=Path,help='Validated raw campaign; create a new source-free publication')
    args=parser.parse_args()
    export_run(args.export,args.output) if args.export else regenerate(args.output)
