"use client";

import React, { useState } from "react";
import AppShell from "@/components/AppShell";
import { api, RunwayResponse } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

export default function BootstrappingPage() {
  const [initialCash, setInitialCash] = useState("150000");
  const [monthlyRevenue, setMonthlyRevenue] = useState("30000");
  const [monthlyFixedCosts, setMonthlyFixedCosts] = useState("45000");
  const [monthlyVariableCosts, setMonthlyVariableCosts] = useState("0");
  const [revenueGrowthRate, setRevenueGrowthRate] = useState("0");

  const [result, setResult] = useState<RunwayResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.startup.runway({
        initial_cash: parseFloat(initialCash),
        monthly_revenue: parseFloat(monthlyRevenue),
        monthly_fixed_costs: parseFloat(monthlyFixedCosts),
        monthly_variable_costs: parseFloat(monthlyVariableCosts),
        revenue_growth_rate: parseFloat(revenueGrowthRate) / 100,
      });
      setResult(res);
    } catch (e: any) {
      setError(e.detail || e.message || "Error al calcular el runway.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="page-header">
        <h2>Bootstrapping & Runway</h2>
        <p>Calcula el "Death Valley", la pista de aterrizaje de efectivo de tu startup y tu Burn Rate.</p>
      </div>

      <div className="grid-2 animate-in" style={{ marginBottom: 24 }}>
        <div className="card">
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: "var(--accent-blue)" }}>Datos de Caja</h3>
          <div className="grid-form">
            <div className="form-group">
              <label className="form-label">Caja Inicial (Liquidez en Banco)</label>
              <input className="form-input" type="number" value={initialCash} onChange={(e) => setInitialCash(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Ingresos Mensuales Promedio</label>
              <input className="form-input" type="number" value={monthlyRevenue} onChange={(e) => setMonthlyRevenue(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Costo Fijo Mensual (Operaciones)</label>
              <input className="form-input" type="number" value={monthlyFixedCosts} onChange={(e) => setMonthlyFixedCosts(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Costo Variable Mensual</label>
              <input className="form-input" type="number" value={monthlyVariableCosts} onChange={(e) => setMonthlyVariableCosts(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Crecimiento Mensual Ingresos (%)</label>
              <input className="form-input" type="number" value={revenueGrowthRate} onChange={(e) => setRevenueGrowthRate(e.target.value)} />
            </div>
          </div>
          
          <button className="btn btn-primary" onClick={handleAnalyze} disabled={loading} style={{ marginTop: 24, width: "100%" }}>
            {loading ? <span className="loading-spinner" /> : "Proyectar Supervivencia"}
          </button>
          
          {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}
        </div>

        <div>
          {result && (
            <div className="card animate-in">
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: "var(--text-primary)" }}>Reporte de Tesorería</h3>
              
              <div className="grid-kpi" style={{ gridTemplateColumns: '1fr', gap: 16, marginBottom: 24 }}>
                <div className={result.net_burn > 0 ? "kpi-card amber" : "kpi-card green"}>
                  <span className="kpi-label">Burn Rate Neto (Pérdida Mensual)</span>
                  <span className="kpi-value">{formatCurrency(result.net_burn)}</span>
                  <span className="kpi-sub">Gastos Brutos: {formatCurrency(result.monthly_burn)}</span>
                </div>
                
                <div className={result.runway_months < 6 ? "kpi-card red" : result.runway_months < 12 ? "kpi-card amber" : "kpi-card blue"}>
                  <span className="kpi-label">Runway Estimado</span>
                  <span className="kpi-value">{result.runway_months === Infinity || result.runway_months === null ? "Infinito" : `${result.runway_months} Meses`}</span>
                  <span className="kpi-sub">Tiempo restante antes de quiebra</span>
                </div>
              </div>

              <div style={{ padding: 16, borderRadius: 8, background: "var(--bg-document)", border: "1px solid var(--border)" }}>
                <h4 style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.5 }}>Diagnóstico del CFO</h4>
                <p style={{ fontSize: 15, fontWeight: 500, color: "var(--text-primary)", lineHeight: 1.5 }}>
                  {result.survival_assessment}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
