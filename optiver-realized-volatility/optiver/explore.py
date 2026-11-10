"""Prepare private, target-free discovery summaries from authorized official files.

Requires an explicit lead-approved discovery-window manifest. Does not train models,
read labels, access the network, or select stock relationships.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import plotly.express as px
from optiver.features import BOOK, TRADE, features_for_stock


PROFILE_COLUMNS = ['mid_rv', 'wap_rv', 'spread_time_mean', 'depth_time_mean',
                   'abs_imbalance_mean', 'book_updates', 'trade_volume', 'order_count']


def read_manifest(path):
    manifest = json.loads(Path(path).read_text())
    if manifest.get('approval') != 'lead-approved' or not manifest.get('decision_id'):
        raise ValueError('A lead-approved discovery manifest and research decision ID are required')
    values = manifest.get('time_ids', [])
    if not values or any(type(x) is not int or x < 0 for x in values) or len(set(values)) != len(values):
        raise ValueError('Discovery time_ids must be unique nonnegative integers')
    return manifest


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as file:
        for block in iter(lambda: file.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read_partition(path, columns, ids):
    path = Path(path)
    if not path.is_dir():
        raise FileNotFoundError(f'Missing official stock partition: {path}')
    files = sorted(path.rglob('*.parquet'))
    if not files:
        raise FileNotFoundError(f'No Parquet files in {path}')
    # Filter before computing features. Only requested discovery windows leave the reader.
    frames = [pq.read_table(file, columns=columns,
                            filters=[('time_id', 'in', ids)]).to_pandas() for file in files]
    return pd.concat(frames, ignore_index=True), files


def stock_profiles(features):
    return features.groupby('stock_id')[PROFILE_COLUMNS].agg(['count', 'median',
                                                             lambda x: x.quantile(.25),
                                                             lambda x: x.quantile(.75)])


def conditional_similarity(features, context_ids, min_pairs):
    """Descriptive correlation of observed log RV, not evidence of forecast skill.

    Context membership is supplied explicitly; this function never reads targets,
    estimates regimes, or selects best pairs. All stocks must belong to discovery.
    """
    if min_pairs < 3:
        raise ValueError('At least three pairs are needed; larger support must be chosen for research')
    if features.duplicated(['stock_id', 'time_id']).any():
        raise ValueError('Duplicate stock/window features')
    subset = features[features.time_id.isin(context_ids)]
    pivot = subset.pivot(index='time_id', columns='stock_id', values='mid_rv')
    log_rv = np.log(pivot.where(pivot > 0))
    present = log_rv.notna().astype(int)
    counts = present.T.dot(present)
    return log_rv.corr(min_periods=min_pairs), counts


def run(data_root, manifest_path, output):
    root, output = Path(data_root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('Use a new output directory to preserve previous runs')
    manifest = read_manifest(manifest_path)
    if not (root / 'train.csv').is_file():
        raise FileNotFoundError('Expected official train.csv beside book_train.parquet and trade_train.parquet')
    # The label file is checked for presence only; targets are never read during feature EDA.
    partitions = sorted((root / 'book_train.parquet').glob('stock_id=*'))
    if not partitions:
        raise FileNotFoundError('Official book_train.parquet/stock_id=* partitions are unavailable')
    records, sources = [], []
    for partition in partitions:
        stock_id = int(partition.name.split('=')[1])
        book, book_files = read_partition(partition, BOOK, manifest['time_ids'])
        if book.empty:
            continue
        trades, trade_files = read_partition(root / 'trade_train.parquet' / partition.name,
                                             TRADE, manifest['time_ids'])
        records.append(features_for_stock(book, trades, stock_id))
        sources.extend(book_files + trade_files)
    if not records:
        raise ValueError('No observations matched approved discovery time_ids')
    features = pd.concat(records, ignore_index=True)
    assert set(features.time_id) <= set(manifest['time_ids'])
    audit = {'status': 'target-free-feature-exploration',
             'decision_id': manifest['decision_id'], 'discovery_manifest_sha256': file_hash(manifest_path),
             'python': platform.python_version(), 'pandas': pd.__version__, 'numpy': np.__version__,
             'stock_window_rows': len(features), 'stocks': int(features.stock_id.nunique()),
             'observed_discovery_windows': int(features.time_id.nunique()),
             'unmatched_requested_time_ids': sorted(set(manifest['time_ids']) - set(features.time_id)),
             'labels_read': False, 'models_trained': False,
             'source_authenticity': 'Operator-supplied files; official provenance must be verified separately',
             'files': [{'path': str(path.relative_to(root)), 'sha256': file_hash(path)} for path in sources]}
    output.mkdir(parents=True)
    features.to_parquet(output / 'features.parquet', index=False)
    profile = stock_profiles(features)
    profile.columns = ['_'.join(map(str, col)).replace('<lambda_0>', 'q25').replace('<lambda_1>', 'q75') for col in profile.columns]
    profile.to_csv(output / 'stock_profiles.csv')
    (output / 'audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    px.box(features, x=features.stock_id.astype(str), y='mid_rv', log_y=True,
           title='Observed within-window RV by anonymous stock · discovery only').write_html(output / 'stock_volatility.html', include_plotlyjs=True)
    px.scatter(features, x='spread_time_mean', y='mid_rv', color=features.stock_id.astype(str),
               log_x=True, log_y=True, title='Spread and contemporaneous RV · association, not forecast evidence').write_html(output / 'spread_vs_observed_volatility.html', include_plotlyjs=True)
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--discovery-manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.data_root, args.discovery_manifest, args.output), indent=2))


if __name__ == '__main__':
    main()
