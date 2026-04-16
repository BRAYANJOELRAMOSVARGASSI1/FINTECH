"""
excel_builder.py — Generación corporativa de Excel usando openpyxl.

Este módulo toma las respuestas Pydantic del motor financiero y
las transforma en hojas de cálculo profesionales con colores, 
tipografías, formatos de moneda y estilos de celda consistentes.
"""

import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.schemas.capex_opex import CapexVsOpexResponse
from app.schemas.amortization import AmortizationTableResponse
from app.schemas.capex_opex import MonteCarloResponse

# Colores corporativos (FinEngine aesthetics)
PRIMARY_COLOR = "0F172A"  # Slate 900
HEADER_COLOR = "3B82F6"   # Blue 500
SUCCESS_COLOR = "10B981"  # Emerald 500
WARNING_COLOR = "F59E0B"  # Amber 500
DANGER_COLOR = "EF4444"   # Red 500
GRAY_LIGHT = "F8FAFC"     # Slate 50

class ExcelStyles:
    """Clase utilitaria para almacenar estilos de celdas reusables."""
    header_font = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=16, bold=True, color=PRIMARY_COLOR)
    kpi_font = Font(name="Calibri", size=14, bold=True)
    normal_font = Font(name="Calibri", size=11)
    
    header_fill = PatternFill(start_color=HEADER_COLOR, end_color=HEADER_COLOR, fill_type="solid")
    alt_row_fill = PatternFill(start_color=GRAY_LIGHT, end_color=GRAY_LIGHT, fill_type="solid")
    
    center_align = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    
    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0"),
    )

def _apply_badge_style(cell, text: str) -> None:
    """Aplica formato condicional al texto según la clasificación financiera."""
    txt = text.upper()
    if "CAPEX" in txt or "ACCEPT" in txt:
        cell.font = Font(color=SUCCESS_COLOR, bold=True)
    elif "OPEX" in txt or "REJECT" in txt:
        cell.font = Font(color=DANGER_COLOR, bold=True)
    else:
        cell.font = Font(color=WARNING_COLOR, bold=True)

def build_capex_vs_opex_excel(data: CapexVsOpexResponse) -> io.BytesIO:
    """Construye un Excel financiero analizando CAPEX vs OPEX."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Análisis CAPEX vs OPEX"

    # Título y Resumen Ejecutivo
    ws["A1"] = "Análisis Comparativo CAPEX vs OPEX"
    ws["A1"].font = ExcelStyles.title_font
    ws.merge_cells("A1:E1")

    # KPI / Recomendación
    ws["A3"] = "Recomendación:"
    ws["A3"].font = Font(bold=True)
    ws["B3"] = data.recommendation
    _apply_badge_style(ws["B3"], data.recommendation)
    
    ws["A4"] = "Ventaja VPN:"
    ws["B4"] = data.npv_advantage
    ws["B4"].number_format = '"$"#,##0.00'

    ws["A5"] = "Justificación:"
    ws["B5"] = data.explanation
    ws.merge_cells("B5:H5")
    ws["B5"].alignment = Alignment(wrap_text=True)

    # Tabla 1: Flujos de Caja CAPEX
    row = 8
    ws.cell(row=row, column=1, value="Proyección de Flujos CAPEX").font = Font(bold=True, size=12)
    row += 1
    
    capex_headers = ["Período", "Flujo Neto", "Costo Mantenimiento", "Depreciación", "Escudo Fiscal"]
    for col, txt in enumerate(capex_headers, 1):
        c = ws.cell(row=row, column=col, value=txt)
        c.font = ExcelStyles.header_font
        c.fill = ExcelStyles.header_fill
        c.alignment = ExcelStyles.center_align
        c.border = ExcelStyles.thin_border
    
    row += 1
    for i, label in enumerate(data.capex.year_labels):
        ws.cell(row=row, column=1, value=label).alignment = ExcelStyles.center_align
        
        cf = data.capex.cash_flows[i] if i < len(data.capex.cash_flows) else 0
        maint = data.capex.maintenance_costs[i] if i < len(data.capex.maintenance_costs) else 0
        depr = data.capex.depreciation_schedule[i] if i < len(data.capex.depreciation_schedule) else 0
        shield = data.capex.tax_shields[i] if i < len(data.capex.tax_shields) else 0
        
        for col, val in enumerate([cf, maint, depr, shield], 2):
            cell = ws.cell(row=row, column=col, value=val)
            cell.number_format = '"$"#,##0.00'
        
        if row % 2 == 0:
            for c in range(1, len(capex_headers)+1):
                ws.cell(row=row, column=c).fill = ExcelStyles.alt_row_fill
        row += 1

    # Tabla 2: Flujos de Caja OPEX
    row += 3
    ws.cell(row=row, column=1, value="Proyección de Flujos OPEX").font = Font(bold=True, size=12)
    row += 1
    
    opex_headers = ["Período", "Flujo Neto", "Costo Nominal", "Ahorro Fiscal"]
    for col, txt in enumerate(opex_headers, 1):
        c = ws.cell(row=row, column=col, value=txt)
        c.font = ExcelStyles.header_font
        c.fill = ExcelStyles.header_fill
        c.alignment = ExcelStyles.center_align
        c.border = ExcelStyles.thin_border
        
    row += 1
    for i, label in enumerate(data.opex.year_labels):
        ws.cell(row=row, column=1, value=label).alignment = ExcelStyles.center_align
        
        cf = data.opex.cash_flows[i] if i < len(data.opex.cash_flows) else 0
        nominal = data.opex.annual_costs_nominal[i] if i < len(data.opex.annual_costs_nominal) else 0
        saving = data.opex.tax_savings[i] if i < len(data.opex.tax_savings) else 0
        
        for col, val in enumerate([cf, nominal, saving], 2):
            cell = ws.cell(row=row, column=col, value=val)
            cell.number_format = '"$"#,##0.00'
            
        if row % 2 == 0:
            for c in range(1, len(opex_headers)+1):
                ws.cell(row=row, column=c).fill = ExcelStyles.alt_row_fill
        row += 1

    # Ajuste automático de columnas
    for col in range(1, 9):
        ws.column_dimensions[get_column_letter(col)].width = 22

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

def build_amortization_excel(data: AmortizationTableResponse) -> io.BytesIO:
    """Construye un Excel financiero con la tabla de amortización."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Amortización"

    ws["A1"] = f"Tabla de Amortización - Sistema {data.system.capitalize()}"
    ws["A1"].font = ExcelStyles.title_font
    ws.merge_cells("A1:D1")
    
    ws["A3"] = "Principal Solicitado:"
    ws["A3"].font = Font(bold=True)
    ws["B3"] = data.principal_amount
    ws["B3"].number_format = '"$"#,##0.00'
    
    ws["A4"] = "Tasa Anual Efectiva:"
    ws["A4"].font = Font(bold=True)
    ws["B4"] = data.annual_rate
    ws["B4"].number_format = '0.00%'
    
    ws["A5"] = "Total Intereses a Pagar:"
    ws["A5"].font = Font(bold=True)
    ws["B5"] = data.total_interest
    ws["B5"].number_format = '"$"#,##0.00'

    row = 7
    headers = ["Período", "Cuota", "Interés", "Principal", "Saldo Resultante"]
    for col, txt in enumerate(headers, 1):
        c = ws.cell(row=row, column=col, value=txt)
        c.font = ExcelStyles.header_font
        c.fill = ExcelStyles.header_fill
        c.alignment = ExcelStyles.center_align
        c.border = ExcelStyles.thin_border

    row += 1
    for r in data.rows:
        ws.cell(row=row, column=1, value=r.period).alignment = ExcelStyles.center_align
        ws.cell(row=row, column=2, value=r.payment).number_format = '"$"#,##0.00'
        ws.cell(row=row, column=3, value=r.interest).number_format = '"$"#,##0.00'
        ws.cell(row=row, column=4, value=r.principal).number_format = '"$"#,##0.00'
        ws.cell(row=row, column=5, value=r.balance).number_format = '"$"#,##0.00'
        
        if row % 2 == 0:
            for c in range(1, 6):
                ws.cell(row=row, column=c).fill = ExcelStyles.alt_row_fill
        row += 1
        
    for index in range(1, 6):
        ws.column_dimensions[get_column_letter(index)].width = 20

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
