#!/usr/bin/env python3
import sys,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs/validation.json').write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),status='PASS' if result.wasSuccessful() else 'FAIL'),indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
