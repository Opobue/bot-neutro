[1mdiff --git a/.github/workflows/ci_tests.yml b/.github/workflows/ci_tests.yml[m
[1mindex 9f33032..2f57b5f 100644[m
[1m--- a/.github/workflows/ci_tests.yml[m
[1m+++ b/.github/workflows/ci_tests.yml[m
[36m@@ -23,8 +23,6 @@[m [mjobs:[m
           python -m pip install --upgrade pip[m
           pip install -e ".[dev]"[m
 [m
[31m-      - name: Run pytest[m
[31m-        run: pytest -q[m
 [m
       - name: Run coverage[m
         run: pytest --cov=src --cov-fail-under=80[m
[1mdiff --git a/src/bot_neutro/api.py b/src/bot_neutro/api.py[m
[1mindex c42c6ee..88bec04 100644[m
[1m--- a/src/bot_neutro/api.py[m
[1m+++ b/src/bot_neutro/api.py[m
[36m@@ -60,7 +60,15 @@[m [mdef _parse_stats_max_sessions() -> int:[m
     return value[m
 [m
 [m
[31m-STATS_MAX_SESSIONS = _parse_stats_max_sessions()[m
[32m+[m
[32m+[m[32mdef _parse_cors_origins() -> list[str]:[m
[32m+[m[32m    raw = os.getenv("MUNAY_CORS_ORIGINS", "")[m
[32m+[m[32m    if not raw:[m
[32m+[m[32m        return ["http://localhost:5173", "http://127.0.0.1:5173"][m
[32m+[m[32m    return [origin.strip() for origin in raw.split(",") if origin.strip()][m
[32m+[m
[32m+[m
[32m+[m[32mCORS_ORIGINS = _parse_cors_origins()[m
 [m
 [m
 def _with_outcome(response, outcome: str = "ok", detail: str | None = None) -> None:[m
[36m@@ -82,14 +90,10 @@[m [mdef create_app() -> FastAPI:[m
         llm_provider=build_llm_provider(),[m
     )[m
 [m
[31m-    origins = [[m
[31m-        "http://localhost:5173",[m
[31m-        "http://127.0.0.1:5173",[m
[31m-    ][m
 [m
     app.add_middleware([m
         CORSMiddleware,[m
[31m-        allow_origins=origins,[m
[32m+[m[32m        allow_origins=CORS_ORIGINS,[m
         allow_credentials=True,[m
         allow_methods=["*"],[m
         allow_headers=["*"],[m
[36m@@ -106,6 +110,22 @@[m [mdef create_app() -> FastAPI:[m
         response.headers.setdefault("X-Outcome", "ok")[m
         return response[m
 [m
[32m+[m[32m    @app.exception_handler(Exception)[m
[32m+[m[32m    async def global_exception_handler(request: Request, exc: Exception):[m
[32m+[m[32m        corr_id = request.headers.get("X-Correlation-Id") or str(uuid4())[m
[32m+[m[32m        logger.exception([m
[32m+[m[32m            "Unhandled exception",[m
[32m+[m[32m            exc_info=exc,[m
[32m+[m[32m            extra={"corr_id": corr_id}[m
[32m+[m[32m        )[m
[32m+[m[32m        response = JSONResponse([m
[32m+[m[32m            {"detail": "Internal Server Error"},[m
[32m+[m[32m            status_code=500[m
[32m+[m[32m        )[m
[32m+[m[32m        _with_outcome(response, outcome="error", detail="internal_error")[m
[32m+[m[32m        response.headers["X-Correlation-Id"] = corr_id[m
[32m+[m[32m        return response[m
[32m+[m
     @app.get("/healthz")[m
     async def healthcheck(request: Request):[m
         METRICS.inc_request("/healthz")[m
