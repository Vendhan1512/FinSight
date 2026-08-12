# FinSight

FinSight is a robust data science and machine learning platform for financial insights, offering a complete data pipeline, ML model serving, and a modern frontend interface.

## Tech Stack
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic
- **Data Science/ML:** Pandas, NumPy, SciPy, Scikit-learn, Statsmodels, XGBoost, LightGBM, SHAP
- **Frontend:** React, TypeScript, Tailwind CSS (via Vite)
- **Database:** PostgreSQL
- **DevOps:** Docker, Docker Compose, GitHub Actions

## Data Sources
- **Market Data:** Alpha Vantage
- **Fundamental Data:** SEC EDGAR
- **Economic Data:** FRED
- **News:** NewsAPI

## Setup Instructions

1. **Clone the repository.**
2. **Setup Environment Variables:**
   Copy `.env.example` to `.env` and fill in your API keys and configuration.
   ```bash
   cp .env.example .env
   ```
3. **Run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```
4. **Access the Application:**
   - Frontend: [http://localhost:5173](http://localhost:5173)
   - Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
