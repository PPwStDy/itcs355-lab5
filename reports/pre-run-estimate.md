# Lab 5 pre-run estimate

Recorded on 2026-10-16 before any Lab 5 managed job or endpoint run.

- Primary: existing Azure ML workspace in East Asia; create isolated Lab 5 compute and serving resources.
- Exact retail SKU: Standard_DS2_v2, Linux on-demand, $0.214/hour.
- Exchange: 33.540328 THB/USD, ECB reference dated 2026-10-15.
- Training allowance: 1 VM-hour = 7.18 THB.
- Serving allowance: 2 VM-hours = 14.36 THB.
- Shared storage, image build, pipeline overhead, monitoring and a small LLM exercise: 10 THB planning allowance; not a verified component rate or measured LLM bill.
- Forecast with 25% contingency: (21.53 + 10) × 1.25 = **39.42 THB**.
- Requested hard additional spending ceiling: 150 THB; run only if it also fits the remaining 800 THB term allowance.
- Prior tagged course billing query: $6.95145721947742 through the captured date, approximately 233.15 THB at this reference rate; 566.85 THB of the course allowance remains before late billing.

This forecast depends on the runtime bounds, shared registry reuse and no new persistent LLM capacity. Unverified component allowances must be replaced with the actual classified bill. No actual Lab 5 spend or provider token count is claimed. Capture the commit hash of this file before executing Task 1.

Sources: [Azure retail API](https://prices.azure.com/api/retail/prices), [ECB exchange reference](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml); raw matched retail items and dated exchange data are retained in reports/evidence/planning-prices.json. Azure Cost Management was queried for course=itcs355; pagination was empty.
