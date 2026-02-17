# 可视区域增强与FOV优化推荐 - 设计文档

**日期**: 2025-02-17
**版本**: 1.0
**状态**: Ready for Implementation
**分支**: `interactive`

---

## 架构概述

本设计文档描述三个独立但相关的功能增强：

1. **页面初始化时对准可视区域**（前端功能）
2. **可视区域软过滤**（后端评分增强）
3. **FOV占比评分优化**（后端评分重构）

---

## 功能1：页面初始化时对准可视区域

### 设计目标

在页面加载完成后，自动将天空图视角对准到优先级最高的自定义可视区域中心。

### 技术设计

#### 1.1 数据结构

可视区域数据结构（已存在）：
```javascript
{
  id: string,           // 区域ID
  name: string,         // 区域名称
  polygon: Array<[      // 多边形顶点（方位角, 高度角）
    number, number
  ]>,
  priority: number,     // 优先级（数值越小优先级越高）
  isDefault: boolean    // 是否为默认区域
}
```

天空图视角结构：
```javascript
this.view = {
  azimuth: 0,      // 观测方位角 (0-360°, 0=北)
  altitude: 0,     // 观测高度角 (0-90°, 0=地平线)
  zoom: 1.0
}
```

#### 1.2 算法设计

**计算可视区域中心点**：

输入：可视区域多边形顶点数组

输出：中心点 `{ azimuth: number, altitude: number }`

算法步骤：
1. 找到优先级最高的可视区域（priority最小）
2. 如果是默认区域，跳过（不改变视角）
3. 计算多边形的几何中心：
   - 方位角中心 = (所有顶点方位角之和) / 顶点数
   - 高度角中心 = (所有顶点高度角之和) / 顶点数
4. 处理方位角跨越0°/360°的特殊情况：
   - 如果最大方位角 - 最小方位角 > 180°
   - 说明跨越0°边界
   - 将所有 >180° 的方位角减去360°
   - 重新计算平均值
   - 如果结果 <0°，加360°还原

#### 1.3 实现代码

**文件**: `frontend/src/scripts/main.js`

**新增函数**：
```javascript
/**
 * 将天空图视角对准到优先级最高的可视区域中心
 */
function centerSkyMapOnVisibleZone() {
  const zones = getVisibleZones();

  if (zones.length === 0) {
    console.log('[centerSkyMap] No zones found, skipping');
    return;
  }

  // 找到优先级最高的非默认区域
  const customZones = zones.filter(z => !z.isDefault);

  if (customZones.length === 0) {
    console.log('[centerSkyMap] No custom zones, skipping');
    return;
  }

  // 按优先级排序，取第一个
  const highestPriorityZone = customZones.reduce((prev, current) =>
    prev.priority < current.priority ? prev : current
  );

  // 计算区域中心
  const polygon = highestPriorityZone.polygon;
  const center = calculatePolygonCenter(polygon);

  console.log('[centerSkyMap] Centering on zone:', highestPriorityZone.name,
              'at azimuth:', center.azimuth.toFixed(1),
              'altitude:', center.altitude.toFixed(1));

  // 对准天空图
  if (skyMap) {
    skyMap.view.azimuth = center.azimuth;
    skyMap.view.altitude = Math.max(0, Math.min(90, center.altitude));
    skyMap.render();
  }
}

/**
 * 计算多边形中心点
 * @param {Array<Array<number>>} polygon - 多边形顶点 [[az, alt], ...]
 * @returns {Object} { azimuth, altitude }
 */
function calculatePolygonCenter(polygon) {
  let sumAz = 0;
  let sumAlt = 0;
  const n = polygon.length;

  // 检查是否跨越0/360度边界
  const azimuths = polygon.map(p => p[0]);
  const maxAz = Math.max(...azimuths);
  const minAz = Math.min(...azimuths);
  const crossesBoundary = (maxAz - minAz) > 180;

  if (crossesBoundary) {
    // 跨越边界，需要特殊处理
    for (const [az, alt] of polygon) {
      const adjustedAz = az > 180 ? az - 360 : az;
      sumAz += adjustedAz;
      sumAlt += alt;
    }
    let centerAz = sumAz / n;
    if (centerAz < 0) centerAz += 360;
    return { azimuth: centerAz, altitude: sumAlt / n };
  } else {
    // 正常情况
    for (const [az, alt] of polygon) {
      sumAz += az;
      sumAlt += alt;
    }
    return { azimuth: sumAz / n, altitude: sumAlt / n };
  }
}
```

**集成位置**：在 `initSkyMap()` 函数末尾

```javascript
async function initSkyMap() {
  // ... 现有的初始化代码 ...

  // 【新增】对准可视区域
  centerSkyMapOnVisibleZone();
}
```

#### 1.4 边界情况处理

| 场景 | 处理方式 |
|------|---------|
| 没有可视区域 | 跳过，保持默认视角 |
| 只有默认全天空区域 | 跳过，保持默认视角 |
| 单个自定义区域 | 对准该区域中心 |
| 多个自定义区域 | 对准优先级最高的 |
| 区域跨越0°方位角 | 特殊算法处理 |
| 区域中心高度角 < 0° | 限制为 0° |
| 区域中心高度角 > 90° | 限制为 90° |

#### 1.5 测试用例

```javascript
// 测试用例1：正常区域
polygon = [[30, 15], [60, 15], [60, 45], [30, 45]]
// 期望：center = { azimuth: 45, altitude: 30 }

// 测试用例2：跨越0°边界
polygon = [[350, 15], [10, 15], [10, 45], [350, 45]]
// 期望：center = { azimuth: 0, altitude: 30 }

// 测试用例3：单个点区域
polygon = [[180, 45], [180, 45], [180, 45], [180, 45]]
// 期望：center = { azimuth: 180, altitude: 45 }

// 测试用例4：优先级排序
zones = [
  { id: 'zone1', priority: 2, ... },
  { id: 'zone2', priority: 1, ... }
]
// 期望：对准 zone2
```

---

## 功能2：可视区域软过滤

### 设计目标

在推荐评分时，对不在可视区域内的目标给予50分惩罚，使其排名靠后但仍然可见。

### 技术设计

#### 2.1 点在多边形内判断

**算法选择**：射线法（Ray Casting）

原理：
1. 从目标点向任意方向发射一条射线
2. 计算射线与多边形边界的交点数量
3. 如果交点数为奇数，点在多边形内；偶数，点在外部

**特殊情况处理**：
- 方位角跨越0°/360°边界
- 点在多边形边界上
- 点正好是多边形顶点

#### 2.2 实现代码

**文件**: `backend/app/services/recommendation.py`

**新增方法**：

```python
def _check_target_in_visible_zones(
    self,
    azimuth: float,
    altitude: float,
    visible_zones: List[VisibleZone]
) -> bool:
    """
    检查目标位置是否在任何可视区域内

    Args:
        azimuth: 目标方位角 (0-360°)
        altitude: 目标高度角 (0-90°)
        visible_zones: 可视区域列表

    Returns:
        True if in any zone, False otherwise
    """
    for zone in visible_zones:
        if self._is_point_in_polygon(azimuth, altitude, zone.polygon):
            return True
    return False


def _is_point_in_polygon(
    self,
    az: float,
    alt: float,
    polygon: List[Tuple[float, float]]
) -> bool:
    """
    射线法判断点是否在多边形内

    Args:
        az: 点的方位角
        alt: 点的高度角
        polygon: 多边形顶点列表 [[az1, alt1], [az2, alt2], ...]

    Returns:
        True if point is inside polygon, False otherwise
    """
    n = len(polygon)
    if n < 3:
        return False

    inside = False

    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]

        # 处理方位角跨越0/360度的情况
        if az > 180:
            az -= 360
        if p1x > 180:
            p1x -= 360
        if p2x > 180:
            p2x -= 360

        # 射线法判断
        if alt > min(p1y, p2y):
            if alt <= max(p1y, p2y):
                if az <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (alt - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or az <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside
```

**集成位置**：在 `generate_recommendations()` 方法中

```python
async def generate_recommendations(self, ...):
    # ... 现有代码 ...

    for db_obj in db_objects:
        target = self.model_adapter.to_target(db_obj)

        # 计算当前位置
        current_alt, current_az = self.astronomy.calculate_position(
            target.ra, target.dec,
            observer_lat, observer_lon,
            date  # 使用传入的时间参数
        )

        # 【新增】检查是否在可视区域内
        is_in_zone = self._check_target_in_visible_zones(
            current_az, current_alt, visible_zones
        )

        # 计算惩罚分数
        zone_penalty = 0 if is_in_zone else 50

        # ... 继续原有的评分逻辑 ...

        # 调用评分时传入惩罚
        score_result = self.scoring.calculate_score(
            magnitude=target.magnitude,
            target_size=target.size,
            fov_horizontal=equipment.get("fov_horizontal", 10),
            fov_vertical=equipment.get("fov_vertical", 7),
            duration_minutes=best_window["duration_minutes"],
            moonlight_pollution=moonlight_pollution,
            zone_penalty=zone_penalty  # 新增参数
        )
```

#### 2.3 边界情况处理

| 场景 | 处理方式 |
|------|---------|
| 目标在边界上 | 视为在区域内 |
| 目标是顶点 | 视为在区域内 |
| 多边形<3个顶点 | 返回False |
| 方位角>180° | 转换为负数再计算 |
| 多边形自身相交 | 可能需要更复杂算法（当前不考虑） |

---

## 功能3：FOV占比评分优化与权重重构

### 设计目标

1. 优化FOV占比评分曲线，扩展理想范围
2. 移除高度角评分（在可视区域内自然满足）
3. 重新分配权重：亮度、FOV、时长、月光各25%

### 技术设计

#### 3.1 FOV评分曲线优化

**文件**: `backend/app/services/scoring.py`

**修改方法**：`_calculate_fov_score()`

```python
def _calculate_fov_score(
    self,
    target_size: float,
    fov_h: float,
    fov_v: float
) -> int:
    """
    FOV匹配度得分 (0-100分) - 优化版本

    评分曲线：
    - <10%:  0-30分 (线性，太小)
    - 10-20%: 30-60分 (线性，可接受)
    - 20-70%: 100分 (理想范围)
    - 70-100%: 100-70分 (线性下降，较大)
    - >100%: 最低20分 (过大，线性下降)
    """
    # 计算FOV对角线
    fov_diagonal = math.sqrt(fov_h**2 + fov_v**2)

    # 将目标大小从角分转换为度
    target_size_degrees = target_size / 60

    # 计算目标占FOV对角线的百分比
    ratio = target_size_degrees / fov_diagonal

    # 分段评分
    if ratio < 0.1:
        # 太小：<10%
        return max(0, min(30, int(ratio / 0.1 * 30)))
    elif 0.1 <= ratio < 0.2:
        # 较小：10-20%
        normalized = (ratio - 0.1) / 0.1
        return 30 + int(normalized * 30)
    elif 0.2 <= ratio <= 0.7:
        # 理想：20-70%
        return 100
    elif 0.7 < ratio <= 1.0:
        # 较大：70-100%
        normalized = (ratio - 0.7) / 0.3
        return 100 - int(normalized * 30)
    else:
        # 太大：>100%
        excess = ratio - 1.0
        return max(20, 70 - int(excess * 50))
```

**评分曲线图示**：

```
得分
100 |        ┌─────────┐
    |        │         │
 75 |        │         │    ┌────
    |        │         │    │
 50 |        │         │    │    ┌────
    |        │         │    │    │
 25 |    ┌───┘         │    │    │    │
    ─────┘              └────┘    └────┘
  0 ┼────────────────────────────────────
    0   10%   20%         70%   100%  150%
    ↑    ↑     ↑            ↑     ↑     ↑
   太小  可接受  理想      可接受  大   过大
```

#### 3.2 评分权重重构

**修改方法**：`calculate_score()`

```python
def calculate_score(
    self,
    magnitude: float,
    target_size: float,
    fov_horizontal: float,
    fov_vertical: float,
    duration_minutes: float,
    moonlight_pollution: float = 0.0,
    zone_penalty: int = 0  # 新增
) -> dict:
    """
    计算推荐得分 (总分100)

    新的权重分配（每项25%）：
    - brightness: 25%
    - fov_match: 25%
    - duration: 25%
    - moonlight: 25%

    移除：
    - altitude: 0% (在可视区域内的目标自然满足)
    """
    # 计算各项得分
    brightness_score = self._calculate_brightness_score(magnitude)
    size_score = self._calculate_fov_score(
        target_size, fov_horizontal, fov_vertical
    )
    duration_score = self._calculate_duration_score(duration_minutes)
    moonlight_score = self._score_moonlight(moonlight_pollution)

    # 新的权重（每项25%）
    weights = {
        "brightness": 0.25,
        "size_match": 0.25,
        "duration": 0.25,
        "moonlight": 0.25
    }

    # 计算总分
    total_score = (
        brightness_score * weights["brightness"] +
        size_score * weights["size_match"] +
        duration_score * weights["duration"] +
        moonlight_score * weights["moonlight"]
    )

    # 扣除可视区域惩罚
    total_score = max(0, total_score - zone_penalty)

    return {
        "total_score": int(total_score),
        "breakdown": {
            "brightness": brightness_score,
            "fov_match": size_score,
            "duration": duration_score,
            "moonlight": moonlight_score
        }
    }
```

#### 3.3 API接口兼容性

**后端修改**：`recommendation.py`

```python
# 旧调用方式
score_result = self.scoring.calculate_score(
    max_altitude=best_window["max_altitude"],  # 移除
    magnitude=target.magnitude,
    ...
)

# 新调用方式
score_result = self.scoring.calculate_score(
    magnitude=target.magnitude,
    target_size=target.size,
    fov_horizontal=equipment.get("fov_horizontal", 10),
    fov_vertical=equipment.get("fov_vertical", 7),
    duration_minutes=best_window["duration_minutes"],
    moonlight_pollution=moonlight_pollution,
    zone_penalty=zone_penalty  # 新增
)
```

---

## 数据流图

### 功能1数据流

```
页面加载
  ↓
initSkyMap()
  ↓
getVisibleZones() → 从localStorage读取
  ↓
centerSkyMapOnVisibleZone()
  ├─ 找到最高优先级区域
  ├─ calculatePolygonCenter() → 计算中心点
  └─ skyMap.view.azimuth/altitude = 中心点
  ↓
skyMap.render() → 重绘天空图
```

### 功能2数据流

```
API.getRecommendations()
  ↓
recommendation_service.generate_recommendations()
  ├─ 遍历所有目标
  ├─ 计算目标位置 (calculate_position)
  ├─ _check_target_in_visible_zones()
  │   └─ _is_point_in_polygon() → 射线法判断
  ├─ zone_penalty = 0 或 50
  └─ scoring.calculate_score(..., zone_penalty)
  ↓
返回推荐列表（已排序）
```

### 功能3数据流

```
scoring.calculate_score()
  ├─ brightness_score → 25%权重
  ├─ fov_score → 25%权重（优化曲线）
  ├─ duration_score → 25%权重
  ├─ moonlight_score → 25%权重
  ↓
total_score = sum(得分 × 权重) - zone_penalty
  ↓
返回总分和细分
```

---

## 错误处理

### 功能1错误处理

```javascript
try {
  centerSkyMapOnVisibleZone();
} catch (error) {
  console.error('[centerSkyMap] Failed to center on visible zone:', error);
  // 失败时保持默认视角，不阻塞页面加载
}
```

### 功能2错误处理

```python
try:
    is_in_zone = self._check_target_in_visible_zones(...)
except Exception as e:
    logger.error(f"Failed to check zone for target {target.id}: {e}")
    # 失败时默认为不在区域内（保守策略）
    is_in_zone = False
    zone_penalty = 50
```

### 功能3错误处理

```python
try:
    ratio = target_size_degrees / fov_diagonal
except ZeroDivisionError:
    logger.error("FOV diagonal is zero")
    ratio = 0  # 默认为无穷小

# 确保得分在0-100范围内
score = max(0, min(100, calculated_score))
```

---

## 性能优化

### 功能1性能
- **计算复杂度**：O(n)，n为多边形顶点数（通常4-8个）
- **执行频率**：页面加载时执行1次
- **优化**：无需特殊优化

### 功能2性能
- **计算复杂度**：O(m × n)，m为可视区域数，n为多边形顶点数
- **执行频率**：每个目标计算1次
- **优化**：
  - 先检查高度角是否在范围内（快速过滤）
  - 只对有效目标（altitude > 0）进行判断

```python
# 优化：快速过滤
if altitude <= 0:
    zone_penalty = 50  # 地平线以下，肯定不在区域
else:
    is_in_zone = self._check_target_in_visible_zones(...)
```

### 功能3性能
- **计算复杂度**：O(1)，简单的数学计算
- **优化**：无需特殊优化

---

## 测试策略

### 单元测试

**功能1测试**：
```python
def test_calculate_polygon_center():
    # 正常情况
    polygon = [[30, 15], [60, 15], [60, 45], [30, 45]]
    center = calculate_polygon_center(polygon)
    assert abs(center['azimuth'] - 45) < 0.1
    assert abs(center['altitude'] - 30) < 0.1

    # 跨越0°边界
    polygon = [[350, 15], [10, 15], [10, 45], [350, 45]]
    center = calculate_polygon_center(polygon)
    assert abs(center['azimuth']) < 1  # 接近0°
    assert abs(center['altitude'] - 30) < 0.1
```

**功能2测试**：
```python
def test_is_point_in_polygon():
    # 点在内部
    polygon = [[0, 0], [10, 0], [10, 10], [0, 10]]
    assert _is_point_in_polygon(5, 5, polygon) == True

    # 点在外部
    assert _is_point_in_polygon(15, 5, polygon) == False

    # 点在边界上
    assert _is_point_in_polygon(0, 5, polygon) == True
```

**功能3测试**：
```python
def test_calculate_fov_score():
    # 理想范围
    assert _calculate_fov_score(30, 10, 7) == 100  # ~30%

    # 太小
    assert _calculate_fov_score(5, 10, 7) < 30     # ~5%

    # 太大
    assert _calculate_fov_score(200, 10, 7) < 50   # ~200%
```

### 集成测试

1. **页面加载测试**：
   - 设置自定义可视区域
   - 刷新页面
   - 验证天空图视角已对准

2. **推荐过滤测试**：
   - 设置东向可视区域
   - 加载推荐
   - 验证西方目标得分较低（-50分）

3. **FOV评分测试**：
   - 使用小FOV设备
   - 验证小目标得分提升
   - 使用大FOV设备
   - 验证大目标得分提升

---

## 部署计划

### Phase 1: FOV评分优化（后端）
**文件**：`backend/app/services/scoring.py`
**估计时间**：30分钟
**测试**：单元测试

### Phase 2: 可视区域检查（后端）
**文件**：`backend/app/services/recommendation.py`
**估计时间**：1小时
**测试**：单元测试 + 集成测试

### Phase 3: 页面初始化对准（前端）
**文件**：`frontend/src/scripts/main.js`
**估计时间**：30分钟
**测试**：浏览器测试

**总计**：约2小时

---

## 回滚计划

如果发现问题，可以独立回滚每个功能：

1. **功能1回滚**：删除 `centerSkyMapOnVisibleZone()` 调用
2. **功能2回滚**：移除 `zone_penalty` 参数和相关检查
3. **功能3回滚**：恢复旧的评分权重和FOV计算逻辑

---

## 附录

### A. 多边形中心点计算公式

**正常情况**：
```
中心.azimuth = sum(所有顶点.azimuth) / n
中心.altitude = sum(所有顶点.altitude) / n
```

**跨越0°边界**：
```
对于每个顶点：
  if azimuth > 180:
    adjusted = azimuth - 360
  else:
    adjusted = azimuth

中心.azimuth = sum(所有adjusted) / n
if 中心.azimuth < 0:
  中心.azimuth += 360
```

### B. 射线法算法伪代码

```
function isPointInPolygon(point, polygon):
  inside = false
  for each edge in polygon:
    if ray intersects edge:
      inside = not inside
  return inside
```

### C. FOV占比计算公式

```
FOV_对角线 = sqrt(FOV_H² + FOV_V²)

目标大小(度) = 目标大小(角分) / 60

占比 = 目标大小(度) / FOV_对角线
```

---

**文档版本**: 1.0
**最后更新**: 2025-02-17
**作者**: Claude Sonnet 4.5
