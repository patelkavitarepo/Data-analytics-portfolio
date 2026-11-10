"""Publish a lossless, self-contained discovery-results bundle; no training."""
import argparse
import json
import shutil
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from daily_study.declines import write_json
from daily_study.quality import sha256
from daily_study.forecast_snapshot import load_snapshot


def compact_parquet(frame,path):
    table=pa.Table.from_pandas(frame,preserve_index=True if isinstance(frame.index,pd.DatetimeIndex) else False)
    floats=[field.name for field in table.schema if pa.types.is_floating(field.type)]
    strings=[field.name for field in table.schema if pa.types.is_string(field.type)]
    pq.write_table(table,path,compression='zstd',compression_level=9,
                   use_dictionary=strings,use_byte_stream_split=floats)
    pd.testing.assert_frame_equal(pd.read_parquet(path),frame,check_index_type=False)


def build(run,output):
    run,output=Path(run),Path(output)
    if output.exists():raise ValueError('Fresh snapshot bundle directory required')
    hashes=json.loads((run/'output_hashes.json').read_text())
    for name,digest in hashes.items():
        if Path(name).name!=name or sha256(run/name)!=digest:
            raise ValueError(f'Forecast artifact integrity mismatch: {name}')
    manifest=json.loads((run/'manifest.json').read_text())
    if manifest['protected_period_observations_loaded'] is not False:
        raise ValueError('Protected-period isolation required')
    output.mkdir(parents=True)
    for name in ['manifest.json','selected_settings.json','scores.json','coverage.json','subgroups.json',
                 'cohort.json','uncertainty.json','failure_cases.json','failure_paths.json','metric_integrity.json',
                 'loss_concentration.json','stock_balanced.json','nonoverlap.json','tuning_scores.json',
                 'model-comparison.png','small-targets.png','quarters.png']:
        shutil.copyfile(run/name,output/name)
    compact_parquet(pd.read_parquet(run/'predictions.parquet'),output/'predictions.parquet')
    fits=pd.read_parquet(run/'fits.parquet')
    compact_parquet(fits[fits.stage=='evaluation'].reset_index(drop=True),output/'evaluation_fits.parquet')
    compact_parquet(pd.read_parquet(run/'stock_scores.parquet'),output/'stock_scores.parquet')
    for policy in ['narrow','conservative']:
        returns=pd.read_parquet(run/f'{policy}_discovery_returns.parquet')
        returns=returns.loc[(returns.index>='2015-01-01')&(returns.index<='2015-12-31')]
        compact_parquet(returns,output/f'{policy}_evaluation_returns.parquet')
    write_json(output/'bundle_hashes.json',{p.name:sha256(p) for p in sorted(output.iterdir()) if p.is_file()})
    snapshot=load_snapshot(output)
    return dict(files=len(list(output.iterdir())),bytes=sum(p.stat().st_size for p in output.iterdir()),
                prediction_rows=len(snapshot['predictions']),scope='2015 only, actual trained forecasts, lossless exports, no runtime fitting')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(build(args.run,args.output),indent=2))
