# Deep Sky Target Recommender Backend

深空拍摄目标推荐工具后端 API 服务

## 技术栈

- **Python 3.11+**
- **FastAPI** - 现代高性能异步 Web 框架
- **Pydantic** - 数据验证和序列化
- **Uvicorn** - ASGI 服务器

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── api/                    # API 路由
│   │   ├── locations.py        # 位置相关接口
│   │   ├── equipment.py        # 设备配置接口
│   │   ├── targets.py          # 深空目标接口
│   │   ├── visibility.py       # 可见性计算接口
│   │   └── recommendations.py  # 推荐引擎接口
│   ├── models/                 # Pydantic 模型
│   │   ├── location.py
│   │   ├── equipment.py
│   │   ├── target.py
│   │   ├── recommendation.py
│   │   └── visibility.py
│   ├── services/               # 业务逻辑
│   │   ├── astronomy.py        # 天体位置计算
│   │   ├── visibility.py       # 可见性计算
│   │   ├── scoring.py          # 评分算法
│   │   ├── recommendation.py   # 推荐引擎
│   │   └── mock_data.py        # Mock 数据生成
│   └── utils/                  # 工具函数
│       └── __init__.py
├── data/                       # 数据文件
│   └── catalogs/               # 天文目录
├── tests/                      # 测试
├── requirements.txt            # 依赖
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 快速开始

### 1. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行开发服务器

```bash
python -m app.main
```

或者使用 uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问 API 文档

启动服务后，访问以下地址查看自动生成的 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 位置管理

- `POST /api/v1/locations/geolocate` - 自动定位
- `POST /api/v1/locations/validate` - 验证位置
- `GET /api/v1/locations` - 获取保存的地点
- `POST /api/v1/locations` - 保存地点
- `DELETE /api/v1/locations/{id}` - 删除地点

### 设备配置

- `GET /api/v1/equipment/presets` - 获取预设配置
- `POST /api/v1/equipment/calculate-fov` - 计算 FOV
- `GET /api/v1/equipment` - 获取保存的设备配置
- `POST /api/v1/equipment` - 保存设备配置

### 深空目标

- `GET /api/v1/targets` - 获取所有目标
- `GET /api/v1/targets/{id}` - 获取目标详情
- `GET /api/v1/targets/search?q=` - 搜索目标

### 可见性计算

- `POST /api/v1/visibility/position` - 计算目标实时位置
- `POST /api/v1/visibility/windows` - 计算可见性窗口
- `POST /api/v1/visibility/positions-batch` - 批量计算位置

### 推荐引擎

- `POST /api/v1/recommendations` - 获取推荐目标
- `POST /api/v1/recommendations/by-period` - 按时段获取推荐
- `POST /api/v1/recommendations/summary` - 获取推荐统计

## Docker 部署

### 构建镜像

```bash
docker build -t deep-sky-api .
```

### 运行容器

```bash
docker run -p 8000:8000 deep-sky-api
```

### 使用 Docker Compose

```bash
docker-compose up -d
```

## 环境变量

创建 `.env` 文件配置环境变量：

```env
# 应用配置
APP_NAME=Deep Sky Target Recommender
APP_VERSION=1.0.0

# Mock 模式
MOCK_MODE=true

# 天文数据库配置
USE_ONLINE_DATABASES=false
SIMBAD_TIMEOUT=30
GAIA_TIMEOUT=60
```

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black app/
flake8 app/
mypy app/
```

## 功能特性

- ✅ RESTful API 设计
- ✅ 自动生成 OpenAPI 文档
- ✅ Pydantic 数据验证
- ✅ CORS 支持
- ✅ Mock 数据支持
- ✅ 天体位置计算
- ✅ 可见性分析
- ✅ 智能推荐算法

## 许可证

MIT License
