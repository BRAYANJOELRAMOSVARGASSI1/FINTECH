"use client";

import React, { useState } from "react";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";
import type { FullValuationResponse, RateConversionResponse } from "@/lib/api";
import { formatCurrency, formatPercentDirect } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { TrendingUp, ArrowLeftRight, Calculator, Dice5 } from "lucide-react";

function KpiCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color: string }) {
  return (
    <div className={`kpi-card ${color} animate-in`}>
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">{value}</span>
      {sub && <span className="kpi-sub">{sub}</span>}
    </div>
  );
}

function QuickRateWidget() {
  const [nominal, setNominal] = useState("18");
  const [compounding, setCompounding] = useState("quarterly");
  const [result, setResult] = useState<RateConversionResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleConvert() {
    setLoading(true);
    try {
      const res = await api.rates.convert(parseFloat(nominal) / 100, compounding);
      setResult(res);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card animate-in">
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
        <ArrowLeftRight size={18} style={{ color: "var(--accent-blue)" }} />
        Conversión Rápida de Tasas
      </h3>
      <div className="grid-form" style={{ marginBottom: 16 }}>
        <div className="form-group">
          <label className="form-label">Tasa Nominal (%)</label>
          <input className="form-input" type="number" value={nominal} onChange={(e) => setNominal(e.target.value)} placeholder="18" />
        </div>
        <div className="form-group">
          <label className="form-label">Capitalización</label>
          <select className="form-select" value={compounding} onChange={(e) => setCompounding(e.target.value)}>
            <option value="annual">Anual</option>
            <option value="semiannual">Semestral</option>
            <option value="quarterly">Trimestral</option>
            <option value="monthly">Mensual</option>
            <option value="daily">Diaria</option>
            <option value="continuous">Continua</option>
          </select>
        </div>
        <div className="form-group" style={{ justifyContent: "flex-end" }}>
          <button className="btn btn-primary" onClick={handleConvert} disabled={loading}>
            {loading ? <span className="loading-spinner" /> : "Calcular TEA"}
          </button>
        </div>
      </div>
      {result && (
        <div style={{ display: "flex", alignItems: "center", gap: 24, padding: "16px", background: "var(--bg-input)", borderRadius: "var(--radius-sm)" }}>
          <div>
            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>TEA</div>
            <div style={{ fontSize: 28, fontWeight: 700, fontFamily: "JetBrains Mono", color: "var(--accent-emerald)" }}>
              {formatPercentDirect(result.effective_annual_rate_pct)}
            </div>
          </div>
          <div style={{ fontSize: 13, color: "var(--text-secondary)", flex: 1 }}>
            {result.explanation}
          </div>
        </div>
      )}
    </div>
  );
}

function QuickValuationWidget() {
  const [flows, setFlows] = useState("-100000, 30000, 40000, 50000, 30000");
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
      const detail = e.detail || e.message || "Error desconocido";
      setError(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setLoading(false);
    }
  }

  const chartData = result
    ? result.cash_flows.map((cf, i) => ({
        name: `Año ${i}`,
        "Flujo": cf,
        "VP": result.npv.present_values[i],
      }))
    : [];

  return (
    <div className="card animate-in">
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
        <TrendingUp size={18} style={{ color: "var(--accent-violet)" }} />
        Valoración Rápida de Proyecto
      </h3>
      <div className="grid-form" style={{ marginBottom: 16 }}>
        <div className="form-group" style={{ gridColumn: "1 / -1" }}>
          <label className="form-label">Flujos de Caja (separados por coma)</label>
          <input className="form-input" value={flows} onChange={(e) => setFlows(e.target.value)} placeholder="-100000, 30000, 40000, 50000" />
        </div>
        <div className="form-group">
          <label className="form-label">Tasa de Descuento (%)</label>
          <input className="form-input" type="number" value={rate} onChange={(e) => setRate(e.target.value)} />
        </div>
        <div className="form-group" style={{ justifyContent: "flex-end" }}>
          <button className="btn btn-primary" onClick={handleCalc} disabled={loading}>
            {loading ? <span className="loading-spinner" /> : "Analizar"}
          </button>
        </div>
      </div>
      {error && <div className="error-box">{error}</div>}
      {result && (
        <>
          <div className="grid-kpi" style={{ marginTop: 16 }}>
            <KpiCard label="VPN" value={formatCurrency(result.npv.npv)} sub={result.npv.decision} color={result.npv.decision === "ACCEPT" ? "green" : "amber"} />
            <KpiCard label="TIR" value={result.irr.irr_pct ? `${result.irr.irr_pct}%` : "N/A"} sub={result.irr.decision || "Sin hurdle"} color="violet" />
            <KpiCard label="Payback" value={result.payback.discounted_payback ? `${result.payback.discounted_payback} años` : "N/A"} sub="Descontado" color="blue" />
            <KpiCard label="PI" value={result.profitability_index.pi.toFixed(4)} sub={result.profitability_index.decision} color={result.profitability_index.decision === "ACCEPT" ? "green" : "amber"} />
          </div>
          <div style={{ marginTop: 16 }}>
            <div className={`badge ${result.overall_recommendation.startsWith("ACCEPT") ? "badge-accept" : result.overall_recommendation.startsWith("REJECT") ? "badge-reject" : "badge-neutral"}`}>
              {result.overall_recommendation}
            </div>
          </div>
          <div style={{ height: 280, marginTop: 24 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
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
        </>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <AppShell>
      <div className="page-header">
        <h2>Dashboard Financiero</h2>
        <p>Centro de control para análisis y toma de decisiones de inversión</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 24 }}>
        <div className="kpi-card green animate-in" style={{ animationDelay: "0.05s" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 40, height: 40, borderRadius: 10, background: "rgba(16, 185, 129, 0.12)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <TrendingUp size={20} style={{ color: "var(--accent-emerald)" }} />
            </div>
            <div>
              <span className="kpi-label">Motor Financiero</span>
              <div style={{ fontSize: 14, color: "var(--text-primary)", fontWeight: 600 }}>6 módulos activos</div>
            </div>
          </div>
        </div>
        <div className="kpi-card blue animate-in" style={{ animationDelay: "0.1s" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 40, height: 40, borderRadius: 10, background: "rgba(59, 130, 246, 0.12)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Calculator size={20} style={{ color: "var(--accent-blue)" }} />
            </div>
            <div>
              <span className="kpi-label">API Endpoints</span>
              <div style={{ fontSize: 14, color: "var(--text-primary)", fontWeight: 600 }}>12 endpoints disponibles</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        <QuickRateWidget />
        <QuickValuationWidget />
      </div>
    </AppShell>
  );
}
