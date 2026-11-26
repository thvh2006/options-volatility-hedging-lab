#!/usr/bin/env python3
"""Verify the exact candidate archive without publishing it."""
import hashlib,json,subprocess
from pathlib import Path,PurePosixPath
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1]

def main():
    out=ROOT/'outputs';archive=out/'P5_Options_Research_Foundation_2026-11-26.zip'
    manifest=json.loads((out/'package_manifest.json').read_text());prefix='options-volatility-hedging-lab/'
    assert manifest['version']=='0.3.0' and manifest['observed_data_admitted'] is False
    with ZipFile(archive) as z:
        assert z.testzip() is None
        expected={prefix+x['path'] for x in manifest['files']}|{prefix+'outputs/package_manifest.json'}
        assert set(z.namelist())==expected
        for x in manifest['files']:
            path=PurePosixPath(x['path']);assert not path.is_absolute() and '..' not in path.parts
            data=z.read(prefix+x['path']);assert len(data)==x['size_bytes'] and hashlib.sha256(data).hexdigest()==x['sha256']
            assert hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()==x['sha256']
    browser=json.loads((out/'browser_checks.json').read_text())
    assert browser['tested_html_sha256']==hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest()
    report=json.loads((out/'report_checks.json').read_text())
    for name,digest in report['evidence_sha256'].items():assert hashlib.sha256((out/name).read_bytes()).hexdigest()==digest
    identities=subprocess.check_output(['git','log','--all','--format=%an <%ae> | %cn <%ce>'],cwd=ROOT,text=True).splitlines()
    expected_identity='thvh2006 <thvh2006@users.noreply.github.com>'
    assert all(line==expected_identity+' | '+expected_identity for line in identities)
    result=dict(status='PASS',version=manifest['version'],archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),archive_bytes=archive.stat().st_size,verified_files=len(manifest['files']),archive_crc='PASS',working_files_match_archive=True,report_evidence_hashes='PASS',browser_html_hash='PASS',existing_git_commit_identities='PASS',identity_scan=manifest['identity_scan'],publication='BLOCKED_PENDING_EXPLICIT_PUBLIC_VISIBILITY_CONFIRMATION',public_remote_created=False)
    (out/'release_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
