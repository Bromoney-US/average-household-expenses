#!/usr/bin/env python3
"""Rebuild bromoney_ces_cpi_crosswalk_2023-2024.csv from frozen inputs.

Reproduces the CES-CPI comparison behind /en/blog/average-household-expenses.

Inputs (both in this directory, frozen 2026-08-20):
  bls_api_request.json           - the exact POST body sent to the BLS API
  bls_api_response_2026-08-20.json - the exact response received

CES figures below are typed from the BLS Consumer Expenditures--2024 release
(USDL-25-1586, published 2025-12-19), table A:
  https://www.bls.gov/news.release/archives/cesan_12192025.pdf

Run:  python build_crosswalk.py
Verify: the output must match ../bromoney_ces_cpi_crosswalk_2023-2024.csv byte for byte.

To refresh against the live API instead of the frozen copy:
  curl -X POST https://api.bls.gov/publicAPI/v1/timeseries/data/ \
       -H "Content-Type: application/json" -d @bls_api_request.json
No registration key is required for the v1 endpoint (25 series, 10 years, 25 queries/day).
"""
import csv
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESPONSE = os.path.join(HERE, "bls_api_response_2026-08-20.json")
OUT = os.path.join(HERE, "crosswalk_rebuilt.csv")

# CPI-U, US city average, not seasonally adjusted. Series ID -> label used here.
SERIES = {
    "CUUR0000SAF112": "Meats, poultry, fish, and eggs",
    "CUUR0000SEFJ": "Dairy and related products",
    "CUUR0000SAF111": "Cereals and bakery products",
    "CUUR0000SAF11": "Food at home",
    "CUUR0000SEFV": "Food away from home",
    "CUUR0000SETE": "Motor vehicle insurance",
    "CUUR0000SETB01": "Gasoline (all types)",
    "CUUR0000SEHA": "Rent of primary residence",
    "CUUR0000SEHC": "Owners' equivalent rent",
    "CUUR0000SAA": "Apparel",
    "CUUR0000SEMF01": "Prescription drugs",
    "CUUR0000SAH1": "Shelter",
}

# CES table A: label, 2023 $, 2024 $, published % change, BLS significance flag,
# CPI series to pair with, crosswalk quality note.
CES = [
    ("Meats, poultry, fish and eggs", 1164, 1414, 21.5, "yes", "CUUR0000SAF112", "direct"),
    ("Drugs", 591, 658, 11.3, "no", "CUUR0000SEMF01",
     "partial: CE Drugs includes nonprescription"),
    ("Dairy products", 602, 631, 4.8, "yes", "CUUR0000SEFJ", "direct"),
    ("Gasoline", 2449, 2411, -1.6, "no", "CUUR0000SETB01", "direct"),
    ("Food at home", 6053, 6224, 2.8, "no", "CUUR0000SAF11", "direct"),
    ("Owned dwellings", 8699, 9310, 7.0, "yes", "CUUR0000SEHC",
     "caution: CE records reported owned-dwelling expenditures but excludes mortgage "
     "principal; CPI OER is imputed"),
    ("Rented dwellings", 5370, 5660, 5.4, "yes", "CUUR0000SEHA", "close"),
    ("Apparel and services", 2041, 2001, -2.0, "no", "CUUR0000SAA",
     "partial: CE line includes services, CPI Apparel is goods only"),
    ("Food away from home", 3933, 3945, 0.3, "no", "CUUR0000SEFV", "direct"),
    ("Vehicle insurance", 1775, 1993, 12.3, "yes", "CUUR0000SETE", "direct"),
    ("Cereals and bakery products", 830, 779, -6.1, "yes", "CUUR0000SAF111", "direct"),
    ("Housing (whole component)", 25436, 26266, 3.3, "yes", "CUUR0000SAH1",
     "NOT COMPARABLE: CE Housing includes utilities, household operations and furnishings; "
     "CPI Shelter does not. Listed for transparency, excluded from analysis."),
]


def annual_averages(path):
    """Extract the M13 (twelve-month average) index level per series per year."""
    doc = json.load(io.open(path, encoding="utf-8"))
    if doc.get("status") != "REQUEST_SUCCEEDED":
        sys.exit("BLS response status: %s" % doc.get("status"))
    out = {}
    for series in doc["Results"]["series"]:
        by_year = {}
        for row in series["data"]:
            if row["period"] == "M13":          # M13 == annual average
                by_year[row["year"]] = float(row["value"])
        out[series["seriesID"]] = by_year
    return out


def main():
    cpi = annual_averages(RESPONSE)
    rows = []
    for label, y23, y24, spend_pct, significant, sid, quality in CES:
        idx = cpi[sid]
        i23, i24 = idx["2023"], idx["2024"]
        price_pct = (i24 - i23) / i23 * 100

        # sanity: the typed CES change must agree with the typed dollar figures
        recomputed = (y24 - y23) / y23 * 100
        if abs(recomputed - spend_pct) > 0.1:
            sys.exit("CES mismatch for %s: %.2f vs published %.1f"
                     % (label, recomputed, spend_pct))

        if quality.startswith("NOT COMPARABLE"):
            residual = ""                        # deliberately not computed
        else:
            residual = round(((1 + spend_pct / 100) / (1 + price_pct / 100) - 1) * 100, 1)

        rows.append({
            "ces_category": label,
            "ces_2023_usd": y23,
            "ces_2024_usd": y24,
            "ces_change_pct": spend_pct,
            "ces_significant_95": significant,
            "cpi_counterpart": SERIES[sid],
            "cpi_series_id": sid,
            "cpi_2023_index": round(i23, 3),
            "cpi_2024_index": round(i24, 3),
            "cpi_change_pct": round(price_pct, 2),
            "crosswalk_quality": quality,
            "price_adjusted_residual_pct": residual,
        })

    with io.open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d rows)" % (OUT, len(rows)))
    print("\nexpected spot checks:")
    for want, label in ((-4.6, "Vehicle insurance"), (0.3, "Rented dwellings"),
                        (-3.6, "Food away from home"), (18.9, "Meats, poultry, fish and eggs")):
        got = next(r["price_adjusted_residual_pct"] for r in rows if r["ces_category"] == label)
        status = "OK " if abs(got - want) < 0.05 else "FAIL"
        print("  %s %-32s residual %+.1f (expected %+.1f)" % (status, label, got, want))


if __name__ == "__main__":
    main()
