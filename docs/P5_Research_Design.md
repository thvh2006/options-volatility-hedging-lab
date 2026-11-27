# P5 Options Volatility and Hedging Lab: research design

Design date: 26 November 2026. Current module: 0.3.0. Author: thvh2006. Evidence mode: synthetic.

## 1. Research question and contribution

**How accurate must an initial option price be to support an effective hedge, and when do transaction costs, volatility misspecification or jumps outweigh the benefits of more frequent rebalancing?**

The contribution is an inspectable workflow connecting contract conventions, assumptions, prices, IV, Greeks, hedge transactions, cash accounting, terminal errors and uncertainty. A pricing calculator alone does not establish hedge quality. The project separates numerical approximation error, model error and implementation costs.

The research should demonstrate that the chosen model matches the contract, every cash flow can be reconciled, and conclusions remain within the evidence. Fitting a snapshot does not uniquely identify the subsequent price dynamics or establish out-of-sample profitability.

## 2. Contract selection

| Candidate | Strength | Issue requiring separate treatment | Decision |
| --- | --- | --- | --- |
| Generic European vanilla | Analytical reference and auditable cash flows | Supplies no observed-market evidence | Reference for numerical validation and the synthetic ledger |
| SPX European | Relevant to traditional derivatives and portfolio risk | AM/PM settlement, licensed history and hedge basis | Alternative market-validation candidate |
| SPY/equity options | Familiar chains and examples | American exercise, dividends and early exercise | Do not treat as European by default |
| BTC_USDC linear options | Documented metadata/API and European convention | Publication rights, collateral, futures hedge and settlement | First market-module candidate; no observed data admitted |
| BTC inverse options | Additional numeraire and coin-exposure questions | Premium, settlement and hedge currencies can differ | Later extension after validating the linear case |

Keep the mathematical USD benchmark separate from the market-contract adapter. A synthetic path must not be relabelled as BTC or SPX history. A cash-funded spot ledger must not be presented as futures variation-margin accounting.

The reviewed Deribit linear-option documentation describes European USDC contracts and a two-step delivery process: an in-the-money option creates a futures position at the strike, followed by immediate cash settlement. Delivery references and multipliers require explicit conventions. A future registry must retain rule versions, effective dates and sources. [S1-S2]

## 3. Conditional hypotheses

| ID | Hypothesis | Test | Conclusion the evidence does not support |
| --- | --- | --- | --- |
| H1 | Under matched-volatility GBM with zero costs, more frequent hedging reduces sample error dispersion | Reuse paths across schedules; compare SD and RMSE | Every individual path improves |
| H2 | Turnover costs can outweigh smaller discretisation error | Fix paths and policies; vary assumed costs | A universally optimal frequency |
| H3 | Volatility mismatch changes systematic hedge errors | Fix hedge volatility and vary the path-generating volatility | Observed trading alpha or a market volatility premium |
| H4 | Jumps can create material hedge errors despite accurate initial diffusion-model pricing | Labelled single-path and multi-path conditional stresses | An estimated market tail probability |
| H5 | Added model complexity is useful only with meaningful evaluation improvements | Lock windows, pricing/hedge losses, stability and compute budget | Lower in-sample calibration error automatically wins |

Do not calculate investor returns or Sharpe ratios from a hedge-error ledger without a capital/margin convention. Do not tune a policy on an evaluation block and continue to describe that block as untouched out-of-sample evidence.

## 4. Module specifications

### Contract registry and quote quality

A market-contract registry requires exercise style, option type, strike, UTC expiry, payoff reference, quote/settlement currencies, contract size, quantity unit, premium timing, settlement process, tick size, time basis and confirming sources.

Canonical records should preserve bid/ask prices and sizes, snapshot and underlying/forward timestamps, source, capture time and data mode. A snapshot timestamp does not establish the age of each individual quote. Rejections must carry specific reasons rather than only a surviving-row count.

The intended pipeline checks missing/nonfinite fields, conventions, expiry/future timestamps, stale or unaligned observations, missing sizes and locked/crossed books, excessive spreads, model bounds and IV inversion. Thresholds must be fixed before calibration. The current QC engine implements foundational checks on synthetic fixtures; fixture acceptance does not establish real-feed provenance, coverage or executability.

### Pricing and numerical validation

BSM handles European spot options with continuous dividend yield. Black76 accepts an explicit forward and discount factor. CRR rejects probabilities outside [0, 1] rather than clamping them; an invalid probability requires a different grid or assumptions.

European Monte Carlo uses terminal GBM draws and antithetic pairs. Standard errors use independent pair averages, not the two correlated payoffs as independent observations. IV uses bracketing/bisection with a price residual and explicit statuses for invalid bounds, zero-volatility boundaries, expiry, absence of a finite solution at the upper bound, and bracket/iteration limits.

Greek units are explicit: delta per underlying unit, gamma per spot-price unit, vega/rho per percentage point, and theta per calendar day. Unsupported boundary Greeks remain unavailable.

### Hedge cash ledger

The engine shorts European calls or puts and trades fractional spot to hedge delta, with zero dividends. The option premium enters cash at inception; negative cash incurs financing. Each trade has a notional and costs. The final row closes the hedge and pays the option payoff, including liquidation costs.

Each row satisfies:

`closing cash = opening cash + interest + option cash + hedge trade cash - costs`

Terminal cash reconciles to cumulative cash flows and represents synthetic USD hedge error, not an investor return. The replication/self-financing context is referenced to MIT material. [S8]

A futures extension needs a separate adapter for initial/maintenance margin, variation margin, collateral interest/haircuts, liquidation, hedge basis and settlement. Renaming the existing spot ledger would not implement these mechanisms.

## 5. Baseline experiment protocol

- Horizon: 0.25 calendar year, ACT/365F; 256 grid steps.
- Paths: 256 independent seeds, 94000-94255, for each realised-volatility setting.
- Hedge volatility: 25%; realised volatility: 15%, 25% or 40%.
- Rebalance intervals: 1, 4, 16 or 64 grid steps, not exchange trading-day labels.
- Assumed spot notional fees: 0, 5 or 20 bps, including entry and liquidation.
- Total: 36 cells, with identical paths reused across fees and schedules.
- Metrics: mean error, SD, RMSE, sample quantiles, standard error of the mean, turnover and costs.

The original single-path 20% down-jump case is an illustration, not an estimated jump frequency. A policy choice would require a pre-specified objective and risk/cost budget. Spread/lot constraints and broader parameter sensitivity remain extensions.

## 6. Evidence and interpretation

### Numerical foundation

The suite has 26 passing unit tests. Seven notebook code cells were executed sequentially through an ordinary-Python harness; a Jupyter-kernel run is not claimed. The JavaScript pricer is compared with 108 Python prices: maximum absolute difference about 0.00001568 USD/unit, against a tolerance of 0.0001. Nine minimal-DOM checks cover calculator states and saved tables; browser observations are recorded separately.

At S = K = 100, T = 1, r = 5% and sigma = 20%, the analytical call is approximately 10.450584 USD. Monte Carlo uses 20,000 independent antithetic pairs, or 40,000 terminal draws. A 40-replication coverage diagnostic gives 92.5%, with an accompanying Wilson interval; not every run must cover the analytical price.

At matched 25% volatility and no fees, error SD is approximately 0.2409 for every-step hedging and 1.9671 for every 64 steps. At 20 bps, RMSE is approximately 1.2498 for every step and 0.8658 for every four steps. This does not establish a universal optimum. The largest baseline cash residual is about 2.83e-13 USD.

These are saved simulation results in `outputs/research_results.json`, not market quotes or realised strategy performance.

### Independent Excel

The workbook has nine sheets: Overview, Inputs, Pricing, Tree, Hedge Ledger, Experiments, Path Data, Checks and Sources. BSM, Greeks, IV bisection, the 16-step tree and 257 ledger rows use Excel formulas. The 36-cell experiment table is explicitly imported from Python.

Changing spot scales the saved path without regenerating a stochastic process. The default one-year calculator and quarter-year hedge have separate horizons and rates. The hedge dividend convention remains zero.

Three call/put cases, including nonzero pricing dividend yield and borrowing spread, produce 21 pricing/Greek/tree and 3,084 ledger comparisons at absolute tolerance 1e-7. Higher fees must reduce final cash on a fixed path. Exported-file and LibreOffice recalculation checks cover the default case. Native Microsoft Excel is not certified. See `scripts/verify_workbook.py` and `outputs/excel_*checks.json`.

### Separate synthetic evaluation block

`configs/holdout.json` was written before executing seeds 304000-304255. It leaves baseline seeds 94000-94255 unchanged. New simulation seeds are not market out-of-sample evidence or external pre-registration.

Four dynamics are specified: constant 25% volatility, 15% to 40%, 40% to 15%, and 25% volatility with a midpoint 20% down jump. Four frequencies and two fees produce 32 cells. Gaussian shocks are paired across dynamics; exact paths are shared across costs and policies.

The fixed comparison, every four steps minus every step, uses 2,000 paired bootstrap resamples of path indices. At 20 bps, the RMSE-difference intervals lie below zero for all four dynamics. At 5 bps, the constant/regime intervals contain zero; the conditional jump interval is negative. Intervals are pointwise, with no multiple-comparison adjustment, and no policy is selected.

The jump occurs on every conditional-stress path and estimates no arrival rate. Lower-tail means describe samples of 256 paths and are not calibrated market VaR/ES. The extension's largest accounting residual is approximately 2.75e-13 USD.

## 7. Observed data and publication rights

Public API documentation establishes schemas; it does not itself provide executable historical quotes or redistribution permission. The reviewed Deribit terms include market/derived-data restrictions in Article 4.6. Venue market and derived data remain excluded until the publication-rights gate is resolved. This records the project's data-admission decision, not a legal opinion. [S3-S5]

No data purchase, exchange account creation or trading is part of this module. A future observed-data study must establish appropriate access and conventions. SPX remains an alternative with its own access and licensing requirements. [S6-S7]

## 8. Deliverables and completion gates

| Stage | Deliverable | Acceptance condition | Current status |
| --- | --- | --- | --- |
| A Design | Charter, contracts, hypotheses, source register | Explicit conventions and claims | Documented |
| B Numerical foundation | Pricing, IV, Greeks, tree, MC, tests | Boundaries, identities and convergence | Implemented and checked |
| C Hedge foundation | Ledger, paired sweeps, explorer, notebook | Cash and fee reconciliation | Implemented and checked |
| D Independent Excel | Formula pricing, Greeks, tree and saved-path ledger | Independent calculation and perturbation agreement | Nine sheets; three-case comparison and default cross-engine checks |
| E Market module | Registry, observed quote QC, calibration coverage | Admitted data/rights and correct conventions | No observed dataset admitted |
| F Model risk | Regimes, jumps, paired intervals, locked challenger | Evaluation, stability and compute evidence | Synthetic extension implemented; market OOS/challenger open |
| G Public delivery | Dashboard, report, validation and repository | Scoped claims, reproducible artifacts and visual review | Public synthetic module; deployment evidence tracked separately |

Keep spreadsheet tabs tied to distinct work. Large MC/surface-calibration results should remain labelled imports; analytical pricing, Greeks, a small tree and one ledger calculate independently.

The explorer contains a live price calculator, baseline cost/frequency tables, paired extension intervals and ledger replay. It does not contain an observed smile or validated volatility surface. A larger market dashboard would need chain quality, smile/term structure and venue-specific hedge/data validation.

The synthetic technical report has nine pages and two result-derived figures. All report text uses Times New Roman, 11 pt. Public repository: https://github.com/thvh2006/options-volatility-hedging-lab. Detailed distribution scope is recorded in `docs/PUBLICATION_REVIEW.md`. The observed-market research programme remains incomplete.

## 9. References

Source-review date: 26 November 2026. The source register records uses and locators; these references are not admitted quote datasets.

- [S1] Deribit linear contract specifications: https://support.deribit.com/hc/en-us/articles/31424932728093-Linear-USDC-Options
- [S2] Deribit delivery-process change: https://insights.deribit.com/exchange-updates/change-to-option-delivery-process/
- [S3] Instrument API: https://docs.deribit.com/api-reference/market-data/public-get_instruments
- [S4] Order-book API: https://docs.deribit.com/api-reference/market-data/public-get_order_book
- [S5] Terms of Service, Article 4.6: https://statics.deribit.com/files/TermsofServiceDeribit.pdf
- [S6] Cboe SPX product page: https://www.cboe.com/tradable-products/sp-500/spx-options/
- [S7] Cboe historical quotes: https://datashop.cboe.com/option-quote-intervals
- [S8] MIT 15.450, Leonid Kogan, lecture 2, replication: https://www.ocw.mit.edu/courses/15-450-analytics-of-finance-fall-2010/0d1260b891a96241316d883d4f5bfaec_MIT15_450F10_lec02.pdf
