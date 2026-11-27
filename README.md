# Options Volatility and Hedging Lab

**European option pricing, independent Excel verification, and the cost of discrete delta hedging.**

This project asks a practical model-risk question: **why can an option be priced accurately at inception while its hedge still performs poorly?** It connects analytical prices and Greeks to an explicit cash ledger, then tests how rebalance frequency, transaction costs, volatility mismatch and jumps change the terminal hedge error.

**Version 0.3.0 · Synthetic research · Python + JavaScript + Excel**

[Live dashboard](https://thvh2006.github.io/options-volatility-hedging-lab/) · [Technical report](outputs/P5_Technical_Report.pdf) · [Download Excel](outputs/P5_Options_Research_Model.xlsx?raw=true) · [Notebook](notebooks/01_foundation_walkthrough.ipynb) · [Download source package](outputs/P5_Options_Research_Foundation_2026-11-26.zip?raw=true)

> All prices, paths and cost experiments in this release are synthetic. The results describe numerical implementation and hedge error under stated assumptions. They are not an observed-market backtest or an investment track record.

## Why this project

A pricing calculator checks only part of a derivatives workflow. Replication also requires trading the hedge, financing its cash balance, paying costs and settling the liability. More frequent rebalancing can reduce discretisation error while increasing transaction costs. A volatility assumption that works for an initial price can also be inappropriate for the subsequent path.

The lab makes each part inspectable: contract conventions, numerical pricing, hedge trades, cash financing, terminal settlement and uncertainty around policy comparisons. Python provides the research engine; a separate JavaScript implementation and a formula-based Excel workbook challenge selected calculations independently.

## What is implemented

| Component | Implementation | Where to inspect |
| --- | --- | --- |
| Analytical pricing | Black–Scholes–Merton with continuous dividend yield; Black76 with explicit forward and discount factor | [Pricing engine](src/options_lab/pricing.py) |
| Numerical pricing | European CRR tree and antithetic Monte Carlo with pair-based standard errors | [Numerical evidence](outputs/research_results.json) |
| IV and Greeks | Bounded IV inversion with solver statuses; analytic BSM Greeks and finite-difference challenges | [Model tests](tests/test_models.py) |
| Delta-hedge accounting | Short option premium, fractional spot trades, financing, fees, spread, borrowing spread, liquidation and payoff | [Hedge engine](src/options_lab/hedging.py), [saved ledger](outputs/representative_hedge_ledger.csv) |
| Cost and model-risk experiments | Paired frequency/cost sweeps, volatility mismatch, regime changes and a conditional jump stress | [Baseline](outputs/hedge_cost_frontier.csv), [extension](outputs/holdout_results.json) |
| Quote-quality foundation | Convention, timestamp, bid/ask, size, alignment, spread and model-bound checks on canonical fixtures | [Quote QC](src/options_lab/quotes.py) |
| Interactive explorer | Independent browser price calculator, saved cost tables, paired intervals and ledger replay | [Run locally](#run-the-explorer) |
| Independent workbook | Excel formulas for BSM, Greeks, IV, a small CRR tree and a full saved-path hedge ledger | [Workbook](outputs/P5_Options_Research_Model.xlsx?raw=true) |

## Main findings

The evidence below is conditional on the configured synthetic processes and cost assumptions. Dollar figures are per one option unit.

| Question | Saved result | Interpretation |
| --- | --- | --- |
| Does the numerical benchmark agree with analytical pricing? | BSM call **10.450584**; Monte Carlo **10.471575**, with 95% interval **[10.369939, 10.573210]** | The analytical reference lies inside this run's Monte Carlo interval. Numerical agreement does not establish market fit. |
| Does more frequent costless hedging reduce error dispersion? | At matched 25% volatility and zero fees, error SD is **0.2409** for every-step hedging versus **1.9671** for every 64 steps | More frequent hedging reduces sample discretisation dispersion in this matched-model experiment. |
| Can costs reverse a frequency ranking? | At 20 bps, baseline RMSE is **1.2498** for every step versus **0.8658** for every 4 steps | A smaller costless replication error does not necessarily imply a smaller error after costs. |
| Does the comparison survive a new seed block? | At 20 bps, all four specified dynamics have negative pointwise 95% intervals for RMSE(every 4) minus RMSE(every 1) | Evidence favours every 4 steps for this comparison and configuration; no universal policy is selected. |

For the extension at **5 bps**, the constant-volatility and regime-change intervals include zero. Intervals use **2,000 paired bootstrap resamples** and are pointwise, without adjustment for multiple comparisons. See the [technical report](outputs/P5_Technical_Report.pdf) for the figures, full interpretation and tail-risk limitations.

## Experiment design

The analytical benchmark and the hedge experiments use different parameters deliberately. They should not be mixed when interpreting prices or cash flows.

| Convention | Analytical benchmark | Hedge experiments |
| --- | --- | --- |
| Contract | Synthetic European call, USD cash settlement | Short one synthetic European call; USD cash-funded spot hedge |
| Initial spot / strike | 100 / 100 | 100 / 100 |
| Horizon | 1 year | 0.25 calendar year; 256 grid steps |
| Continuous rate | 5% | 4% financing rate; specified physical drift also 4% |
| Pricing / hedge volatility | 20% | Hedge volatility fixed at 25% |
| Dividend yield | 0% benchmark; pricer supports nonzero yield | 0% required by the spot-hedge ledger |
| Units | One underlying unit per option | One option unit; unrestricted fractional spot trades |

### Baseline: 36 scenario cells

- Realised volatility: **15%, 25%, 40%**.
- Rebalance every **1, 4, 16 or 64 grid steps**.
- Transaction fee: **0, 5 or 20 bps** of absolute spot trade notional, including entry and liquidation.
- **256 paths per realised-volatility setting**, seeds **94000–94255**. The exact same paths are reused across costs and rebalance policies.

The saved baseline uses zero half-spread and borrowing spread. Those controls are supported by the ledger and workbook; they are not additional dimensions in the saved 36-cell sweep. Configuration: [research.json](configs/research.json).

### Extension: 32 scenario cells and 8 paired comparisons

The separate seed block **304000–304255** evaluates four specified dynamics: constant 25% volatility, 15%→40%, 40%→15%, and 25% diffusion with an imposed 20% down jump at the midpoint. Four rebalance intervals and fees of 5/20 bps produce 32 cells and **8,192 path/policy records**.

The comparison is fixed as RMSE(every 4 steps) minus RMSE(every step). Bootstrap resampling preserves the path pairing. Path-level errors and hashes are saved in [holdout_path_errors.csv](outputs/holdout_path_errors.csv); the protocol is in [holdout.json](configs/holdout.json).

New synthetic seeds are not market out-of-sample evidence. The jump occurs on every jump-stress path and estimates neither a jump frequency nor a market tail probability. The extension configuration was written before execution, but was not externally pre-registered.

## How to read the hedge ledger

At inception, the option seller receives the model premium and trades into the delta hedge. At each subsequent step, opening cash accrues financing interest, the hedge is rebalanced when scheduled, and trading costs are deducted. The final row closes the spot position and pays the option payoff.

```text
closing cash = opening cash + financing interest + option cash
               - trade units × spot price - trading costs

net wealth   = closing cash + spot holding × spot price - option liability
```

Negative cash may borrow at the financing rate plus the specified borrowing spread. Once the final spot holding is zero and the option is settled, **terminal cash is the hedge error**. It is not a capital-normalised portfolio return. The saved baseline and extension cash reconciliations are below **3 × 10⁻¹³ USD**.

## Explore the deliverables

| Start with | What it answers |
| --- | --- |
| [Technical report — 9 pages](outputs/P5_Technical_Report.pdf) | Assumptions, numerical validation, ledger mechanics, cost/risk results, paired uncertainty and limitations |
| [Excel model — 9 sheets](outputs/P5_Options_Research_Model.xlsx?raw=true) | How prices, Greeks, IV, tree values and a complete cash ledger are calculated with spreadsheet formulas |
| [Walkthrough notebook](notebooks/01_foundation_walkthrough.ipynb) | Seven sequentially executed Python cells connecting pricing, accounting and experiments |
| [Research design — English](docs/P5_Research_Design.md) | Research questions, hypotheses, contract choices, data requirements and remaining milestones |
| [Validation note](docs/VALIDATION_NOTE.md) | Exact scope of implementation checks and cross-engine comparisons |
| [Claim/evidence matrix](docs/claim_evidence.csv) | Which claims have synthetic evidence and which remain untested |
| [Source register](configs/sources.json) | Contract/API documentation and replication references reviewed for the project |

### Using the Excel model

Edit the **blue inputs** on `Inputs` and check the displayed pricing/hedge status. `Pricing`, `Tree` and `Hedge Ledger` recalculate from formulas; `Experiments` contains explicitly labelled saved Python results.

| Sheet | Purpose |
| --- | --- |
| Overview | Live price, Greeks, IV, hedge cash summary and net-wealth chart |
| Inputs | Separate calculator, IV and hedge controls |
| Pricing | BSM values, analytic Greeks and explicit 60-iteration IV bisection |
| Tree | Visible 16-step European CRR price and backward-value lattice |
| Hedge Ledger | 257 rows covering inception, all grid steps, financing, costs and terminal settlement |
| Experiments | Imported baseline results and Monte Carlo benchmark |
| Path Data | Saved synthetic path, normalised for spot scaling |
| Checks | Parity, holdings, cash reconciliation and IV residual diagnostics |
| Sources | Reference URLs and their use |

Changing spot scales the saved hedge path; it does not generate a new stochastic process. The pricing dividend yield affects the calculator/tree only. The hedge uses its own quarter-year horizon and zero dividends. The small visible tree has discretisation error and is not the converged benchmark. Greeks at expiry or zero volatility are unavailable.

## Quick start

### Run the core tests and research

The pricing, simulation and core tests require **Python 3.10+ and the standard library only**. No market-data credentials are needed.

```bash
git clone https://github.com/thvh2006/options-volatility-hedging-lab.git
cd options-volatility-hedging-lab

python3 scripts/check.py
python3 scripts/run_research.py
python3 scripts/run_holdout.py
python3 scripts/build_walkthrough.py
```

These commands check the models, reproduce the baseline and extension, and rebuild the walkthrough plus JavaScript pricing reference cases. The notebook builder executes ordinary Python sequentially; it does not claim a Jupyter-kernel run.

### Run the explorer

**Open the hosted dashboard: [https://thvh2006.github.io/options-volatility-hedging-lab/](https://thvh2006.github.io/options-volatility-hedging-lab/)**

The prebuilt `index.html` is self-contained. From the repository root:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Open **http://127.0.0.1:8000/**. Change the calculator inputs, inspect the saved cost/frequency tables and move the ledger slider through terminal settlement. Calculator changes do not rerun the saved experiments. Stop the local server with `Ctrl+C`.

To rebuild the explorer and execute its JavaScript checks, use Node.js:

```bash
node scripts/build_explorer.mjs
```

The dashboard is hosted on GitHub Pages from the public `main` branch. The same self-contained explorer can also run locally using the command above. Pricing controls recalculate in the browser; saved experiments remain fixed.

### Optional workbook, report and release builds

| Build | Additional requirement | Command |
| --- | --- | --- |
| Excel golden inputs | Python standard library | `python3 scripts/prepare_workbook_data.py` |
| Formula-based workbook | Node.js with access to `@oai/artifact-tool` | `node scripts/build_workbook.mjs` |
| Read-only XLSX verification | `openpyxl` | `python3 scripts/verify_workbook.py` |
| PDF report | `reportlab`, `pypdf` and Times New Roman regular/bold TTF fonts | `python3 scripts/build_report.py` |
| Source package | `pypdf` for PDF text/metadata inspection | `python3 scripts/package.py` |
| Archive/evidence verification | Python standard library; Git history for attribution check | `python3 scripts/verify_release.py` |

Install the optional Python tools with `python3 -m pip install openpyxl reportlab pypdf`. The Excel authoring dependency is supplied in the authoring environment; this repository does not provide a public installation route for it. **The published XLSX can be used without that dependency.**

Run builds in the table's order after the core research and explorer commands. The report consumes the saved browser evidence; rebuilding it does not rerun Chrome QA. Package verification compares current files against the archive, so rebuild the package after changing repository content. A second-engine XLSX check can be recorded with `python3 scripts/verify_workbook.py /path/to/recalculated.xlsx`; recalculation itself must be performed separately.

The PDF uses **Times New Roman, 11 pt throughout**, including headings, table cells, chart labels and footers. Font files are embedded in the PDF but are not redistributed as standalone assets. Report builds look in the macOS supplemental-font directory by default; set `P5_REPORT_FONT_DIR` when the regular and bold TTF files are stored elsewhere.

The recorded build used **Python 3.12.14** and **Node.js 24.22.3**. The engine's declared Python minimum and the recorded build versions serve different purposes; a compatibility matrix has not been established.

## Validation evidence

| Layer | Recorded checks | Evidence |
| --- | --- | --- |
| Core mathematics and accounting | **26 unit tests**: parity, boundaries, Greeks, IV, tree, MC, ledger, costs and fixture QC | [validation.json](outputs/validation.json), [tests](tests) |
| Independent JavaScript pricing | **108 price comparisons**, tolerance `1e-4` USD/unit; largest difference about `1.568e-5` | [javascript_checks.json](outputs/javascript_checks.json) |
| Explorer application | **9 minimal-DOM checks**, plus separate local Chrome desktop controls/layout/download inspection | [browser_checks.json](outputs/browser_checks.json) |
| Independent Excel calculation | **21 price/Greek/tree** and **3,084 ledger** comparisons across three input cases, tolerance `1e-7` | [excel_checks.json](outputs/excel_checks.json) |
| Export and second engine | **1,031 default-case comparisons** after XLSX export and LibreOffice recalculation; largest cross-engine difference below `8e-13` | [Export checks](outputs/excel_export_checks.json), [cross-engine checks](outputs/excel_cross_engine_checks.json) |
| Release integrity | Archive CRC, per-file hashes, evidence hashes and identity scans including Office XML and PDF text/metadata | [release_checks.json](outputs/release_checks.json), [manifest](outputs/package_manifest.json) |

These checks establish specific implementation properties. Native Microsoft Excel, mobile layout, a Jupyter kernel and a deployed dashboard host have not been certified. Monte Carlo and bootstrap intervals quantify uncertainty conditional on the configured simulation assumptions.

## Repository map

| Path | Contents |
| --- | --- |
| [`src/options_lab/`](src/options_lab) | Pricing, hedge accounting and canonical quote QC |
| [`configs/`](configs) | Baseline/extension protocols and source register |
| [`tests/`](tests) | Mathematical, accounting, QC and paired-bootstrap challenges |
| [`scripts/`](scripts) | Research, walkthrough, explorer, workbook, report and packaging builds |
| [`dashboard/`](dashboard) | Explorer template and independent JavaScript pricer |
| [`notebooks/`](notebooks) | Executed foundation walkthrough |
| [`outputs/`](outputs) | Synthetic results, ledgers, workbook, PDF and verification artifacts |
| [`docs/`](docs) | Research design, validation, claim matrix and publication scope |

## Scope and next research steps

The current hedge is a synthetic cash-funded spot account with fractional trades and unrestricted borrowing. It does not model futures variation margin, collateral, funding, liquidation, execution depth, lot constraints or a venue's delivery/TWAP hedge. Assumed bps costs are not an exchange fee schedule.

The quote-QC module is tested on fixtures. No rights-cleared observed option chain, calibrated smile/surface or empirically validated market strategy is included. BTC_USDC linear European options are a documented candidate for a future market module; admitting them requires both data-rights evidence and the appropriate contract/settlement adapter.

Remaining work is to admit suitable observed data, validate quote coverage and calibration, implement venue-specific hedge accounting, compare a locked challenger under explicit objectives and costs, and test mobile/deployed-host behaviour. More complex models are not presented as superior before those comparisons exist.

Public project attribution: **thvh2006**. The distributable package excludes private snapshots, credentials, personal home paths, dependency directories and internal QA images.
