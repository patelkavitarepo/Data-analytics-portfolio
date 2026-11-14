"""Opt-in local checkpoint commands; stdout is whitelisted audit metadata only."""
import argparse
from datetime import datetime, timezone
import json

from .audit import audit_dataset
from .parser import DataError, parse_archive
from .safeguards import PrivateStore


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('record-permission','suspend','acquire','audit'))
    parser.add_argument('--snapshot-id')
    parser.add_argument('--permission-active',action='store_true',help='Owner confirms scoped permission remains active; never overrides a suspension.')
    args=parser.parse_args();store=PrivateStore()
    try:
        if args.command=='record-permission':
            if not args.permission_active:raise DataError('CURRENT_PERMISSION_ATTESTATION_REQUIRED')
            store.record_owner_permission();print('Private owner-attested scope receipt recorded. No correspondence copied.')
        elif args.command=='suspend':store.suspend();print('Acquisition/read/audit suspended; owner retention/publication review required.')
        elif args.command=='acquire':
            from .acquire import acquire_private
            digest=acquire_private(store,permission_active=args.permission_active)
            print(json.dumps(dict(snapshot_id=digest,raw_snapshot='private; never commit or redistribute')))
        else:
            data,manifest=store.load_snapshot(args.snapshot_id or '',permission_active=args.permission_active)
            report=audit_dataset(parse_archive(data),manifest)
            store.gate(permission_active=args.permission_active)
            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ').lower()
            store.write_json('audit_'+stamp+'.json',report)
            print(json.dumps(report,sort_keys=True,indent=2,allow_nan=False))
        return 0
    except Exception:
        # Never stringify arbitrary underlying exceptions, raw rows, response bodies or paths.
        import sys
        error=sys.exc_info()[1]
        code=error.code if isinstance(error,DataError) else 'CHECKPOINT_INTERNAL_ERROR'
        print(json.dumps(dict(status='blocked',code=code,performance_cleared=False,raw_observations_in_output=False)))
        return 1


if __name__=='__main__':raise SystemExit(main())
