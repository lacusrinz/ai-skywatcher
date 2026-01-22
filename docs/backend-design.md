# 深空拍摄目标推荐工具 - 后端开发文档

**创建日期**: 2025-01-22
**技术栈**: Python 3.11+
**API 设计**: RESTful API
**数据策略**: Mock 接口

---

## 1. 后端架构概述

### 1.1 技术选型

**Web 框架**
- **FastAPI** - 现代高性能异步框架
  - 自动生成 OpenAPI 文档
  - 类型注解支持
  - 原生异步支持

**数据处理**
- **Pydantic** - 数据验证和序列化
- **astroquery** - 天文数据库查询 (SIMBAD, Gaia, VizieR)
- **skyfield** - 天体位置计算
- **astropy** - 天文数据处理
- **dateutil/pytz** - 时区处理

**数据存储**
- **JSON 文件** - Mock 数据存储（开发阶段）
- **SQLite** (可选) - 本地缓存

**部署**
- **uvicorn** - ASGI 服务器
- **Docker** - 容器化部署

### 1.2 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   │
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── locations.py        # 位置相关接口
│   │   ├── equipment.py        # 设备配置接口
│   │   ├── targets.py          # 深空目标接口
│   │   ├── visibility.py       # 可见性计算接口
│   │   └── recommendations.py  # 推荐引擎接口
│   │
│   ├── models/                 # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── location.py
│   │   ├── equipment.py
│   │   ├── target.py
│   │   └── recommendation.py
│   │
│   ├── services/               # 业务逻辑
│   │   ├── __init__.py
│   │   ├── astronomy.py        # 天体位置计算
│   │   ├── visibility.py       # 可见性计算
│   │   ├── scoring.py          # 评分算法
│   │   ├── mock_data.py        # Mock 数据生成
│   │   └── databases.py        # 天文数据库集成
│   │
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── coordinates.py      # 坐标转换
│       └── time_utils.py       # 时间处理
│
├── data/                       # 数据文件
│   ├── catalogs/               # 天文目录
│   │   ├── messier.json        # Messier 目录
│   │   ├── ngc.json            # NGC 目录
│   │   └── opengc.csv          # OpenNGC 完整数据
│   ├── deepsky_objects.json    # 深空天体数据库 (生成)
│   └── locations.json          # 预设地点
│
├── tests/                      # 测试
│   ├── test_api/
│   ├── test_services/
│   └── conftest.py
│
├── requirements.txt            # 依赖
├── Dockerfile
└── README.md
```

---

## 2. API 接口设计

### 2.1 基础信息

**Base URL**: `http://localhost:8000/api/v1`

**通用响应格式**

成功响应:
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

错误响应:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": [ ... ]
  }
}
```

### 2.2 位置管理 API

#### 2.2.1 自动定位

**端点**: `POST /locations/geolocate`

**请求**: 无需请求体

**响应**:
```json
{
  "success": true,
  "data": {
    "name": "自动定位",
    "latitude": 39.9042,
    "longitude": 116.4074,
    "timezone": "Asia/Shanghai",
    "country": "CN",
    "region": "Beijing"
  }
}
```

**Mock 策略**:
- 开发环境返回固定坐标（北京/上海/纽约）
- 可通过请求参数 `?mock_city=shanghai` 切换

#### 2.2.2 手动输入位置

**端点**: `POST /locations/validate`

**请求**:
```json
{
  "latitude": 40.4461,
  "longitude": -79.9822
}
```

或度分秒格式:
```json
{
  "latitude_dms": "40°26'46\"N",
  "longitude_dms": "79°58'56\"W"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "latitude": 40.4461,
    "longitude": -79.9822,
    "timezone": "America/New_York",
    "validated": true
  }
}
```

#### 2.2.3 保存常用地点

**端点**: `POST /locations`

**请求**:
```json
{
  "name": "常用观测点",
  "latitude": 39.9042,
  "longitude": 116.4074,
  "timezone": "Asia/Shanghai"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "loc_12345",
    "name": "常用观测点",
    "latitude": 39.9042,
    "longitude": 116.4074,
    "timezone": "Asia/Shanghai",
    "created_at": "2025-01-22T10:30:00Z"
  }
}
```

#### 2.2.4 获取保存的地点列表

**端点**: `GET /locations`

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": "loc_12345",
      "name": "常用观测点",
      "latitude": 39.9042,
      "longitude": 116.4074,
      "timezone": "Asia/Shanghai",
      "is_default": true
    }
  ]
}
```

---

### 2.3 设备配置 API

#### 2.3.1 获取预设配置

**端点**: `GET /equipment/presets`

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": "preset_ff_200mm",
      "name": "全画幅 + 200mm",
      "sensor_size": "full-frame",
      "sensor_width": 36.0,
      "sensor_height": 24.0,
      "focal_length": 200,
      "fov_horizontal": 10.3,
      "fov_vertical": 6.9
    },
    {
      "id": "preset_apsc_85mm",
      "name": "APS-C + 85mm",
      "sensor_size": "aps-c",
      "sensor_width": 23.6,
      "sensor_height": 15.6,
      "focal_length": 85,
      "fov_horizontal": 15.2,
      "fov_vertical": 10.1
    }
  ]
}
```

#### 2.3.2 计算 FOV

**端点**: `POST /equipment/calculate-fov`

**请求**:
```json
{
  "sensor_width": 36.0,
  "sensor_height": 24.0,
  "focal_length": 200
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "fov_horizontal": 10.3,
    "fov_vertical": 6.9,
    "fov_diagonal": 12.4,
    "aspect_ratio": "3:2"
  }
}
```

**计算公式**:
```python
import math

def calculate_fov(sensor_size, focal_length):
    """计算视场角"""
    fov_rad = 2 * math.atan(sensor_size / (2 * focal_length))
    fov_deg = math.degrees(fov_rad)
    return fov_deg
```

#### 2.3.3 保存设备配置

**端点**: `POST /equipment`

**请求**:
```json
{
  "name": "我的设备",
  "sensor_size": "full-frame",
  "sensor_width": 36.0,
  "sensor_height": 24.0,
  "focal_length": 200,
  "custom_name": "全画幅+200mm"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "eq_67890",
    "name": "我的设备",
    "fov_horizontal": 10.3,
    "fov_vertical": 6.9
  }
}
```

---

### 2.4 深空目标 API

#### 2.4.1 获取所有目标

**端点**: `GET /targets`

**查询参数**:
- `type`: `emission-nebula` | `galaxy` | `cluster` | `planetary-nebula`
- `constellation`: 星座名称
- `min_magnitude`: 最小星等
- `max_magnitude`: 最大星等
- `page`: 页码
- `page_size`: 每页数量

**响应**:
```json
{
  "success": true,
  "data": {
    "targets": [
      {
        "id": "M42",
        "name": "猎户座大星云",
        "name_en": "Orion Nebula",
        "type": "emission-nebula",
        "ra": 83.633,
        "dec": -5.391,
        "magnitude": 4.0,
        "size": 85,
        "constellation": "Orion",
        "difficulty": 1,
        "optimal_fov": {
          "min": 100,
          "max": 400
        }
      }
    ],
    "total": 300,
    "page": 1,
    "page_size": 20
  }
}
```

#### 2.4.2 获取单个目标详情

**端点**: `GET /targets/{target_id}`

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "M42",
    "name": "猎户座大星云",
    "name_en": "Orion Nebula",
    "type": "emission-nebula",
    "ra": 83.633,
    "dec": -5.391,
    "magnitude": 4.0,
    "size": 85,
    "constellation": "Orion",
    "difficulty": 1,
    "description": "最明亮的弥漫星云...",
    "optimal_season": ["December", "January", "February"],
    "optimal_fov": {
      "min": 100,
      "max": 400
    },
    "tags": ["nebula", "emission", "bright"]
  }
}
```

#### 2.4.3 搜索目标

**端点**: `GET /targets/search`

**查询参数**:
- `q`: 搜索关键词（名称、Messier编号、星座）

**响应**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "M42",
        "name": "猎户座大星云",
        "type": "emission-nebula",
        "magnitude": 4.0
      }
    ]
  }
}
```

---

### 2.5 可视区域管理 API

#### 2.5.1 创建可视区域

**端点**: `POST /visible-zones`

**请求**:
```json
{
  "name": "东侧空地",
  "polygon": [
    [90, 20],
    [120, 20],
    [120, 60],
    [90, 60]
  ],
  "priority": 1
}
```

**坐标说明**: `[方位角, 高度角]`

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "zone_abc123",
    "name": "东侧空地",
    "polygon": [
      [90, 20],
      [120, 20],
      [120, 60],
      [90, 60]
    ],
    "priority": 1,
    "azimuth_range": [90, 120],
    "altitude_range": [20, 60]
  }
}
```

#### 2.5.2 更新可视区域

**端点**: `PUT /visible-zones/{zone_id}`

**请求**: 同创建

**响应**: 同创建

#### 2.5.3 删除可视区域

**端点**: `DELETE /visible-zones/{zone_id}`

**响应**:
```json
{
  "success": true,
  "message": "可视区域已删除"
}
```

#### 2.5.4 获取可视区域列表

**端点**: `GET /visible-zones`

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": "zone_abc123",
      "name": "东侧空地",
      "polygon": [...],
      "priority": 1
    }
  ]
}
```

---

### 2.6 可见性计算 API

#### 2.6.1 计算目标实时位置

**端点**: `POST /visibility/position`

**请求**:
```json
{
  "target_id": "M42",
  "location": {
    "latitude": 39.9042,
    "longitude": 116.4074
  },
  "timestamp": "2025-01-22T20:30:00+08:00"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "target_id": "M42",
    "altitude": 45.2,
    "azimuth": 135.6,
    "rise_time": "2025-01-22T18:30:00+08:00",
    "set_time": "2025-01-23T04:15:00+08:00",
    "transit_time": "2025-01-22T23:22:00+08:00",
    "transit_altitude": 68.5,
    "is_visible": true
  }
}
```

#### 2.6.2 计算目标可见性窗口

**端点**: `POST /visibility/windows`

**请求**:
```json
{
  "target_id": "M42",
  "location": {
    "latitude": 39.9042,
    "longitude": 116.4074
  },
  "date": "2025-01-22",
  "visible_zones": [
    {
      "id": "zone_1",
      "polygon": [[90, 20], [120, 20], [120, 60], [90, 60]]
    }
  ]
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "target_id": "M42",
    "windows": [
      {
        "zone_id": "zone_1",
        "start_time": "2025-01-22T20:30:00+08:00",
        "end_time": "2025-01-22T23:45:00+08:00",
        "max_altitude": 65.0,
        "max_altitude_time": "2025-01-22T22:15:00+08:00",
        "duration_minutes": 195
      }
    ],
    "total_duration_minutes": 195
  }
}
```

#### 2.6.3 批量计算多个目标位置

**端点**: `POST /visibility/positions-batch`

**请求**:
```json
{
  "target_ids": ["M42", "M31", "M45"],
  "location": {
    "latitude": 39.9042,
    "longitude": 116.4074
  },
  "timestamp": "2025-01-22T20:30:00+08:00"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "positions": [
      {
        "target_id": "M42",
        "altitude": 45.2,
        "azimuth": 135.6,
        "is_visible": true
      },
      {
        "target_id": "M31",
        "altitude": 32.1,
        "azimuth": 89.5,
        "is_visible": true
      }
    ]
  }
}
```

---

### 2.7 推荐引擎 API

#### 2.7.1 获取推荐目标

**端点**: `POST /recommendations`

**请求**:
```json
{
  "location": {
    "latitude": 39.9042,
    "longitude": 116.4074,
    "timezone": "Asia/Shanghai"
  },
  "date": "2025-01-22",
  "equipment": {
    "fov_horizontal": 10.3,
    "fov_vertical": 6.9
  },
  "visible_zones": [
    {
      "id": "zone_1",
      "polygon": [[90, 20], [120, 20], [120, 60], [90, 60]]
    }
  ],
  "filters": {
    "min_magnitude": 6,
    "types": ["emission-nebula", "galaxy"],
    "min_score": 50
  },
  "sort_by": "score",
  "limit": 20
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "target": {
          "id": "M42",
          "name": "猎户座大星云",
          "type": "emission-nebula",
          "magnitude": 4.0,
          "size": 85,
          "constellation": "Orion"
        },
        "visibility_windows": [
          {
            "zone_id": "zone_1",
            "start_time": "2025-01-22T20:30:00+08:00",
            "end_time": "2025-01-22T23:45:00+08:00",
            "max_altitude": 65.0,
            "max_altitude_time": "2025-01-22T22:15:00+08:00"
          }
        ],
        "current_position": {
          "altitude": 45.2,
          "azimuth": 135.6,
          "timestamp": "2025-01-22T20:30:00+08:00"
        },
        "score": 87,
        "score_breakdown": {
          "altitude": 38,
          "brightness": 28,
          "fov_match": 15,
          "duration": 6
        },
        "period": "tonight-golden"
      }
    ],
    "summary": {
      "total": 45,
      "by_period": {
        "tonight-golden": 18,
        "post-midnight": 15,
        "pre-dawn": 12
      }
    }
  }
}
```

#### 2.7.2 按时段获取推荐

**端点**: `POST /recommendations/by-period`

**请求**: 同上，额外添加 `period` 参数

```json
{
  "period": "tonight-golden",
  ...
}
```

**可选时段**:
- `tonight-golden`: 日落后2小时至午夜
- `post-midnight`: 午夜至凌晨3点
- `pre-dawn`: 凌晨3点至天文晨光前

**响应**: 同普通推荐，但只返回指定时段的目标

#### 2.7.3 获取推荐统计

**端点**: `POST /recommendations/summary`

**请求**: 同推荐接口

**响应**:
```json
{
  "success": true,
  "data": {
    "total_targets": 45,
    "visible_targets": 38,
    "high_score_targets": 12,
    "by_type": {
      "emission-nebula": 15,
      "galaxy": 12,
      "cluster": 18,
      "planetary-nebula": 5
    },
    "by_period": {
      "tonight-golden": 18,
      "post-midnight": 15,
      "pre-dawn": 12
    },
    "average_score": 72.5
  }
}
```

---

### 2.8 天空图数据 API

#### 2.8.1 获取天空图数据

**端点**: `POST /sky-map/data`

**请求**:
```json
{
  "location": {
    "latitude": 39.9042,
    "longitude": 116.4074
  },
  "timestamp": "2025-01-22T20:30:00+08:00",
  "include_targets": true,
  "target_types": ["emission-nebula", "galaxy", "cluster"]
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "timestamp": "2025-01-22T20:30:00+08:00",
    "location": {
      "latitude": 39.9042,
      "longitude": 116.4074
    },
    "grid": {
      "altitude_lines": [0, 15, 30, 45, 60, 75, 90],
      "azimuth_labels": {
        "0": "N",
        "90": "E",
        "180": "S",
        "270": "W"
      }
    },
    "targets": [
      {
        "id": "M42",
        "name": "猎户座大星云",
        "altitude": 45.2,
        "azimuth": 135.6,
        "type": "emission-nebula",
        "magnitude": 4.0,
        "color": "#FF6B6B"
      }
    ],
    "reference_lines": {
      "ecliptic": [[...]],
      "celestial_equator": [[...]]
    }
  }
}
```

#### 2.8.2 获取时间轴数据

**端点**: `POST /sky-map/timeline`

**请求**:
```json
{
  "location": {
    "latitude": 39.9042,
    "longitude": 116.4074
  },
  "date": "2025-01-22",
  "interval_minutes": 30,
  "target_ids": ["M42", "M31"]
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "date": "2025-01-22",
    "timeline": [
      {
        "timestamp": "2025-01-22T18:00:00+08:00",
        "targets": [
          {
            "id": "M42",
            "altitude": 25.3,
            "azimuth": 110.2
          }
        ]
      }
    ]
  }
}
```

---

## 3. 数据模型

### 3.1 Pydantic 模型定义

#### Location 模型
```python
from pydantic import BaseModel, Field
from typing import Optional

class Location(BaseModel):
    name: str
    latitude: float = Field(..., ge=-90, le=90, description="纬度")
    longitude: float = Field(..., ge=-180, le=180, description="经度")
    timezone: str
    country: Optional[str] = None
    region: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "北京",
                "latitude": 39.9042,
                "longitude": 116.4074,
                "timezone": "Asia/Shanghai"
            }
        }
```

#### Equipment 模型
```python
class Equipment(BaseModel):
    name: str
    sensor_size: str = Field(..., pattern="^(full-frame|aps-c|m4/3|custom)$")
    sensor_width: float = Field(..., gt=0, description="传感器宽度 (mm)")
    sensor_height: float = Field(..., gt=0, description="传感器高度 (mm)")
    focal_length: float = Field(..., gt=0, description="焦距 (mm)")
    fov_horizontal: Optional[float] = None
    fov_vertical: Optional[float] = None
```

#### DeepSkyTarget 模型
```python
class DeepSkyTarget(BaseModel):
    id: str
    name: str
    name_en: str
    type: str = Field(..., pattern="^(emission-nebula|galaxy|cluster|planetary-nebula)$")
    ra: float = Field(..., ge=0, le=360, description="赤经 (度)")
    dec: float = Field(..., ge=-90, le=90, description="赤纬 (度)")
    magnitude: float
    size: float = Field(..., description="视大小 (角分)")
    constellation: str
    difficulty: int = Field(..., ge=1, le=5)
    description: Optional[str] = None
```

#### VisibleZone 模型
```python
from typing import List, Tuple

class VisibleZone(BaseModel):
    id: str
    name: str
    polygon: List[Tuple[float, float]] = Field(..., description="[方位角, 高度角]")
    priority: int = Field(default=1, ge=1, le=10)
```

#### Recommendation 模型
```python
class ScoreBreakdown(BaseModel):
    altitude: int = Field(..., ge=0, le=50)
    brightness: int = Field(..., ge=0, le=30)
    fov_match: int = Field(..., ge=0, le=20)
    duration: int = Field(..., ge=0, le=10)

class VisibilityWindow(BaseModel):
    zone_id: str
    start_time: str
    end_time: str
    max_altitude: float
    max_altitude_time: str

class TargetPosition(BaseModel):
    altitude: float
    azimuth: float
    timestamp: str

class Recommendation(BaseModel):
    target: DeepSkyTarget
    visibility_windows: List[VisibilityWindow]
    current_position: TargetPosition
    score: int = Field(..., ge=0, le=100)
    score_breakdown: ScoreBreakdown
    period: str
```

---

## 4. 业务逻辑设计

### 4.1 天体位置计算服务

**文件**: `app/services/astronomy.py`

```python
from typing import Tuple
from datetime import datetime
import math

class AstronomyService:
    """天体位置计算服务"""

    def __init__(self):
        # Mock 数据: 使用简化算法
        pass

    def calculate_position(
        self,
        target_ra: float,
        target_dec: float,
        observer_lat: float,
        observer_lon: float,
        timestamp: datetime
    ) -> Tuple[float, float]:
        """
        计算目标的当前高度角和方位角

        Args:
            target_ra: 目标赤经 (度)
            target_dec: 目标赤纬 (度)
            observer_lat: 观测者纬度
            observer_lon: 观测者经度
            timestamp: 时间戳

        Returns:
            (altitude, azimuth) 高度角和方位角 (度)
        """
        # Mock 实现: 使用简化算法
        # 生产环境使用 skyfield 或 astronomy-engine

        # 1. 计算本地恒星时
        lst = self._calculate_local_sidereal_time(observer_lon, timestamp)

        # 2. 计算时角
        ha = lst - target_ra

        # 3. 转换为地平坐标
        alt, az = self._horizontal_to_equatorial(
            target_dec, ha, observer_lat
        )

        return alt, az

    def _calculate_local_sidereal_time(
        self,
        longitude: float,
        timestamp: datetime
    ) -> float:
        """计算本地恒星时"""
        # Mock: 简化计算
        return (timestamp.hour + timestamp.minute / 60) * 15 + longitude

    def _horizontal_to_equatorial(
        self,
        dec: float,
        ha: float,
        lat: float
    ) -> Tuple[float, float]:
        """从赤道坐标转换为地平坐标"""
        dec_rad = math.radians(dec)
        ha_rad = math.radians(ha)
        lat_rad = math.radians(lat)

        # 计算高度角
        sin_alt = (
            math.sin(dec_rad) * math.sin(lat_rad) +
            math.cos(dec_rad) * math.cos(lat_rad) * math.cos(ha_rad)
        )
        alt = math.degrees(math.asin(sin_alt))

        # 计算方位角
        cos_az = (
            (math.sin(dec_rad) - math.sin(lat_rad) * sin_alt) /
            (math.cos(lat_rad) * math.cos(math.radians(alt)))
        )
        az = math.degrees(math.acos(max(-1, min(1, cos_az))))

        # 根据时角调整方位角
        if math.sin(ha_rad) > 0:
            az = 360 - az

        return alt, az

    def calculate_rise_set_transit(
        self,
        target_ra: float,
        target_dec: float,
        observer_lat: float,
        observer_lon: float,
        date: datetime
    ) -> dict:
        """
        计算目标的升起、中天、落下时间

        Returns:
            {
                "rise_time": datetime,
                "transit_time": datetime,
                "set_time": datetime,
                "transit_altitude": float
            }
        """
        # Mock 实现
        # 生产环境使用精确的天文算法

        # 简化: 假设目标在特定时间升起和落下
        base_hour = 18  # 下午6点
        rise_time = date.replace(hour=base_hour, minute=30, second=0)
        transit_time = date.replace(hour=base_hour + 5, minute=0, second=0)
        set_time = date.replace(hour=base_hour + 11, minute=30, second=0)

        # 计算中天高度
        transit_alt = 90 - abs(observer_lat - target_dec)

        return {
            "rise_time": rise_time,
            "transit_time": transit_time,
            "set_time": set_time,
            "transit_altitude": transit_alt
        }
```

### 4.2 可见性计算服务

**文件**: `app/services/visibility.py`

```python
from typing import List, Optional
from datetime import datetime, timedelta
from app.services.astronomy import AstronomyService
from app.models.target import VisibleZone

class VisibilityService:
    """可见性计算服务"""

    def __init__(self):
        self.astronomy = AstronomyService()

    def calculate_visibility_windows(
        self,
        target_ra: float,
        target_dec: float,
        observer_lat: float,
        observer_lon: float,
        date: datetime,
        visible_zones: List[VisibleZone],
        min_altitude: float = 15.0
    ) -> List[dict]:
        """
        计算目标在指定日期和可视区域的可见窗口

        Args:
            target_ra: 目标赤经
            target_dec: 目标赤纬
            observer_lat: 观测者纬度
            observer_lon: 观测者经度
            date: 观测日期
            visible_zones: 可视区域列表
            min_altitude: 最小高度角

        Returns:
            可见窗口列表
        """
        windows = []

        # 生成时间样本 (每5分钟)
        samples = self._generate_time_samples(date, interval_minutes=5)

        for zone in visible_zones:
            zone_windows = self._calculate_windows_for_zone(
                target_ra, target_dec,
                observer_lat, observer_lon,
                samples, zone,
                min_altitude
            )
            windows.extend(zone_windows)

        return windows

    def _generate_time_samples(
        self,
        date: datetime,
        interval_minutes: int = 5
    ) -> List[datetime]:
        """生成时间样本"""
        start = date.replace(hour=18, minute=0, second=0)  # 傍晚6点
        end = date + timedelta(days=1)
        end = end.replace(hour=6, minute=0, second=0)  # 次日早晨6点

        samples = []
        current = start
        while current <= end:
            samples.append(current)
            current += timedelta(minutes=interval_minutes)

        return samples

    def _calculate_windows_for_zone(
        self,
        target_ra: float,
        target_dec: float,
        observer_lat: float,
        observer_lon: float,
        time_samples: List[datetime],
        zone: VisibleZone,
        min_altitude: float
    ) -> List[dict]:
        """计算单个区域的可见窗口"""
        windows = []
        in_window = False
        window_start = None
        max_altitude = 0
        max_altitude_time = None

        for time in time_samples:
            # 计算当前位置
            alt, az = self.astronomy.calculate_position(
                target_ra, target_dec,
                observer_lat, observer_lon,
                time
            )

            # 判断是否在区域内且高度足够
            is_in_zone = self._point_in_polygon(
                (az, alt), zone.polygon
            )
            meets_altitude = alt >= min_altitude

            if is_in_zone and meets_altitude:
                if not in_window:
                    window_start = time
                    in_window = True

                # 记录最大高度
                if alt > max_altitude:
                    max_altitude = alt
                    max_altitude_time = time
            else:
                if in_window:
                    # 窗口结束
                    windows.append({
                        "zone_id": zone.id,
                        "start_time": window_start.isoformat(),
                        "end_time": time.isoformat(),
                        "max_altitude": max_altitude,
                        "max_altitude_time": max_altitude_time.isoformat()
                    })
                    in_window = False
                    window_start = None
                    max_altitude = 0

        return windows

    def _point_in_polygon(
        self,
        point: tuple,
        polygon: List[tuple]
    ) -> bool:
        """射线法判断点是否在多边形内"""
        x, y = point
        inside = False

        for i in range(len(polygon)):
            j = (i - 1) % len(polygon)
            xi, yi = polygon[i]
            xj, yj = polygon[j]

            intersect = ((yi > y) != (yj > y)) and \
                        (x < (xj - xi) * (y - yi) / (yj - yi) + xi)

            if intersect:
                inside = not inside

        return inside
```

### 4.3 评分服务

**文件**: `app/services/scoring.py`

```python
import math

class ScoringService:
    """评分服务"""

    def calculate_score(
        self,
        max_altitude: float,
        magnitude: float,
        target_size: float,
        fov_horizontal: float,
        fov_vertical: float,
        duration_minutes: float
    ) -> dict:
        """
        计算推荐得分 (总分100)

        Args:
            max_altitude: 最大高度角
            magnitude: 星等
            target_size: 目标视大小 (角分)
            fov_horizontal: 水平FOV (度)
            fov_vertical: 垂直FOV (度)
            duration_minutes: 可见时长 (分钟)

        Returns:
            {
                "total_score": int,
                "breakdown": {
                    "altitude": int,
                    "brightness": int,
                    "fov_match": int,
                    "duration": int
                }
            }
        """
        altitude_score = self._calculate_altitude_score(max_altitude)
        brightness_score = self._calculate_brightness_score(magnitude)
        fov_score = self._calculate_fov_score(
            target_size, fov_horizontal, fov_vertical
        )
        duration_score = self._calculate_duration_score(duration_minutes)

        total_score = altitude_score + brightness_score + fov_score + duration_score

        return {
            "total_score": total_score,
            "breakdown": {
                "altitude": altitude_score,
                "brightness": brightness_score,
                "fov_match": fov_score,
                "duration": duration_score
            }
        }

    def _calculate_altitude_score(self, max_altitude: float) -> int:
        """高度得分 (40分满分, 但最高可到50分)"""
        if max_altitude < 30:
            return max(0, int((max_altitude - 15) / 15 * 40))
        elif max_altitude < 60:
            return int(40 + (max_altitude - 30) / 30 * 10)
        else:
            return 50

    def _calculate_brightness_score(self, magnitude: float) -> int:
        """亮度得分 (30分满分)"""
        if magnitude <= 2:
            return 30
        elif magnitude <= 4:
            return 25
        elif magnitude <= 6:
            return 18
        elif magnitude <= 8:
            return 10
        else:
            return 5

    def _calculate_fov_score(
        self,
        target_size: float,
        fov_h: float,
        fov_v: float
    ) -> int:
        """FOV匹配度得分 (20分满分)"""
        # 将FOV转换为角分
        fov_h_arcmin = fov_h * 60
        fov_v_arcmin = fov_v * 60
        min_fov = min(fov_h_arcmin, fov_v_arcmin)

        # 计算目标占画幅的比例
        ratio = target_size / min_fov

        if ratio < 0.1:
            return 5  # 太小
        elif ratio > 1.5:
            return 3  # 太大
        elif 0.2 <= ratio <= 0.7:
            return 20  # 理想
        elif 0.1 <= ratio < 0.2:
            return 15
        elif 0.7 < ratio <= 1.0:
            return 12
        else:
            return 8

    def _calculate_duration_score(self, duration_minutes: float) -> int:
        """时长得分 (10分满分)"""
        if duration_minutes > 240:  # >4小时
            return 10
        elif duration_minutes >= 120:  # 2-4小时
            return 8
        elif duration_minutes >= 60:  # 1-2小时
            return 5
        else:  # <1小时
            return 2
```

### 4.4 推荐引擎服务

**文件**: `app/services/recommendation.py`

```python
from typing import List, Optional
from datetime import datetime
from app.services.visibility import VisibilityService
from app.services.scoring import ScoringService
from app.services.astronomy import AstronomyService
from app.models.target import DeepSkyTarget, VisibleZone

class RecommendationService:
    """推荐引擎服务"""

    def __init__(self):
        self.visibility = VisibilityService()
        self.scoring = ScoringService()
        self.astronomy = AstronomyService()

    def generate_recommendations(
        self,
        targets: List[DeepSkyTarget],
        observer_lat: float,
        observer_lon: float,
        date: datetime,
        equipment: dict,
        visible_zones: List[VisibleZone],
        filters: Optional[dict] = None,
        limit: int = 20
    ) -> List[dict]:
        """
        生成推荐目标列表

        Args:
            targets: 候选目标列表
            observer_lat: 观测者纬度
            observer_lon: 观测者经度
            date: 观测日期
            equipment: 设备参数
            visible_zones: 可视区域
            filters: 过滤条件
            limit: 返回数量限制

        Returns:
            推荐列表
        """
        recommendations = []

        for target in targets:
            # 应用过滤条件
            if filters and not self._apply_filters(target, filters):
                continue

            # 计算可见窗口
            windows = self.visibility.calculate_visibility_windows(
                target.ra, target.dec,
                observer_lat, observer_lon,
                date, visible_zones
            )

            if not windows:
                continue

            # 计算最佳窗口的评分
            best_window = max(windows, key=lambda w: w["max_altitude"])

            # 计算得分
            score_result = self.scoring.calculate_score(
                max_altitude=best_window["max_altitude"],
                magnitude=target.magnitude,
                target_size=target.size,
                fov_horizontal=equipment["fov_horizontal"],
                fov_vertical=equipment["fov_vertical"],
                duration_minutes=self._calculate_duration(best_window)
            )

            # 确定时段
            period = self._determine_period(best_window["start_time"])

            # 获取当前位置
            current_alt, current_az = self.astronomy.calculate_position(
                target.ra, target.dec,
                observer_lat, observer_lon,
                datetime.now()
            )

            recommendations.append({
                "target": target.dict(),
                "visibility_windows": windows,
                "current_position": {
                    "altitude": current_alt,
                    "azimuth": current_az,
                    "timestamp": datetime.now().isoformat()
                },
                "score": score_result["total_score"],
                "score_breakdown": score_result["breakdown"],
                "period": period
            })

        # 排序
        recommendations.sort(key=lambda r: r["score"], reverse=True)

        return recommendations[:limit]

    def _apply_filters(self, target: DeepSkyTarget, filters: dict) -> bool:
        """应用过滤条件"""
        if "min_magnitude" in filters and target.magnitude > filters["min_magnitude"]:
            return False

        if "types" in filters and target.type not in filters["types"]:
            return False

        if "min_score" in filters:
            # 需要先计算分数，这里简化处理
            pass

        return True

    def _calculate_duration(self, window: dict) -> float:
        """计算窗口时长(分钟)"""
        start = datetime.fromisoformat(window["start_time"])
        end = datetime.fromisoformat(window["end_time"])
        return (end - start).total_seconds() / 60

    def _determine_period(self, start_time: str) -> str:
        """确定时段"""
        hour = datetime.fromisoformat(start_time).hour

        if 18 <= hour < 24:
            return "tonight-golden"
        elif 0 <= hour < 3:
            return "post-midnight"
        else:
            return "pre-dawn"
```

---

## 5. Mock 数据设计

### 5.1 深空天体数据库

**文件**: `data/deepsky_objects.json`

**结构示例**:
```json
{
  "targets": [
    {
      "id": "M42",
      "name": "猎户座大星云",
      "name_en": "Orion Nebula",
      "type": "emission-nebula",
      "ra": 83.633,
      "dec": -5.391,
      "magnitude": 4.0,
      "size": 85,
      "constellation": "Orion",
      "difficulty": 1,
      "description": "全天最明亮的弥漫星云...",
      "optimal_season": ["December", "January", "February"],
      "optimal_fov": {"min": 100, "max": 400},
      "tags": ["nebula", "emission", "bright", "beginner-friendly"]
    },
    {
      "id": "M31",
      "name": "仙女座星系",
      "name_en": "Andromeda Galaxy",
      "type": "galaxy",
      "ra": 10.684,
      "dec": 41.269,
      "magnitude": 3.4,
      "size": 178,
      "constellation": "Andromeda",
      "difficulty": 1,
      "description": "本星系群中最大的星系...",
      "optimal_season": ["October", "November", "December"],
      "optimal_fov": {"min": 200, "max": 500},
      "tags": ["galaxy", "spiral", "bright", "large"]
    }
  ],
  "metadata": {
    "total": 300,
    "last_updated": "2025-01-22"
  }
}
```

**Mock 数据生成策略**:
1. 包含全部 110 个 Messier 天体
2. 精选 150 个 NGC 天体
3. 精选 40 个 IC 天体
4. 每个目标包含完整的天体参数

### 5.2 预设地点数据库

**文件**: `data/locations.json`

```json
{
  "locations": [
    {
      "id": "beijing",
      "name": "北京",
      "latitude": 39.9042,
      "longitude": 116.4074,
      "timezone": "Asia/Shanghai",
      "country": "CN",
      "region": "Beijing"
    },
    {
      "id": "shanghai",
      "name": "上海",
      "latitude": 31.2304,
      "longitude": 121.4737,
      "timezone": "Asia/Shanghai",
      "country": "CN",
      "region": "Shanghai"
    },
    {
      "id": "new-york",
      "name": "New York",
      "latitude": 40.7128,
      "longitude": -74.0060,
      "timezone": "America/New_York",
      "country": "US",
      "region": "New York"
    }
  ]
}
```

### 5.3 Mock 数据服务

**文件**: `app/services/mock_data.py`

```python
import json
from typing import List, Optional
from app.models.target import DeepSkyTarget

class MockDataService:
    """Mock 数据服务"""

    def __init__(self):
        self.targets_cache = None

    def load_targets(self) -> List[DeepSkyTarget]:
        """加载深空天体数据"""
        if self.targets_cache is not None:
            return self.targets_cache

        with open("data/deepsky_objects.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        self.targets_cache = [
            DeepSkyTarget(**target) for target in data["targets"]
        ]
        return self.targets_cache

    def get_target_by_id(self, target_id: str) -> Optional[DeepSkyTarget]:
        """根据ID获取目标"""
        targets = self.load_targets()
        for target in targets:
            if target.id == target_id:
                return target
        return None

    def get_targets_by_type(self, target_type: str) -> List[DeepSkyTarget]:
        """根据类型获取目标"""
        targets = self.load_targets()
        return [t for t in targets if t.type == target_type]

    def get_targets_by_constellation(
        self,
        constellation: str
    ) -> List[DeepSkyTarget]:
        """根据星座获取目标"""
        targets = self.load_targets()
        return [t for t in targets if t.constellation == constellation]

    def search_targets(self, query: str) -> List[DeepSkyTarget]:
        """搜索目标"""
        targets = self.load_targets()
        query_lower = query.lower()

        return [
            t for t in targets
            if query_lower in t.name.lower()
            or query_lower in t.name_en.lower()
            or query_lower in t.id.lower()
            or query_lower in t.constellation.lower()
        ]
```

---

## 6. FastAPI 应用配置

### 6.1 主应用入口

**文件**: `app/main.py`

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    allow_origins=["*"],  # 生产环境应限制具体域名
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
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

### 6.2 配置管理

**文件**: `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    APP_NAME: str = "Deep Sky Target Recommender"
    APP_VERSION: str = "1.0.0"

    # API 配置
    API_PREFIX: str = "/api/v1"

    # 数据文件路径
    DATA_DIR: str = "data"
    TARGETS_DATA_FILE: str = "deepsky_objects.json"
    LOCATIONS_DATA_FILE: str = "locations.json"

    # 计算配置
    TIME_SAMPLES_INTERVAL_MINUTES: int = 5
    MIN_ALTITUDE_DEGREES: float = 15.0

    # Mock 配置
    MOCK_MODE: bool = True
    MOCK_DEFAULT_CITY: str = "beijing"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

## 7. 依赖文件

### 7.1 requirements.txt

```
# Web 框架
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# 天文数据查询 (核心)
astroquery>=0.4.7          # SIMBAD, Gaia, VizieR 访问
astropy>=6.0.0             # 天文数据处理
skyfield>=1.49             # 天体位置计算

# 时间处理
python-dateutil>=2.8.2
pytz>=2023.3

# 数据处理
pandas>=2.1.0
numpy>=1.26.0

# 工具
python-multipart==0.0.6
email-validator==2.1.0
requests>=2.31.0

# 测试
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0

# 开发工具
black==23.12.1
flake8==7.0.0
mypy==1.8.0
```

---

## 8. 开发流程

### 8.1 环境搭建

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
python -m app.main
```

访问 `http://localhost:8000/docs` 查看 API 文档

### 8.2 测试策略

**单元测试** (`tests/test_services/`):
- 测试天体位置计算
- 测试可见性计算
- 测试评分算法

**API 测试** (`tests/test_api/`):
- 测试所有 API 端点
- 测试参数验证
- 测试错误处理

**示例测试**:

```python
# tests/test_services/test_scoring.py
import pytest
from app.services.scoring import ScoringService

def test_altitude_score():
    service = ScoringService()

    # 测试低高度
    score = service._calculate_altitude_score(20)
    assert 0 <= score <= 40

    # 测试高高度
    score = service._calculate_altitude_score(70)
    assert score == 50

def test_brightness_score():
    service = ScoringService()

    # 测试明亮天体
    score = service._calculate_brightness_score(1.5)
    assert score == 30

    # 测试暗天体
    score = service._calculate_brightness_score(9.0)
    assert score == 5
```

---

## 9. 部署方案

### 9.1 Docker 配置

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY data/ ./data/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - MOCK_MODE=true
    restart: unless-stopped
```

### 9.2 部署命令

```bash
# 构建镜像
docker build -t deep-sky-api .

# 运行容器
docker run -p 8000:8000 deep-sky-api

# 或使用 docker-compose
docker-compose up -d
```

---

## 10. 性能优化建议

### 10.1 缓存策略

1. **深空天体数据缓存**: 应用启动时加载到内存
2. **计算结果缓存**: 使用 Redis 或内存缓存缓存储存计算结果
3. **CDN**: 静态资源使用 CDN 加速

### 10.2 异步处理

```python
from fastapi import BackgroundTasks

async def generate_recommendations_async(
    background_tasks: BackgroundTasks,
    ...
):
    """异步生成推荐"""
    background_tasks.add_task(
        recommendation_service.generate_recommendations,
        ...
    )
    return {"task_id": "task_123"}
```

### 10.3 数据库优化

生产环境建议:
- 使用 PostgreSQL 替代 JSON 文件
- 添加适当的索引
- 实现查询结果分页

---

## 11. 安全考虑

### 11.1 输入验证

- 使用 Pydantic 进行严格的类型检查
- 限制数值范围 (如纬度 -90 到 90)
- 验证字符串格式 (如时区)

### 11.2 速率限制

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/recommendations")
@limiter.limit("10/minute")
async def get_recommendations(...):
    ...
```

### 11.3 CORS 配置

生产环境应限制允许的源:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 12. 未来扩展

### 12.1 用户系统

- 用户注册/登录
- 保存个人配置
- 拍摄历史记录

### 12.2 高级功能

- 天气数据集成
- 光污染评估
- 月亮影响计算
- 社区分享

### 12.3 数据库迁移

```python
# 从 JSON 迁移到 PostgreSQL 的示例
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:password@localhost/dbname"
engine = create_engine(DATABASE_URL)
```

---

## 13. 天文数据库集成

### 13.1 数据源概览

本项目集成了多个开源天文数据库,提供准确的深空天体数据:

| 数据库 | 用途 | 访问方式 | 许可证 |
|--------|------|---------|--------|
| **OpenNGC** | 主要深空天体目录 | 本地 CSV | MIT |
| **SIMBAD** | 在线补充查询 | astroquery | 学术免费 |
| **Gaia DR3** | 参考恒星数据 | astroquery | 开源 |
| **VizieR** | 备用数据源 | astroquery | 多种 |

### 13.2 数据架构

```
应用启动
    ↓
加载本地数据 (OpenNGC + Messier)
    ↓
┌─────────────────────────────────────┐
│  快速查询 (内存缓存)                  │
│  - 110 Messier 对象                  │
│  - 8000+ NGC/IC 对象                 │
│  - 基本信息 (RA/Dec/星等/类型)       │
└─────────────────────────────────────┘
    ↓
在线查询 (按需)
    ↓
┌─────────────────────────────────────┐
│  SIMBAD                              │
│  - 遗漏数据补充                      │
│  - 详细参数查询                      │
│  - 交叉验证                          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Gaia DR3                            │
│  - 参考恒星获取                      │
│  - 星团成员确认                      │
│  - 精确位置校正                      │
└─────────────────────────────────────┘
```

### 13.3 数据库服务实现

**文件**: `app/services/databases.py`

```python
"""
天文数据库集成服务
整合 OpenNGC, SIMBAD, Gaia, VizieR 等数据源
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
import pandas as pd
import json
from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor

# astroquery imports
from astroquery.simbad import Simbad
from astroquery.gaia import Gaia
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u

from app.config import settings


class AstronomyDatabaseService:
    """统一的天文数据库访问服务"""

    def __init__(self):
        self._simbad = None
        self._local_cache = {}
        self.catalogs_dir = Path(settings.DATA_DIR) / "catalogs"
        self.catalogs_dir.mkdir(parents=True, exist_ok=True)

        # 线程池用于异步查询
        self.executor = ThreadPoolExecutor(max_workers=5)

    # ==================== SIMBAD 集成 ====================

    def _get_simbad(self):
        """获取配置好的 SIMBAD 连接"""
        if self._simbad is None:
            self._simbad = Simbad()
            self._simbad.add_votable_fields(
                'ra(d;ICRS;J2000)',
                'dec(d;ICRS;J2000)',
                'flux(V)',
                'flux(B)',
                'flux(R)',
                'morphology',
                'dimensions',
                'otype'  # 对象类型
            )
            self._simbad.ROW_LIMIT = -1
        return self._simbad

    async def query_simbad_async(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        异步查询 SIMBAD

        Args:
            identifier: 天体标识符 (如 "M31", "NGC224")

        Returns:
            天体数据字典
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._query_simbad_sync,
            identifier
        )

    def _query_simbad_sync(self, identifier: str) -> Optional[Dict[str, Any]]:
        """同步查询 SIMBAD"""
        try:
            simbad = self._get_simbad()
            result = simbad.query_object(identifier)

            if result is None or len(result) == 0:
                return None

            row = result[0]

            # 提取数据
            data = {
                'id': identifier,
                'main_id': str(row['MAIN_ID']),
                'ra': float(row['RA_d_ICRS_J2000']),
                'dec': float(row['DEC_d_ICRS_J2000']),
            }

            # 可选字段
            if 'FLUX_V' in row.colnames and row['FLUX_V'] is not None:
                data['magnitude'] = float(row['FLUX_V'])

            if 'FLUX_B' in row.colnames and row['FLUX_B'] is not None:
                data['b_mag'] = float(row['FLUX_B'])

            if 'FLUX_R' in row.colnames and row['FLUX_R'] is not None:
                data['r_mag'] = float(row['FLUX_R'])

            if 'MORPHOLOGY' in row.colnames:
                data['morphology'] = str(row['MORPHOLOGY'])

            if 'OTYPE' in row.colnames:
                data['object_type'] = str(row['OTYPE'])

            return data

        except Exception as e:
            print(f"SIMBAD 查询失败 {identifier}: {e}")
            return None

    def query_region_simbad(
        self,
        ra: float,
        dec: float,
        radius_deg: float = 1.0,
        max_mag: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        查询指定区域内的天体 (SIMBAD)

        Args:
            ra: 中心赤经 (度)
            dec: 中心赤纬 (度)
            radius_deg: 搜索半径 (度)
            max_mag: 最大星等限制

        Returns:
            天体列表
        """
        try:
            coord = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs')
            radius = radius_deg * u.degree

            simbad = self._get_simbad()
            result = simbad.query_region(coord, radius=radius)

            if result is None:
                return []

            objects = []
            for row in result:
                mag = float(row['FLUX_V']) if 'FLUX_V' in row.colnames else None

                if max_mag is not None and mag is not None and mag > max_mag:
                    continue

                objects.append({
                    'main_id': str(row['MAIN_ID']),
                    'ra': float(row['RA_d_ICRS_J2000']),
                    'dec': float(row['DEC_d_ICRS_J2000']),
                    'magnitude': mag,
                })

            return objects

        except Exception as e:
            print(f"SIMBAD 区域查询失败: {e}")
            return []

    # ==================== Gaia DR3 集成 ====================

    async def query_gaia_reference_stars(
        self,
        ra: float,
        dec: float,
        radius_deg: float = 0.5,
        max_magnitude: float = 15.0,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        查询 Gaia DR3 参考恒星 (异步)

        Args:
            ra: 中心赤经
            dec: 中心赤纬
            radius_deg: 搜索半径
            max_magnitude: 最大 G 星等
            limit: 返回数量限制

        Returns:
            恒星数据 DataFrame
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._query_gaia_sync,
            ra, dec, radius_deg, max_magnitude, limit
        )

    def _query_gaia_sync(
        self,
        ra: float,
        dec: float,
        radius_deg: float,
        max_magnitude: float,
        limit: int
    ) -> pd.DataFrame:
        """同步查询 Gaia DR3"""
        query = f"""
        SELECT TOP {limit}
          source_id, ra, dec, pmra, pmdec,
          phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag,
          parallax, bp_rp
        FROM gaiadr3.gaia_source
        WHERE 1=CONTAINS(
          POINT('ICRS', ra, dec),
          CIRCLE('ICRS', {ra}, {dec}, {radius_deg})
        )
        AND phot_g_mean_mag < {max_magnitude}
        AND parallax IS NOT NULL
        ORDER BY phot_g_mean_mag ASC
        """

        try:
            job = Gaia.launch_job(query)
            return job.get_results().to_pandas()
        except Exception as e:
            print(f"Gaia 查询失败: {e}")
            return pd.DataFrame()

    def crossmatch_with_gaia(
        self,
        target_ra: float,
        target_dec: float,
        radius_arcsec: float = 10.0
    ) -> Optional[Dict[str, Any]]:
        """
        交叉匹配目标位置与 Gaia 星表

        用于验证位置或获取精确自行数据
        """
        query = f"""
        SELECT TOP 1
          source_id, ra, dec, pmra, pmdec,
          phot_g_mean_mag, parallax
        FROM gaiadr3.gaia_source
        WHERE 1=CONTAINS(
          POINT('ICRS', ra, dec),
          CIRCLE('ICRS', {target_ra}, {target_dec}, {radius_arcsec/3600})
        )
        ORDER BY phot_g_mean_mag ASC
        """

        try:
            job = Gaia.launch_job(query)
            result = job.get_results()

            if len(result) > 0:
                return {
                    'source_id': result['source_id'][0],
                    'ra': float(result['ra'][0]),
                    'dec': float(result['dec'][0]),
                    'pmra': float(result['pmra'][0]),
                    'pmdec': float(result['pmdec'][0]),
                    'g_mag': float(result['phot_g_mean_mag'][0]),
                    'parallax': float(result['parallax'][0])
                }
        except Exception as e:
            print(f"Gaia 交叉匹配失败: {e}")

        return None

    # ==================== VizieR 集成 ====================

    def query_messier_catalog(self) -> pd.DataFrame:
        """从 VizieR 获取完整 Messier 目录"""
        try:
            vizier = Vizier()
            vizier.ROW_LIMIT = 110

            # 查找 Messier 目录
            catalogs = Vizier.find_catalogs('Messier')
            if not catalogs:
                print("未找到 Messier 目录")
                return pd.DataFrame()

            messier_catalog_key = list(catalogs.keys())[0]
            result = Vizier.query_catalog(messier_catalog_key)

            if result:
                return result[0].to_pandas()

        except Exception as e:
            print(f"VizieR Messier 查询失败: {e}")

        return pd.DataFrame()

    def query_ngc_catalog(
        self,
        min_magnitude: Optional[float] = None
    ) -> pd.DataFrame:
        """从 VizieR 获取 NGC 目录"""
        try:
            # 使用 OpenNGC 或其他 NGC 目录
            vizier = Vizier()
            vizier.ROW_LIMIT = -1

            # 查询 NGC 2000.0 目录
            result = Vizier.query_catalog('VII/119')

            if result:
                df = result[0].to_pandas()

                if min_magnitude is not None and 'Vmag' in df.columns:
                    df = df[df['Vmag'] <= min_magnitude]

                return df

        except Exception as e:
            print(f"VizieR NGC 查询失败: {e}")

        return pd.DataFrame()

    # ==================== 本地 OpenNGC 集成 ====================

    def load_opengc_csv(self) -> pd.DataFrame:
        """加载本地 OpenNGC CSV 文件"""
        opengc_file = self.catalogs_dir / "opengc.csv"

        if not opengc_file.exists():
            raise FileNotFoundError(
                f"OpenNGC 文件不存在: {opengc_file}\n"
                f"请从 https://github.com/mattiaverga/OpenNGC 下载"
            )

        try:
            df = pd.read_csv(opengc_file)
            return df
        except Exception as e:
            print(f"加载 OpenNGC 失败: {e}")
            return pd.DataFrame()

    def get_messier_from_opengc(self) -> List[Dict[str, Any]]:
        """从 OpenNGC 提取 Messier 天体"""
        df = self.load_opengc_csv()

        if df.empty:
            return []

        # 筛选 Messier 天体
        messier_df = df[df['name'].str.startswith('M ', na=False)]

        objects = []
        for _, row in messier_df.iterrows():
            obj = {
                'id': row['name'].replace(' ', ''),
                'name': row['name'],
                'type': self._map_object_type(row['type']),
                'ra': self._parse_ra(row['ra']),
                'dec': self._parse_dec(row['dec']),
            }

            if pd.notna(row.get('mag')):
                obj['magnitude'] = float(row['mag'])

            if pd.notna(row.get('size')):
                obj['size'] = float(row['size'])

            if pd.notna(row.get('const')):
                obj['constellation'] = row['const']

            objects.append(obj)

        return objects

    def get_ngc_from_opengc(
        self,
        min_magnitude: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """从 OpenNGC 提取 NGC/IC 天体"""
        df = self.load_opengc_csv()

        if df.empty:
            return []

        # 筛选 NGC/IC 天体
        ngc_df = df[df['name'].str.match(r'^(NGC|IC) ', na=False)]

        if min_magnitude is not None:
            ngc_df = ngc_df[ngc_df['mag'] <= min_magnitude]

        objects = []
        for _, row in ngc_df.iterrows():
            obj = {
                'id': row['name'].replace(' ', ''),
                'name': row['name'],
                'type': self._map_object_type(row['type']),
                'ra': self._parse_ra(row['ra']),
                'dec': self._parse_dec(row['dec']),
            }

            if pd.notna(row.get('mag')):
                obj['magnitude'] = float(row['mag'])

            if pd.notna(row.get('size')):
                obj['size'] = float(row['size'])

            objects.append(obj)

        return objects

    def _map_object_type(self, code: str) -> str:
        """映射 OpenNGC 类型代码到应用类型"""
        type_map = {
            'G': 'galaxy',
            'G*': 'galaxy',  # 借用星系
            'PN': 'planetary-nebula',
            'HII': 'emission-nebula',
            'OCL': 'cluster',  # 疏散星团
            'GCL': 'globular-cluster',
            'NB': 'nebula',
            'DRK': 'dark-nebula',
            'RN': 'reflection-nebula',
            'SNR': 'supernova-remnant',
            '*': 'star',
            '**': 'double-star',
        }
        return type_map.get(code, 'unknown')

    def _parse_ra(self, ra_str: str) -> float:
        """解析赤经字符串 (如 "00 42 44.4") 为度"""
        try:
            parts = str(ra_str).split()
            h, m, s = map(float, parts[:3])
            return (h + m/60 + s/3600) * 15
        except:
            return 0.0

    def _parse_dec(self, dec_str: str) -> float:
        """解析赤纬字符串 (如 "+41 16 12") 为度"""
        try:
            parts = str(dec_str).split()
            sign = -1 if parts[0].startswith('-') else 1
            d, m, s = map(float, parts[0:3])
            return sign * (d + m/60 + s/3600)
        except:
            return 0.0

    # ==================== 综合查询 ====================

    async def get_target_complete_data(
        self,
        identifier: str,
        use_simbad_fallback: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        获取目标完整数据 (本地 + 在线)

        Args:
            identifier: 天体标识符
            use_simbad_fallback: 本地无数据时是否查询 SIMBAD

        Returns:
            完整的天体数据
        """
        # 1. 先尝试本地 OpenNGC
        try:
            opengc_data = self._get_from_local(identifier)
            if opengc_data:
                return opengc_data
        except:
            pass

        # 2. 回退到 SIMBAD
        if use_simbad_fallback:
            return await self.query_simbad_async(identifier)

        return None

    def _get_from_local(self, identifier: str) -> Optional[Dict[str, Any]]:
        """从本地缓存获取数据"""
        # 实现 LRU 缓存查询
        if identifier in self._local_cache:
            return self._local_cache[identifier]
        return None

    def cache_target(self, identifier: str, data: Dict[str, Any]):
        """缓存目标数据到内存"""
        self._local_cache[identifier] = data

    @lru_cache(maxsize=1000)
    def get_target_cached(self, identifier: str) -> Optional[Dict[str, Any]]:
        """带 LRU 缓存的目标查询"""
        return self._get_from_local(identifier)

    # ==================== 批量操作 ====================

    async def batch_query_targets(
        self,
        identifiers: List[str]
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """批量查询多个目标"""
        tasks = [self.query_simbad_async(id) for id in identifiers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return dict(zip(identifiers, results))

    async def batch_query_positions(
        self,
        targets: List[Dict[str, float]],
        radius_deg: float = 0.5
    ) -> Dict[str, List[Dict]]:
        """
        批量查询多个区域的参考恒星

        Args:
            targets: [{"id": "M42", "ra": 83.633, "dec": -5.391}, ...]
            radius_deg: 搜索半径

        Returns:
            {target_id: [stars...]}
        """
        results = {}

        for target in targets:
            stars = await self.query_gaia_reference_stars(
                ra=target['ra'],
                dec=target['dec'],
                radius_deg=radius_deg
            )

            results[target['id']] = stars.to_dict('records')

        return results

    # ==================== 数据导出 ====================

    def export_targets_to_json(
        self,
        targets: List[Dict[str, Any]],
        output_file: str
    ):
        """导出目标列表为 JSON"""
        output_path = self.catalogs_dir / output_file

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(targets, f, ensure_ascii=False, indent=2)

        print(f"已导出 {len(targets)} 个天体到 {output_path}")

    def generate_combined_catalog(
        self,
        output_file: str = "deepsky_objects.json"
    ):
        """
        生成本地综合目录

        整合 OpenNGC + SIMBAD + Gaia 数据
        """
        print("正在生成综合深空天体目录...")

        all_targets = []

        # 1. Messier 天体
        print("加载 Messier 天体...")
        messier = self.get_messier_from_opengc()
        all_targets.extend(messier)

        # 2. 亮 NGC/IC 天体
        print("加载亮 NGC/IC 天体...")
        bright_ngc = self.get_ngc_from_opengc(min_magnitude=12)
        all_targets.extend(bright_ngc)

        # 3. 添加元数据
        catalog = {
            "version": "1.0",
            "generated_at": pd.Timestamp.now().isoformat(),
            "sources": ["OpenNGC", "SIMBAD", "Gaia DR3"],
            "total": len(all_targets),
            "targets": all_targets
        }

        # 4. 导出
        self.export_targets_to_json(catalog, output_file)

        print(f"生成完成! 共 {len(all_targets)} 个天体")

        return catalog


# ==================== 便捷函数 ====================

def get_database_service() -> AstronomyDatabaseService:
    """获取数据库服务单例"""
    return AstronomyDatabaseService()


async def initialize_catalogs():
    """
    初始化天文目录

    下载/更新必要的目录文件
    """
    service = get_database_service()

    print("检查天文目录...")

    # 检查 OpenNGC 文件
    opengc_file = service.catalogs_dir / "opengc.csv"

    if not opengc_file.exists():
        print("OpenNGC 文件不存在")
        print("请从以下地址下载:")
        print("https://github.com/mattiaverga/OpenNGC/raw/master/openngc.csv")
        print(f"保存到: {opengc_file}")
        return False

    print("✓ OpenNGC 文件已存在")

    # 可选: 生成综合目录
    if not (service.catalogs_dir / "deepsky_objects.json").exists():
        print("生成综合深空天体目录...")
        service.generate_combined_catalog()
    else:
        print("✓ 综合目录已存在")

    return True


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test():
        service = get_database_service()

        # 测试 SIMBAD 查询
        print("测试 SIMBAD 查询 M31...")
        m31_data = await service.query_simbad_async("M31")
        print(f"M31: {m31_data}")

        # 测试本地数据
        print("\n测试本地 OpenNGC 数据...")
        messier_objects = service.get_messier_from_opengc()
        print(f"找到 {len(messier_objects)} 个 Messier 天体")

    asyncio.run(test())
```

### 13.4 使用示例

#### 13.4.1 在 API 路由中使用

**文件**: `app/api/targets.py`

```python
from fastapi import APIRouter, HTTPException
from app.services.databases import AstronomyDatabaseService

router = APIRouter()
db_service = AstronomyDatabaseService()

@router.get("/targets/{target_id}")
async def get_target(target_id: str):
    """获取目标详情"""

    # 先查本地缓存
    cached = db_service.get_target_cached(target_id)
    if cached:
        return {"success": True, "data": cached}

    # 查询在线数据库
    data = await db_service.get_target_complete_data(target_id)

    if data is None:
        raise HTTPException(status_code=404, detail="Target not found")

    # 缓存结果
    db_service.cache_target(target_id, data)

    return {"success": True, "data": data}


@router.get("/targets")
async def list_targets(
    type: Optional[str] = None,
    constellation: Optional[str] = None,
    min_magnitude: Optional[float] = None
):
    """列出天体"""

    # 从本地 OpenNGC 获取
    if type == "messier" or type is None:
        targets = db_service.get_messier_from_opengc()
    else:
        targets = db_service.get_ngc_from_opengc(min_magnitude=min_magnitude)

    # 应用过滤
    if constellation:
        targets = [t for t in targets if t.get('constellation') == constellation]

    return {
        "success": True,
        "data": {
            "targets": targets[:20],  # 分页
            "total": len(targets)
        }
    }
```

#### 13.4.2 启动时初始化

**文件**: `app/main.py`

```python
from fastapi import FastAPI
from app.services.databases import initialize_catalogs

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    print("初始化天文目录...")
    success = await initialize_catalogs()

    if not success:
        print("警告: 天文目录初始化失败,部分功能可能不可用")
```

### 13.5 数据获取脚本

**文件**: `scripts/download_catalogs.py`

```python
#!/usr/bin/env python
"""
下载天文目录数据
"""
import requests
from pathlib import Path

def download_opengc():
    """下载 OpenNGC CSV 文件"""
    url = "https://github.com/mattiaverga/OpenNGC/raw/master/openngc.csv"
    output_dir = Path("data/catalogs")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "opengc.csv"

    print(f"正在下载 OpenNGC...")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(output_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"✓ 下载完成: {output_file}")
    return output_file


def generate_messier_json():
    """从 OpenNGC 生成 Messier JSON"""
    from app.services.databases import AstronomyDatabaseService

    print("正在生成 Messier JSON...")
    service = AstronomyDatabaseService()

    try:
        messier_objects = service.get_messier_from_opengc()
        service.export_targets_to_json(messier_objects, "messier.json")
        print(f"✓ 生成完成: {len(messier_objects)} 个 Messier 天体")
    except FileNotFoundError as e:
        print(f"✗ 错误: {e}")
        print("请先运行 download_opengc()")


if __name__ == "__main__":
    # 1. 下载 OpenNGC
    download_opengc()

    # 2. 生成 JSON 文件
    generate_messier_json()

    print("\n完成! 现在可以运行应用了")
```

### 13.6 性能优化策略

#### 13.6.1 多级缓存

```python
from functools import lru_cache
import pickle
from pathlib import Path

class CachedDatabaseService(AstronomyDatabaseService):
    """带缓存的数据库服务"""

    def __init__(self):
        super().__init__()
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @lru_cache(maxsize=1000)
    async def get_target_data(self, object_id: str) -> dict:
        """三级缓存: 内存 -> 磁盘 -> 在线"""

        # L1: 内存缓存 (lru_cache)
        # L2: 磁盘缓存
        cache_file = self.cache_dir / f"{object_id}.pkl"

        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)

        # L3: 在线查询
        data = await self.query_simbad_async(object_id)

        # 保存到磁盘
        if data:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)

        return data
```

#### 13.6.2 批量查询优化

```python
async def batch_get_targets(
    target_ids: List[str]
) -> Dict[str, dict]:
    """批量查询优化"""

    # 1. 先从缓存获取
    cached = {}
    remaining = []

    for tid in target_ids:
        data = get_target_cached(tid)
        if data:
            cached[tid] = data
        else:
            remaining.append(tid)

    # 2. 批量查询剩余的
    if remaining:
        # 分批查询,避免过载
        batch_size = 10
        for i in range(0, len(remaining), batch_size):
            batch = remaining[i:i+batch_size]
            results = await batch_query_targets(batch)
            cached.update(results)

    return cached
```

### 13.7 数据库配置

**文件**: `app/config.py` (扩展)

```python
class Settings(BaseSettings):
    """应用配置"""

    # ... 现有配置 ...

    # 天文数据库配置
    USE_ONLINE_DATABASES: bool = True      # 是否使用在线数据库
    SIMBAD_TIMEOUT: int = 30               # SIMBAD 查询超时 (秒)
    GAIA_TIMEOUT: int = 60                 # Gaia 查询超时 (秒)

    # 缓存配置
    ENABLE_CACHE: bool = True
    CACHE_DIR: str = "data/cache"
    CACHE_TTL: int = 86400                 # 缓存过期时间 (秒)

    # OpenNGC 配置
    OPENNGC_PATH: str = "data/catalogs/opengc.csv"
    AUTO_UPDATE_CATALOGS: bool = False     # 是否自动更新目录

    # 数据源优先级
    DATA_SOURCE_PRIORITY: list = [
        "local",     # 优先使用本地数据
        "simbad",    # 回退到 SIMBAD
        "vizier"     # 最后使用 VizieR
    ]
```

### 13.8 错误处理

```python
class DatabaseError(Exception):
    """数据库错误基类"""
    pass

class SIMBADQueryError(DatabaseError):
    """SIMBAD 查询失败"""
    pass

class GaiaQueryError(DatabaseError):
    """Gaia 查询失败"""
    pass

class LocalDataError(DatabaseError):
    """本地数据错误"""
    pass


# 使用示例
async def safe_query_target(target_id: str):
    """带错误处理的安全查询"""
    try:
        return await db_service.query_simbad_async(target_id)
    except Exception as e:
        print(f"查询失败: {e}")
        # 回退到本地数据
        return db_service.get_target_cached(target_id)
```

---

## 附录

### A. 错误代码列表

| 代码 | 说明 |
|------|------|
| `VALIDATION_ERROR` | 参数验证失败 |
| `NOT_FOUND` | 资源不存在 |
| `CALCULATION_ERROR` | 计算错误 |
| `INTERNAL_ERROR` | 服务器内部错误 |

### B. API 版本控制

- 当前版本: `v1`
- URL 路径: `/api/v1/...`
- 向后兼容策略: 主版本号变化时通知客户端

### C. 天文数据库参考资源

**官方文档**
- [SIMBAD Astronomical Database](http://simbad.u-strasbg.fr/simbad/)
- [Gaia Archive](https://www.cosmos.esa.int/web/gaia/dr3)
- [VizieR Catalog Service](https://vizier.cds.unistra.fr/)
- [astroquery Documentation](https://astroquery.readthedocs.io/)
- [astropy Documentation](https://docs.astropy.org/)

**开源数据**
- [OpenNGC (GitHub)](https://github.com/mattiaverga/OpenNGC) - MIT 许可证
- [skycatalog (GitHub)](https://github.com/MarScaper/skycatalog)

**教程**
- [Astronomical Data in Python](https://allendowney.github.io/AstronomicalData/)
- [Gaia 程序化访问指南](https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access)
- [如何提取 Gaia 数据](https://www.cosmos.esa.int/web/gaia-users/archive/extract-data)

---

**文档版本**: 1.0
**最后更新**: 2025-01-22
**维护者**: 开发团队
