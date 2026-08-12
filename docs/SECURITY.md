# FinSight Security Hardening

## 1. Authentication & Authorization
- The API is secured via JWT (JSON Web Tokens).
- `SECRET_KEY` is loaded securely via environment variables (never committed to source).
- User passwords (if implemented) are hashed using `bcrypt` via `passlib`.

## 2. Network Security
- CORS policies in `main.py` restrict origins in production.
- Database ports (5432) are internal to the VPC and not exposed to the public internet.

## 3. Data Integrity
- SQLAlchemy ORM parameterization prevents SQL Injection natively.
- No dynamic shell execution (`os.system` / `subprocess.Popen`) accepts untrusted user input, preventing Command Injection.

## 4. Secrets Management
- All API Keys (AlphaVantage, FRED, NewsAPI) and Database credentials are moved to a secret manager or `.env` file at deployment.
- Developers use `.env.template` to bootstrap local environments.
