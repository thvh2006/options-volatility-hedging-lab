#!/usr/bin/env python3
"""Create a reproducible source/evidence package without personal paths or VCS."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,re,unicodedata
ROOT=Path(__file__).resolve().parents[1]
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())

def main():
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(x in p.parts for x in ['.git','__pycache__','node_modules','private_snapshots','qa']) and p.suffix not in ['.zip','.pyc'] and not p.name.endswith('.inspect.ndjson') and p.name not in ['package_manifest.json','release_checks.json'])
    home_id=norm(Path.home().name);rows=[]
    for p in files:
        raw=p.read_bytes();text=raw.decode('utf8','ignore')
        if str(Path.home()) in text or (len(home_id)>12 and home_id in norm(text)):raise ValueError('Identity policy failed: '+str(p.relative_to(ROOT)))
        if p.suffix=='.pdf':
            from pypdf import PdfReader
            reader=PdfReader(p);visible='\n'.join(page.extract_text() for page in reader.pages)+str(reader.metadata)
            if str(Path.home()) in visible or (len(home_id)>12 and home_id in norm(visible)):raise ValueError('PDF identity policy failed: '+str(p.relative_to(ROOT)))
        if p.suffix=='.xlsx':
            with ZipFile(p) as office:
                for name in office.namelist():
                    embedded=office.read(name).decode('utf8','ignore')
                    if str(Path.home()) in embedded or (len(home_id)>12 and home_id in norm(embedded)):raise ValueError('Office identity policy failed: '+str(p.relative_to(ROOT)))
        rows.append(dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw)))
    manifest=ROOT/'outputs/package_manifest.json'
    manifest.write_text(json.dumps(dict(version='0.3.0',status='SYNTHETIC_FOUNDATION',identity_scan='PASS_CURRENT_FILES_OFFICE_XML_AND_PDF_TEXT_METADATA',observed_data_admitted=False,files=rows),indent=2)+'\n')
    out=ROOT/'outputs/P5_Options_Research_Foundation_2026-11-26.zip'
    with ZipFile(out,'w',ZIP_DEFLATED) as z:
        for p in files+[manifest]:z.write(p,'options-volatility-hedging-lab/'+str(p.relative_to(ROOT)))
    print(json.dumps(dict(files=len(files),zip_bytes=out.stat().st_size,identity_scan='PASS',status='SYNTHETIC_FOUNDATION')))

if __name__=='__main__':main()
