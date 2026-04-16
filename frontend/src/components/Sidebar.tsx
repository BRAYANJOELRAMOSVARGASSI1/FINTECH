"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Calculator,
  ArrowLeftRight,
  Table2,
  TrendingUp,
  Dice5,
  Activity,
  Briefcase,
  Store,
  DollarSign
} from "lucide-react";

const navItems = [
  {
    section: "Análisis",
    items: [
      { href: "/", label: "Dashboard", icon: BarChart3 },
      { href: "/rates", label: "Tasas de Interés", icon: ArrowLeftRight },
      { href: "/valuation", label: "Valoración (VPN/TIR)", icon: TrendingUp },
      { href: "/amortization", label: "Amortización", icon: Table2 },
    ],
  },
  {
    section: "Decisión",
    items: [
      { href: "/capex-opex", label: "CAPEX vs OPEX", icon: Calculator },
      { href: "/montecarlo", label: "Monte Carlo", icon: Dice5 },
    ],
  },
  {
    section: "Startups & Pymes",
    items: [
      { href: "/bootstrapping", label: "Burn Rate & Runway", icon: DollarSign },
      { href: "/venture-capital", label: "Venture Capital (SAFE)", icon: Briefcase },
      { href: "/working-capital", label: "Capital de Trabajo", icon: Store },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="nav-sidebar">
      <div className="nav-brand">
        <h1>FinEngine</h1>
        <p>Motor de Decisión Financiera</p>
      </div>

      {navItems.map((section) => (
        <div key={section.section}>
          <div className="nav-section">{section.section}</div>
          {section.items.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-link ${isActive ? "active" : ""}`}
              >
                <Icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </div>
      ))}

      <div style={{ flex: 1 }} />
      <div
        style={{
          padding: "16px",
          borderTop: "1px solid var(--border)",
          fontSize: "12px",
          color: "var(--text-muted)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Activity size={14} style={{ color: "var(--accent-emerald)" }} />
          <span>API conectada</span>
        </div>
        <span style={{ fontSize: 11, marginTop: 4, display: "block" }}>v0.1.0</span>
      </div>
    </nav>
  );
}
