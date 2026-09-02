# Reproducibility package — CES↔CPI crosswalk, 2023–2024

Reproduces the one table that needed original computation in *[What Average Household Expenses Show About Price Pressure — and What They Can't](https://bromoney.com/en/blog/average-household-expenses)*: the comparison of household **spending** (BLS Consumer Expenditure Survey) against **prices** (BLS Consumer Price Index) over the same two calendar years. It also rebuilds the three published charts.

**Scope, stated plainly.** This package reproduces the crosswalk and the charts. The article's other tables — the full category breakdown, the SHED response figures, the BEA saving rate, the documented limits — are transcribed from published releases rather than computed here. Their provenance is traceable through `source_manifest.csv` and `evidence_ledger_2026-08-20.csv`, but that is an audit trail, not an automated pipeline. Calling this a reproducibility package for the whole article would overstate it.

## Run it

```bash
python build_crosswalk.py       # rebuilds the crosswalk CSV
python build_charts.py          # rebuilds all seven chart files
python extract_visible_text.py  # strips JSON-LD and comments before any text check
```

No dependencies beyond the standard library for the crosswalk; the charts need `matplotlib`.

`build_crosswalk.py` prints four spot checks and exits non-zero if the transcribed CES dollar figures disagree with the published percent changes. Its output should be byte-identical to the published `../bromoney_ces_cpi_crosswalk_2023-2024.csv`.

Chart output is deterministic: PNG and SVG are byte-identical between runs, because the SVG date metadata is suppressed and the element-id hash salt is fixed.

## What is in here

| File | What it is |
|---|---|
| `build_crosswalk.py` | The crosswalk computation. CES figures transcribed from the release; CPI read from the frozen API response |
| `build_charts.py` | The three charts, in 16:9 and 4:3, plus 1:1 for the flagship. Each aspect has its own margins |
| `chart_inputs.csv` | Inputs for the quintile and data-age charts, with a note and source per row |
| `extract_visible_text.py` | Strips HTML comments and `<script>` blocks so text checks measure the article, not its metadata. Self-tests that the JSON-LD MIME type is gone |
| `bls_api_request.json` | The exact POST body sent to the BLS API |
| `bls_api_response_2026-08-20.json` | The exact response received, frozen |
| `crosswalk_rebuilt.csv` | Output of `build_crosswalk.py` |
| `evidence_ledger_2026-08-20.csv` | Claim-by-claim audit trail for every figure in the article — 64 rows |
| `source_manifest.csv` | Every source: URL, retrieval date, byte size, SHA-256 |
| `../CITATION.cff` | Citation metadata. GitHub renders a **Cite this repository** button from it |
| `../LICENSE.md` | MIT for the code, CC BY 4.0 for data and charts |
| `../charts/` | Seven SVG and seven PNG, ready to republish |

Raw PDFs are not committed. `source_manifest.csv` carries a SHA-256 for each, so anyone can download from the URL and confirm they have the same bytes we did.

## Method

**Spending.** BLS Consumer Expenditure Survey 2024, table A, as published. No adjustment.

**Prices.** CPI-U twelve-month averages (period `M13`), US city average, not seasonally adjusted, for 2023 and 2024. Series IDs are in the output. Retrieved from the BLS public data API v1, which needs no registration key (25 series, 10 years, 25 queries per day).

**Residual.** `(1 + spending change) ÷ (1 + price change) − 1`, per consumer unit.

**Data age**, used in the third chart, is measured one way for all four sources: from the end of the period the data covers to 20 August 2026 — not from the release date. The two are different, and mixing them is the mistake the chart exists to prevent.

## What the residual is not

It is a deflation, not an identification. It does **not** measure quantity — not units bought, not restaurant visits, not square footage, not insurance coverage.

The residual absorbs, without separating:

- changes in household composition
- the share of households that bought the category at all
- trading up or down within a category
- the number of vehicles or tenants per unit
- sample geography
- differences between the CPI-U and CES populations
- CES sampling and non-sampling error, including questionnaire changes
- the two surveys' differing category weights

It carries no confidence interval and is not tested for significance.

Read a residual as a place to ask a question, not as an answer. Phrase findings as *consistent with*, never *because* or *implies N fewer*.

## Crosswalk quality

| Label | Meaning |
|---|---|
| `direct` | Category definitions align closely |
| `close` | Minor scope difference, usable |
| `caution` | A known conceptual mismatch — read with the note |
| `partial` | One side is broader; directional only |
| `NOT COMPARABLE` | Included for transparency, excluded from any conclusion |

One row is `NOT COMPARABLE`: CES **Housing** against CPI **Shelter**. The CES component also carries utilities, household operations and furnishings. It is present so readers can see the pairing was considered and rejected, not quietly dropped.

## Significance

Asterisks on CES changes are BLS's own, at the 95 percent level, tested on dollar differences using balanced repeated replication. Where a change lacks an asterisk, the correct reading is that the estimate was not statistically distinguishable from zero at that level — not that the change was zero or small. A real effect may exist; the survey is not precise enough to show it.

## Access note

On 2026-08-20, `bls.gov` returned HTTP 403 to a default `curl` request and to a plain browser User-Agent, and returned 200 to a User-Agent carrying a contact address. That is the behaviour we observed on that date. We are not aware of a published BLS policy document stating it, so treat it as an observation rather than a rule.

## Citation

> Bromoney. *CES–CPI Household Spending Crosswalk, 2023–2024*, version 1.0.0. https://bromoney.com/en/data/ces-cpi-household-spending-crosswalk-2023-2024

Add the release date and DOI once the first tagged release is archived. `../CITATION.cff` carries the machine-readable form.

The underlying figures in this package come from BLS. The article draws on BEA and Federal Reserve releases too, but nothing computed here does.

Figures were checked against source releases on 2026-08-20. Sources update on their own schedules; see the article's source table for the next release dates.
