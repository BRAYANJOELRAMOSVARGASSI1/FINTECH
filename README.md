# FinEngine — Motor de Decisión Financiera y Riesgo

> Motor de decisión para análisis financiero empresarial: conversión de tasas, valoración de proyectos, tablas de amortización, análisis CAPEX vs OPEX y simulación de Monte Carlo.

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Backend API | Python 3.12 + FastAPI |
| Matemáticas | numpy + numpy-financial + pandas |
| Validación | Pydantic v2 |
| Base de Datos | PostgreSQL + TimescaleDB (fase 3) |
| Frontend | Next.js + Tailwind CSS (fase 4) |
| Gráficos | Recharts (fase 4) |
| Exportación | openpyxl (fase 5) |

## Quick Start

```bash
# 1. Crear virtual environment
cd backend
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar tests
pytest tests/ -v

# 4. Levantar servidor
uvicorn app.main:app --reload --port 8000

# 5. Ver documentación API
# → http://localhost:8000/docs (Swagger)
# → http://localhost:8000/redoc (ReDoc)
```

## API Endpoints

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/api/v1/rates/convert` | Tasa nominal → TEA |
| POST | `/api/v1/rates/compare` | Comparar múltiples tasas |
| POST | `/api/v1/rates/fisher` | Ecuación de Fisher (tasa real) |
| POST | `/api/v1/rates/wacc` | Calcular WACC |
| POST | `/api/v1/valuation/npv` | Valor Presente Neto |
| POST | `/api/v1/valuation/irr` | Tasa Interna de Retorno |
| POST | `/api/v1/valuation/fcf` | Flujo de Caja Libre |
| POST | `/api/v1/valuation/full` | Valoración completa |
| POST | `/api/v1/amortization/schedule` | Tabla de amortización |
| POST | `/api/v1/amortization/compare` | Comparar 3 sistemas |
| POST | `/api/v1/analysis/capex-vs-opex` | Análisis CAPEX vs OPEX |
| POST | `/api/v1/analysis/montecarlo` | Simulación Monte Carlo |

## Arquitectura

```
backend/app/
├── core/          ← Motor matemático puro (sin dependencias de framework)
│   ├── rates.py         (Conversión universal de tasas)
│   ├── valuation.py     (VPN, TIR, FCF, Payback, PI)
│   ├── taxes.py         (Depreciación, escudos fiscales)
│   ├── amortization.py  (Francés, Alemán, Americano)
│   ├── capex_opex.py    (Análisis comparativo)
│   └── montecarlo.py    (Simulación de riesgo)
├── schemas/       ← Validación Pydantic v2
├── api/v1/        ← Endpoints FastAPI
├── models/        ← SQLAlchemy ORM (fase 3)
├── services/      ← Lógica de negocio
└── export/        ← Exportación Excel
```

## Licencia

Propiedad privada — Todos los derechos reservados.
