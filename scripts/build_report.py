#!/usr/bin/env python3
"""Build an evidence-linked technical report from saved synthetic results."""
import json,math
from pathlib import Path
import hashlib
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle
from reportlab.graphics.shapes import Drawing,Line,PolyLine,String,Circle
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs'
NAVY=colors.HexColor('#183B5B');BLUE=colors.HexColor('#236A91');GOLD=colors.HexColor('#AA7328');GREY=colors.HexColor('#627486');LIGHT=colors.HexColor('#EDF3F7')
W=503
styles=getSampleStyleSheet()
styles.add(ParagraphStyle('TitleP5',fontName='Helvetica-Bold',fontSize=25,leading=29,textColor=NAVY,spaceAfter=18))
styles.add(ParagraphStyle('HeadP5',fontName='Helvetica-Bold',fontSize=16,leading=20,textColor=NAVY,spaceAfter=12))
styles.add(ParagraphStyle('SubP5',fontName='Helvetica-Bold',fontSize=11,leading=15,textColor=NAVY,spaceBefore=12,spaceAfter=7))
styles.add(ParagraphStyle('BodyP5',fontName='Helvetica',fontSize=10,leading=14,textColor=NAVY,spaceAfter=10))
styles.add(ParagraphStyle('SmallP5',fontName='Helvetica',fontSize=8,leading=11,textColor=GREY,spaceAfter=7,wordWrap='CJK'))
styles.add(ParagraphStyle('CellP5',fontName='Helvetica',fontSize=8.2,leading=11,textColor=NAVY))
styles.add(ParagraphStyle('CodeP5',fontName='Courier',fontSize=8.2,leading=12,textColor=NAVY,spaceAfter=9))

def P(s,kind='BodyP5'):return Paragraph(escape(str(s)),styles[kind])
def T(headers,rows,widths):
    t=Table([[P(x,'CellP5') for x in headers]]+[[P(x,'CellP5') for x in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('LINEBELOW',(0,0),(-1,0),.7,NAVY),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#DBE3EA')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    return t
def F(x,n=4):return f'{x:,.{n}f}'

def line_chart(series,labels,title,ylabel):
    d=Drawing(W,269);left=48;bottom=37;top=208;right=W-15
    vals=[v for _,ys,_ in series for v in ys];hi=max(vals)*1.12;hi=hi or 1
    d.add(String(0,257,title,fontName='Helvetica-Bold',fontSize=11,fillColor=NAVY))
    d.add(String(0,242,ylabel,fontSize=8,fillColor=GREY))
    for j in range(5):
        v=hi*j/4;y=bottom+(top-bottom)*j/4
        d.add(Line(left,y,right,y,strokeColor=LIGHT));d.add(String(left-7,y-3,F(v,2),textAnchor='end',fontSize=8,fillColor=GREY))
    for j,label in enumerate(labels):
        x=left+(right-left)*j/(len(labels)-1);d.add(String(x,bottom-15,str(label),textAnchor='middle',fontSize=8,fillColor=GREY))
    d.add(String((left+right)/2,5,'Rebalance every grid steps (categorical spacing)',textAnchor='middle',fontSize=8,fillColor=GREY))
    for i,(name,ys,col) in enumerate(series):
        pts=[]
        for j,v in enumerate(ys):
            x=left+(right-left)*j/(len(ys)-1);y=bottom+(top-bottom)*v/hi;pts.extend([x,y]);d.add(Circle(x,y,2.6,fillColor=col,strokeColor=col))
        d.add(PolyLine(pts,strokeColor=col,strokeWidth=1.7));x=left+130*i;d.add(Line(x,224,x+15,224,strokeColor=col,strokeWidth=2));d.add(String(x+19,221,name,fontSize=8,fillColor=col))
    return d

def intervals(rows):
    d=Drawing(W,282);left=172;right=W-18;bottom=32;top=250;lo=-.8;hi=.3
    x=lambda v:left+(v-lo)/(hi-lo)*(right-left)
    d.add(String(0,269,'RMSE difference: every 4 steps minus every step',fontName='Helvetica-Bold',fontSize=10.5,fillColor=NAVY))
    for v in [-.8,-.6,-.4,-.2,0,.2]:
        d.add(Line(x(v),bottom,x(v),top,strokeColor=GREY if v==0 else LIGHT,strokeWidth=.8));d.add(String(x(v),bottom-15,F(v,1),textAnchor='middle',fontSize=8,fillColor=GREY))
    names={'flat_25':'Constant 25%','low_to_high':'15% to 40%','high_to_low':'40% to 15%','conditional_down_jump':'Conditional jump'}
    for i,r in enumerate(rows):
        y=top-14-i*26;a,b=r['rmse_difference_percentile95'];col=BLUE if b<0 else GREY
        d.add(String(left-9,y-3,f"{names[r['scenario']]} | {r['fee_bps']} bps",textAnchor='end',fontSize=8.5,fillColor=NAVY))
        d.add(Line(x(a),y,x(b),y,strokeColor=col,strokeWidth=2));d.add(Line(x(a),y-4,x(a),y+4,strokeColor=col));d.add(Line(x(b),y-4,x(b),y+4,strokeColor=col));d.add(Circle(x(r['rmse_difference']),y,3,fillColor=col,strokeColor=col))
    d.add(String((left+right)/2,1,'USD per option unit; pointwise 95% paired bootstrap intervals',textAnchor='middle',fontSize=8,fillColor=GREY))
    return d

def footer(canvas,doc):
    canvas.setStrokeColor(LIGHT);canvas.line(46,48,549,48);canvas.setFillColor(GREY);canvas.setFont('Helvetica',8)
    canvas.drawString(46,34,'P5 | Synthetic research | thvh2006 | 26 November 2026');canvas.drawRightString(549,34,str(doc.page))
    canvas.setTitle('P5 Options Volatility and Hedging Lab - Technical Report');canvas.setAuthor('thvh2006');canvas.setSubject('Synthetic pricing and hedge-cost experiments; no observed market performance')

def main():
    r=json.loads((OUT/'research_results.json').read_text());h=json.loads((OUT/'holdout_results.json').read_text());ledger=json.loads((OUT/'representative_hedge.json').read_text());browser=json.loads((OUT/'browser_checks.json').read_text());s=[]
    def p(text,style='BodyP5'):s.append(P(text,style))
    def page(title):
        if s:s.append(PageBreak())
        p(title,'HeadP5')
    p('P5 OPTIONS VOLATILITY AND HEDGING LAB','SmallP5');p('Pricing accuracy does not settle hedge quality','TitleP5')
    p('Technical report | Synthetic module 0.3.0 | 26 November 2026','SubP5')
    p('A numerical model can price its own European option accurately and still leave substantial terminal hedge error. This project separates approximation error from discrete trading, transaction costs, volatility mismatch and an imposed jump. The evidence is reproducible simulation, rather than a market backtest.')
    s.append(T(['Finding','Evidence','Interpretation'],[
        ['Numerical foundation','BSM call 10.450584; 26 unit tests pass','The implementation matches analytical and accounting identities within explicit tolerances.'],
        ['Costless frequency effect','Matched-vol error SD: 0.2409 at every step; 1.9671 at every 64 steps','More frequent trading reduces sample discretisation dispersion under the matched assumptions.'],
        ['Costs reverse one ranking','20 bps baseline RMSE: 1.2498 every step; 0.8658 every 4 steps','Lower replication dispersion alone does not choose the best net-cost policy.'],
        ['Separate simulation block','32 cells; 8 paired comparisons; 256 new seeds per scenario','At 20 bps all four RMSE-difference intervals are below zero; this remains conditional evidence.']
    ],[103,159,241]));s.append(Spacer(1,13))
    p('Scope of this report','SubP5');p('One synthetic USD European option unit is shorted and delta-hedged with a cash-funded, fractional spot position. The ledger includes premium, financing, trades, costs, liquidation and payoff. It excludes observed quotes, exchange margin and any claim about executable investment returns.')
    p('Deliverables: a Python engine, independent JavaScript calculator, nine-sheet formula-based Excel model, executed walkthrough, saved experiment tables and this report. Public distribution is owner-approved. Source: https://github.com/thvh2006/options-volatility-hedging-lab.','SmallP5')

    page('1. Contract and pricing assumptions')
    s.append(T(['Convention','Synthetic reference'],[['Exercise and settlement','European, cash-settled in USD; one underlying unit per option'],['Time and rates','ACT/365F calendar years; continuously compounded rates'],['Pricing benchmark','S = K = 100; T = 1 year; r = 5%; sigma = 20%; q = 0'],['Hedge experiment','T = 0.25 year; 256 steps; r = physical drift = 4%; hedge sigma = 25%; q = 0'],['Positions and financing','Short one call; unrestricted fractional spot hedge; cash may borrow'],['Trading costs','Assumed bps of absolute spot trade notional, including entry and liquidation']],[151,352]));s.append(Spacer(1,11))
    p('The pricing benchmark and hedge scenario deliberately use different horizons, rates and volatilities. The workbook separates these controls. A price calculated at the one-year benchmark must not be substituted for the quarter-year hedge premium.')
    p('Analytical reference [S8]','SubP5')
    for text in ['d1 = [ln(S/K) + (r - q + sigma^2/2)T] / [sigma sqrt(T)]','d2 = d1 - sigma sqrt(T)','Call = S exp(-qT) N(d1) - K exp(-rT) N(d2)','Put = K exp(-rT) N(-d2) - S exp(-qT) N(-d1)']:p(text,'CodeP5')
    p('Black76 uses a forward and a discount factor as separate inputs. The CRR implementation is European and rejects probabilities outside [0, 1] instead of clamping them. Neither automatically establishes suitability for American or inverse-settled options.')
    p('Boundary behaviour and Greek units','SubP5');p('At expiry the option value is its payoff. At zero volatility the deterministic discounted payoff is used. Greeks at these boundaries are unavailable. Smooth-case delta is per underlying unit, gamma is per USD spot change, vega and rho are per one percentage point, and theta is per calendar day.')

    page('2. Numerical validation and uncertainty')
    p('The analytical call price is '+F(r['benchmark']['analytical_call'],9)+' USD. The tests challenge parity, boundaries, finite-difference Greeks, IV inversion, forward/spot consistency, tree convergence and cash accounting. Numerical agreement verifies implementation under these assumptions; it does not validate a market return process.')
    s.append(T(['CRR steps','European price USD','Difference from BSM USD'],[[x['steps'],F(x['price'],7),F(x['error'],7)] for x in r['benchmark']['tree']],[90,191,222]));s.append(Spacer(1,12))
    mc=r['benchmark']['monte_carlo'];cv=r['monte_carlo_coverage']
    p('Antithetic Monte Carlo','SubP5');p(f"The benchmark uses {mc['independent_pairs']:,} independent antithetic pairs ({mc['terminal_draws']:,} terminal draws), seed {mc['seed']}. Estimated price is {F(mc['price'],6)}, with standard error {F(mc['standard_error'],6)} and normal-approximation 95% interval [{F(mc['ci95'][0],6)}, {F(mc['ci95'][1],6)}]. Pair averages, rather than the individual correlated draws, define the standard error.")
    p(f"A diagnostic across {cv['replications']} independent runs with {cv['independent_pairs_per_replication']:,} pairs per run covers the analytical price in {cv['coverage']:.1%} of runs. Its binomial Wilson interval is [{cv['wilson95'][0]:.1%}, {cv['wilson95'][1]:.1%}]. Forty replications give imprecise coverage evidence; a 95% interval is not expected to contain the reference on every seed.")
    p('Independent implementations','SubP5')
    s.append(T(['Implementation','Checks','Limit'],[['JavaScript','108 Python prices; maximum difference 0.00001568; tolerance 0.0001','Numerical normal-CDF approximation; displayed Greeks use finite differences.'],['Excel authoring engine','21 price/Greek/tree and 3,084 ledger comparisons; tolerance 1e-7','Three smooth input cases; boundary limitations remain explicit.'],['Export and second engine','1,031 default-case comparisons after export and LibreOffice recalculation','No native Microsoft Excel certification.']],[110,199,194]))

    page('3. Self-financing spot hedge and cash ledger')
    p('The option seller receives the model premium at inception and buys the target delta hedge. The remaining cash may be negative. Before each subsequent trade, cash accrues interest. When cash is negative, the optional borrowing spread is added to the base financing rate. The terminal row liquidates the spot hedge and pays the short option payoff. [S8]')
    for text in ['trade_units_i = target_units_i - previous_holding_i','trade_cash_i = -trade_units_i * spot_i','cost_i = abs(trade_units_i) * spot_i * (fee + half_spread)/10000','close_cash_i = open_cash_i + interest_i + option_cash_i','               + trade_cash_i - cost_i','net_wealth_i = close_cash_i + holding_i * spot_i - option_liability_i']:p(text,'CodeP5')
    p('Representative saved path: seed 94000; hedge every four steps; 5 bps fee. All figures below are USD except step and trade units. The option cash column is the initial premium, zero between inception and expiry, and the negative payoff at settlement.','SmallP5')
    rows=[]
    for i in [0,1,4,128,252,255,256]:
        x=ledger['ledger'][i];rows.append([i,F(x['spot']),F(x['trade_units']),F(x['interest']),F(x['option_cash']),F(x['costs']),F(x['closing_cash'])])
    s.append(T(['Step','Spot','Trade units','Interest','Option cash','Costs','Close cash'],rows,[35,72,79,70,88,69,90]));s.append(Spacer(1,12))
    p(f"Initial premium is {F(ledger['premium'],6)}, total fees {F(ledger['total_costs'],6)}, total interest {F(ledger['total_interest'],6)}, and terminal payoff {F(ledger['terminal_payoff'],6)}. After the final holding is reduced to zero, terminal cash and hedge error are both {F(ledger['hedging_error'],6)}.")
    p('Reconciliation is checked at every row and over the whole ledger. A zero terminal target is a close instruction, not a claim that mathematical delta is zero at expiry. This is a spot cash account; it is not a futures margin, funding, collateral or liquidation model.','SmallP5')

    page('4. Baseline: the cost of trading more often')
    p('The baseline fixes 256 paths for each realised volatility, with seeds 94000-94255. Every cost/frequency combination reuses those exact paths. Three realised volatilities, four rebalance intervals and three fees give 36 cells. The physical drift is explicitly 4%, not a fitted expected return.')
    matched=[x for x in r['hedge_cases'] if x['realised_vol']==.25]
    series=[(f'{fee} bps',[next(x['rmse'] for x in matched if x['fee_bps']==fee and x['rebalance_every']==ev) for ev in [1,4,16,64]],col) for fee,col in [(0,BLUE),(5,GREY),(20,GOLD)]]
    s.append(line_chart(series,[1,4,16,64],'Matched volatility: RMSE after financing and trading costs','RMSE, USD per short option unit'))
    s.append(T(['Fee bps','Every 1: RMSE','Every 4: RMSE','Every 16: RMSE','Every 64: RMSE'],[[fee]+[F(next(x['rmse'] for x in matched if x['fee_bps']==fee and x['rebalance_every']==ev)) for ev in [1,4,16,64]] for fee in [0,5,20]],[63,110,110,110,110]));s.append(Spacer(1,12))
    p('With no transaction cost and matched volatility, every-step hedging has the smallest sample error dispersion among these policies. At 20 bps, repeated spot trades create enough cost drag that every-four-step hedging has a lower sample RMSE than every-step hedging.')
    p('RMSE measures distance from zero terminal hedge error. It combines mean error and dispersion. A policy that reduces cost can improve RMSE even when its discretisation error increases. A different loss function, capital requirement, fee schedule or path process could rank these policies differently.')
    p('This is a conditional cost/risk frontier. There is no universal optimum, capital-normalised return, Sharpe ratio, liquidity estimate or empirical alpha claim.','SmallP5')

    page('5. Separate seeds, regimes and paired inference')
    p('The extension uses seeds 304000-304255, disjoint from the baseline. Its configuration was written before execution, but is not an independently registered protocol. Four specified dynamics, four rebalance intervals and two fees give 32 cells and 8,192 path/policy records. Common Gaussian shocks are used across dynamics, and exact paths are reused across policies and fees.')
    s.append(T(['Dynamics','Construction'],[['Constant','25% volatility throughout'],['Low to high','15% for the first 128 steps; 40% for the next 128'],['High to low','40% for the first 128 steps; 15% for the next 128'],['Conditional jump','25% diffusion plus a permanent 0.80 multiplier at step 128 on every path']],[125,378]));s.append(Spacer(1,12))
    s.append(intervals(h['paired_comparisons']));s.append(Spacer(1,10))
    p('The pre-specified comparison is RMSE(every 4 steps) minus RMSE(every step). Each interval is a percentile interval from 2,000 paired bootstrap resamples of the 256 path indices. Resampling the same index for both policies preserves the path pairing.')
    p('All four 20 bps intervals lie below zero. At 5 bps, the constant and regime intervals include zero, whereas the conditional jump interval is negative. These are pointwise intervals without multiple-comparison adjustment; no policy was selected. New random seeds are not market out-of-sample evidence.','SmallP5')

    page('6. Model risk, tails and what the samples cannot say')
    p('Volatility mismatch changes both the distribution of hedge error and the initial liability value relative to the realised diffusion. A positive average hedge error in a low-volatility scenario is not evidence of a market volatility premium. No observed prices or estimated return distribution enter these experiments.')
    s.append(T(['Realised vol','Hedge every','Mean error USD','RMSE USD'],[[f"{x['realised_vol']:.0%}",x['rebalance_every'],F(x['mean_error']),F(x['rmse'])] for x in r['hedge_cases'] if x['fee_bps']==5 and x['rebalance_every'] in [1,4,64]],[100,100,151,152]));s.append(Spacer(1,12))
    p('The jump stress is deliberately conditional','SubP5');p('Every jump-stress path receives the same 20% down jump at the midpoint. It explores a failure mechanism of a diffusion-based delta hedge. It does not estimate a jump arrival process, a market tail probability or how often such a loss should occur.')
    tail=[x for x in h['summary'] if x['fee_bps']==20 and x['rebalance_every']==4]
    s.append(T(['Every 4 steps, 20 bps','5th percentile error','Mean of lower sample tail'],[[x['scenario'],F(x['p05']),F(x['lower_tail_mean'])] for x in tail],[190,148,165]));s.append(Spacer(1,9))
    p('With only 256 paths per cell, the lower-tail mean averages about 13 observations. These descriptive sample statistics are unstable and are not calibrated market VaR or expected shortfall. A larger simulation and parameter sensitivity study would be necessary for a tail-risk claim.','SmallP5')

    page('7. Operational evidence and remaining research gates')
    s.append(T(['Evidence gate','Current result','Open limitation'],[['Core and notebook','26 tests; 7 code cells executed sequentially','Notebook uses an ordinary-Python harness; a Jupyter kernel run is not claimed.'],['Excel','9 sheets; live formula pricing, tree and hedge ledger','Imported experiment tables do not respond to calculator inputs.'],['Desktop browser',f"Chrome at {browser['viewport']['width']} px; input/reset, fee, expiry and ledger controls checked",'Local desktop validation only; mobile and deployed-host behaviour not certified.'],['Download','Downloaded XLSX byte hash matches original','Public dashboard hosting not configured.'],['Accounting','Baseline and extension residuals below 3e-13','No position-size, lot, margin, collateral or liquidity constraints.'],['Identity','Attribution thvh2006 or blank; package content scan','Not a certification of every prior repository or third-party cache.']],[110,185,208]));s.append(Spacer(1,10))
    p('Observed market module','SubP5');p('No observed quotes have been admitted. Contract metadata, source timestamps, price currency and settlement currency must be established before calibration. The fixture QC rejects stale or unaligned snapshots, crossed/locked books, absent executable size, unsupported conventions and prices outside model bounds. A passing fixture does not prove a real feed is complete or executable. [S1-S4]')
    p('The market-data publication-rights gate remains unresolved. Venue market and derived data are excluded from the distributable package. Contract documentation and public API schemas are not themselves a licensed historical quote dataset. The venue-specific settlement and hedge adapter remains separate work. [S5-S7]')
    p('A challenger must beat a locked baseline under explicit objectives','SubP5');p('Before adding a complex model, define its calibration window, evaluation window, loss function, cost convention and compute budget. Compare pricing fit, parameter stability and hedge loss separately. Neither an elaborate volatility model nor a lower in-sample pricing error is evidence of superior out-of-sample hedging.')
    p('The owner-approved synthetic module is published at github.com/thvh2006/options-volatility-hedging-lab. This report is a completed account of the synthetic module, not completion of the observed-market research programme.','SmallP5')

    page('8. Sources, artifacts and reproduction')
    p('The numerical tables and figures are generated from this project\'s saved synthetic outputs. External references establish contract conventions, metadata requirements and replication context; they are not observations used to estimate these results. Sources were reviewed on 26 November 2026.','SmallP5')
    sources=json.loads((ROOT/'configs/sources.json').read_text())['sources']
    for i,x in enumerate(sources,1):
        p(f"[S{i}] {x['publisher']} | {x['id']}",'SubP5');p(x['url'],'SmallP5')
    p('Artifacts to inspect','SubP5')
    p('research_results.json: baseline and numerical evidence. holdout_results.json: protocol, summary and paired intervals. holdout_path_errors.csv: seed, exact-path hash and path-level policy results. representative_hedge_ledger.csv: auditable cash rows. excel_*checks.json and browser_checks.json: implementation checks. P5_Options_Research_Model.xlsx: independently calculated formulas.','SmallP5')
    p('Reproduction','SubP5');p('Run the commands in README from the project root. The Python pricing and simulation engines use the standard library. Excel builds require artifact-tool; read-only workbook checks use openpyxl. Report generation uses ReportLab and pypdf. Browser QA is manual automation evidence and must be repeated for a changed host or layout. The original 0.1 baseline is preserved as a distinct configuration.','SmallP5')
    out=OUT/'P5_Technical_Report.pdf';doc=SimpleDocTemplate(str(out),pagesize=A4,leftMargin=46,rightMargin=46,topMargin=42,bottomMargin=62,title='P5 Options Volatility and Hedging Lab - Technical Report',author='thvh2006')
    doc.build(s,onFirstPage=footer,onLaterPages=footer)
    reader=PdfReader(out);assert len(reader.pages)==9,len(reader.pages)
    texts=[p.extract_text() for p in reader.pages];assert all(len(t)>300 for t in texts)
    report=dict(status='PASS',pages=len(texts),author=reader.metadata.author,figures=2,source_mode='saved synthetic project outputs',title=reader.metadata.title)
    report['evidence_sha256']={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['research_results.json','holdout_results.json','representative_hedge.json','browser_checks.json','excel_checks.json','excel_export_checks.json','excel_cross_engine_checks.json','validation.json']}
    (OUT/'report_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
