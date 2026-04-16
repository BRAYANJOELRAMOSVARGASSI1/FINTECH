"use client";

import React, { useState } from "react";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";
import type { CapexVsOpexResponse } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell,
  ScatterChart, Scatter, ZAxis,
} from "recharts";

export default function CapexOpexPage() {
  // CAPEX inputs
  const [capexInv, setCapexInv] = useState("500000");
  const [capexLife, setCapexLife] = useState("5");
  const [capexSalvage, setCapexSalvage] = useState("50000");
  const [capexMaint, setCapexMaint] = useState("20000");
  const [capexTax, setCapexTax] = useState("30");
  const [capexDepr, setCapexDepr] = useState("straight_line");
  const [capexGrowth, setCapexGrowth] = useState("2");

  // OPEX inputs
  const [opexCost, setOpexCost] = useState("120000");
  const [opexYears, setOpexYears] = useState("5");
  const [opexTax, setOpexTax] = useState("30");
  const [opexInflation, setOpexInflation] = useState("5");
  const [opexSetup, setOpexSetup] = useState("0");

  const [wacc, setWacc] = useState("10");
  const [result, setResult] = useState<CapexVsOpexResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleAnalyze() {
    setLoading(true);
    setError("");
    try {
      const res = await api.analysis.capexVsOpex({
        capex: {
          initial_investment: parseFloat(capexInv),
          useful_life_years: parseInt(capexLife),
          salvage_value: parseFloat(capexSalvage),
          annual_maintenance: parseFloat(capexMaint),
          tax_rate: parseFloat(capexTax) / 100,
          depreciation_method: capexDepr,
          maintenance_growth_rate: parseFloat(capexGrowth) / 100,
        },
        opex: {
          annual_cost: parseFloat(opexCost),
          contract_years: parseInt(opexYears),
          tax_rate: parseFloat(opexTax) / 100,
          inflation_rate: parseFloat(opexInflation) / 100,
          setup_cost: parseFloat(opexSetup),
        },
        wacc: parseFloat(wacc) / 100,
        run_sensitivity: true,
      });
      setResult(res);
    } catch (e: any) {
      setError(e.detail || e.message);
    } finally {
      setLoading(false);
    }
  }

  const cashFlowChart = result ? result.capex.year_labels.map((label, i) => ({
    name: label,
    CAPEX: result.capex.cash_flows[i] || 0,
    OPEX: result.opex.cash_flows[i] || 0,
  })) : [];

  const sensitivityChart = result ? result.sensitivity.map((sp) => ({
    name: `${sp.variable_name} ${sp.variation_pct > 0 ? "+" : ""}${sp.variation_pct}%`,
    "CAPEX VPN": sp.capex_npv,
    "OPEX VPN": sp.opex_npv,
    recommendation: sp.recommendation,
  })) : [];

  return (
    <AppShell>
      <div className="page-header">
        <h2>CAPEX vs OPEX</h2>
        <p>¿Comprar el activo o contratar el servicio? El análisis que todo CFO necesita</p>
      </div>

      <div className="grid-2 animate-in" style={{ marginBottom: 24 }}>
        {/* CAPEX Card */}
        <div className="card">
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: "var(--accent-blue)" }}>CAPEX — Compra del Activo</h3>
          <div className="grid-form">
            <div className="form-group">
              <label className="form-label">Inversión Inicial ($)</label>
              <input className="form-input" type="number" value={capexInv} onChange={(e) => setCapexInv(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Vida Útil (años)</label>
              <input className="form-input" type="number" value={capexLife} onChange={(e) => setCapexLife(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Valor de Salvamento ($)</label>
              <input className="form-input" type="number" value={capexSalvage} onChange={(e) => setCapexSalvage(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Mantenimiento Anual ($)</label>
              <input className="form-input" type="number" value={capexMaint} onChange={(e) => setCapexMaint(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Tasa Impositiva (%)</label>
              <input className="form-input" type="number" value={capexTax} onChange={(e) => setCapexTax(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Método Depreciación</label>
              <select className="form-select" value={capexDepr} onChange={(e) => setCapexDepr(e.target.value)}>
                <option value="straight_line">Línea Recta</option>
                <option value="declining_balance">Doble Saldo Decreciente</option>
                <option value="sum_of_years_digits">Suma Dígitos</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Crecimiento Mantenim. (%)</label>
              <input className="form-input" type="number" value={capexGrowth} onChange={(e) => setCapexGrowth(e.target.value)} />
            </div>
          </div>
        </div>

        {/* OPEX Card */}
        <div className="card">
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: "var(--accent-violet)" }}>OPEX — Gasto Operativo</h3>
          <div className="grid-form">
            <div className="form-group">
              <label className="form-label">Costo Anual ($)</label>
              <input className="form-input" type="number" value={opexCost} onChange={(e) => setOpexCost(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Años de Contrato</label>
              <input className="form-input" type="number" value={opexYears} onChange={(e) => setOpexYears(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Tasa Impositiva (%)</label>
              <input className="form-input" type="number" value={opexTax} onChange={(e) => setOpexTax(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Inflación Anual (%)</label>
              <input className="form-input" type="number" value={opexInflation} onChange={(e) => setOpexInflation(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Costo Setup ($)</label>
              <input className="form-input" type="number" value={opexSetup} onChange={(e) => setOpexSetup(e.target.value)} />
            </div>
          </div>
        </div>
      </div>

      {/* WACC + Button */}
      <div className="card animate-in" style={{ marginBottom: 24, display: "flex", alignItems: "end", gap: 24, animationDelay: "0.05s" }}>
        <div className="form-group">
          <label className="form-label">WACC / Tasa de Descuento (%)</label>
          <input className="form-input" type="number" value={wacc} onChange={(e) => setWacc(e.target.value)} style={{ width: 160 }} />
        </div>
        <button className="btn btn-primary" onClick={handleAnalyze} disabled={loading} style={{ height: 42 }}>
          {loading ? <span className="loading-spinner" /> : "Ejecutar Análisis Comparativo"}
        </button>
      </div>

      {error && <div className="error-box" style={{ marginBottom: 24 }}>{error}</div>}

      {result && (
        <>
          {/* Decision */}
          <div className="card-glass animate-in" style={{ marginBottom: 24, textAlign: "center", padding: 32, animationDelay: "0.1s" }}>
            <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 8 }}>RECOMENDACIÓN</div>
            <div style={{ fontSize: 40, fontWeight: 800, marginBottom: 12, background: result.recommendation === "CAPEX" ? "var(--gradient-primary)" : result.recommendation === "OPEX" ? "var(--gradient-success)" : "var(--gradient-danger)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              {result.recommendation}
            </div>
            <div style={{ fontSize: 14, color: "var(--text-secondary)", maxWidth: 700, margin: "0 auto", lineHeight: 1.6 }}>
              {result.explanation}
            </div>
          </div>

          {/* KPIs */}
          <div className="grid-kpi animate-in" style={{ marginBottom: 24, animationDelay: "0.15s" }}>
            <div className="kpi-card blue">
              <span className="kpi-label">CAPEX VPN</span>
              <span className="kpi-value" style={{ fontSize: 22 }}>{formatCurrency(result.capex.npv_cost)}</span>
              <span className="kpi-sub">Costo nominal: {formatCurrency(result.capex.total_cost_nominal)}</span>
            </div>
            <div className="kpi-card violet">
              <span className="kpi-label">OPEX VPN</span>
              <span className="kpi-value" style={{ fontSize: 22 }}>{formatCurrency(result.opex.npv_cost)}</span>
              <span className="kpi-sub">Costo nominal: {formatCurrency(result.opex.total_cost_nominal)}</span>
            </div>
            <div className={`kpi-card ${result.npv_advantage > 0 ? "green" : "amber"}`}>
              <span className="kpi-label">Ventaja VPN</span>
              <span className="kpi-value" style={{ fontSize: 22 }}>{formatCurrency(Math.abs(result.npv_advantage))}</span>
              <span className="kpi-sub">A favor de {result.recommendation}</span>
            </div>
            <div className="kpi-card green">
              <span className="kpi-label">Escudo Fiscal CAPEX</span>
              <span className="kpi-value" style={{ fontSize: 22 }}>{formatCurrency(result.capex.tax_shields.reduce((a, b) => a + b, 0))}</span>
              <span className="kpi-sub">Total acumulado</span>
            </div>
          </div>

          {/* Charts */}
          <div className="grid-2 animate-in" style={{ marginBottom: 24, animationDelay: "0.2s" }}>
            <div className="card">
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: "var(--text-secondary)" }}>Flujos de Caja: CAPEX vs OPEX</h4>
              <div style={{ height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={cashFlowChart}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8 }} />
                    <Legend />
                    <Bar dataKey="CAPEX" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="OPEX" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="card">
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: "var(--text-secondary)" }}>Análisis de Sensibilidad</h4>
              <div style={{ height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={sensitivityChart} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                    <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8 }} />
                    <Legend />
                    <Bar dataKey="CAPEX VPN" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                    <Bar dataKey="OPEX VPN" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}
    </AppShell>
  );
}
