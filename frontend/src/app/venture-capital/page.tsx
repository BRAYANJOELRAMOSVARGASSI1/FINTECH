"use client";

import React, { useState } from "react";
import AppShell from "@/components/AppShell";
import { api, ConvertibleNoteResponse } from "@/lib/api";

export default function VentureCapitalPage() {
  const [investment, setInvestment] = useState("200000");
  const [valuationCap, setValuationCap] = useState("2000000");
  const [discountRate, setDiscountRate] = useState("20");
  const [nextRoundPreMoney, setNextRoundPreMoney] = useState("2500000");

  const [result, setResult] = useState<ConvertibleNoteResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.startup.convertibleNote({
        investment: parseFloat(investment),
        valuation_cap: parseFloat(valuationCap),
        discount_rate: parseFloat(discountRate) / 100,
        next_round_pre_money: parseFloat(nextRoundPreMoney),
      });
      setResult(res);
    } catch (e: any) {
      setError(e.detail || e.message || "Error al calcular la dilución del SAFE/Nota.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="page-header">
        <h2>Venture Capital (SAFE / Notas Convertibles)</h2>
        <p>Calcula la dilución del fundador tras el choque entre el tope de valoración (Cap) y el descuento.</p>
      </div>

      <div className="grid-2 animate-in" style={{ marginBottom: 24 }}>
        <div className="card">
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: "var(--accent-blue)" }}>Términos del Acuerdo (Term Sheet)</h3>
          <div className="grid-form">
            <div className="form-group">
              <label className="form-label">Inversión Levantada ($)</label>
              <input className="form-input" type="number" value={investment} onChange={(e) => setInvestment(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Valuation Cap ($)</label>
              <input className="form-input" type="number" value={valuationCap} onChange={(e) => setValuationCap(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Tasa de Descuento (%)</label>
              <input className="form-input" type="number" value={discountRate} onChange={(e) => setDiscountRate(e.target.value)} />
            </div>
          </div>
          
          <h3 style={{ fontSize: 16, fontWeight: 600, marginTop: 24, marginBottom: 16, color: "var(--accent-emerald)" }}>Escenario de Conversión Futura</h3>
          <div className="grid-form">
            <div className="form-group">
              <label className="form-label">Valoración Pre-Money (Próxima Ronda) ($)</label>
              <input className="form-input" type="number" value={nextRoundPreMoney} onChange={(e) => setNextRoundPreMoney(e.target.value)} />
            </div>
          </div>
          
          <button className="btn btn-primary" onClick={handleAnalyze} disabled={loading} style={{ marginTop: 24, width: "100%" }}>
            {loading ? <span className="loading-spinner" /> : "Ejecutar Conversión a Equity"}
          </button>
          
          {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}
        </div>

        <div>
           {result && (
            <div className="card animate-in">
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: "var(--text-primary)" }}>Cap Table Resultante</h3>
              
              <div style={{ marginBottom: 24, textAlign: "center", padding: "16px", borderRadius: 8, background: "var(--bg-document)", border: "1px solid var(--border)" }}>
                <div style={{ fontSize: 12, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 4 }}>Condición Ejecutada (Mejor para Inversor)</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: "var(--accent-violet)" }}>
                  {result.conversion_method === "CAP" ? "Tope de Valoración Agresivo (Cap limitó precio)" : 
                   result.conversion_method === "DISCOUNT" ? "Descuento Directo Aplicado" : "Sin Descuento ni Cap"}
                </div>
              </div>

              <div className="grid-kpi" style={{ gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
                <div className={result.founder_retained_pct < 0.65 ? "kpi-card amber" : "kpi-card blue"}>
                  <span className="kpi-label">Propiedad del Fundador (Retenida)</span>
                  <span className="kpi-value">{(result.founder_retained_pct * 100).toFixed(2)}%</span>
                  <span className="kpi-sub">Alerta si baja de 65% en Pymes locales</span>
                </div>
                
                <div className="kpi-card green">
                  <span className="kpi-label">Equity del Inversionista</span>
                  <span className="kpi-value">{(result.investor_ownership_pct * 100).toFixed(2)}%</span>
                  <span className="kpi-sub">Porción final tras conversión</span>
                </div>
              </div>

            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
