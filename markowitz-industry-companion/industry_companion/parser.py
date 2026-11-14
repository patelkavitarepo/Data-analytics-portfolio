"""Strict official-format parser. Returns only development-window private observations."""
import csv
from dataclasses import dataclass, field
from datetime import date
import hashlib
import io
import math
from pathlib import PurePosixPath
import re
import zipfile

START=date(2016,1,1)
END=date(2024,12,31)
INDUSTRIES=('NoDur','Durbl','Manuf','Enrgy','HiTec','Telcm','Shops','Hlth','Utils','Other')
PRIMARY='value_weighted'
PANELS=('value_weighted','equal_weighted')
MEMBER='10_industry_portfolios_daily.csv'
MAX_ARCHIVE=20*1024*1024
MAX_UNCOMPRESSED=64*1024*1024


class DataError(ValueError):
    """Public-safe stable code only; never offending values, rows or private headers."""
    def __init__(self,code):
        self.code=code
        super().__init__(code)


@dataclass(frozen=True,repr=False)
class Panel:
    weighting:str
    dates:tuple=field(repr=False)
    returns:tuple=field(repr=False)
    def __repr__(self):
        return f'PrivateDevelopmentPanel(weighting={self.weighting}, rows={len(self.dates)}, values=redacted)'


@dataclass(frozen=True,repr=False)
class Dataset:
    panels:dict=field(repr=False)
    archive_sha256:str
    member_sha256:str
    publisher_vintage:str | None
    excluded_outside_window:bool
    def __repr__(self):
        return 'PrivateIndustryDataset(development_window=2016..2024, values=redacted)'
    @property
    def primary(self):return self.panels[PRIMARY]


def archive_member(data):
    if not isinstance(data,bytes) or not data or len(data)>MAX_ARCHIVE:raise DataError('ARCHIVE_SIZE')
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members=archive.infolist()
            if len(members)!=1:raise DataError('ARCHIVE_MEMBER_COUNT')
            entry=members[0];path=PurePosixPath(entry.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in entry.filename or len(path.parts)!=1:raise DataError('UNSAFE_ARCHIVE_PATH')
            if entry.filename.casefold()!=MEMBER:raise DataError('WRONG_DAILY_ARCHIVE_MEMBER')
            if entry.flag_bits&1:raise DataError('ENCRYPTED_ARCHIVE')
            if entry.file_size>MAX_UNCOMPRESSED or entry.file_size/max(1,entry.compress_size)>100:raise DataError('ARCHIVE_EXPANSION_LIMIT')
            with archive.open(entry) as stream:content=stream.read(MAX_UNCOMPRESSED+1)
            if len(content)!=entry.file_size or len(content)>MAX_UNCOMPRESSED:raise DataError('ARCHIVE_EXPANSION_LIMIT')
            return content
    except DataError:raise
    except (zipfile.BadZipFile,RuntimeError,OSError,NotImplementedError,EOFError):raise DataError('INVALID_ZIP') from None


def parse_archive(data,*,units='percentage_points'):
    """No networking, implicit files, output or dates outside the fixed research window.

    Date tokens are inspected for filtering, but out-of-window RETURN tokens are
    never converted, validated, retained or exposed. Both daily panels required.
    """
    if units!='percentage_points':raise DataError('WRONG_UNITS_CONTRACT')
    content=archive_member(data)
    try:text=content.decode('utf-8-sig')
    except UnicodeDecodeError:raise DataError('UNSUPPORTED_ENCODING') from None
    data_by_panel={};active=None;header=False;excluded=False;vintage=None
    for line in text.splitlines():
        # Inspect only the date prefix before even tokenizing out-of-scope values.
        prefix=line.partition(',')[0].strip()
        if active and header and re.fullmatch(r'\d{8}',prefix):
            try:day=date(int(prefix[:4]),int(prefix[4:6]),int(prefix[6:]))
            except ValueError:raise DataError('INVALID_DATE') from None
            if not START<=day<=END:
                excluded=True
                continue
        normalized=' '.join(line.strip().split()).casefold()
        if not data_by_panel:
            found=re.search(r'using\s+(?:the\s+)?(\d{6})\s+crsp',normalized)
            if found:
                token=found.group(1)
                try:date(int(token[:4]),int(token[4:]),1)
                except ValueError:raise DataError('INVALID_VINTAGE') from None
                vintage=token
        if 'return' in normalized and re.search(r'\bdecimal(?:s)?\b',normalized):raise DataError('CONFLICTING_UNITS_HEADER')
        section=re.fullmatch(r'(?:average )?(value|equal)[ -]weighted returns\s*--\s*daily',normalized)
        if section:
            active='value_weighted' if section.group(1)=='value' else 'equal_weighted'
            if active in data_by_panel:raise DataError('DUPLICATE_RETURN_SECTION')
            data_by_panel[active]=dict(dates=[],returns=[],seen=set())
            header=False
            continue
        if re.search(r'(?:value|equal)[ -]weighted returns',normalized):raise DataError('WRONG_FREQUENCY_SECTION')
        if not normalized:
            if active and header:active=None
            continue
        if not active:continue
        try:cells=next(csv.reader([line],strict=True))
        except csv.Error:raise DataError('MALFORMED_CSV') from None
        if not header:
            columns=[c.strip() for c in cells]
            if len(columns)!=11 or columns[0] or tuple(c.casefold() for c in columns[1:])!=tuple(c.casefold() for c in INDUSTRIES):
                raise DataError('INDUSTRY_HEADER_MISMATCH')
            header=True
            continue
        token=cells[0].strip() if cells else ''
        if not re.fullmatch(r'\d{8}',token):
            if re.fullmatch(r'\d{4}|\d{6}',token):raise DataError('NON_DAILY_DATE')
            if re.match(r'(?:number of firms|average (?:firm )?size)',normalized):
                active=None;continue
            raise DataError('UNEXPECTED_RETURN_SECTION_CONTENT')
        try:observed=date(int(token[:4]),int(token[4:6]),int(token[6:]))
        except ValueError:raise DataError('INVALID_DATE') from None
        if not START<=observed<=END:
            excluded=True
            continue  # Deliberately do not examine/convert ANY return tokens.
        if len(cells)!=11:raise DataError('ROW_WIDTH')
        panel=data_by_panel[active]
        if observed in panel['seen']:raise DataError('DUPLICATE_DATE')
        if panel['dates'] and observed<panel['dates'][-1]:raise DataError('NONMONOTONE_DATE')
        converted=[]
        for cell in cells[1:]:
            if not cell.strip():raise DataError('MISSING_RETURN')
            try:value=float(cell)
            except (ValueError,OverflowError):raise DataError('INVALID_RETURN_TOKEN') from None
            if not math.isfinite(value):raise DataError('NONFINITE_RETURN')
            if value in (-99.99,-999.):raise DataError('MISSING_SENTINEL')
            if value < -100.:raise DataError('IMPOSSIBLE_SIMPLE_RETURN')
            converted.append(value/100.)
        panel['dates'].append(observed);panel['returns'].append(tuple(converted));panel['seen'].add(observed)
    if set(data_by_panel)!=set(PANELS):raise DataError('REQUIRED_DAILY_PANELS_MISSING')
    panels={}
    for name,values in data_by_panel.items():
        if not values['dates']:raise DataError('EMPTY_DEVELOPMENT_PANEL')
        panels[name]=Panel(name,tuple(values['dates']),tuple(values['returns']))
    return Dataset(panels,hashlib.sha256(data).hexdigest(),hashlib.sha256(content).hexdigest(),vintage,excluded)
