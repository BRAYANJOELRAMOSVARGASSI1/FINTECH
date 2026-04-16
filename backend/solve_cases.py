from app.core.valuation import net_present_value, internal_rate_of_return
from app.core.venture_capital import convertible_note_conversion, terminal_value_multiple
from app.core.working_capital import cash_conversion_cycle
from app.core.cash_management import calculate_startup_runway
from app.core.rates import compare_simple_vs_compound
from app.core.amortization import revolving_credit_facility

def solve():
    print("--- EMPEZANDO RESOLUCIÓN ---")
    
    # S1: Bootstrapping
    print("\n[S1] Bootstrapping - Runway")
    r1 = calculate_startup_runway(initial_cash=150000, monthly_revenue=30000, monthly_fixed_costs=45000)
    print(f"Base: {r1.runway_months} meses. Muerte: {r1.survival_assessment}")
    
    # S3: Nota Convertible
    print("\n[S3] Nota Convertible - VC")
    r3 = convertible_note_conversion(investment=200000, valuation_cap=2000000, discount_rate=0.20, next_round_pre_money=2500000)
    print(f"Método usado: {r3.conversion_method}. Fundador retiene: {r3.founder_retained_pct*100}%")
    
    # S4: Working Capital
    print("\n[S4] Ciclo de Caja - E-commerce")
    # Ventas 120k mensual -> 1.44M anual. Cuentas por cobrar = 60 dias (2 meses = 240k)
    # Asumamos margen 50%, COGS = 720k anual. Cuentas por pagar 30 dias (1 mes = 60k). Inventario (Asumimos 1 mes = 60k)
    r4 = cash_conversion_cycle(annual_revenue=1440000, accounts_receivable=240000, annual_cogs=720000, inventory=60000, accounts_payable=60000)
    print(f"Ciclo Días: {r4.ccc_days}. Capital inmovilizado: Bs. {r4.capital_tied_up}")

    # S8: Simple vs Compuesto
    print("\n[S8] Simple vs Compuesto")
    r8 = compare_simple_vs_compound(principal=100000, annual_rate=0.15, years=2)
    print(f"Oferta 1 (Simple 15%): {r8['simple_future_value']}")
    r8_2 = compare_simple_vs_compound(principal=100000, annual_rate=0.11, years=2)
    print(f"Oferta 2 (Compues 11%): {r8_2['compound_future_value']}")

solve()
