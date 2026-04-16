"use client";

import React, { useState } from "react";
import AppShell from "@/components/AppShell";
import { api, CashCycleResponse } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

export default function WorkingCapitalPage() {
  const [annualRevenue, setAnnualRevenue] = useState("1440000"); // 120k * 12
  const [accountsReceivable, setAccountsReceivable] = useState("240000"); // 60 days
  const [annualCogs, setAnnualCogs] = useState("720000"); // 50% margin
  const [inventory, setInventory] = useState("60000"); // 30 days
  const [accountsPayable, setAccountsPayable] = useState("60000"); // 30 days

  const [result, setResult] = useState<CashCycleResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.startup.cashCycle({
        annual_revenue: parseFloat(annualRevenue),
        accounts_receivable: parseFloat(accountsReceivable),
        annual_cogs: parseFloat(annualCogs),
        inventory: parseFloat(inventory),
        accounts_payable: parseFloat(accountsPayable),
      });
      setResult(res);
    } catch (e: any) {
      setError(e.detail || e.message || "Error al calcular el Capital de Trabajo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="page-header">
        <h2>Capital de Trabajo (Ciclo de Caja)</h2>
        <p>Mide los días en que el efectivo de la empresa queda inmovilizado en la operación comercial.</p>
      </div>

      <div className="grid-2 animate-in" style={{ marginBottom: 24 }}>
        <div className="card">
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: "var(--accent-emerald)" }}>Ingresos & Costos Anualizados</h3>
          <div className="grid-form">
            <div className="form-group">
              <label className="form-label">Ingresos Anuales ($)</label>
              <input className="form-input" type="number" value={annualRevenue} onChange={(e) => setAnnualRevenue(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Costo de Ventas (COGS Anual) ($)</label>
              <input className="form-input" type="number" value={annualCogs} onChange={(e) => setAnnualCogs(e.target.value)} />
            </div>
          </div>
          
          <h3 style={{ fontSize: 16, fontWeight: 600, marginTop: 24, marginBottom: 16, color: "var(--accent-violet)" }}>Saldos Cierre de Mes</h3>
          <div className="grid-form">
            <div className="form-group">
              <label className="form-label">Cuentas por Cobrar (Clientes) ($)</label>
              <input className="form-input" type="number" value={accountsReceivable} onChange={(e) => setAccountsReceivable(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Inventario Activo ($)</label>
              <input className="form-input" type="number" value={inventory} onChange={(e) => setInventory(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Cuentas por Pagar (Proveedores) ($)</label>
              <input className="form-input" type="number" value={accountsPayable} onChange={(e) => setAccountsPayable(e.target.value)} />
            </div>
          </div>
          
          <button className="btn btn-primary" onClick={handleAnalyze} disabled={loading} style={{ marginTop: 24, width: "100%" }}>
            {loading ? <span className="loading-spinner" /> : "Diagnosticar Liquidez Operativa"}
          </button>
          
          {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}
        </div>

        <div>
           {result && (
            <div className="card animate-in">
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: "var(--text-primary)" }}>Resultados del Ciclo de Caja (CCC)</h3>
              
              <div className="grid-kpi" style={{ gridTemplateColumns: '1fr', gap: 16, marginBottom: 24 }}>
                <div className="kpi-card blue">
                  <span className="kpi-label">Ciclo de Conversión de Efectivo</span>
                  <span className="kpi-value">{result.ccc_days} Días</span>
                  <span className="kpi-sub">{result.interpretation}</span>
                </div>
                
                <div className="kpi-card red" style={{ opacity: 0.9 }}>
                  <span className="kpi-label">Capital de Trabajo Inmovilizado</span>
                  <span className="kpi-value">{formatCurrency(result.capital_tied_up)}</span>
                  <span className="kpi-sub">Efectivo congelado en la operación</span>
                </div>
              </div>

              <div className="grid-2" style={{ gap: 12 }}>
                <div style={{ padding: 12, borderRadius: 8, background: "var(--bg-document)", border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>Días de Cobro (DSO)</div>
                  <div style={{ fontSize: 18, fontWeight: 600 }}>{result.dso} d</div>
                </div>
                <div style={{ padding: 12, borderRadius: 8, background: "var(--bg-document)", border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>Días de Inventario (DIO)</div>
                  <div style={{ fontSize: 18, fontWeight: 600 }}>{result.dio} d</div>
                </div>
                <div style={{ padding: 12, borderRadius: 8, background: "var(--bg-document)", border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>Días de Pago (DPO)</div>
                  <div style={{ fontSize: 18, fontWeight: 600 }}>{result.dpo} d</div>
                </div>
                <div style={{ padding: 12, borderRadius: 8, background: "var(--bg-document)", border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>Ventas Diarias</div>
                  <div style={{ fontSize: 18, fontWeight: 600 }}>{formatCurrency(result.daily_sales)}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
