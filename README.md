# Options Volatility and Hedging Lab

P5 research foundation: pricing accuracy, cash accounting and the cost of discrete delta hedging. **Version 0.3.0 is synthetic research, not a completed market study or professional release.**

The question is why accurate initial pricing can coexist with poor hedge outcomes under discrete trading, costs, volatility mismatch and jumps.

## Start here

- `docs/P5_Research_Design_VI.md`: detailed research choices, hypotheses, data constraints and milestones.
- `index.html`: standalone explorer. Open it in a browser. Pricing is independently calculated in JavaScript. Cost/frequency tables and ledger replay are labelled saved synthetic experiments.
- `notebooks/01_foundation_walkthrough.ipynb`: seven executed ordinary-Python cells. Jupyter kernel not verified.
- `outputs/P5_Options_Research_Model.xlsx`: independent formula-based 9-sheet workbook. Edit blue Inputs cells; Pricing and Hedge Ledger have separate maturities/rates.
- `outputs/research_results.json`: 36 baseline paired scenario cells and numerical evidence.
- `outputs/holdout_results.json`: 32 extension cells, 8 paired comparisons and pointwise bootstrap uncertainty.
- `outputs/P5_Technical_Report.pdf`: nine-page account of assumptions, numerical evidence, costs, regimes and limits.
- `outputs/browser_checks.json`: real Chrome desktop control, layout and download checks.
- `docs/VALIDATION_NOTE.md`: scope, cross-engine checks and interpretation.
- `outputs/representative_hedge_ledger.csv`: explicit premium, hedge trades, cash financing, costs and terminal settlement.

## Current scope

Implemented: BSM, Black76 benchmark, European CRR tree, antithetic Monte Carlo, bounded IV inversion, analytic BSM Greeks, finite-difference challenges, synthetic spot hedge ledger, quote-QC schema and seeded cost/frequency experiments.

The reference cash-settled European contract has one unit of a synthetic USD underlying. Spot hedging requires zero dividend yield and allows fractional positions financed through cash borrowing. It does not emulate exchange futures margin, collateral, liquidation or delivery mechanics.

The first market candidate is BTC_USDC linear European options. Observed data has not been admitted. Venue publication rights, contract metadata and the correct hedge/settlement adapter remain separate work. SPX is an alternative when appropriate quote history and contract conventions are available.

## Reproduce

Core engines use Python3.10+ and the standard library. Browser build/tests require Node:

```bash
python scripts/check.py
python scripts/run_research.py
python scripts/run_holdout.py
python scripts/build_walkthrough.py
node scripts/build_explorer.mjs
python scripts/prepare_workbook_data.py
node scripts/build_workbook.mjs
python scripts/verify_workbook.py
python scripts/build_report.py
python scripts/package.py
python scripts/verify_release.py
```

The suite has 26 unit tests. Excel authoring requires `@oai/artifact-tool`; read-only exported-file verification requires `openpyxl`. These build dependencies are separate from the standard-library pricing engine. The browser pricer is compared with 108 Python prices with an absolute tolerance of 0.0001 USD per unit. Nine minimal-DOM application checks run during the build. Separate real Chrome checks cover the local desktop controls, table layout and XLSX download; mobile and deployed-host behaviour remain unverified. Report generation uses ReportLab and pypdf, and consumes the saved browser evidence. Rebuilding the report does not itself repeat browser QA.

## Next milestones

Rights-cleared observed quote QC/calibration; exchange-specific hedge accounting; locked model comparison; mobile/deployed-host QA. These are open work, not hidden behind a completion badge.

Public author identity: `thvh2006` or blank. No raw venue market data, private credentials or personal home paths belong in the repository.

## Publication status

Public source repository: [https://github.com/thvh2006/options-volatility-hedging-lab](https://github.com/thvh2006/options-volatility-hedging-lab). Owner approved public distribution on 26 November 2026. The initial GitHub archive was downloaded and all 53 published files matched their reviewed local hashes. Public commit author names were checked and use `thvh2006`. The downloadable source ZIP includes methods, synthetic outputs, Excel and the PDF report. `docs/PUBLICATION_REVIEW.md` records the release scope. This is a public synthetic research module; market-data and venue-accounting milestones remain open.
