"""Private ignored immutable storage and revocation gate. No data/network on import."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

from .parser import DataError

PROJECT=Path(__file__).resolve().parents[1]
SOURCE_URL='https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/10_Industry_Portfolios_daily_CSV.zip'
SCOPE='French daily 10 Industry Portfolios only'


def utc(value):
    try:
        parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
        if parsed.utcoffset() is None or parsed.utcoffset().total_seconds()!=0:raise ValueError
        return parsed
    except (ValueError,TypeError,AttributeError):raise DataError('UTC_TIMESTAMP_REQUIRED') from None


def _git(project,args):
    try:return subprocess.run(['git','-C',str(project),*args],capture_output=True,check=False).returncode
    except OSError:raise DataError('GIT_SAFEGUARD_UNAVAILABLE') from None


class PrivateStore:
    def __init__(self,project=PROJECT):
        self.project=Path(project).absolute()
        self.root=self.project/'private'
    def path(self,name,*,create=False):
        if not isinstance(name,str) or not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{0,160}',name):raise DataError('PRIVATE_NAME_REQUIRED')
        if any(part.is_symlink() for part in (self.project,*self.project.parents,self.root)):raise DataError('PRIVATE_SYMLINK')
        if create and not self.root.exists():
            try:self.root.mkdir(mode=0o700)
            except OSError:raise DataError('PRIVATE_DIRECTORY_CREATE_FAILED') from None
        if not self.root.is_dir():raise DataError('PRIVATE_DIRECTORY_REQUIRED')
        if stat.S_IMODE(self.root.stat().st_mode)&0o077:raise DataError('PRIVATE_DIRECTORY_PERMISSIONS')
        path=self.root/name
        if path.is_symlink() or not path.resolve().is_relative_to(self.root.resolve()):raise DataError('PRIVATE_SYMLINK')
        if _git(self.project,['check-ignore','-q','--',str(path)])!=0:raise DataError('PRIVATE_PATH_NOT_IGNORED')
        if _git(self.project,['ls-files','--error-unmatch','--',str(path)])==0:raise DataError('PRIVATE_FILE_TRACKED')
        return path
    def write(self,name,data):
        path=self.path(name,create=True)
        try:
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'wb') as stream:stream.write(data)
        except FileExistsError:raise DataError('IMMUTABLE_FILE_EXISTS') from None
        except OSError:raise DataError('PRIVATE_WRITE_FAILED') from None
        return path
    def read(self,name):
        path=self.path(name)
        try:
            if not stat.S_ISREG(path.stat(follow_symlinks=False).st_mode):raise DataError('PRIVATE_REGULAR_FILE_REQUIRED')
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            with os.fdopen(fd,'rb') as stream:
                info=os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode):raise DataError('PRIVATE_REGULAR_FILE_REQUIRED')
                if stat.S_IMODE(info.st_mode)&0o077:raise DataError('PRIVATE_FILE_PERMISSIONS')
                return stream.read(21*1024*1024)
        except OSError:raise DataError('PRIVATE_READ_FAILED') from None
    def write_json(self,name,value):
        return self.write(name,(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
    def read_json(self,name):
        try:value=json.loads(self.read(name))
        except (ValueError,UnicodeDecodeError):raise DataError('INVALID_PRIVATE_METADATA') from None
        if not isinstance(value,dict):raise DataError('INVALID_PRIVATE_METADATA')
        return value
    def gate(self,*,permission_active=False):
        # This explicit attestation is not a new permission grant or an email check.
        if permission_active is not True:raise DataError('CURRENT_PERMISSION_ATTESTATION_REQUIRED')
        for marker in ('revoked.json','permission-unknown.json'):
            if (self.root/marker).exists() or (self.root/marker).is_symlink():raise DataError('PERMISSION_SUSPENDED')
        receipt=self.read_json('permission-receipt.json')
        if receipt.get('status')!='active' or receipt.get('scope')!=SCOPE:raise DataError('PERMISSION_NOT_ACTIVE_FOR_SCOPE')
        required=('limited_automation','private_retention','educational_analysis','aggregate_publication')
        if any(receipt.get(k) is not True for k in required) or receipt.get('raw_redistribution') is not False or receipt.get('rescission_possible') is not True:
            raise DataError('PERMISSION_SCOPE_INCOMPLETE')
        utc(receipt.get('recorded_at_utc'));return receipt
    def record_owner_permission(self):
        return self.write_json('permission-receipt.json',dict(status='active',scope=SCOPE,
            received_date='2026-11-13',recorded_at_utc=datetime.now(timezone.utc).isoformat(),
            evidence_type='Owner-attested direct permission, documented in issue #11 and task instruction; original correspondence not copied',
            evidence_reference='https://github.com/patelkavitarepo/Data-analytics-portfolio/issues/11',
            limited_automation=True,private_retention=True,educational_analysis=True,aggregate_publication=True,
            raw_redistribution=False,rescission_possible=True))
    def suspend(self):
        return self.write_json('revoked.json',dict(status='suspended',recorded_at_utc=datetime.now(timezone.utc).isoformat(),
            action='Stop acquisition/read/audit/publication; quarantine retained snapshots pending owner review; do not automatically delete.'))
    def snapshot(self,data,*,retrieved_at_utc,permission_active=False):
        self.gate(permission_active=permission_active);utc(retrieved_at_utc)
        digest=hashlib.sha256(data).hexdigest();name='snapshot_'+digest+'.zip'
        self.write(name,data)
        self.write_json('manifest_'+digest+'.json',dict(source_url=SOURCE_URL,archive_sha256=digest,
            retrieved_at_utc=retrieved_at_utc,raw_redistribution=False,development_start='2016-01-01',development_end='2024-12-31',
            historical_release_availability_verified=False,performance_cleared=False))
        return digest
    def load_snapshot(self,digest,*,permission_active=False):
        self.gate(permission_active=permission_active)
        if not re.fullmatch(r'[0-9a-f]{64}',digest):raise DataError('SNAPSHOT_ID_REQUIRED')
        manifest=self.read_json('manifest_'+digest+'.json')
        if manifest.get('source_url')!=SOURCE_URL or manifest.get('archive_sha256')!=digest:raise DataError('SNAPSHOT_PROVENANCE_MISMATCH')
        utc(manifest.get('retrieved_at_utc'))
        data=self.read('snapshot_'+digest+'.zip')
        if hashlib.sha256(data).hexdigest()!=digest:raise DataError('SNAPSHOT_FINGERPRINT_MISMATCH')
        return data,manifest
