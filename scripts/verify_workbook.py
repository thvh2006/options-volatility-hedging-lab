#!/usr/bin/env python3
"""Read-only verification of exported/cross-engine-recalculated XLSX caches."""
import json,math,sys
from pathlib import Path
import openpyxl
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'outputs/P5_Options_Research_Model.xlsx'
    w=openpyxl.load_workbook(p,data_only=True);formulas=openpyxl.load_workbook(p,data_only=False)
    g=json.loads((ROOT/'outputs/workbook_golden.json').read_text())['cases'][0]
    errors=[(s.title,c.coordinate,c.value) for s in w for row in s for c in row if c.data_type=='e'];assert not errors,errors
    diffs=[]
    for sheet,cell,expected in [('Pricing','D14',g['price']),('Tree','D4',g['tree']),('Pricing','D26',g['vol'])]:
        value=w[sheet][cell].value;assert isinstance(value,(int,float)) and math.isfinite(value)
        diffs.append(abs(value-expected));assert diffs[-1]<1e-7,(sheet,cell,value,expected)
        assert formulas[sheet][cell].data_type=='f'
    for i,row in enumerate(g['hedge']['ledger']):
        for col,key in [('O','closing_cash'),('P','holding'),('N','costs'),('R','net_wealth')]:
            cell=f'{col}{i+7}';value=w['Hedge Ledger'][cell].value
            assert isinstance(value,(int,float)) and math.isfinite(value)
            diffs.append(abs(value-row[key]));assert diffs[-1]<1e-7,(cell,value,row[key])
            assert formulas['Hedge Ledger'][cell].data_type=='f'
    for row in range(7,12):assert abs(w['Checks'][f'D{row}'].value)<=w['Checks'][f'E{row}'].value
    result=dict(status='PASS',comparisons=len(diffs),maximum_absolute_difference=max(diffs),formula_errors=0,reader='openpyxl read-only validation',case='default call with saved path and 5bps fee',native_microsoft_excel_tested=False)
    print(json.dumps(result,indent=2))
    (ROOT/'outputs'/('excel_cross_engine_checks.json' if len(sys.argv)>1 else 'excel_export_checks.json')).write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
