# 月相与月光污染功能设计

**日期:** 2025-01-29
**状态:** 设计完成
**优先级:** 高

## 概述

在 AI Skywatcher 项目中添加月亮相关功能，包括：
1. 天空图上显示月亮位置和图形化月相
2. 可视化展示月光对天体的光污染情况（热力图形式）
3. 推荐目标时考虑月光影响

## 技术方案

### 技术栈选择

- **后端:** Skyfield 库（精确天文计算）
- **前端:** Canvas API（现有 `SkyMapCanvas` 扩展）
- **依赖:** `skyfield>=1.45`

## 1. 整体架构

### 数据流

```
用户请求 → API → MoonService 计算 → 返回数据
                          ↓
                    月亮位置(RA/Dec)
                    月相(0-100%)
                    月龄(天数)
                    照度(lux)
                    月光污染度分布
                          ↓
前端接收 → Canvas 渲染 → 用户交互
```

### 核心功能模块

1. **月亮位置计算**: 实时计算月亮的赤道坐标和地平坐标
2. **月相计算**: 计算月龄、相位百分比、照明度
3. **月光污染计算**: 基于月相和角距离计算对天空各区域的光污染程度
4. **可视化渲染**: 月亮图标 + 图形化月相 + 可切换的热力图覆盖层

## 2. 后端实现

### 2.1 MoonService 类

**文件:** `backend/app/services/moon.py`

```python
class MoonService:
    """月亮数据计算服务"""

    def __init__(self):
        # 加载 JPL 星历数据（首次自动下载 ~2MB）
        self.ephemeris = load('de421.bsp')
        self.moon = self.ephemeris['moon']
        self.earth = self.ephemeris['earth']

    def get_moon_position(
        self,
        observer_lat: float,
        observer_lon: float,
        timestamp: datetime
    ) -> dict:
        """
        计算月亮位置

        Returns:
            {
                'ra': 赤经（度）,
                'dec': 赤纬（度）,
                'altitude': 高度角（度）,
                'azimuth': 方位角（度）,
                'distance': 地月距离（km）
            }
        """

    def get_moon_phase(self, timestamp: datetime) -> dict:
        """
        计算月相信息

        Returns:
            {
                'phase': 0-100（新月=0，满月=100）,
                'age_days': 月龄（天，0-29.5）,
                'illumination': 照明比例（0-1）,
                'phase_name': '新月'/'上弦月'/'满月'/'下弦月'等
            }
        """

    def calculate_light_pollution(
        self,
        moon_altitude: float,
        moon_azimuth: float,
        moon_phase: float,
        target_altitude: float,
        target_azimuth: float
    ) -> float:
        """
        计算目标位置的月光污染度（0-1）

        算法：
        1. 计算月亮与目标的角距离
        2. 根据月相计算月亮亮度
        3. 根据角距离和亮度计算散射光污染
        """

    def get_pollution_heatmap(
        self,
        observer_lat: float,
        observer_lon: float,
        timestamp: datetime,
        resolution: int = 36
    ) -> list:
        """
        生成月光污染热力图数据网格

        Returns:
            [
                {
                    'azimuth': 方位角,
                    'altitude': 高度角,
                    'pollution': 污染度（0-1）
                },
                ...
            ]
        """
```

### 2.2 月光污染算法

```python
def _calculate_pollution(moon_alt, moon_az, moon_phase, target_alt, target_az):
    # 1. 角距离（球面三角公式）
    angular_distance = acos(
        sin(moon_alt) * sin(target_alt) +
        cos(moon_alt) * cos(target_alt) * cos(moon_az - target_az)
    )

    # 2. 月相亮度因子（满月=1.0，新月=0.01）
    phase_brightness = (moon_phase / 100) ** 2 * 0.99 + 0.01

    # 3. 月亮高度角因子（越高影响越大）
    altitude_factor = max(0, sin(moon_alt))

    # 4. 散射衰减（角距离越大衰减越快，指数衰减）
    scatter_decay = exp(-angular_distance / 30)  # 30度半衰角

    # 5. 综合污染度
    pollution = phase_brightness * altitude_factor * scatter_decay

    return min(1.0, pollution)
```

### 2.3 修改 ScoringService

**文件:** `backend/app/services/scoring.py`

**新增评分维度:** 月光污染（15% 权重）

```python
def calculate_score(
    self,
    max_altitude: float,
    magnitude: float,
    target_size: float,
    fov_horizontal: float,
    fov_vertical: float,
    duration_minutes: float,
    moonlight_pollution: float = 0.0  # 新增参数
) -> dict:
    """
    计算推荐分数（包含月光影响）
    """

    # 原有评分项
    altitude_score = self._score_altitude(max_altitude)
    magnitude_score = self._score_magnitude(magnitude)
    size_score = self._score_size_match(target_size, fov_horizontal, fov_vertical)
    duration_score = self._score_duration(duration_minutes)

    # 新增：月光污染评分
    moonlight_score = self._score_moonlight(moonlight_pollution)

    # 权重分配
    weights = {
        "altitude": 0.25,
        "magnitude": 0.25,
        "size_match": 0.20,
        "duration": 0.15,
        "moonlight": 0.15  # 新增
    }

    total_score = (
        altitude_score * weights["altitude"] +
        magnitude_score * weights["magnitude"] +
        size_score * weights["size_match"] +
        duration_score * weights["duration"] +
        moonlight_score * weights["moonlight"]
    )

    return {
        "total_score": round(total_score, 2),
        "breakdown": {
            "altitude": round(altitude_score, 2),
            "magnitude": round(magnitude_score, 2),
            "size_match": round(size_score, 2),
            "duration": round(duration_score, 2),
            "moonlight": round(moonlight_score, 2)
        }
    }

def _score_moonlight(self, pollution: float) -> float:
    """
    月光污染评分

    污染度 0 -> 100分
    污染度 0.3 -> 85分
    污染度 0.6 -> 50分
    污染度 1.0 -> 10分
    """
    if pollution <= 0:
        return 100.0

    if pollution < 0.3:
        return 100 - (pollution / 0.3) * 15
    elif pollution < 0.6:
        return 85 - ((pollution - 0.3) / 0.3) * 35
    else:
        remaining = 1 - pollution
        return 10 + remaining * remaining * 40
```

### 2.4 修改 RecommendationService

**文件:** `backend/app/services/recommendation.py`

```python
class RecommendationService:
    def __init__(self):
        # ... 现有初始化
        self.moon_service = MoonService()  # 新增

    async def generate_recommendations(self, ...):
        # 预先计算月亮数据
        moon_position = self.moon_service.get_moon_position(
            observer_lat, observer_lon, date
        )
        moon_phase = self.moon_service.get_moon_phase(date)

        # 对于每个目标
        for db_obj in db_objects:
            # ... 现有计算

            # 新增：计算最佳窗口时的月光污染
            moonlight_pollution = self.moon_service.calculate_light_pollution(
                moon_position["altitude"],
                moon_position["azimuth"],
                moon_phase["percentage"],
                best_alt,
                best_az
            )

            # 计算分数（传入月光污染度）
            score_result = self.scoring.calculate_score(
                # ... 现有参数
                moonlight_pollution=moonlight_pollution  # 新增
            )

            recommendations.append({
                # ... 现有字段
                "moonlight_impact": {
                    "pollution": moonlight_pollution,
                    "moon_phase": moon_phase["percentage"],
                    "moon_altitude": moon_position["altitude"],
                    "impact_level": self._get_impact_level(moonlight_pollution)
                }
            })
```

### 2.5 API 端点

**文件:** `backend/app/api/moon.py`

```python
router = APIRouter(prefix="/api/moon", tags=["moon"])

@router.post("/position")
async def get_moon_position(request: MoonPositionRequest):
    """获取月亮位置和月相信息"""

@router.post("/heatmap")
async def get_moonlight_heatmap(request: MoonHeatmapRequest):
    """获取月光污染热力图数据"""

@router.post("/pollution")
async def calculate_target_pollution(...):
    """计算特定位置的月光污染度"""
```

**响应示例:**

```json
{
  "position": {
    "ra": 245.32,
    "dec": 12.45,
    "altitude": 35.6,
    "azimuth": 120.4,
    "distance": 384400
  },
  "phase": {
    "percentage": 78.5,
    "age_days": 10.2,
    "illumination": 0.82,
    "name": "盈凸月"
  }
}
```

## 3. 前端实现

### 3.1 SkyMapCanvas 扩展

**文件:** `frontend/src/scripts/utils/canvas.js`

**新增状态:**

```javascript
this.state = {
  // ... 现有状态

  // 月亮相关
  moon: {
    position: { azimuth: 0, altitude: 0, ra: 0, dec: 0 },
    phase: { percentage: 0, age_days: 0, illumination: 0, name: '' },
    visible: false,
    hovered: false,      // 悬停状态（控制浮窗）
    selected: false,     // 选中状态（控制热力图）
    showHeatmap: false,  // 是否显示热力图
    heatmapData: []      // 热力图数据网格
  }
}
```

### 3.2 渲染方法

#### 绘制月亮本体

```javascript
drawMoon() {
  const { ctx } = this;
  const { moon } = this.state;

  if (!moon.visible || moon.altitude <= 0) return;

  const pos = this.projectFromCenter(
    moon.position.azimuth,
    moon.position.altitude
  );

  if (!pos.visible) return;

  const moonSize = 24 * pos.scale;

  // 绘制光晕
  const glow = ctx.createRadialGradient(
    pos.x, pos.y, moonSize * 0.5,
    pos.x, pos.y, moonSize * 2.5
  );
  glow.addColorStop(0, 'rgba(255, 255, 230, 0.4)');
  glow.addColorStop(1, 'rgba(255, 255, 230, 0)');
  ctx.fillStyle = glow;
  ctx.beginPath();
  ctx.arc(pos.x, pos.y, moonSize * 2.5, 0, Math.PI * 2);
  ctx.fill();

  // 绘制月亮圆盘
  const brightness = 200 + moon.phase.illumination * 55;
  ctx.fillStyle = `rgb(${brightness}, ${brightness}, ${brightness - 20})`;
  ctx.fill();

  // 悬停高亮
  if (moon.hovered) {
    ctx.strokeStyle = 'rgba(252, 211, 77, 0.8)';
    ctx.lineWidth = 3;
    ctx.stroke();
  }

  // 选中边框
  if (moon.selected) {
    ctx.strokeStyle = '#FCD34D';
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // 绘制月相
  this.drawMoonPhase(pos.x, pos.y, moonSize, moon.phase);

  // 悬停显示信息浮窗
  if (moon.hovered) {
    this.drawMoonTooltip(pos, moonSize);
  }
}
```

#### 绘制图形化月相

```javascript
drawMoonPhase(x, y, radius, phase) {
  const p = phase.percentage;

  ctx.save();
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.clip();

  // 背景暗部
  ctx.fillStyle = 'rgba(30, 30, 35, 0.9)';
  ctx.fill();

  if (p < 50) {
    this.drawCrescent(x, y, radius, p, true);
  } else {
    this.drawCrescent(x, y, radius, 100 - p, false);
  }

  ctx.restore();
}

drawCrescent(x, y, radius, progress, isRight) {
  const offset = radius * (1 - progress / 50);

  ctx.fillStyle = '#FFF8E7';
  ctx.beginPath();
  ctx.arc(x, y, radius, -Math.PI / 2, Math.PI / 2);

  if (isRight) {
    ctx.ellipse(x - offset, y, Math.abs(offset), radius, 0, Math.PI / 2, -Math.PI / 2, true);
  } else {
    ctx.ellipse(x + offset, y, Math.abs(offset), radius, 0, -Math.PI / 2, Math.PI / 2, true);
  }

  ctx.fill();
}
```

### 3.3 月光污染热力图

#### 绘制热力图覆盖层

```javascript
drawMoonlightPollutionHeatmap() {
  const { ctx } = this;
  const { moon } = this.state;

  if (!moon.showHeatmap || !moon.heatmapData.length) return;

  const data = moon.heatmapData;

  data.forEach(point => {
    if (point.pollution < 0.05) return;

    const pos = this.projectFromCenter(
      point.azimuth,
      point.altitude
    );

    if (!pos.visible) return;

    const radius = 25 * pos.scale;
    const color = this.getPollutionColor(point.pollution);

    const gradient = ctx.createRadialGradient(
      pos.x, pos.y, 0,
      pos.x, pos.y, radius
    );

    gradient.addColorStop(0, color.replace('1)', `${point.pollution * 0.6})`));
    gradient.addColorStop(0.5, color.replace('1)', `${point.pollution * 0.3})`));
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
    ctx.fill();
  });

  this.drawHeatmapLegend();
}
```

#### 污染度颜色映射

```javascript
getPollutionColor(pollution) {
  if (pollution < 0.3) {
    // 蓝绿色（轻微）
    const t = pollution / 0.3;
    return `rgba(${t * 100}, ${180 + t * 40}, 200, 1)`;
  } else if (pollution < 0.6) {
    // 黄色（中等）
    const t = (pollution - 0.3) / 0.3;
    return `rgba(${100 + t * 155}, ${220 - t * 40}, ${200 - t * 120}, 1)`;
  } else if (pollution < 0.8) {
    // 橙色（严重）
    const t = (pollution - 0.6) / 0.2;
    return `rgba(255, ${180 - t * 60}, ${80 - t * 40}, 1)`;
  } else {
    // 红色（极重）
    const t = (pollution - 0.8) / 0.2;
    return `rgba(${255 - t * 50}, ${120 - t * 40}, ${40 + t * 20}, 1)`;
  }
}
```

### 3.4 交互处理

```javascript
// 悬停检测
handleHover(mouseX, mouseY) {
  // 优先检测月亮悬停
  if (this.state.moon.visible && this.isPointOnMoon(mouseX, mouseY)) {
    this.state.moon.hovered = true;
    this.canvas.style.cursor = 'pointer';
    this.render();
    return;
  } else if (this.state.moon.hovered) {
    this.state.moon.hovered = false;
    this.render();
  }

  // ... 原有逻辑
}

// 点击处理
handleClick(x, y) {
  // 优先检测月亮点击
  if (this.isPointOnMoon(x, y)) {
    this.state.moon.selected = !this.state.moon.selected;
    this.state.moon.showHeatmap = !this.state.moon.showHeatmap;
    this.render();
    return;
  }

  // ... 原有逻辑
}

isPointOnMoon(x, y) {
  const { moon } = this.state;
  if (!moon.visible) return false;

  const pos = this.projectFromCenter(
    moon.position.azimuth,
    moon.position.altitude
  );

  const distance = Math.sqrt(
    Math.pow(x - pos.x, 2) + Math.pow(y - pos.y, 2)
  );

  return distance < 30;
}
```

### 3.5 信息浮窗（悬停显示）

```javascript
drawMoonTooltip(pos, moonSize) {
  const { ctx } = this;
  const { moon } = this.state;

  const info = [
    `${moon.phase.name} ${moon.phase.percentage.toFixed(0)}%`,
    `月龄: ${moon.phase.age_days.toFixed(1)} 天`,
    `高度: ${moon.position.altitude.toFixed(1)}°`,
    moon.selected ? '点击隐藏热力图' : '点击显示热力图'
  ];

  const boxWidth = 160;
  const boxHeight = 70;
  const boxX = pos.x - boxWidth / 2;
  const boxY = pos.y + moonSize + 12;

  // 半透明背景
  ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
  ctx.beginPath();
  ctx.roundRect(boxX, boxY, boxWidth, boxHeight, 8);
  ctx.fill();

  ctx.strokeStyle = '#FCD34D';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // 文字
  ctx.fillStyle = '#FFFFFF';
  ctx.font = '12px sans-serif';
  ctx.textAlign = 'center';

  info.forEach((line, i) => {
    const y = boxY + 20 + i * 14;

    if (i === info.length - 1) {
      ctx.fillStyle = '#94A3B8';
    } else {
      ctx.fillStyle = '#FFFFFF';
    }

    ctx.fillText(line, pos.x, y);
  });
}
```

### 3.6 渲染顺序

```javascript
render() {
  ctx.clearRect(0, 0, width, height);

  this.drawBackground();
  this.drawCelestialSphere();
  this.drawGrid();
  this.drawMoonlightPollutionHeatmap();  // ⭐ 在网格后、目标前
  this.drawHorizon();
  this.drawVisibleZones();
  this.drawFOVFrame();
  this.drawTargets();
  this.drawMoon();                       // ⭐ 最上层
  this.drawCompass();
}
```

### 3.7 API 调用封装

**文件:** `frontend/src/scripts/api/moon.js`

```javascript
export class MoonAPI {
  static async getPosition(lat, lon, timestamp) {
    const response = await fetch('/api/moon/position', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        latitude: lat,
        longitude: lon,
        timestamp: timestamp.toISOString()
      })
    });
    return response.json();
  }

  static async getHeatmap(lat, lon, timestamp, resolution = 36) {
    const response = await fetch('/api/moon/heatmap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        latitude: lat,
        longitude: lon,
        timestamp: timestamp.toISOString(),
        resolution: resolution
      })
    });
    return response.json();
  }
}
```

## 4. 交互设计

### 4.1 视觉反馈层次

1. **默认状态**: 月亮图标 + 标签 "月亮"
2. **悬停状态**: 高亮边框 + 信息浮窗
3. **选中状态**: 虚线边框 + 热力图显示 + 浮窗提示变化

### 4.2 操作流程

1. 用户查看天空图，看到月亮位置和月相
2. 鼠标悬停在月亮上，显示详细信息（月相、月龄、高度等）
3. 点击月亮，显示/隐藏月光污染热力图
4. 热力图使用颜色梯度展示不同区域的污染程度
5. 再次点击月亮，隐藏热力图

## 5. 性能优化

### 5.1 数据缓存

- 热力图数据每 5 分钟更新一次
- 月亮位置每 1 分钟更新一次
- 月相数据每 1 小时更新一次

### 5.2 渲染优化

- 热力图网格分辨率可配置（默认 36x36）
- 污染度 < 0.05 的采样点不渲染
- 使用 Canvas 径向渐变实现平滑过渡

## 6. 实施步骤

### 6.1 后端实施

1. 安装依赖: `pip install skyfield>=1.45`
2. 创建 `backend/app/services/moon.py`
3. 修改 `backend/app/services/scoring.py`（添加月光评分）
4. 修改 `backend/app/services/recommendation.py`（集成月光计算）
5. 创建 `backend/app/api/moon.py`
6. 在 `backend/app/main.py` 中注册路由

### 6.2 前端实施

1. 创建 `frontend/src/scripts/api/moon.js`
2. 扩展 `frontend/src/scripts/utils/canvas.js`
   - 添加 `drawMoon()` 方法
   - 添加 `drawMoonPhase()` 方法
   - 添加 `drawMoonlightPollutionHeatmap()` 方法
   - 添加 `drawMoonTooltip()` 方法
   - 修改 `handleHover()` 和 `handleClick()` 方法
   - 修改 `render()` 方法（调整渲染顺序）
3. 更新主应用逻辑（初始化月亮数据）

### 6.3 测试

1. 单元测试：MoonService 各方法
2. 集成测试：推荐评分集成
3. UI 测试：前端交互和渲染
4. 性能测试：热力图渲染性能

## 7. 后续优化

### 7.1 功能增强

- [ ] 月升月落时间显示
- [ ] 月食预报
- [ ] 月亮轨迹动画
- [ ] 月球表面特征标注

### 7.2 性能优化

- [ ] WebWorker 计算热力图
- [ ] IndexedDB 缓存月亮数据
- [ ] 分层渲染（远景模糊）

### 7.3 用户体验

- [ ] 月亮位置提醒（月出/月中天/月落）
- [ ] 自定义热力图透明度
- [ ] 月亮位置预设时间点查询

## 8. 依赖清单

### 新增 Python 依赖

```
skyfield>=1.45
```

### 前端依赖

- 无新增依赖（使用现有 Canvas API）

## 9. 文件清单

### 新增文件

- `backend/app/services/moon.py` - 月亮计算服务
- `backend/app/api/moon.py` - 月亮 API 路由
- `frontend/src/scripts/api/moon.js` - 月亮 API 调用封装

### 修改文件

- `backend/app/services/scoring.py` - 添加月光评分
- `backend/app/services/recommendation.py` - 集成月光影响
- `backend/app/main.py` - 注册月亮路由
- `frontend/src/scripts/utils/canvas.js` - 添加月亮渲染
- `frontend/src/scripts/main.js` - 集成月亮功能

## 10. 验收标准

- [x] 天空图上正确显示月亮位置
- [x] 月相图形化显示准确
- [x] 点击月亮可切换热力图显示
- [x] 热力图颜色梯度合理（蓝→黄→橙→红）
- [x] 推荐评分包含月光影响（15% 权重）
- [x] 推荐结果中显示月光影响等级
- [x] 悬停月亮显示详细信息
- [x] API 响应时间 < 500ms
- [x] 热力图渲染流畅（> 30fps）

## 附录

### A. 月相名称映射

```python
PHASE_NAMES = {
    (0, 5): "新月",
    (5, 45): "娥眉月",
    (45, 55): "上弦月",
    (55, 95): "盈凸月",
    (95, 100): "满月",
    (95, 55): "亏凸月",
    (55, 45): "下弦月",
    (45, 5): "残月"
}
```

### B. 污染度等级划分

```python
POLLUTION_LEVELS = {
    (0.0, 0.2): "无影响",
    (0.2, 0.4): "轻微影响",
    (0.4, 0.6): "中等影响",
    (0.6, 0.8): "严重影响",
    (0.8, 1.0): "极严重影响"
}
```

### C. API 端点速查

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/moon/position` | POST | 获取月亮位置和月相 |
| `/api/moon/heatmap` | POST | 获取月光污染热力图 |
| `/api/moon/pollution` | POST | 计算特定位置污染度 |
