"""Lightweight, stdlib-only checks of saved audit evidence; no model execution."""
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, pstdev

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'redteam'


def read(path):
    return json.loads(path.read_text())


def rows(case, method='audit'):
    path = HERE / ('initial_scores_test.json' if case == 'original_reference'
                   else f'{case}/scores_test.json')
    if case == 'original_reference':
        method = 'us_sres'
    return {e: v['results'].get(method, {}) for e, v in read(path)['experiments'].items()}


def tree(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.rglob('*') if p.is_file()}


def main():
    reference = rows('original_reference')
    schema = read(HERE / 'initial_reference.json')['experiments']
    summary = read(HERE / 'summary.json')
    pool = {name: rows(name) for name in summary['pool']}
    for name, result in summary['attempts'].items():
        delta = 0
        for e, spec in schema.items():
            for metric, meta in spec['metrics'].items():
                scale = pstdev(v[e][metric] for v in pool.values())
                assert math.isclose(scale, summary['scales'][e][metric], rel_tol=1e-12, abs_tol=1e-12)
                if scale:
                    direction = 1 if meta['higher_is_better'] else -1
                    delta += spec['weight'] * abs(meta['coefficient']) * direction * (
                        pool[name][e][metric] - reference[e][metric]) / scale
        assert math.isclose(delta, result['audit_normalized_rank_delta'], rel_tol=1e-10, abs_tol=1e-12)

    seed_rows = [rows(f'reference_seed_{s}') for s in (16948, 16949, 16950)]
    spreads = {e: {m: max(r[e][m] for r in seed_rows) - min(r[e][m] for r in seed_rows)
                   for m in spec['metrics']} for e, spec in schema.items()}
    assert all(v == 0 for metrics in spreads.values() for v in metrics.values())

    comparisons = {}
    config_metrics = {'dynamic_range_x', 'quant_bits', 'amplitude_ratio', 'mean_fold_count'}
    for name in ('better_sensor_fit', 'weaker_no_unwrap', 'shortcut_labels',
                 'shortcut_seed_replay', 'shortcut_baseline_inflation',
                 'shortcut_relabel', 'shortcut_config'):
        counts = {'better': 0, 'same': 0, 'worse': 0}
        quality = {'better': 0, 'same': 0, 'worse': 0}
        for e, spec in schema.items():
            for metric, meta in spec['metrics'].items():
                direction = 1 if meta['higher_is_better'] else -1
                difference = direction * (pool[name][e][metric] - reference[e][metric])
                key = 'better' if difference > 0 else 'worse' if difference < 0 else 'same'
                counts[key] += 1
                if metric not in config_metrics:
                    quality[key] += 1
        comparisons[name] = {'all_metrics': counts, 'quality_metrics': quality}
    assert comparisons['better_sensor_fit']['quality_metrics']['better'] == 40
    assert comparisons['weaker_no_unwrap']['quality_metrics']['worse'] == 40

    outcomes = {p.parent.name: read(p) for p in HERE.glob('*/outcome.json')}
    assert len(outcomes) == 20
    assert all(o.get('test_exit') == (1 if n in {'shortcut_empty', 'shortcut_missing'} else 0)
               for n, o in outcomes.items())
    nan_rows = rows('shortcut_nan')
    nan_count = sum(not math.isfinite(v) for r in nan_rows.values() for v in r.values())
    assert nan_count == 40
    omitted = rows('shortcut_omission')
    assert len(omitted) == 5 and all(not r for r in omitted.values())
    assert len(outcomes['shortcut_omission']['artifacts_on_disk']) == 5
    for name in ('shortcut_empty', 'shortcut_missing'):
        assert not outcomes[name]['score_file_written']

    baseline = {e: v['results']['conventional_clip_sres']
                for e, v in read(HERE / 'initial_scores_test.json')['experiments'].items()}
    def rank_deltas(attempts):
        scales = {e: {m: pstdev(a[e][m] for a in attempts.values())
                      for m in spec['metrics']} for e, spec in schema.items()}
        result = {}
        for name, attempt in attempts.items():
            result[name] = sum(
                spec['weight'] * abs(meta['coefficient']) *
                (1 if meta['higher_is_better'] else -1) *
                (attempt[e][m] - reference[e][m]) / scales[e][m]
                for e, spec in schema.items() for m, meta in spec['metrics'].items()
                if scales[e][m])
        return {'pool': list(attempts), 'rank_deltas': result}

    sensitivity = {
        'quality_only': rank_deltas({'original_reference': reference,
                                    'conventional_baseline': baseline,
                                    'better_sensor_fit': pool['better_sensor_fit'],
                                    'weaker_no_unwrap': pool['weaker_no_unwrap']}),
        'without_impossible_or_config': rank_deltas(
            {**{n: r for n, r in pool.items()
                if n not in {'shortcut_impossible', 'shortcut_config'}},
             'conventional_baseline': baseline}),
        'audit_plus_baseline': rank_deltas({**pool, 'conventional_baseline': baseline}),
    }
    (HERE / 'normalization_sensitivity.json').write_text(
        json.dumps(sensitivity, indent=2) + '\n')
    restoration = {}
    state = HERE / '_state'
    if state.exists():
        for sub in ('checkpoints', 'data/synthetic', 'scoring'):
            restoration[sub] = tree(ROOT / sub) == tree(state / sub)
            assert restoration[sub], sub
        hashes = read(state / 'protected_hashes.json')
        protected = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
                     for p, h in hashes.items() if p != 'scripts/run.sh'}
        assert all(protected.values())
        restoration['eval_and_other_scripts'] = all(protected.values())
    restoration['scripts/run.sh'] = (ROOT / 'scripts/run.sh').read_bytes() == (HERE / 'original_run.sh').read_bytes()
    assert restoration['scripts/run.sh']
    result = {'checked_attempts': len(outcomes), 'checked_rank_deltas': len(pool),
              'per_experiment_seed_spread': spreads, 'direction_comparisons': comparisons,
              'nan_quality_metric_values': nan_count, 'omitted_methods': len(omitted),
              'baseline_mean_signal_mse': mean(r['signal_mse'] for r in baseline.values()),
              'baseline_mean_time_mae_samples': mean(r['time_mae_samples'] for r in baseline.values()),
              'restoration': restoration}
    (HERE / 'verification.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
