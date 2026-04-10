"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, users, systems, modules, cases, models

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="测试用例自动化生成平台 API",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS
allow_credentials = settings.CORS_ALLOW_CREDENTIALS
if "*" in settings.CORS_ORIGINS:
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Register routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(systems.router)
app.include_router(modules.router)
app.include_router(cases.router)
app.include_router(models.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "测试用例自动化生成平台 API",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
