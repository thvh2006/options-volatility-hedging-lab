# P5 Options Volatility and Hedging Lab

Ngày chốt thiết kế: 26/11/2026. Bản hiện tại: 0.3.0, nền tảng mô phỏng đã chạy. Tác giả: thvh2006.

## 1 Câu hỏi nghiên cứu và luận điểm của dự án

Câu hỏi chính: **một mô hình định giá khớp đến mức nào mới đủ để hedge tốt, và khi nào chi phí, biến động sai mô hình hoặc bước nhảy giá làm lợi ích của việc hedge thường xuyên biến mất?**

Đây là bài nghiên cứu về chất lượng định giá và kiểm soát rủi ro phái sinh. Chỉ có một máy tính Black–Scholes sẽ chưa chứng minh đủ năng lực quant. Giá trị của P5 nằm ở chuỗi có thể kiểm tra: hợp đồng → giả định → giá/IV/Greeks → giao dịch hedge → sổ tiền → sai số → chi phí và giới hạn mô hình.

Ba điểm cần thể hiện trong portfolio:

1. Biết vì sao một công thức được phép dùng cho một hợp đồng cụ thể.
2. Phân biệt sai số số học, sai mô hình và chi phí triển khai.
3. Biết giới hạn kết luận: fit một snapshot không xác định duy nhất động lực giá và không chứng minh lợi nhuận hay hedge hiệu quả ngoài mẫu.

## 2 Cân nhắc loại hợp đồng

| Lựa chọn | Điểm mạnh | Vấn đề phải giải quyết | Quyết định |
| --- | --- | --- | --- |
| European vanilla tổng quát | Có nghiệm chuẩn, kiểm tra được từng dòng tiền, dễ tái lập | Không cung cấp bằng chứng thị trường | Dùng cho nền tảng toán và ledger |
| SPX European | Gắn với thị trường truyền thống và quản lý danh mục | Phải phân biệt AM/PM settlement, dữ liệu lịch sử và hedge thực tế có basis | Ứng viên kiểm chứng thứ hai khi có dữ liệu phù hợp |
| SPY/equity options | Nhiều ví dụ và option chain | American exercise, cổ tức và early exercise làm thay đổi mô hình | Không dùng như European mặc định |
| BTC_USDC linear options | Metadata/API rõ, hợp đồng European, phù hợp nghiên cứu volatility | Quyền dữ liệu, collateral, futures hedge và settlement phải được mô hình hóa riêng | Ứng viên market module đầu tiên, chưa nhận dữ liệu quan sát |
| BTC inverse options | Có thêm bài toán numeraire và coin exposure | Premium/settlement/hedge có thể khác tiền tệ, dễ sai đơn vị | Để extension sau khi linear đã được kiểm chứng |

Quyết định hiện tại: tách **benchmark toán học bằng USD** khỏi **adapter hợp đồng thị trường**. Không đổi nhãn một đường giá tổng hợp thành dữ liệu BTC hoặc SPX. Không dùng ledger spot vay tiền để giả lập futures variation margin.

Tài liệu Deribit hiện mô tả quyền chọn USDC là European. Khi ITM, quyền chọn tạo vị thế futures tại strike rồi futures tất toán tiền mặt; giá delivery dựa trên TWAP và có multiplier theo hợp đồng. Registry phải lưu phiên bản quy tắc, thời điểm hiệu lực và nguồn. [S1–S2]

## 3 Những giả thuyết sẽ kiểm tra

| Mã | Giả thuyết có điều kiện | Phép kiểm tra | Điều không được kết luận |
| --- | --- | --- | --- |
| H1 | Với GBM khớp volatility và không có phí, hedge thường xuyên làm giảm độ phân tán sai số | Cùng đường giá, nhiều lịch rebalance; so standard deviation và RMSE | Mỗi đường giá riêng lẻ luôn tốt hơn |
| H2 | Khi có phí, giảm sai số discretisation có thể bị lấn át bởi turnover | Giữ nguyên path/trade policy, thay cost; dựng cost/error frontier | Có một tần suất tối ưu cho mọi điều kiện |
| H3 | Dùng sai volatility tạo ra sai lệch hệ thống trong hedge error | Hedge vol cố định, thay vol tạo path; so paired errors | Đây là alpha giao dịch quan sát được |
| H4 | Jump risk có thể làm hedge kém dù initial vanilla price vẫn khớp | Stress jump có nhãn; sau đó mở rộng thành phân phối nhiều đường giá | Một path nhảy giá chứng minh xác suất tail thực tế |
| H5 | Mô hình phức tạp chỉ đáng dùng khi cải thiện ngoài mẫu có ý nghĩa | Khóa cửa sổ, pricing error, hedge error, parameter stability và compute budget | Calibration error thấp tự động thắng |

Không dùng return/Sharpe từ hedge-error ledger chưa có capital/margin convention. Không chọn tham số sau khi xem holdout rồi vẫn gọi đó là ngoài mẫu.

## 4 Thiết kế các module

### Hợp đồng và dữ liệu

Registry tối thiểu: style, option type, strike, expiry UTC, payoff reference, quote currency, settlement currency, contract size, quantity unit, premium timing, settlement process, tick size, time basis và nguồn xác nhận.

Canonical quote giữ bid/ask và size, thời điểm snapshot, thời điểm underlying/forward, source, capture time và trạng thái dữ liệu. Snapshot timestamp không chứng minh tuổi thật của từng lệnh chào. Pipeline phải xuất lý do loại từng record; không chỉ đưa ra số lượng còn lại.

Thứ tự loại: thiếu trường/không hữu hạn → sai convention → hết hạn/timestamp tương lai → snapshot cũ/underlying lệch → thiếu size/locked/crossed → spread quá rộng → ngoài model bounds → IV không giải được. Các ngưỡng phải chốt trước calibration. Code QC hiện đã thực hiện phần nền tảng với fixture tổng hợp.

### Pricing và numerical validation

BSM cho European spot với continuous dividend yield. Black76 dùng forward và discount factor riêng. CRR không clamp xác suất ngoài [0,1]; lỗi đó yêu cầu sửa lưới hoặc giả định. Monte Carlo dùng exact terminal GBM cho payoff European, antithetic pairs và standard error trên pair averages. Không coi hai payoff trong cùng cặp là hai quan sát độc lập.

IV dùng bracketing và bisection với price residual. Phân biệt giá ngoài bounds, zero-vol boundary, expiry không có IV xác định, upper bound không có IV hữu hạn và giới hạn bracket. Greeks ghi rõ delta theo một đơn vị underlying, vega/rho theo một điểm phần trăm, theta theo ngày lịch. Không tự gán giá trị hợp lý giả cho boundary chưa hỗ trợ.

### Hedge cash ledger

Nền tảng hiện tại là short European call/put, mua/bán spot để hedge delta, q=0. Premium đi vào cash tại đầu kỳ. Cash âm chịu lãi vay. Mỗi trade có notional và phí. Cuối kỳ đóng hedge về 0 và thanh toán option payoff. Sổ tiền bao gồm phí mở, phí rebalance và phí đóng.

Mỗi dòng phải thỏa: closing cash = opening cash + interest + option cash + hedge trade cash − costs. Cuối cùng, terminal cash phải bằng tổng tất cả dòng tiền. P&L đang trình bày là **hedging error bằng USD của hợp đồng mô phỏng**, không phải return của nhà đầu tư. Lý luận replication/self-financing được đối chiếu với tài liệu MIT. [S8]

Để dùng futures thật cần một adapter khác: initial/maintenance margin, variation margin, collateral interest/haircut, liquidation rule, hedge basis và cơ chế settlement. Không tái sử dụng spot cash ledger rồi chỉ thay tên tab.

## 5 Thiết kế thí nghiệm đã khóa cho bản nền tảng

- Horizon 0,25 năm lịch, ACT/365F; 256 bước trên cùng lưới thời gian.
- 256 path độc lập theo seed 94000–94255 cho mỗi mức realised volatility.
- Hedge volatility 25%; realised volatility 15%, 25%, 40%.
- Rebalance mỗi 1, 4, 16 hoặc 64 bước; đây không phải nhãn ngày giao dịch.
- Chi phí giả định 0, 5, 20 bps của notional spot; gồm entry và liquidation.
- Tổng cộng 36 ô thí nghiệm. Chi phí và lịch hedge so trên cùng các path, không bốc lại mẫu cho từng ô.
- Báo cáo mean error, standard deviation, RMSE, tail quantiles, standard error của mean, turnover và chi phí.
- Một jump giảm 20% là minh họa có chủ đích, không phải ước lượng tần suất jump.

Bản mở rộng phải thêm seed ngoài mẫu đã khóa, paired confidence intervals, borrowing spread, spread/lot constraints và dynamics có regimes/jumps. Muốn chọn policy phải quy định trước objective và risk/cost budget. Kết quả hiện tại chỉ cho phép mô tả một frontier có điều kiện.

## 6 Kết quả nền tảng đã có

26 unit tests pass. Notebook có 7 code cells đã chạy tuần tự bằng Python thường. JavaScript đối chiếu 108 giá với Python, sai khác lớn nhất khoảng 0,00001568 USD/đơn vị; tolerance 0,0001 USD. Chín kiểm tra ứng dụng bao gồm đổi loại option, giá trị thiếu, reset và expiry. Đã kiểm tra Chrome desktop local ở width1512px: control/reset, invalid input, fee, terminal ledger, table layout và tải Excel; chưa kiểm tra mobile hoặc host public.

Benchmark S=K=100, T=1, r=5%, sigma=20% cho call khoảng10,450584 USD. Monte Carlo dùng20.000 cặp antithetic; đây là40.000 terminal draws nhưng chỉ20.000 quan sát độc lập. Chẩn đoán coverage qua40replications đạt92,5%, có Wilson interval đi kèm; không yêu cầu tất cả seed luôn bao phủ analytic price.

Ở realised vol = hedge vol =25%, phí0: standard deviation của hedge error khoảng0,2409 USD khi rebalance mỗi bước và1,9671 USD khi mỗi64bước. Ở phí20bps, RMSE khoảng1,2498 USD cho mỗi bước và0,8658 USD cho mỗi4bước. Không suy ra tần suất4bước là tối ưu phổ quát. Accounting residual lớn nhất khoảng2,83×10⁻¹³ USD.

Các con số trên là **kết quả mô phỏng** đọc từ `outputs/research_results.json`, không phải quote hay performance thị trường.

### Bổ sung bản0.2: Excel độc lập và uncertainty

Workbook `outputs/P5_Options_Research_Model.xlsx` có 9 sheet: Overview, Inputs, Pricing, Tree, Hedge Ledger, Experiments, Path Data, Checks và Sources. Giá BSM, Greeks, bisection IV, tree16bước và257dòng ledger dùng công thức Excel; bảng36thí nghiệm là số nhập từ Python và được ghi nhãn riêng. Thay spot sẽ scale đường giá đã lưu; không giả vờ tái sinh stochastic path. Thời hạn định giá mặc định1năm, horizon hedge0,25năm và hai mức rate được tách rõ ở Inputs.

Ba bộ input gồm call, put và call có dividend yield/borrowing spread cho21đối chiếu pricing/Greeks/tree,3.084đối chiếu cash/holding/cost/net wealth. Phí tăng phải làm giảm cash cuối trên cùng path. File đã xuất được đọc kiểm tra và tái tính bằng LibreOffice; chưa kiểm tra Microsoft Excel native. Tolerance tuyệt đối1e-7USD/đơn vị. `scripts/verify_workbook.py` và các file `outputs/excel_*checks.json` lưu bằng chứng.

Extension khóa riêng trong `configs/holdout.json`, trước khi chạy block seed304000–304255; không đổi kết quả baseline seed94000–94255. Đây là256seed mô phỏng mới, **không phải market out-of-sample hay pre-registration độc lập**. Bốn dynamics: vol25%cố định;15%→40%;40%→15%; và vol25%kèm jump−20%ở midpoint. Mỗi dynamics có4tần suất×2mức phí=32cells. Cùng shock Gaussian theo seed giữa các dynamics; cùng exact path giữa các policy/cost.

So sánh cố định mỗi4bước trừ mỗi1bước dùng2.000paired bootstrap resamples trên path index. Ở phí20bps, RMSE difference cho cả4dynamics đều âm với95%interval nằm dưới0. Ở phí5bps, các interval constant/regime vẫn chứa0; conditional jump stress có interval âm. Các interval là pointwise, không điều chỉnh multiple comparisons và không chọn policy. Jump được áp đặt trên mọi stress path, không ước lượng xác suất/tần suất jump. Lower-tail mean là mô tả mẫu256paths, không phải VaR/ES thị trường đã calibrated. Accounting residual extension lớn nhất khoảng2,75e-13USD.

## 7 Dữ liệu thị trường và quyền công bố

Tài liệu API công khai giúp xác định schema, không đồng nghĩa có lịch sử bid/ask thực thi hoặc quyền tái công bố. Điều4.6 trong bản Terms of Service Deribit được tìm thấy giới hạn việc sử dụng/công bố market data và derived data ngoài mục đích cá nhân. Vì vậy không đưa dữ liệu đó vào gói công khai khi chưa có căn cứ cho phép. [S3–S5]

Không mua dữ liệu, tạo tài khoản giao dịch hoặc gửi yêu cầu đến sàn trong giai đoạn này. Hướng tiếp tục là kiểm tra quyền sử dụng một nguồn phù hợp, hoặc giữ observed analysis riêng và chỉ công bố synthetic replication. SPX có thể thay thế khi có dữ liệu và convention phù hợp, nhưng dữ liệu lịch sử/underlying index cũng có yêu cầu truy cập riêng. [S6–S7]

## 8 Đầu ra và tiêu chuẩn hoàn tất

| Chặng | Đầu ra | Điều kiện qua chặng | Trạng thái |
| --- | --- | --- | --- |
| A Thiết kế | Charter, lựa chọn hợp đồng, hypotheses, source register | Quy ước và giới hạn claim rõ | Đã viết |
| B Numerical foundation | Pricing, IV, Greeks, tree, MC, tests | Math/boundary/convergence kiểm tra được | Đã chạy bản0.1 |
| C Hedge foundation | Ledger, paired sweeps, explorer, notebook | Cash reconciliation và phí đúng | Đã chạy bản0.1 |
| D Independent Excel | Pricing/Greeks, small tree, một path có cash ledger, checks | Tính độc lập và input perturbation khớp Python | Đã có 9 sheet; đối chiếu 3 bộ input và tái tính chéo |
| E Market module | Registry xác nhận, quote QC, IV coverage và source dates | Dữ liệu/rights được giải quyết, không tráo mark với executable quotes | Chưa nhận dữ liệu |
| F Model risk | Regimes/jumps, paired uncertainty, locked challenger | OOS, parameter stability và compute cost có bằng chứng | Đã có seed riêng, regimes và paired intervals; chưa có market OOS/challenger |
| G Professional release | Dashboard kiểm tra thật, technical report, validation note, public repo | Tất cả claim đúng phạm vi, output tái lập và review render | Đã có report9trang và desktop QA; public release chờ xác nhận, market gates còn mở |

Excel bản0.2 có 9 sheet, gộp Greeks/IV vào Pricing và giữ Experiments dưới nhãn imported. Kiến trúc đề xuất theo nghiệp vụ: Overview; Inputs and Contract; Pricing; Small Tree; Greeks and IV; Hedge Ledger; Cost and Risk; Model Comparison; Checks; Sources. Thêm tab khi có công việc riêng, không tạo19tab chỉ để đủ danh sách. MC lớn và surface calibration được nhập dưới nhãn kết quả mô phỏng/imported; analytical price, Greeks, tree nhỏ và một ledger phải tính độc lập bằng công thức.

Dashboard hoàn chỉnh cần Pricing, Greeks, Chain Quality, Smile/Term Structure, Hedge Replay, Cost/Risk và Data/Validation. Bản0.1 đã có calculator độc lập, bảng36thí nghiệm và replay ledger, chưa có observed smile hoặc validated surface.

Bản0.3 có technical report9trang cho synthetic module, với2figure được dựng từ kết quả đã lưu; đã rà render cả9trang. Report thị trường cuối cùng chỉ viết sau evidence gate, không kéo dài bằng cách lặp code/notebook. Public GitHub chưa được tạo: automatic approval review yêu cầu xác nhận rõ visibility public. Gói cụ thể được liệt kê trong `docs/PUBLICATION_REVIEW.md`.

## 9 Nguồn đã xem

- [S1] Deribit linear contract specifications: https://support.deribit.com/hc/en-us/articles/31424932728093-Linear-USDC-Options
- [S2] Deribit delivery-process change: https://insights.deribit.com/exchange-updates/change-to-option-delivery-process/
- [S3] Instrument API: https://docs.deribit.com/api-reference/market-data/public-get_instruments
- [S4] Order-book API: https://docs.deribit.com/api-reference/market-data/public-get_order_book
- [S5] Terms of Service, Article4.6: https://statics.deribit.com/files/TermsofServiceDeribit.pdf
- [S6] Cboe SPX product page: https://www.cboe.com/tradable-products/sp-500/spx-options/
- [S7] Cboe historical quotes product: https://datashop.cboe.com/option-quote-intervals
- [S8] MIT15.450, Leonid Kogan, lecture2, option replication: https://www.ocw.mit.edu/courses/15-450-analytics-of-finance-fall-2010/0d1260b891a96241316d883d4f5bfaec_MIT15_450F10_lec02.pdf

Nguồn được xem ngày26/11/2026. `configs/sources.json` ghi use/locator. Bản này là khởi tạo nghiên cứu có code chạy, không phải tuyên bố P5 đã đạt professional release.
