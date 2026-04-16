"""
api/v1/export.py — Endpoints para descargar respuestas Pydantic como archivos Excel.
"""

from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.capex_opex import CapexVsOpexResponse
from app.schemas.amortization import AmortizationTableResponse
from app.export.excel_builder import build_capex_vs_opex_excel, build_amortization_excel

router = APIRouter(prefix="/export", tags=["Exportación"])

@router.post(
    "/excel/capex-vs-opex",
    response_class=StreamingResponse,
    summary="Exportar análisis CAPEX vs OPEX a Excel",
    description="Convierte un JSON de respuesta CapexVsOpexResponse en un archivo .xlsx formateado."
)
async def export_capex_vs_opex(data: CapexVsOpexResponse):
    """Genera streaming de un Excel a partir de datos financieros."""
    try:
        excel_io = build_capex_vs_opex_excel(data)
        
        headers = {
            "Content-Disposition": 'attachment; filename="capex_opex_analysis.xlsx"',
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        return StreamingResponse(
            iter([excel_io.getvalue()]), 
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando Excel: {str(e)}")

@router.post(
    "/excel/amortization",
    response_class=StreamingResponse,
    summary="Exportar Tabla de Amortización a Excel",
    description="Convierte un JSON de respuesta de amortización en un archivo .xlsx."
)
async def export_amortization(data: AmortizationTableResponse):
    """Genera streaming de la tabla de amortización."""
    try:
        excel_io = build_amortization_excel(data)
        
        headers = {
            "Content-Disposition": f'attachment; filename="amortizacion_{data.system}.xlsx"',
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        return StreamingResponse(
            iter([excel_io.getvalue()]), 
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando Excel: {str(e)}")
