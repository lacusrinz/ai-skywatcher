"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api import locations, equipment, targets, visibility, recommendations
from app.config import settings

app = FastAPI(
    title="Deep Sky Target Recommender API",
    description="深空拍摄目标推荐工具后端API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite 默认端口
        "http://localhost:3000",  # 其他开发服务器
        "http://localhost:8000",  # 生产环境
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(
    locations.router,
    prefix="/api/v1/locations",
    tags=["locations"]
)

app.include_router(
    equipment.router,
    prefix="/api/v1/equipment",
    tags=["equipment"]
)

app.include_router(
    targets.router,
    prefix="/api/v1/targets",
    tags=["targets"]
)

app.include_router(
    visibility.router,
    prefix="/api/v1/visibility",
    tags=["visibility"]
)

app.include_router(
    recommendations.router,
    prefix="/api/v1/recommendations",
    tags=["recommendations"]
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Deep Sky Target Recommender API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
