"use client";

import React, { useState } from "react";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";
import type { MonteCarloResponse } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine, Cell,
} from "recharts";

export default function MonteCarloPage() {
  const [flows, setFlows] = useState("-100000, 30000, 35000, 40000, 45000, 50000");
  const [rate, setRate] = useState("10");
  const [iterations, setIterations] = useState("10000");

  const [varName1, setVarName1] = useState("revenue_growth");
  const [varBase1, setVarBase1] = useState("1.0");
  const [varStd1, setVarStd1] = useState("0.15");
  const [varMin1, setVarMin1] = useState("0.5");
  const [varMax1, setVarMax1] = useState("1.5");

  const [varName2, setVarName2] = useState("cost_inflation");
  const [varBase2, setVarBase2] = useState("1.0");
  const [varStd2, setVarStd2] = useState("0.10");
  const [varMin2, setVarMin2] = useState("0.7");
  const [varMax2, setVarMax2] = useState("1.3");

  const [result, setResult] = useState<MonteCarloResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleRun() {
    setLoading(true);
    setError("");
    try {
      const cashFlows = flows.split(",").map((s) => parseFloat(s.trim()));
      const futureIndices = cashFlows.map((_, i) => i).filter((i) => i > 0);

      const res = await api.analysis.monteCarlo({
        cash_flows: cashFlows,
        discount_rate: parseFloat(rate) / 100,
        variables: [
          { name: varName1, base_value: parseFloat(varBase1), std_dev: parseFloat(varStd1), min_value: parseFloat(varMin1), max_value: parseFloat(varMax1), distribution: "normal" },
          { name: varName2, base_value: parseFloat(varBase2), std_dev: parseFloat(varStd2), min_value: parseFloat(varMin2), max_value: parseFloat(varMax2), distribution: "normal" },
        ],
        cash_flow_impacts: {
          [varName1]: futureIndices,
          [varName2]: futureIndices,
        },
        iterations: parseInt(iterations),
        seed: 42,
      });
      setResult(res);
    } catch (e: any) {
      setError(e.detail || e.message);
    } finally {
      setLoading(false);
    }
  }

  const histogramData = result
    ? result.histogram_counts.map((count, i) => ({
        range: `${(result.histogram_bins[i] / 1000).toFixed(0)}k`,
        rangeValue: result.histogram_bins[i],
        count,
        isPositive: result.histogram_bins[i] >= 0,
      }))
    : [];

  const decisionColor = result?.decision === "HIGH_CONFIDENCE_ACCEPT" ? "var(--accent-emerald)" : result?.decision === "MODERATE_RISK" ? "var(--accent-amber)" : "var(--accent-rose)";
  const decisionBg = result?.decision === "HIGH_CONFIDENCE_ACCEPT" ? "rgba(16,185,129,0.08)" : result?.decision === "MODERATE_RISK" ? "rgba(245,158,11,0.08)" : "rgba(244,63,94,0.08)";
  const decisionLabel = result?.decision === "HIGH_CONFIDENCE_ACCEPT" ? "ACEPTAR (Alta Confianza)" : result?.decision === "MODERATE_RISK" ? "RIESGO MODERADO" : "RECHAZAR (Alto Riesgo)";

  return (
    <AppShell>
      <div className="page-header">
        <h2>Simulación de Monte Carlo</h2>
        <p>Estresa tu proyecto con miles de escenarios para conocer la probabilidad real de éxito</p>
      </div>

      <div className="card animate-in" style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Configuración</h3>
        <div className="grid-form" style={{ marginBottom: 20 }}>
          <div className="form-group" style={{ gridColumn: "1 / -1" }}>
            <label className="form-label">Flujos de Caja Base (separados por coma)</label>
            <input className="form-input" value={flows} onChange={(e) => setFlows(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Tasa de Descuento (%)</label>
            <input className="form-input" type="number" value={rate} onChange={(e) => setRate(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Iteraciones</label>
            <input className="form-input" type="number" value={iterations} onChange={(e) => setIterations(e.target.value)} />
          </div>
        </div>

        <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: "var(--text-secondary)" }}>Variables Estocásticas</h4>
        <div className="grid-form" style={{ marginBottom: 12 }}>
          <div className="form-group"><label className="form-label">Variable 1</label><input className="form-input" value={varName1} onChange={(e) => setVarName1(e.target.value)} /></div>
          <div className="form-group"><label className="form-label">Base</label><input className="form-input" type="number" value={varBase1} onChange={(e) => setVarBase1(e.target.value)} /></div>
          <div className="form-group"><label className="form-label">Std Dev</label><input className="form-input" type="number" value={varStd1} onChange={(e) => setVarStd1(e.target.value)} /></div>
          <div className="form-group"><label className="form-label">Min</label><input className="form-input" type="number" value={varMin1} onChange={(e) => setVarMin1(e.target.value)} /></div>
          <div className="form-group"><label className="form-label">Max</label><input className="form-input" type="number" value={varMax1} onChange={(e) => setVarMax1(e.target.value)} /></div>
        </div>
        <div className="grid-form" style={{ marginBottom: 20 }}>
          <div className="form-group"><label className="form-label">Variable 2</label><input className="form-input" value={varName2} onChange={(e) => setVarName2(e.target.value)} /></div>
          <div className="form-group"><label className="form-label">Base</label><input className="form-input" type="number" value={varBase2} onChange={(e) => setVarBase2(e.target.value)} /></div>
          <div className="form-group"><label className="form-label">Std Dev</label><input className="form-input" type="number" value={varStd2} onChange={(e) => setVarStd2(e.target.value)} /></div>
          <div className="form-group"><label className="form-label">Min</label><input className="form-input" type="number" value={varMin2} onChange={(e) => setVarMin2(e.target.value)} /></div>
          <div className="form-group"><label className="form-label">Max</label><input className="form-input" type="number" value={varMax2} onChange={(e) => setVarMax2(e.target.value)} /></div>
        </div>

        <button className="btn btn-primary" onClick={handleRun} disabled={loading}>
          {loading ? <><span className="loading-spinner" /> Simulando...</> : `Ejecutar ${iterations} Simulaciones`}
        </button>
        {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}
      </div>

      {result && (
        <>
          {/* Decision */}
          <div className="card-glass animate-in" style={{ marginBottom: 24, textAlign: "center", padding: 32, animationDelay: "0.05s", border: `1px solid ${decisionColor}22` }}>
            <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 8 }}>EVALUACION DE RIESGO</div>
            <div style={{ fontSize: 36, fontWeight: 800, color: decisionColor, marginBottom: 8 }}>
              {decisionLabel}
            </div>
            <div style={{ fontSize: 60, fontWeight: 800, fontFamily: "JetBrains Mono", color: decisionColor, lineHeight: 1 }}>
              {(result.stats.probability_positive * 100).toFixed(1)}%
            </div>
            <div style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 8 }}>Probabilidad de VPN positivo</div>
          </div>

          {/* KPIs */}
          <div className="grid-kpi animate-in" style={{ marginBottom: 24, animationDelay: "0.1s" }}>
            <div className="kpi-card green">
              <span className="kpi-label">VPN Promedio</span>
              <span className="kpi-value" style={{ fontSize: 20 }}>{formatCurrency(result.stats.mean)}</span>
              <span className="kpi-sub">Mediana: {formatCurrency(result.stats.median)}</span>
            </div>
            <div className="kpi-card blue">
              <span className="kpi-label">Desviación Estándar</span>
              <span className="kpi-value" style={{ fontSize: 20 }}>{formatCurrency(result.stats.std_dev)}</span>
              <span className="kpi-sub">Volatilidad del resultado</span>
            </div>
            <div className="kpi-card amber">
              <span className="kpi-label">Peor Escenario (P5)</span>
              <span className="kpi-value" style={{ fontSize: 20 }}>{formatCurrency(result.stats.percentile_5)}</span>
              <span className="kpi-sub">P10: {formatCurrency(result.stats.percentile_10)}</span>
            </div>
            <div className="kpi-card violet">
              <span className="kpi-label">Mejor Escenario (P95)</span>
              <span className="kpi-value" style={{ fontSize: 20 }}>{formatCurrency(result.stats.percentile_95)}</span>
              <span className="kpi-sub">P90: {formatCurrency(result.stats.percentile_90)}</span>
            </div>
          </div>

          {/* Histogram */}
          <div className="card animate-in" style={{ marginBottom: 24, animationDelay: "0.15s" }}>
            <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: "var(--text-secondary)" }}>
              Distribución de VPN — {result.iterations.toLocaleString()} Simulaciones
            </h4>
            <div style={{ height: 350 }}>
              <ResponsiveContainer>
                <BarChart data={histogramData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" interval="preserveStartEnd" tick={{ fontSize: 10 }} />
                  <YAxis label={{ value: "Frecuencia", angle: -90, position: "insideLeft", style: { fill: "var(--text-secondary)" } }} />
                  <Tooltip
                    formatter={(v: number) => [v, "Frecuencia"]}
                    labelFormatter={(l) => `VPN ~ $${l}`}
                    contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8 }}
                  />
                  <ReferenceLine x={histogramData.findIndex((d) => d.rangeValue >= 0)} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: "VPN=0", fill: "#f59e0b", fontSize: 11 }} />
                  <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                    {histogramData.map((entry, i) => (
                      <Cell key={i} fill={entry.isPositive ? "#10b981" : "#f43f5e"} fillOpacity={0.7} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Box Stats */}
          <div className="grid-2 animate-in" style={{ animationDelay: "0.2s" }}>
            <div className="card">
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: "var(--text-secondary)" }}>Intervalos de Confianza</h4>
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <div style={{ padding: 16, background: "var(--bg-input)", borderRadius: "var(--radius-sm)" }}>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>IC 90%</div>
                  <div style={{ fontFamily: "JetBrains Mono", fontSize: 15, color: "var(--accent-cyan)" }}>
                    {formatCurrency(result.confidence_interval_90[0])} — {formatCurrency(result.confidence_interval_90[1])}
                  </div>
                </div>
                <div style={{ padding: 16, background: "var(--bg-input)", borderRadius: "var(--radius-sm)" }}>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>IC 95%</div>
                  <div style={{ fontFamily: "JetBrains Mono", fontSize: 15, color: "var(--accent-violet)" }}>
                    {formatCurrency(result.confidence_interval_95[0])} — {formatCurrency(result.confidence_interval_95[1])}
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div style={{ padding: 12, background: "var(--bg-input)", borderRadius: "var(--radius-sm)" }}>
                    <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Skewness</div>
                    <div style={{ fontFamily: "JetBrains Mono", fontSize: 18, fontWeight: 600 }}>{result.stats.skewness.toFixed(4)}</div>
                  </div>
                  <div style={{ padding: 12, background: "var(--bg-input)", borderRadius: "var(--radius-sm)" }}>
                    <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Kurtosis</div>
                    <div style={{ fontFamily: "JetBrains Mono", fontSize: 18, fontWeight: 600 }}>{result.stats.kurtosis.toFixed(4)}</div>
                  </div>
                </div>
              </div>
            </div>
            <div className="card">
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: "var(--text-secondary)" }}>Evaluación de Riesgo</h4>
              <div style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.8, padding: 16, background: decisionBg, borderRadius: "var(--radius-sm)", border: `1px solid ${decisionColor}22` }}>
                {result.risk_assessment}
              </div>
              <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div style={{ padding: 12, background: "rgba(16,185,129,0.08)", borderRadius: "var(--radius-sm)", textAlign: "center" }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>P(Ganancia)</div>
                  <div style={{ fontFamily: "JetBrains Mono", fontSize: 22, fontWeight: 700, color: "var(--accent-emerald)" }}>
                    {(result.stats.probability_positive * 100).toFixed(1)}%
                  </div>
                </div>
                <div style={{ padding: 12, background: "rgba(244,63,94,0.08)", borderRadius: "var(--radius-sm)", textAlign: "center" }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>P(Pérdida)</div>
                  <div style={{ fontFamily: "JetBrains Mono", fontSize: 22, fontWeight: 700, color: "var(--accent-rose)" }}>
                    {(result.stats.probability_negative * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </AppShell>
  );
}
