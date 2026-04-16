"use client";

import React, { useState } from "react";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";
import type { AmortizationCompareResponse } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  LineChart, Line,
} from "recharts";

export default function AmortizationPage() {
  const [principal, setPrincipal] = useState("100000");
  const [annualRate, setAnnualRate] = useState("12");
  const [periods, setPeriods] = useState("24");
  const [periodsPerYear, setPeriodsPerYear] = useState("12");
  const [result, setResult] = useState<AmortizationCompareResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"french" | "german" | "american">("french");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleCompare() {
    setLoading(true);
    setError("");
    try {
      const res = await api.amortization.compare(
        parseFloat(principal), parseFloat(annualRate) / 100,
        parseInt(periods), parseInt(periodsPerYear),
      );
      setResult(res);
    } catch (e: any) {
      setError(e.detail || e.message);
    } finally {
      setLoading(false);
    }
  }

  const activeTable = result ? result[activeTab] : null;

  const comparisonChart = result ? [
    { name: "Francés", "Interés Total": result.french.total_interest, "Total Pagado": result.french.total_paid },
    { name: "Alemán", "Interés Total": result.german.total_interest, "Total Pagado": result.german.total_paid },
    { name: "Americano", "Interés Total": result.american.total_interest, "Total Pagado": result.american.total_paid },
  ] : [];

  const paymentChart = result ? result.french.rows.map((_, i) => ({
    period: i + 1,
    Francés: result.french.rows[i]?.payment || 0,
    Alemán: result.german.rows[i]?.payment || 0,
    Americano: result.american.rows[i]?.payment || 0,
  })) : [];

  return (
    <AppShell>
      <div className="page-header">
        <h2>Tablas de Amortización</h2>
        <p>Compara los sistemas Francés, Alemán y Americano — ¿cuál te conviene más?</p>
      </div>

      <div className="card animate-in" style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Parámetros del Préstamo</h3>
        <div className="grid-form">
          <div className="form-group">
            <label className="form-label">Principal ($)</label>
            <input className="form-input" type="number" value={principal} onChange={(e) => setPrincipal(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Tasa Anual (%)</label>
            <input className="form-input" type="number" value={annualRate} onChange={(e) => setAnnualRate(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Total Cuotas</label>
            <input className="form-input" type="number" value={periods} onChange={(e) => setPeriods(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Cuotas / Año</label>
            <select className="form-select" value={periodsPerYear} onChange={(e) => setPeriodsPerYear(e.target.value)}>
              <option value="12">Mensual (12)</option>
              <option value="4">Trimestral (4)</option>
              <option value="2">Semestral (2)</option>
              <option value="1">Anual (1)</option>
            </select>
          </div>
          <div className="form-group" style={{ justifyContent: "flex-end" }}>
            <button className="btn btn-primary" onClick={handleCompare} disabled={loading}>
              {loading ? <span className="loading-spinner" /> : "Comparar Sistemas"}
            </button>
          </div>
        </div>
        {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}
      </div>

      {result && (
        <>
          {/* KPI Summary */}
          <div className="grid-3 animate-in" style={{ marginBottom: 24, animationDelay: "0.05s" }}>
            {(["french", "german", "american"] as const).map((sys) => {
              const table = result[sys];
              const isCheapest = result.cheapest_system === sys;
              const labels = { french: "Francés", german: "Alemán", american: "Americano" };
              return (
                <div key={sys} className={`kpi-card ${isCheapest ? "green" : "blue"}`} onClick={() => setActiveTab(sys)} style={{ cursor: "pointer", border: activeTab === sys ? "1px solid var(--accent-blue)" : undefined }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span className="kpi-label">{labels[sys]}</span>
                    {isCheapest && <span className="badge badge-accept" style={{ fontSize: 10 }}>MÁS BARATO</span>}
                  </div>
                  <span className="kpi-value" style={{ fontSize: 22 }}>{formatCurrency(table.total_interest)}</span>
                  <span className="kpi-sub">Intereses totales | Pagado: {formatCurrency(table.total_paid)}</span>
                </div>
              );
            })}
          </div>

          {/* Charts */}
          <div className="grid-2 animate-in" style={{ marginBottom: 24, animationDelay: "0.1s" }}>
            <div className="card">
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: "var(--text-secondary)" }}>Comparación de Intereses Totales</h4>
              <div style={{ height: 280 }}>
                <ResponsiveContainer>
                  <BarChart data={comparisonChart}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8 }} />
                    <Legend />
                    <Bar dataKey="Interés Total" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Total Pagado" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="card">
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: "var(--text-secondary)" }}>Evolución de Cuotas</h4>
              <div style={{ height: 280 }}>
                <ResponsiveContainer>
                  <LineChart data={paymentChart}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`} />
                    <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8 }} />
                    <Legend />
                    <Line type="stepAfter" dataKey="Francés" stroke="#3b82f6" strokeWidth={2} dot={false} />
                    <Line type="stepAfter" dataKey="Alemán" stroke="#10b981" strokeWidth={2} dot={false} />
                    <Line type="stepAfter" dataKey="Americano" stroke="#f59e0b" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Schedule Table */}
          {activeTable && (
            <div className="card animate-in" style={{ animationDelay: "0.15s" }}>
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: "var(--text-secondary)" }}>
                Tabla de Amortización — {activeTab === "french" ? "Francés" : activeTab === "german" ? "Alemán" : "Americano"}
              </h4>
              <div className="table-container" style={{ maxHeight: 400, overflowY: "auto" }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Período</th>
                      <th>Cuota</th>
                      <th>Interés</th>
                      <th>Capital</th>
                      <th>Saldo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeTable.rows.map((row) => (
                      <tr key={row.period}>
                        <td style={{ fontFamily: "Inter" }}>{row.period}</td>
                        <td>{formatCurrency(row.payment)}</td>
                        <td style={{ color: "var(--accent-rose)" }}>{formatCurrency(row.interest)}</td>
                        <td style={{ color: "var(--accent-emerald)" }}>{formatCurrency(row.principal)}</td>
                        <td>{formatCurrency(row.balance)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Recommendation */}
          <div className="card animate-in" style={{ marginTop: 24, animationDelay: "0.2s" }}>
            <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}>{result.recommendation}</div>
          </div>
        </>
      )}
    </AppShell>
  );
}
