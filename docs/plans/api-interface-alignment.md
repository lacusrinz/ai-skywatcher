# 前后端接口对齐文档

**创建日期**: 2025-01-22
**文档目的**: 对齐前后端 API 接口设计，确保数据结构、端点命名、请求响应格式一致

---

## 1. API 基础配置对齐

### 1.1 Base URL 统一

**对齐方案**:
```
Base URL: http://localhost:8000/api/v1
```

**说明**:
- 采用 RESTful API 版本控制
- 使用 `/api/v1` 前缀
- 为未来版本升级预留空间

### 1.2 响应格式统一

**标准响应格式** (后端已有，前端需采用):
```json
{
  "success": true,
  "data": { /* 实际数据 */ },
  "message": "操作成功"
}
```

**错误响应格式**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": []
  }
}
```

**前端 API 调用封装**:
```javascript
// src/scripts/api.js
async request(endpoint, options = {}) {
  const url = `${this.baseURL}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  });

  const result = await response.json();

  // 统一处理响应格式
  if (!result.success) {
    throw new Error(result.error?.message || '请求失败');
  }

  return result.data;
}
```

---

## 2. 接口端点对齐表

### 2.1 位置管理 (Location)

| 功能 | 对齐后的端点 | 方法 | 前端原方案 | 后端原方案 |
|------|-------------|------|-----------|-----------|
| 自动定位 | `/locations/geolocate` | POST | `GET /location/current` | ✓ |
| 位置验证 | `/locations/validate` | POST | 无 | ✓ |
| 保存地点 | `/locations` | POST | `POST /location/saved` | ✓ |
| 获取地点列表 | `/locations` | GET | `GET /location/saved` | ✓ |
| 删除地点 | `/locations/{id}` | DELETE | 无 | 无 |

**请求/响应格式**:

#### 自动定位
```javascript
// 前端调用
async getCurrentLocation() {
  return this.request('/locations/geolocate', {
    method: 'POST'
  });
}

// 响应
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

#### 获取保存的地点
```javascript
// 前端调用
async getSavedLocations() {
  return this.request('/locations');
}

// 响应
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

### 2.2 设备配置 (Equipment)

| 功能 | 对齐后的端点 | 方法 | 前端原方案 | 后端原方案 |
|------|-------------|------|-----------|-----------|
| 获取预设 | `/equipment/presets` | GET | ✓ | ✓ |
| 计算 FOV | `/equipment/calculate-fov` | POST | 无 | ✓ |
| 保存配置 | `/equipment` | POST | `POST /equipment/config` | ✓ |

**对齐说明**:
- 前端需要添加 `calculate-fov` 端点调用
- 统一使用 `/equipment` 而非 `/equipment/config`

---

### 2.3 深空目标 (Targets)

| 功能 | 对齐后的端点 | 方法 | 前端原方案 | 后端原方案 |
|------|-------------|------|-----------|-----------|
| 获取目标列表 | `/targets` | GET | `GET /objects` | ✓ |
| 获取目标详情 | `/targets/{id}` | GET | `GET /objects/{id}` | ✓ |
| 搜索目标 | `/targets/search` | GET | 无 | ✓ |

**对齐说明**:
- **统一使用 `/targets` 而非 `/objects`** (主要变更)
- 前端需要将所有 `/objects` 替换为 `/targets`

**前端代码修改**:
```javascript
// 修改前
async getDeepskyObjects() {
  return this.request('/objects');
}

async getDeepskyObject(targetId) {
  return this.request(`/objects/${targetId}`);
}

// 修改后
async getDeepskyObjects() {
  return this.request('/targets');
}

async getDeepskyObject(targetId) {
  return this.request(`/targets/${targetId}`);
}
```

---

### 2.4 可视区域 (Visible Zones)

| 功能 | 对齐后的端点 | 方法 | 前端原方案 | 后端原方案 |
|------|-------------|------|-----------|-----------|
| 获取区域列表 | `/visible-zones` | GET | `GET /zones` | ✓ |
| 创建区域 | `/visible-zones` | POST | `POST /zones` | ✓ |
| 更新区域 | `/visible-zones/{id}` | PUT | 无 | ✓ |
| 删除区域 | `/visible-zones/{id}` | DELETE | `DELETE /zones/{id}` | ✓ |

**对齐说明**:
- 统一使用 `/visible-zones` 而非 `/zones`
- 前端需要添加 `PUT` 方法支持

---

### 2.5 可见性计算 (Visibility)

| 功能 | 对齐后的端点 | 方法 | 前端原方案 | 后端原方案 |
|------|-------------|------|-----------|-----------|
| 计算位置 | `/visibility/position` | POST | `GET /objects/{id}/position?time=` | ✓ |
| 计算可见窗口 | `/visibility/windows` | POST | 无 | ✓ |
| 批量计算位置 | `/visibility/positions-batch` | POST | 无 | ✓ |

**对齐说明**:
- 从 `GET` 改为 `POST` (支持更复杂的参数)
- 从查询参数改为请求体

**前端代码修改**:
```javascript
// 修改前
async getTargetPosition(targetId, time) {
  const query = new URLSearchParams({ time: time.toISOString() }).toString();
  return this.request(`/objects/${targetId}/position?${query}`);
}

// 修改后
async getTargetPosition(targetId, location, timestamp) {
  return this.request('/visibility/position', {
    method: 'POST',
    body: JSON.stringify({
      target_id: targetId,
      location: location,
      timestamp: timestamp.toISOString()
    })
  });
}
```

---

### 2.6 推荐引擎 (Recommendations)

| 功能 | 对齐后的端点 | 方法 | 前端原方案 | 后端原方案 |
|------|-------------|------|-----------|-----------|
| 获取推荐 | `/recommendations` | POST | `GET /recommendations?period=` | ✓ |
| 按时段获取 | `/recommendations/by-period` | POST | 无 | ✓ |
| 获取统计 | `/recommendations/summary` | POST | 无 | ✓ |

**对齐说明**:
- **从 `GET` 改为 `POST`** (主要变更)
- 从查询参数改为请求体
- 后端的 `/recommendations` 返回所有时段，前端自行筛选或使用 `/by-period`

**前端代码修改**:
```javascript
// 修改前
async getRecommendations(params) {
  const query = new URLSearchParams(params).toString();
  return this.request(`/recommendations?${query}`);
}

// 修改后
async getRecommendations(params) {
  return this.request('/recommendations', {
    method: 'POST',
    body: JSON.stringify(params)
  });
}

// 新增: 按时段获取
async getRecommendationsByPeriod(period, params) {
  return this.request('/recommendations/by-period', {
    method: 'POST',
    body: JSON.stringify({
      period: period,
      ...params
    })
  });
}
```

**请求体格式**:
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

---

### 2.7 天空图 (Sky Map)

| 功能 | 对齐后的端点 | 方法 | 前端原方案 | 后端原方案 |
|------|-------------|------|-----------|-----------|
| 获取天空图数据 | `/sky-map/data` | POST | `GET /skymap?` | ✓ |
| 获取时间轴数据 | `/sky-map/timeline` | POST | 无 | ✓ |

**对齐说明**:
- 从 `GET` 改为 `POST`
- 统一使用 `/sky-map` 而非 `/skymap`

---

## 3. 数据结构对齐

### 3.1 位置对象 (Location)

```typescript
interface Location {
  id?: string;              // 可选，保存的地点有ID
  name: string;             // 地点名称
  latitude: number;         // 纬度 (-90 ~ 90)
  longitude: number;        // 经度 (-180 ~ 180)
  timezone: string;         // 时区 (IANA 格式，如 "Asia/Shanghai")
  country?: string;         // 国家代码
  region?: string;          // 地区
  is_default?: boolean;     // 是否默认地点
}
```

### 3.2 设备对象 (Equipment)

```typescript
interface Equipment {
  id?: string;              // 设备ID
  name: string;             // 设备名称
  sensor_size: string;      // 传感器尺寸: "full-frame" | "aps-c" | "m4/3" | "custom"
  sensor_width: number;     // 传感器宽度 (mm)
  sensor_height: number;    // 传感器高度 (mm)
  focal_length: number;     // 焦距 (mm)
  fov_horizontal?: number;  // 水平视场角 (度) - 可选，可计算
  fov_vertical?: number;    // 垂直视场角 (度) - 可选，可计算
  fov_diagonal?: number;    // 对角视场角 (度)
  aspect_ratio?: string;    // 宽高比 (如 "3:2")
}
```

### 3.3 深空目标对象 (DeepSkyTarget)

```typescript
interface DeepSkyTarget {
  id: string;               // 目标ID (如 "M42", "NGC224")
  name: string;             // 中文名称
  name_en: string;          // 英文名称
  type: TargetType;         // 类型
  ra: number;               // 赤经 (度 0~360)
  dec: number;              // 赤纬 (度 -90~90)
  magnitude: number;        // 星等
  size: number;             // 视大小 (角分)
  constellation: string;    // 所属星座
  difficulty: number;       // 难度 (1-5)
  description?: string;     // 描述
  optimal_season?: string[]; // 最佳观测季节
  optimal_fov?: {           // 最佳视场范围
    min: number;            // 最小视场 (角分)
    max: number;            // 最大视场 (角分)
  };
  tags?: string[];          // 标签
}

type TargetType =
  | "emission-nebula"
  | "galaxy"
  | "cluster"
  | "planetary-nebula";
```

### 3.4 可视区域对象 (VisibleZone)

```typescript
interface VisibleZone {
  id: string;               // 区域ID
  name: string;             // 区域名称
  polygon: [number, number][]; // 多边形顶点 [[方位角, 高度角], ...]
  priority?: number;        // 优先级 (1-10)
  azimuth_range?: [number, number];   // 方位角范围 [min, max]
  altitude_range?: [number, number];  // 高度角范围 [min, max]
}
```

### 3.5 推荐结果对象 (Recommendation)

```typescript
interface Recommendation {
  target: DeepSkyTarget;                    // 目标信息
  visibility_windows: VisibilityWindow[];   // 可见窗口列表
  current_position: TargetPosition;         // 当前位置
  score: number;                            // 总分 (0-100)
  score_breakdown: ScoreBreakdown;          // 得分明细
  period: string;                           // 时段
}

interface VisibilityWindow {
  zone_id: string;              // 可视区域ID
  start_time: string;           // 开始时间 (ISO 8601)
  end_time: string;             // 结束时间 (ISO 8601)
  max_altitude: number;         // 最大高度角
  max_altitude_time: string;    // 最大高度角时间
  duration_minutes?: number;    // 持续时长(分钟)
}

interface TargetPosition {
  altitude: number;             // 高度角
  azimuth: number;              // 方位角
  timestamp: string;            // 时间戳
  is_visible?: boolean;         // 是否可见
}

interface ScoreBreakdown {
  altitude: number;             // 高度得分 (0-50)
  brightness: number;           // 亮度得分 (0-30)
  fov_match: number;            // FOV匹配度 (0-20)
  duration: number;             // 时长得分 (0-10)
}
```

---

## 4. 前端需要修改的代码

### 4.1 API 基础配置

**文件**: `src/scripts/api.js`

```javascript
const API = {
  // 修改基础 URL
  baseURL: 'http://localhost:8000/api/v1',

  // 通用请求方法 - 添加响应包装处理
  async request(endpoint, options = {}) {
    await new Promise(resolve => setTimeout(resolve, this.delay));

    const url = `${this.baseURL}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();

    // 统一处理响应格式
    if (!result.success) {
      throw new Error(result.error?.message || '请求失败');
    }

    return result.data; // 返回实际数据
  },

  // ... 其他方法
};
```

### 4.2 位置相关接口

```javascript
// ===== 位置 (统一使用 /locations) =====

// 自动定位 - 改为 POST
async getCurrentLocation() {
  return this.request('/locations/geolocate', {
    method: 'POST'
  });
}

// 获取保存的地点 - 保持 GET
async getSavedLocations() {
  return this.request('/locations');
}

// 保存地点 - 保持 POST
async saveLocation(location) {
  return this.request('/locations', {
    method: 'POST',
    body: JSON.stringify(location)
  });
}

// 删除地点 - 新增
async deleteLocation(locationId) {
  return this.request(`/locations/${locationId}`, {
    method: 'DELETE'
  });
}
```

### 4.3 目标相关接口

```javascript
// ===== 深空目标 (从 /objects 改为 /targets) =====

// 获取所有目标
async getDeepskyObjects(params) {
  const query = new URLSearchParams(params).toString();
  return this.request(`/targets${query ? `?${query}` : ''}`);
}

// 获取单个目标
async getDeepskyObject(targetId) {
  return this.request(`/targets/${targetId}`);
}

// 搜索目标 - 新增
async searchTargets(query) {
  return this.request(`/targets/search?q=${encodeURIComponent(query)}`);
}
```

### 4.4 推荐相关接口

```javascript
// ===== 推荐 (从 GET 改为 POST) =====

// 获取推荐 - 改为 POST，使用请求体
async getRecommendations(params) {
  return this.request('/recommendations', {
    method: 'POST',
    body: JSON.stringify(params)
  });
}

// 按时段获取 - 新增
async getRecommendationsByPeriod(period, params) {
  return this.request('/recommendations/by-period', {
    method: 'POST',
    body: JSON.stringify({
      period: period,
      ...params
    })
  });
}

// 获取统计 - 新增
async getRecommendationsSummary(params) {
  return this.request('/recommendations/summary', {
    method: 'POST',
    body: JSON.stringify(params)
  });
}
```

### 4.5 可见性相关接口

```javascript
// ===== 可见性计算 (新增) =====

// 计算目标位置 - 新增
async getTargetPosition(targetId, location, timestamp) {
  return this.request('/visibility/position', {
    method: 'POST',
    body: JSON.stringify({
      target_id: targetId,
      location: location,
      timestamp: timestamp.toISOString()
    })
  });
}

// 计算可见窗口 - 新增
async getVisibilityWindows(targetId, location, date, visibleZones) {
  return this.request('/visibility/windows', {
    method: 'POST',
    body: JSON.stringify({
      target_id: targetId,
      location: location,
      date: date,
      visible_zones: visibleZones
    })
  });
}

// 批量计算位置 - 新增
async getBatchTargetPositions(targetIds, location, timestamp) {
  return this.request('/visibility/positions-batch', {
    method: 'POST',
    body: JSON.stringify({
      target_ids: targetIds,
      location: location,
      timestamp: timestamp.toISOString()
    })
  });
}
```

### 4.6 可视区域接口

```javascript
// ===== 可视区域 (从 /zones 改为 /visible-zones) =====

// 获取可视区域
async getVisibleZones() {
  return this.request('/visible-zones');
}

// 保存可视区域
async saveVisibleZone(zone) {
  return this.request('/visible-zones', {
    method: 'POST',
    body: JSON.stringify(zone)
  });
}

// 更新可视区域 - 新增
async updateVisibleZone(zoneId, zone) {
  return this.request(`/visible-zones/${zoneId}`, {
    method: 'PUT',
    body: JSON.stringify(zone)
  });
}

// 删除可视区域 - 修改路径
async deleteVisibleZone(zoneId) {
  return this.request(`/visible-zones/${zoneId}`, {
    method: 'DELETE'
  });
}
```

---

## 5. 后端需要调整的部分

### 5.1 API 响应格式

后端的响应格式已经统一，无需调整。确保所有端点都返回以下格式:

```python
# 成功响应
return {
    "success": True,
    "data": { /* 实际数据 */ },
    "message": "操作成功"
}

# 错误响应
return {
    "success": False,
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "details": []
    }
}
```

### 5.2 CORS 配置

确保 CORS 配置允许前端访问:

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite/Vue 默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 6. 迁移计划

### Phase 1: 基础设施调整 (1天)
1. ✅ 更新前端 API 基础配置 (`baseURL`, 响应处理)
2. ✅ 后端验证所有端点响应格式
3. ✅ 配置 CORS

### Phase 2: 核心接口对齐 (2-3天)
1. ✅ 位置接口: `/locations`
2. ✅ 设备接口: `/equipment`
3. ✅ 目标接口: `/objects` → `/targets`
4. ✅ 可视区域: `/zones` → `/visible-zones`

### Phase 3: 高级功能对齐 (2-3天)
1. ✅ 可见性计算: 添加 POST 端点
2. ✅ 推荐引擎: GET → POST
3. ✅ 天空图: GET → POST

### Phase 4: 测试验证 (1-2天)
1. 单元测试更新
2. 集成测试
3. 前后端联调测试

---

## 7. 测试用例

### 7.1 位置接口测试

```javascript
// 测试自动定位
const location = await API.getCurrentLocation();
console.assert(location.latitude === 39.9042);
console.assert(location.success !== undefined); // 应该被解包

// 测试获取保存的地点
const saved = await API.getSavedLocations();
console.assert(Array.isArray(saved));
```

### 7.2 推荐接口测试

```javascript
// 测试推荐接口 (POST)
const recommendations = await API.getRecommendations({
  location: { latitude: 39.9042, longitude: 116.4074, timezone: 'Asia/Shanghai' },
  date: '2025-01-22',
  equipment: { fov_horizontal: 10.3, fov_vertical: 6.9 },
  visible_zones: [],
  limit: 20
});

console.assert(Array.isArray(recommendations.recommendations));
```

---

## 8. 附录

### 8.1 完整的 API 端点对照表

| 模块 | 功能 | 端点 | 方法 | 请求体 | 响应数据 |
|------|------|------|------|--------|----------|
| **Location** | 自动定位 | `/locations/geolocate` | POST | 无 | `Location` |
| | 获取列表 | `/locations` | GET | 无 | `Location[]` |
| | 保存地点 | `/locations` | POST | `Location` | `Location` |
| | 删除地点 | `/locations/{id}` | DELETE | 无 | `message` |
| **Equipment** | 获取预设 | `/equipment/presets` | GET | 无 | `Equipment[]` |
| | 计算 FOV | `/equipment/calculate-fov` | POST | `{sensor_width, sensor_height, focal_length}` | `{fov_h, fov_v, fov_d, aspect_ratio}` |
| | 保存配置 | `/equipment` | POST | `Equipment` | `Equipment` |
| **Targets** | 获取列表 | `/targets` | GET | 查询参数 | `{targets, total, page}` |
| | 获取详情 | `/targets/{id}` | GET | 无 | `DeepSkyTarget` |
| | 搜索 | `/targets/search` | GET | `q` | `{results}` |
| **Visibility** | 计算位置 | `/visibility/position` | POST | `{target_id, location, timestamp}` | `{altitude, azimuth, ...}` |
| | 计算窗口 | `/visibility/windows` | POST | `{target_id, location, date, visible_zones}` | `{windows, total_duration}` |
| | 批量位置 | `/visibility/positions-batch` | POST | `{target_ids, location, timestamp}` | `{positions[]}` |
| **Zones** | 获取列表 | `/visible-zones` | GET | 无 | `VisibleZone[]` |
| | 创建区域 | `/visible-zones` | POST | `VisibleZone` | `VisibleZone` |
| | 更新区域 | `/visible-zones/{id}` | PUT | `VisibleZone` | `VisibleZone` |
| | 删除区域 | `/visible-zones/{id}` | DELETE | 无 | `message` |
| **Recommend** | 获取推荐 | `/recommendations` | POST | `RecommendationRequest` | `{recommendations[], summary}` |
| | 按时段 | `/recommendations/by-period` | POST | `{period, ...}` | `{recommendations[]}` |
| | 统计 | `/recommendations/summary` | POST | `RecommendationRequest` | `{total, by_type, by_period, ...}` |
| **SkyMap** | 天空图数据 | `/sky-map/data` | POST | `{location, timestamp, ...}` | `{grid, targets[], reference_lines}` |
| | 时间轴数据 | `/sky-map/timeline` | POST | `{location, date, target_ids, ...}` | `{timeline[]}` |

### 8.2 TypeScript 类型定义文件

创建 `src/types/api.ts`:

```typescript
// 通用类型
type ApiResponse<T> = {
  success: boolean;
  data?: T;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: any[];
  };
};

// 位置
export interface Location {
  id?: string;
  name: string;
  latitude: number;
  longitude: number;
  timezone: string;
  country?: string;
  region?: string;
  is_default?: boolean;
}

// 设备
export interface Equipment {
  id?: string;
  name: string;
  sensor_size: 'full-frame' | 'aps-c' | 'm4/3' | 'custom';
  sensor_width: number;
  sensor_height: number;
  focal_length: number;
  fov_horizontal?: number;
  fov_vertical?: number;
  fov_diagonal?: number;
  aspect_ratio?: string;
}

// 目标类型
export type TargetType =
  | 'emission-nebula'
  | 'galaxy'
  | 'cluster'
  | 'planetary-nebula';

// 深空目标
export interface DeepSkyTarget {
  id: string;
  name: string;
  name_en: string;
  type: TargetType;
  ra: number;
  dec: number;
  magnitude: number;
  size: number;
  constellation: string;
  difficulty: number;
  description?: string;
  optimal_season?: string[];
  optimal_fov?: {
    min: number;
    max: number;
  };
  tags?: string[];
}

// 可视区域
export interface VisibleZone {
  id: string;
  name: string;
  polygon: [number, number][];
  priority?: number;
  azimuth_range?: [number, number];
  altitude_range?: [number, number];
}

// 推荐请求
export interface RecommendationRequest {
  location: {
    latitude: number;
    longitude: number;
    timezone?: string;
  };
  date: string; // YYYY-MM-DD
  equipment: {
    fov_horizontal: number;
    fov_vertical: number;
  };
  visible_zones?: VisibleZone[];
  filters?: {
    min_magnitude?: number;
    types?: TargetType[];
    min_score?: number;
  };
  sort_by?: 'score' | 'brightness' | 'time';
  limit?: number;
}

// 可见窗口
export interface VisibilityWindow {
  zone_id: string;
  start_time: string;
  end_time: string;
  max_altitude: number;
  max_altitude_time: string;
  duration_minutes?: number;
}

// 目标位置
export interface TargetPosition {
  altitude: number;
  azimuth: number;
  timestamp: string;
  is_visible?: boolean;
}

// 得分明细
export interface ScoreBreakdown {
  altitude: number;
  brightness: number;
  fov_match: number;
  duration: number;
}

// 推荐结果
export interface Recommendation {
  target: DeepSkyTarget;
  visibility_windows: VisibilityWindow[];
  current_position: TargetPosition;
  score: number;
  score_breakdown: ScoreBreakdown;
  period: string;
}

// 推荐响应
export interface RecommendationsResponse {
  recommendations: Recommendation[];
  summary: {
    total: number;
    by_period: {
      [key: string]: number;
    };
  };
}
```

---

**文档版本**: 1.0
**最后更新**: 2025-01-22
**维护者**: 开发团队
