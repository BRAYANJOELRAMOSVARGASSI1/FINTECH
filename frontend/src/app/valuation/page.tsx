"use client";

import React, { useState } from "react";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";
import type { FullValuationResponse } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  LineChart, Line, AreaChart, Area, ReferenceLine,
} from "recharts";

export default function ValuationPage() {
  const [flows, setFlows] = useState("-100000, 30000, 40000, 50000, 30000, 25000");
  const [rate, setRate] = useState("10");
  const [result, setResult] = useState<FullValuationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleCalc() {
    setLoading(true);
    setError("");
    try {
      const cashFlows = flows.split(",").map((s) => parseFloat(s.trim()));
      const res = await api.valuation.full(cashFlows, parseFloat(rate) / 100);
      setResult(res);
    } catch (e: any) {
      setError(e.detail || e.message);
    } finally {
      setLoading(false);
    }
  }

  const cashFlowChart = result
    ? result.cash_flows.map((cf, i) => ({ name: `Año ${i}`, Flujo: cf, VP: result.npv.present_values[i] }))
    : [];

  const cumulativeChart = result
    ? result.payback.cumulative_flows.map((cf, i) => ({
        name: `Año ${i}`,
        "Acumulado Nominal": cf,
        "Acumulado VP": result.payback.cumulative_pv_flows[i],
      }))
    : [];

  return (
    <AppShell>
      <div className="page-header">
        <h2>Valoración de Proyectos</h2>
        <p>VPN, TIR, Payback descontado e Índice de Rentabilidad en una sola vista</p>
      </div>

      <div className="card animate-in" style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Datos del Proyecto</h3>
        <div className="grid-form">
          <div className="form-group" style={{ gridColumn: "1 / -1" }}>
            <label className="form-label">Flujos de Caja (separados por coma, Año 0 = inversión negativa)</label>
            <input className="form-input" value={flows} onChange={(e) => setFlows(e.target.value)} placeholder="-100000, 30000, 40000, 50000" />
          </div>
          <div className="form-group">
            <label className="form-label">Tasa de Descuento / WACC (%)</label>
            <input className="form-input" type="number" value={rate} onChange={(e) => setRate(e.target.value)} />
          </div>
          <div className="form-group" style={{ justifyContent: "flex-end" }}>
            <button className="btn btn-primary" onClick={handleCalc} disabled={loading}>
              {loading ? <span className="loading-spinner" /> : "Valorar Proyecto"}
            </button>
          </div>
        </div>
        {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}
      </div>

      {result && (
        <>
          {/* KPI Cards */}
          <div className="grid-kpi animate-in" style={{ animationDelay: "0.05s" }}>
            <div className={`kpi-card ${result.npv.decision === "ACCEPT" ? "green" : "amber"}`}>
              <span className="kpi-label">Valor Presente Neto</span>
              <span className="kpi-value">{formatCurrency(result.npv.npv)}</span>
              <span className={`badge ${result.npv.decision === "ACCEPT" ? "badge-accept" : "badge-reject"}`}>{result.npv.decision}</span>
            </div>
            <div className="kpi-card violet">
              <span className="kpi-label">Tasa Interna de Retorno</span>
              <span className="kpi-value">{result.irr.irr_pct ? `${result.irr.irr_pct}%` : "N/A"}</span>
              <span className="kpi-sub">{result.irr.converged ? `Hurdle: ${parseFloat(rate)}%` : "No convergió"}</span>
            </div>
            <div className="kpi-card blue">
              <span className="kpi-label">Payback Descontado</span>
              <span className="kpi-value">{result.payback.discounted_payback !== null ? `${result.payback.discounted_payback} años` : "Nunca"}</span>
              <span className="kpi-sub">Simple: {result.payback.simple_payback !== null ? `${result.payback.simple_payback} años` : "Nunca"}</span>
            </div>
            <div className={`kpi-card ${result.profitability_index.decision === "ACCEPT" ? "green" : "amber"}`}>
              <span className="kpi-label">Índice de Rentabilidad</span>
              <span className="kpi-value">{result.profitability_index.pi.toFixed(4)}</span>
              <span className={`badge ${result.profitability_index.decision === "ACCEPT" ? "badge-accept" : "badge-reject"}`}>{result.profitability_index.decision}</span>
            </div>
          </div>

          {/* Overall */}
          <div className="card animate-in" style={{ marginBottom: 24, animationDelay: "0.1s" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <span style={{ fontSize: 16, fontWeight: 600 }}>Recomendación:</span>
              <span className={`badge ${result.overall_recommendation.startsWith("ACCEPT") ? "badge-accept" : result.overall_recommendation.startsWith("REJECT") ? "badge-reject" : "badge-neutral"}`} style={{ fontSize: 14 }}>
                {result.overall_recommendation}
              </span>
            </div>
          </div>

          {/* Charts */}
          <div className="grid-2 animate-in" style={{ animationDelay: "0.15s" }}>
            <div className="card">
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: "var(--text-secondary)" }}>Flujos de Caja vs Valor Presente</h4>
              <div style={{ height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={cashFlowChart}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8 }} />
                    <Legend />
                    <Bar dataKey="Flujo" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="VP" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="card">
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: "var(--text-secondary)" }}>Flujo Acumulado (Payback Visual)</h4>
              <div style={{ height: 300 }}>
                <ResponsiveContainer>
                  <AreaChart data={cumulativeChart}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8 }} />
                    <Legend />
                    <ReferenceLine y={0} stroke="#f59e0b" strokeDasharray="3 3" label="Breakeven" />
                    <Area type="monotone" dataKey="Acumulado Nominal" stroke="#10b981" fill="rgba(16,185,129,0.1)" />
                    <Area type="monotone" dataKey="Acumulado VP" stroke="#06b6d4" fill="rgba(6,182,212,0.1)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}
    </AppShell>
  );
}
