# P5 validation note — version 0.3.0

As of 26 November 2026. Author: thvh2006. Status: synthetic research foundation.

The option liability, hedge trades and cash financing reconcile numerically. The extension adds uncertainty around cost/frequency comparisons. Neither establishes a market-calibrated model or an investment track record.

## Implementation and evidence

| Component | Calculation | Evidence and limit |
| --- | --- | --- |
| Python core | BSM, Black76, European CRR, antithetic MC, bounded IV and analytic Greeks | 26 passing unit tests; standard library engine |
| Browser pricer | Separate JavaScript implementation | 108 Python prices; maximum absolute difference 0.00001568, tolerance 0.0001 USD/unit |
| Explorer application | Pricing inputs, reset, expiry, saved ledger and experiment tables | 9 minimal-DOM checks; real Chrome local and hosted desktop controls, tables and XLSX download checked |
| Excel | Independent BSM, Greeks, 60-row IV bisection, 16-step European tree, 257-row cash ledger | 21 pricing/Greek/tree and 3,084 ledger comparisons over call, put and nonzero dividend/borrowing-spread cases; tolerance 1e-7 |
| Exported XLSX | Formula caches read without authoring | 1,031 default-case comparisons; zero formula errors |
| Second calculation engine | LibreOffice recalculation of exported XLSX | 1,031 default-case comparisons; maximum difference below 8e-13; Microsoft Excel native not tested |
| Input perturbations | Fee 5 to 20 bps; negative spot, zero hedge vol, zero IV bracket | Higher cost reduces fixed-path terminal cash; three invalid inputs explicitly rejected |

These are numerical implementation checks, not a formal audit. Cross-engine recalculation covers the default case; the three-case sweep runs in the authoring calculation engine.

## Excel operating instructions

Open `outputs/P5_Options_Research_Model.xlsx`. Edit the blue cells on Inputs and inspect the input status. The workbook recalculates pricing, tree, and hedge formulas; Experiments contains explicitly labelled imported Python results.

Pricing maturity defaults to one year, pricing rate to 5%, pricing vol to 20%. The saved hedge path spans a quarter year, hedge rate defaults to 4%, hedge vol to 25%, dividend yield is fixed to zero for its ledger. The calculator's dividend yield affects pricing/tree only. Changing spot scales the saved path. Path Data is source material, not a path-generation control. Terminal target delta of zero is a liquidation instruction; expiry Greeks themselves are unavailable.

Each hedge row accrues interest on opening cash, receives the option premium or pays the terminal payoff, trades spot, deducts notional transaction costs, and carries the resulting cash. Negative cash accrues the base rate plus borrowing spread. Fractional spot trades and borrowing are unrestricted. Initial and final fees are included. No venue futures margin, collateral, funding, delivery-TWAP hedge or liquidation mechanics are represented.

The visible 16-step tree is deliberately small for auditability and has discretisation error. It must not be presented as the converged benchmark. The IV solver reports a bracket/iteration status; quotes at invalid bounds do not become observed volatility estimates.

## New synthetic evaluation block

`configs/holdout.json` was written before executing this extension. Seeds 304000–304255 are disjoint from baseline seeds 94000–94255. This is a new simulation block, not an external pre-registration or market out-of-sample validation. Each of four dynamics uses 256 paths, 256 steps and a quarter-year horizon. Four rebalance intervals and two fees produce 32 cells and 8,192 path/policy records. The same path is reused across each cost/frequency policy. Per-path hashes and errors are saved for independent review.

The comparison was fixed as RMSE(every 4 steps) minus RMSE(every step). Negative differences favour every 4 steps for this objective and configuration. Each interval uses 2,000 paired resamples of path indices, with a fixed bootstrap seed.

| Dynamics | Fee bps | RMSE difference USD | Pointwise 95% paired bootstrap interval |
| --- | ---: | ---: | --- |
| flat_25 | 5 | 0.0729 | [-0.0101, 0.1481] |
| flat_25 | 20 | -0.4525 | [-0.5439, -0.3674] |
| low_to_high | 5 | -0.0368 | [-0.2194, 0.1260] |
| low_to_high | 20 | -0.5124 | [-0.6995, -0.3399] |
| high_to_low | 5 | -0.0338 | [-0.1035, 0.0449] |
| high_to_low | 20 | -0.4175 | [-0.5008, -0.3303] |
| conditional_down_jump | 5 | -0.1439 | [-0.2625, -0.0276] |
| conditional_down_jump | 20 | -0.3822 | [-0.5056, -0.2611] |

At 20 bps the four intervals lie below zero. At 5 bps the constant/regime intervals include zero. This is conditional evidence about the specified model and cost assumptions. No policy was selected, intervals are pointwise without multiple-comparison adjustment, and parameter stability has not been established.

The conditional jump scenario imposes a 20% down jump at the midpoint of every stress path. It estimates neither jump frequency nor market tail probability. The sample lower-tail mean is descriptive and based on only about 13 paths per cell. Maximum cash reconciliation residual is below 3e-13 USD.

## Reproduction and remaining work

Run commands in README in order. `run_research.py` preserves the original baseline; `run_holdout.py` writes separate extension outputs. Rebuilding Excel requires artifact-tool; read-only workbook verification uses openpyxl. Core pricing and simulation have no third-party dependencies. Notebook cells run through an ordinary-Python sequential harness; a Jupyter-kernel execution is not claimed.

Observed quote rights/QC/calibration, exchange-specific hedge accounting, a locked advanced challenger, mobile and cross-browser visual QA and the observed-market report remain open. The package contains no admitted venue quotes. Public attribution is thvh2006 or blank; personal home paths and names are excluded from packaged files and Office XML.

The synthetic module now has a nine-page technical report, rendered and inspected page by page. Public distribution was explicitly approved and the repository is available at https://github.com/thvh2006/options-volatility-hedging-lab. The first downloaded public archive matched all 53 reviewed file hashes; public commit author names use thvh2006.

The English dashboard is hosted at https://thvh2006.github.io/options-volatility-hedging-lab/ . Desktop Chrome pricing, boundary states, fee selection, terminal ledger and workbook download were checked on 27 November 2026. The research design is available in English; its earlier filename retains an English compatibility link.
