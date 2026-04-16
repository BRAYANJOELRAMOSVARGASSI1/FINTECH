"use client";

import React, { useState } from "react";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";
import type { RateComparisonResponse } from "@/lib/api";
import { formatPercentDirect } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

const COLORS = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#f43f5e", "#06b6d4"];

export default function RatesPage() {
  const [entries, setEntries] = useState([
    { label: "Banco A", nominal_rate: "18", compounding: "annual" },
    { label: "Banco B", nominal_rate: "18", compounding: "quarterly" },
    { label: "Banco C", nominal_rate: "17.5", compounding: "monthly" },
  ]);
  const [perspective, setPerspective] = useState("borrower");
  const [result, setResult] = useState<RateComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Fisher
  const [fisherNom, setFisherNom] = useState("15");
  const [fisherInf, setFisherInf] = useState("5");
  const [fisherResult, setFisherResult] = useState<any>(null);

  // WACC
  const [waccEq, setWaccEq] = useState("600000");
  const [waccDebt, setWaccDebt] = useState("400000");
  const [waccKe, setWaccKe] = useState("12");
  const [waccKd, setWaccKd] = useState("8");
  const [waccTax, setWaccTax] = useState("30");
  const [waccResult, setWaccResult] = useState<any>(null);

  function addEntry() {
    setEntries([...entries, { label: `Opción ${entries.length + 1}`, nominal_rate: "12", compounding: "monthly" }]);
  }

  function removeEntry(idx: number) {
    if (entries.length > 2) setEntries(entries.filter((_, i) => i !== idx));
  }

  function updateEntry(idx: number, field: string, value: string) {
    const updated = [...entries];
    (updated[idx] as any)[field] = value;
    setEntries(updated);
  }

  async function handleCompare() {
    setLoading(true);
    setError("");
    try {
      const rates = entries.map((e) => ({
        label: e.label,
        nominal_rate: parseFloat(e.nominal_rate) / 100,
        compounding: e.compounding,
      }));
      const res = await api.rates.compare(rates, perspective);
      setResult(res);
    } catch (e: any) {
      setError(e.detail || e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleFisher() {
    try {
      const res = await api.rates.fisher(parseFloat(fisherNom) / 100, parseFloat(fisherInf) / 100);
      setFisherResult(res);
    } catch { /* ignore */ }
  }

  async function handleWacc() {
    try {
      const res = await api.rates.wacc(
        parseFloat(waccEq), parseFloat(waccDebt),
        parseFloat(waccKe) / 100, parseFloat(waccKd) / 100, parseFloat(waccTax) / 100,
      );
      setWaccResult(res);
    } catch { /* ignore */ }
  }

  const chartData = result?.items.map((item, i) => ({
    name: item.label,
    TEA: item.effective_annual_rate_pct,
    fill: COLORS[i % COLORS.length],
  })) || [];

  return (
    <AppShell>
      <div className="page-header">
        <h2>Tasas de Interés</h2>
        <p>Comparación universal de tasas — ninguna decisión se toma con la tasa nominal</p>
      </div>

      {/* Rate Comparison */}
      <div className="card animate-in" style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20 }}>Comparación de Tasas (Nominal → TEA)</h3>

        {entries.map((entry, idx) => (
          <div key={idx} className="grid-form" style={{ marginBottom: 12, alignItems: "end" }}>
            <div className="form-group">
              <label className="form-label">Nombre</label>
              <input className="form-input" value={entry.label} onChange={(e) => updateEntry(idx, "label", e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Tasa Nominal (%)</label>
              <input className="form-input" type="number" value={entry.nominal_rate} onChange={(e) => updateEntry(idx, "nominal_rate", e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Capitalización</label>
              <select className="form-select" value={entry.compounding} onChange={(e) => updateEntry(idx, "compounding", e.target.value)}>
                <option value="annual">Anual</option>
                <option value="semiannual">Semestral</option>
                <option value="quarterly">Trimestral</option>
                <option value="monthly">Mensual</option>
                <option value="daily">Diaria</option>
                <option value="continuous">Continua</option>
              </select>
            </div>
            <button className="btn btn-outline" onClick={() => removeEntry(idx)} style={{ padding: "10px 14px" }}>✕</button>
          </div>
        ))}

        <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
          <button className="btn btn-outline" onClick={addEntry}>+ Agregar Tasa</button>
          <select className="form-select" style={{ width: 200 }} value={perspective} onChange={(e) => setPerspective(e.target.value)}>
            <option value="borrower">Perspectiva: Deudor</option>
            <option value="investor">Perspectiva: Inversor</option>
          </select>
          <button className="btn btn-primary" onClick={handleCompare} disabled={loading}>
            {loading ? <span className="loading-spinner" /> : "Comparar"}
          </button>
        </div>

        {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}

        {result && (
          <div style={{ marginTop: 24 }}>
            <div style={{ display: "flex", gap: 24 }}>
              <div style={{ flex: 1 }}>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Rank</th>
                        <th>Nombre</th>
                        <th>Nominal</th>
                        <th>Capitaliz.</th>
                        <th>TEA</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.items.map((item) => (
                        <tr key={item.rank}>
                          <td style={{ fontFamily: "Inter", fontWeight: 600, color: item.rank === 1 ? "var(--accent-emerald)" : "var(--text-secondary)" }}>
                            #{item.rank}
                          </td>
                          <td style={{ fontFamily: "Inter" }}>{item.label}</td>
                          <td>{formatPercentDirect(item.nominal_rate * 100)}</td>
                          <td style={{ fontFamily: "Inter", textTransform: "capitalize" }}>{item.compounding}</td>
                          <td style={{ fontWeight: 700, color: item.rank === 1 ? "var(--accent-emerald)" : "var(--text-primary)" }}>
                            {formatPercentDirect(item.effective_annual_rate_pct)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div style={{ marginTop: 16, fontSize: 13, color: "var(--text-secondary)" }}>
                  <span className="badge badge-info" style={{ marginRight: 12 }}>{result.spread_bps} bps spread</span>
                  {result.recommendation}
                </div>
              </div>
              <div style={{ width: 350, height: 260 }}>
                <ResponsiveContainer>
                  <BarChart data={chartData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" domain={["auto", "auto"]} tickFormatter={(v) => `${v}%`} />
                    <YAxis type="category" dataKey="name" width={80} />
                    <Tooltip formatter={(v: number) => `${v.toFixed(4)}%`} contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8 }} />
                    <Bar dataKey="TEA" radius={[0, 4, 4, 0]}>
                      {chartData.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Fisher + WACC */}
      <div className="grid-2">
        <div className="card animate-in" style={{ animationDelay: "0.1s" }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Ecuación de Fisher (Tasa Real)</h3>
          <div className="grid-form">
            <div className="form-group">
              <label className="form-label">Tasa Nominal (%)</label>
              <input className="form-input" type="number" value={fisherNom} onChange={(e) => setFisherNom(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Inflación (%)</label>
              <input className="form-input" type="number" value={fisherInf} onChange={(e) => setFisherInf(e.target.value)} />
            </div>
          </div>
          <button className="btn btn-primary" onClick={handleFisher} style={{ marginTop: 16 }}>Calcular Tasa Real</button>
          {fisherResult && (
            <div style={{ marginTop: 16, padding: 16, background: "var(--bg-input)", borderRadius: "var(--radius-sm)" }}>
              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>TASA REAL</div>
              <div style={{ fontSize: 32, fontWeight: 700, fontFamily: "JetBrains Mono", color: "var(--accent-cyan)" }}>
                {formatPercentDirect(fisherResult.real_rate_pct)}
              </div>
              <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 8 }}>{fisherResult.explanation}</div>
            </div>
          )}
        </div>

        <div className="card animate-in" style={{ animationDelay: "0.15s" }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>WACC</h3>
          <div className="grid-form">
            <div className="form-group">
              <label className="form-label">Equity ($)</label>
              <input className="form-input" type="number" value={waccEq} onChange={(e) => setWaccEq(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Deuda ($)</label>
              <input className="form-input" type="number" value={waccDebt} onChange={(e) => setWaccDebt(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Ke (%)</label>
              <input className="form-input" type="number" value={waccKe} onChange={(e) => setWaccKe(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Kd (%)</label>
              <input className="form-input" type="number" value={waccKd} onChange={(e) => setWaccKd(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Tax Rate (%)</label>
              <input className="form-input" type="number" value={waccTax} onChange={(e) => setWaccTax(e.target.value)} />
            </div>
          </div>
          <button className="btn btn-primary" onClick={handleWacc} style={{ marginTop: 16 }}>Calcular WACC</button>
          {waccResult && (
            <div style={{ marginTop: 16, padding: 16, background: "var(--bg-input)", borderRadius: "var(--radius-sm)" }}>
              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>WACC</div>
              <div style={{ fontSize: 32, fontWeight: 700, fontFamily: "JetBrains Mono", color: "var(--accent-violet)" }}>
                {formatPercentDirect(waccResult.wacc_pct)}
              </div>
              <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 8 }}>{waccResult.explanation}</div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
