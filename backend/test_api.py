"""Quick API integration test."""
import httpx

BASE = "http://localhost:8000"

# Test 1: Rate Conversion
print("=" * 60)
print("TEST 1: Rate Conversion (18% nominal quarterly -> TEA)")
r = httpx.post(f"{BASE}/api/v1/rates/convert", json={
    "nominal_rate": 0.18,
    "compounding": "quarterly"
})
data = r.json()
print(f"  TEA: {data['effective_annual_rate_pct']}%")
print(f"  Status: PASS" if r.status_code == 200 else "  Status: FAIL")

# Test 2: Rate Comparison
print("\nTEST 2: Rate Comparison (3 banks, same 18% nominal)")
r = httpx.post(f"{BASE}/api/v1/rates/compare", json={
    "rates": [
        {"label": "Banco A", "nominal_rate": 0.18, "compounding": "annual"},
        {"label": "Banco B", "nominal_rate": 0.18, "compounding": "quarterly"},
        {"label": "Banco C", "nominal_rate": 0.175, "compounding": "monthly"},
    ],
    "perspective": "borrower"
})
data = r.json()
print(f"  Cheapest: {data['cheapest_label']}")
print(f"  Spread: {data['spread_bps']} bps")
print(f"  Status: PASS" if r.status_code == 200 else "  Status: FAIL")

# Test 3: CAPEX vs OPEX
print("\nTEST 3: CAPEX vs OPEX Analysis")
r = httpx.post(f"{BASE}/api/v1/analysis/capex-vs-opex", json={
    "capex": {
        "initial_investment": 500000,
        "useful_life_years": 5,
        "salvage_value": 50000,
        "annual_maintenance": 20000,
        "tax_rate": 0.30,
        "depreciation_method": "straight_line"
    },
    "opex": {
        "annual_cost": 120000,
        "contract_years": 5,
        "tax_rate": 0.30,
        "inflation_rate": 0.05
    },
    "wacc": 0.10
})
data = r.json()
print(f"  Recommendation: {data['recommendation']}")
print(f"  CAPEX NPV: ${data['capex']['npv_cost']:,.2f}")
print(f"  OPEX NPV: ${data['opex']['npv_cost']:,.2f}")
print(f"  Sensitivity points: {len(data['sensitivity'])}")
print(f"  Status: PASS" if r.status_code == 200 else "  Status: FAIL")

# Test 4: Full Valuation
print("\nTEST 4: Full Project Valuation")
r = httpx.post(f"{BASE}/api/v1/valuation/full", json={
    "cash_flows": [-100000, 30000, 40000, 50000, 30000],
    "discount_rate": 0.10
})
data = r.json()
print(f"  NPV: ${data['npv']['npv']:,.2f} -> {data['npv']['decision']}")
print(f"  IRR: {data['irr']['irr_pct']}%")
print(f"  Payback: {data['payback']['simple_payback']} years")
print(f"  PI: {data['profitability_index']['pi']}")
print(f"  Overall: {data['overall_recommendation']}")
print(f"  Status: PASS" if r.status_code == 200 else "  Status: FAIL")

# Test 5: Amortization Comparison
print("\nTEST 5: Amortization Systems Comparison ($100k, 12%, 24 months)")
r = httpx.post(f"{BASE}/api/v1/amortization/compare", json={
    "principal": 100000,
    "annual_rate": 0.12,
    "total_periods": 24,
    "periods_per_year": 12
})
data = r.json()
print(f"  French total interest: ${data['french']['total_interest']:,.2f}")
print(f"  German total interest: ${data['german']['total_interest']:,.2f}")
print(f"  American total interest: ${data['american']['total_interest']:,.2f}")
print(f"  Cheapest: {data['cheapest_system']}")
print(f"  Status: PASS" if r.status_code == 200 else "  Status: FAIL")

# Test 6: Monte Carlo
print("\nTEST 6: Monte Carlo Simulation (10,000 iterations)")
r = httpx.post(f"{BASE}/api/v1/analysis/montecarlo", json={
    "cash_flows": [-100000, 30000, 35000, 40000, 45000, 50000],
    "discount_rate": 0.10,
    "variables": [
        {"name": "revenue", "base_value": 1.0, "std_dev": 0.15, "min_value": 0.5, "max_value": 1.5},
        {"name": "costs", "base_value": 1.0, "std_dev": 0.10, "min_value": 0.7, "max_value": 1.3},
    ],
    "cash_flow_impacts": {
        "revenue": [1, 2, 3, 4, 5],
        "costs": [1, 2, 3, 4, 5]
    },
    "iterations": 10000,
    "seed": 42
})
data = r.json()
print(f"  P(NPV > 0): {data['stats']['probability_positive']*100:.1f}%")
print(f"  Mean NPV: ${data['stats']['mean']:,.2f}")
print(f"  P5 (worst reasonable): ${data['stats']['percentile_5']:,.2f}")
print(f"  P95 (best reasonable): ${data['stats']['percentile_95']:,.2f}")
print(f"  Decision: {data['decision']}")
print(f"  Status: PASS" if r.status_code == 200 else "  Status: FAIL")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED")
