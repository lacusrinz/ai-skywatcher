# Deep Sky Target Recommender Backend

深空拍摄目标推荐工具后端 API 服务

## 技术栈

- **Python 3.11+**
- **FastAPI** - 现代高性能异步 Web 框架
- **Pydantic** - 数据验证和序列化
- **Uvicorn** - ASGI 服务器
- **SQLite** - 嵌入式数据库
- **aiosqlite** - 异步SQLite操作
- **httpx** - 异步HTTP客户端（SIMBAD API）

## 真实天文数据

本系统使用真实的深空天体数据库，替代之前的mock数据：

- **本地数据库**: SQLite数据库存储 ~13,000个深空天体
  - 数据来源: OpenNGC (开放NGC/IC/Messier目录)
  - 包含: Messier (110), Caldwell (109), NGC/IC (~13,000) 天体
  - 数据字段: 名称、类型、坐标、星等、尺寸、星座、观测信息等

- **API回退**: 自动回退到SIMBAD TAP API查询本地数据库中缺失的天体
  - 查询速度: 本地数据库 ~1-5ms，SIMBAD API ~200-500ms
  - 自动缓存: SIMBAD查询结果自动缓存到本地数据库

- **数据覆盖**:
  - 星系 (GALAXY): ~5,000个
  - 星云 (NEBULA): ~4,000个
  - 星团 (CLUSTER): ~3,000个
  - 行星状星云 (PLANETARY): ~1,000个

### 数据库结构

```
backend/app/data/deep_sky.db
├── objects          # 主表：天体基本信息
├── aliases          # 别名表：NGC/IC/Messier编号
└── observational_info # 观测信息表：最佳观测月份、难度等
```

详细文档: [DATABASE.md](docs/DATABASE.md)

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── data/                   # 数据文件
│   │   ├── deep_sky.db        # SQLite数据库 (~13,000天体)
│   │   └── schema.sql         # 数据库结构定义
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
│   │   ├── visibility.py
│   │   └── database.py        # 数据库模型
│   ├── services/               # 业务逻辑
│   │   ├── astronomy.py        # 天体位置计算 + 数据查询入口
│   │   ├── database.py        # 本地数据库服务
│   │   ├── simbad.py          # SIMBAD API服务
│   │   ├── visibility.py       # 可见性计算
│   │   ├── scoring.py          # 评分算法
│   │   ├── recommendation.py   # 推荐引擎
│   │   └── mock_data.py        # Mock数据生成（已弃用）
│   └── utils/                  # 工具函数
│       └── __init__.py
├── docs/                       # 文档
│   └── DATABASE.md            # 数据库详细文档
├── tests/                      # 测试
│   ├── test_database_*.py      # 数据库相关测试
│   ├── test_simbad_service.py  # SIMBAD服务测试
│   ├── test_astronomy_service.py # 天文服务测试
│   └── test_api_targets.py    # API端点测试
├── scripts/                    # 工具脚本
│   └── import_openngc.py      # OpenNGC数据导入脚本
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

**新增端点 (v2.0 - 真实数据库)**:

- `GET /api/v1/targets/{id}` - 获取天体详情（支持M/NGC/IC编号）
  - 本地数据库查询: ~1-5ms
  - 自动回退SIMBAD API: ~200-500ms
  - 自动缓存API结果

- `GET /api/v1/targets/search?q=` - 搜索天体（按名称或别名）
  - 支持模糊搜索
  - 限制返回数量（默认20条）

- `GET /api/v1/targets/stats` - 获取数据库统计信息
  - 天体总数
  - 按类型分布
  - 覆盖的星座数量

- `GET /api/v1/targets` - 列出天体（支持过滤）
  - 按类型过滤: `?type=GALAXY`
  - 按星座过滤: `?constellation=Orion`
  - 分页支持: `?page=1&page_size=20`

- `POST /api/v1/targets/sync` - 手动触发SIMBAD同步
  - 用于刷新特定天体的数据
  - 或添加新天体到本地数据库

**旧版端点（已弃用）**:

- `GET /api/v1/targets` - 获取所有目标（仍可用，使用mock数据）

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

### 核心功能
- ✅ 真实天文数据库（~13,000深空天体）
- ✅ 本地SQLite数据库（快速查询）
- ✅ SIMBAD API集成（自动回退）
- ✅ 智能缓存机制（API结果自动缓存）
- ✅ RESTful API设计
- ✅ 自动生成OpenAPI文档
- ✅ Pydantic数据验证
- ✅ CORS支持
- ✅ 异步IO（高性能）

### 天文计算
- ✅ 天体位置计算（赤道坐标 ↔ 地平坐标）
- ✅ 可见性分析（升起、中天、落下时间）
- ✅ 智能推荐算法（综合评分系统）

### 数据来源
- **OpenNGC**: 开放的NGC/IC/Messier目录数据库
- **SIMBAD**: 专业天文数据库（CDS Strasbourg）
- **License**: OpenNGC使用CC-BY-SA-4.0许可证

## 许可证

MIT License
