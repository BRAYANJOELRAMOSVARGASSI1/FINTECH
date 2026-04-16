/**
 * api.ts — Cliente HTTP para comunicarse con el backend FastAPI.
 *
 * Centraliza todas las llamadas al backend con tipado estricto,
 * manejo de errores consistente y configuración base.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Types — Respuestas del backend
// ---------------------------------------------------------------------------

export interface RateConversionResponse {
  original_nominal_rate: number;
  compounding: string;
  effective_annual_rate: number;
  effective_annual_rate_pct: number;
  periodic_rate: number;
  explanation: string;
}

export interface RateComparisonItem {
  rank: number;
  label: string;
  nominal_rate: number;
  compounding: string;
  effective_annual_rate: number;
  effective_annual_rate_pct: number;
}

export interface RateComparisonResponse {
  perspective: string;
  items: RateComparisonItem[];
  cheapest_label: string;
  most_expensive_label: string;
  spread_bps: number;
  recommendation: string;
}

export interface NPVResponse {
  npv: number;
  npv_formatted: string;
  discount_rate: number;
  periods: number;
  decision: string;
  present_values: number[];
  explanation: string;
}

export interface IRRResponse {
  irr: number | null;
  irr_pct: number | null;
  converged: boolean;
  hurdle_rate: number | null;
  decision: string | null;
  explanation: string;
}

export interface PaybackResponse {
  simple_payback: number | null;
  discounted_payback: number | null;
  discount_rate: number;
  cumulative_flows: number[];
  cumulative_pv_flows: number[];
}

export interface ProfitabilityIndexResponse {
  pi: number;
  decision: string;
}

export interface FullValuationResponse {
  npv: NPVResponse;
  irr: IRRResponse;
  payback: PaybackResponse;
  profitability_index: ProfitabilityIndexResponse;
  cash_flows: number[];
  discount_rate: number;
  overall_recommendation: string;
}

export interface AmortizationRow {
  period: number;
  payment: number;
  interest: number;
  principal: number;
  balance: number;
}

export interface AmortizationTableResponse {
  system: string;
  principal_amount: number;
  annual_rate: number;
  annual_rate_pct: number;
  periodic_rate: number;
  total_periods: number;
  total_paid: number;
  total_interest: number;
  interest_ratio: number;
  first_payment: number;
  last_payment: number;
  rows: AmortizationRow[];
}

export interface AmortizationCompareResponse {
  french: AmortizationTableResponse;
  german: AmortizationTableResponse;
  american: AmortizationTableResponse;
  cheapest_system: string;
  recommendation: string;
}

export interface CapexAnalysis {
  cash_flows: number[];
  depreciation_schedule: number[];
  tax_shields: number[];
  maintenance_costs: number[];
  salvage_net_proceeds: number;
  total_cost_nominal: number;
  npv_cost: number;
  year_labels: string[];
}

export interface OpexAnalysis {
  cash_flows: number[];
  annual_costs_nominal: number[];
  tax_savings: number[];
  total_cost_nominal: number;
  npv_cost: number;
  year_labels: string[];
}

export interface SensitivityPoint {
  variable_name: string;
  variation_pct: number;
  capex_npv: number;
  opex_npv: number;
  recommendation: string;
}

export interface CapexVsOpexResponse {
  capex: CapexAnalysis;
  opex: OpexAnalysis;
  npv_advantage: number;
  recommendation: string;
  explanation: string;
  wacc_used: number;
  sensitivity: SensitivityPoint[];
}

export interface MonteCarloStats {
  mean: number;
  median: number;
  std_dev: number;
  min_value: number;
  max_value: number;
  percentile_5: number;
  percentile_10: number;
  percentile_25: number;
  percentile_75: number;
  percentile_90: number;
  percentile_95: number;
  probability_positive: number;
  probability_negative: number;
  skewness: number;
  kurtosis: number;
}

export interface MonteCarloResponse {
  iterations: number;
  stats: MonteCarloStats;
  histogram_bins: number[];
  histogram_counts: number[];
  variables_stressed: string[];
  confidence_interval_90: number[];
  confidence_interval_95: number[];
  decision: string;
  risk_assessment: string;
}

export interface ConvertibleNoteResponse {
  investment: number;
  cap: number;
  discount: number;
  next_round_valuation: number;
  effective_valuation: number;
  investor_ownership_pct: number;
  founder_retained_pct: number;
  conversion_method: string;
}

export interface TerminalValueResponse {
  last_metric: number;
  multiple: number;
  terminal_value: number;
  discounted_tv: number;
  discount_rate: number;
  years: number;
}

export interface CashCycleResponse {
  dso: number;
  dio: number;
  dpo: number;
  ccc_days: number;
  interpretation: string;
  daily_sales: number;
  capital_tied_up: number;
}

export interface RunwayResponse {
  initial_cash: number;
  monthly_revenue: number;
  monthly_burn: number;
  net_burn: number;
  runway_months: number;
  death_valley_date_months: number;
  survival_assessment: string;
}

// ---------------------------------------------------------------------------
// HTTP Client
// ---------------------------------------------------------------------------

class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(detail);
    this.name = "ApiError";
  }
}

async function post<T>(endpoint: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Error desconocido" }));
    const detail = error.detail || "Error del servidor";
    const message = typeof detail === "string" ? detail : JSON.stringify(detail);
    throw new ApiError(res.status, message);
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

export const api = {
  rates: {
    convert: (nominal_rate: number, compounding: string) =>
      post<RateConversionResponse>("/api/v1/rates/convert", { nominal_rate, compounding }),

    compare: (rates: { label: string; nominal_rate: number; compounding: string }[], perspective = "borrower") =>
      post<RateComparisonResponse>("/api/v1/rates/compare", { rates, perspective }),

    fisher: (nominal_rate: number, inflation_rate: number) =>
      post<{ nominal_rate: number; inflation_rate: number; real_rate: number; real_rate_pct: number; explanation: string }>(
        "/api/v1/rates/fisher", { nominal_rate, inflation_rate }
      ),

    wacc: (equity: number, debt: number, cost_of_equity: number, cost_of_debt: number, tax_rate: number) =>
      post<{ wacc: number; wacc_pct: number; weight_equity: number; weight_debt: number; explanation: string }>(
        "/api/v1/rates/wacc", { equity, debt, cost_of_equity, cost_of_debt, tax_rate }
      ),
  },

  valuation: {
    npv: (cash_flows: number[], discount_rate: number) =>
      post<NPVResponse>("/api/v1/valuation/npv", { cash_flows, discount_rate }),

    irr: (cash_flows: number[], hurdle_rate?: number) =>
      post<IRRResponse>("/api/v1/valuation/irr", { cash_flows, hurdle_rate }),

    full: (cash_flows: number[], discount_rate: number, hurdle_rate?: number) =>
      post<FullValuationResponse>("/api/v1/valuation/full", { cash_flows, discount_rate, hurdle_rate }),
  },

  amortization: {
    schedule: (principal: number, annual_rate: number, total_periods: number, periods_per_year: number, system: string) =>
      post<AmortizationTableResponse>("/api/v1/amortization/schedule", {
        principal, annual_rate, total_periods, periods_per_year, system,
      }),

    compare: (principal: number, annual_rate: number, total_periods: number, periods_per_year: number) =>
      post<AmortizationCompareResponse>("/api/v1/amortization/compare", {
        principal, annual_rate, total_periods, periods_per_year,
      }),
  },

  analysis: {
    capexVsOpex: (data: {
      capex: { initial_investment: number; useful_life_years: number; salvage_value: number; annual_maintenance: number; tax_rate: number; depreciation_method: string; maintenance_growth_rate: number };
      opex: { annual_cost: number; contract_years: number; tax_rate: number; inflation_rate: number; setup_cost: number };
      wacc: number;
      run_sensitivity: boolean;
    }) => post<CapexVsOpexResponse>("/api/v1/analysis/capex-vs-opex", data),

    monteCarlo: (data: {
      cash_flows: number[];
      discount_rate: number;
      variables: { name: string; base_value: number; std_dev: number; min_value?: number; max_value?: number; distribution: string }[];
      cash_flow_impacts: Record<string, number[]>;
      iterations: number;
      seed?: number;
    }) => post<MonteCarloResponse>("/api/v1/analysis/montecarlo", data),
  },

  startup: {
    convertibleNote: (data: { investment: number; valuation_cap: number; discount_rate: number; next_round_pre_money: number }) =>
      post<ConvertibleNoteResponse>("/api/v1/startup/convertible-note", data),

    terminalValue: (data: { last_year_metric: number; multiple: number; discount_rate: number; years: number }) =>
      post<TerminalValueResponse>("/api/v1/startup/terminal-value", data),

    cashCycle: (data: { annual_revenue: number; accounts_receivable: number; annual_cogs: number; inventory: number; accounts_payable: number; days_in_year?: number }) =>
      post<CashCycleResponse>("/api/v1/startup/working-capital/ccc", data),

    runway: (data: { initial_cash: number; monthly_revenue: number; monthly_fixed_costs: number; monthly_variable_costs?: number; revenue_growth_rate?: number }) =>
      post<RunwayResponse>("/api/v1/startup/runway", data),
  },
};
