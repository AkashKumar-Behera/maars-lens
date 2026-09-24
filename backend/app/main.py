from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.core.config import settings
from app.core.ratelimit import limiter
from app.routers import auth, scans, rules, violations, customers, admin, reports, notifications, areas, products, inquiries

app = FastAPI(title="MAARS Lens API", version="1.0.0")
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )

app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(scans.router, prefix="/api/v1/scans", tags=["scans"])
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(rules.router, prefix="/api/v1/rules", tags=["rules"])
app.include_router(violations.router, prefix="/api/v1/violations", tags=["violations"])
app.include_router(customers.router, prefix="/api/v1/customer", tags=["customers"])
app.include_router(inquiries.router, prefix="/api/v1/inquiries", tags=["inquiries"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(areas.router, prefix="/api/v1/areas", tags=["areas"])

import os
from fastapi.staticfiles import StaticFiles
os.makedirs("uploads/proofs", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def read_root():
    return {"message": "MAARS Lens API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "maars-lens-api"}


@app.get("/health/ocr")
def ocr_health_check():
    from fastapi.responses import JSONResponse
    from app.services.ocr.extractor import PaddleOCRExtractor

    engine_type = settings.OCR_ENGINE.lower().strip()
    if engine_type == "mock":
        return {
            "status": "ok",
            "engine": "mock",
            "mode": "SIMULATED",
            "languages_loaded": ["en", "hi"],
            "warning": "Mock OCR is active for unit testing only. Do not use in production.",
        }

    status_data = PaddleOCRExtractor.get_health_status()
    if status_data.get("status") != "ok":
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "engine": "paddleocr",
                "detail": status_data.get("error", "PaddleOCR failed to initialize"),
            },
        )

    return status_data
