# 深空拍摄目标推荐工具 - 设计文档

**创建日期**: 2025-01-21
**目标用户**: 有经验的天文摄影师
**产品类型**: 离线优先的单页面应用（PWA）

## 1. 产品概述

### 1.1 核心功能
根据用户当前位置（自动获取GPS或手动输入坐标）、镜头FOV、可观测天空的朝向（考虑建筑遮挡），智能推荐当天最佳深空拍摄目标。

### 1.2 关键特性
- 离线优先：支持野外无网络环境使用
- 交互式天空图：可视化标记可视区域
- 智能推荐：基于高度、亮度、FOV匹配度综合评分
- 时段分组：按"今晚黄金时段"、"后半夜"、"黎明前"展示目标

---

## 2. 系统架构

### 2.1 技术栈

**前端框架**
- Vanilla JavaScript + HTML5
- Canvas API（交互式天空图）
- CSS Grid/Flexbox（响应式布局）

**核心库**
- `astronomy-engine` 或 `satellite.js`（天体位置计算）
- `date-fns` 或 `luxon`（时区处理）

**离线存储**
- IndexedDB（缓存配置和计算结果）
- Service Worker（PWA离线支持）

**地理定位**
- Geolocation API（自动获取位置）
- 手动输入GPS坐标

### 2.2 数据流

```
用户输入（位置 + 镜头参数 + 可视区域）
    ↓
本地计算（天体位置、高度角、方位角、可见时间窗口）
    ↓
匹配算法（目标在可视区域内的时段 + FOV适配度评分）
    ↓
分组展示（按三个时段分组 + 实时更新）
```

### 2.3 离线策略

**首次加载时**
1. 预计算当晚所有目标的可见性时间窗口
2. 存储到 IndexedDB
3. 24小时内直接使用缓存数据

**数据更新**
- 每分钟刷新目标位置（实时更新高度角、方位角）
- 跨日期时重新计算并缓存

---

## 3. 核心功能模块

### 3.1 地理定位模块

**功能**
- 自动获取：使用 Geolocation API，支持高精度模式
- 手动输入：
  - 度分秒格式：`40°26'46"N 79°58'56"W`
  - 十进制格式：`40.4461°N 79.9822°W`
- 位置库：保存常用观测点（如"家"、"常用野外观测地"）
- 时区处理：自动检测时区，所有时间以本地时间显示

**数据结构**
```javascript
{
  name: "常用观测点",
  lat: 39.9042,
  lng: 116.4074,
  timezone: "Asia/Shanghai"
}
```

### 3.2 设备配置模块

**功能**
- 快速预设：提供常见组合（如"全画幅+200mm"、"APS-C+85mm"等）
- 自定义输入：
  - 相机传感器尺寸（全画幅/APS-C/M4/3）
  - 镜头焦距
  - 或直接输入FOV角度
- 支持多设备配置保存

**FOV计算公式**
```
FOV = 2 × arctan(sensorSize / (2 × focalLength))
```

**预设示例**
- 全画幅 + 200mm → 10.3° × 6.9°
- APS-C + 85mm → 15.2° × 10.1°
- M4/3 + 300mm → 4.4° × 3.3°

### 3.3 交互式天空图模块

**功能**
- 360°全景视图：使用Canvas绘制方位角-高度角网格
- 交互标记：
  - 点击/拖拽创建多边形标记可视区域
  - 支持多个独立区域（如"东侧窗户"、"南侧空地"）
  - 实时显示每个区域的角度范围
- 天体叠加：显示主要深空目标在天空中的实时位置
- 时间轴：拖动时间滑块，预览不同时刻的天空状态

**Canvas绘制要素**
- 地平线网格（高度角 0°、15°、30°、45°、60°、75°、90°）
- 方位角刻度（N/NE/E/SE/S/SW/W/NW，每10°细分）
- 黄道线、天赤道线
- 深空目标标记（不同颜色代表类型）
- 可视区域多边形（半透明遮罩）

**交互操作**
- 单击目标：显示详细信息
- 拖拽绘制/编辑可视区域
- 滚轮缩放（仅高度角）

### 3.4 推荐引擎模块

#### 3.4.1 评分算法（总分100分）

**1. 高度得分（40%）**
```
计算目标在可视区域内的最大高度角
- 30°以下：快速下降 (maxAltitude - 15) / 15 × 40
- 30-60°：线性增长 40 + (maxAltitude - 30) / 30 × 10
- 60°以上：满分 50分
```

**2. 亮度得分（30%）**
```
基于目标星等（magnitude）
- ≤2等：30分
- ≤4等：25分
- ≤6等：18分
- ≤8等：10分
- >8等：5分
```

**3. FOV匹配度（20%）**
```
目标视大小占画幅比例 = targetSize / min(fovH, fovV)
- 20%-70%（理想）：20分
- 10%-20%：15分
- 70%-100%：12分
- <10%：5分
- >100%：3分
```

**4. 时长得分（10%）**
```
在可视区域内的连续可见时长
- >4小时：10分
- 2-4小时：8分
- 1-2小时：5分
- <1小时：2分
```

#### 3.4.2 时段分组逻辑

**今晚黄金时段**
- 时间范围：日落后2小时至午夜前
- 条件：目标在此时段内高度>30°

**后半夜目标**
- 时间范围：午夜至凌晨3点
- 条件：目标在此时段内可见

**黎明前目标**
- 时间范围：凌晨3点至天文晨光前
- 条件：目标在此时段内可见

#### 3.4.3 推荐结果数据结构
```javascript
{
  targetId: "M42",
  visibilityWindows: [
    {
      startTime: "2025-01-21T20:30:00+08:00",
      endTime: "2025-01-22T00:45:00+08:00",
      maxAltitude: 65,
      maxAltitudeTime: "2025-01-21T22:15:00+08:00",
      zoneId: "zone-1"
    }
  ],
  score: 87,
  scoreBreakdown: {
    altitude: 38,
    brightness: 28,
    fovMatch: 15,
    duration: 6
  },
  period: "tonight-golden",
  currentAltitude: 45.2,
  currentAzimuth: 135.6
}
```

---

## 4. UI/UX设计

### 4.1 整体布局

**顶部栏**（固定）
- 左侧：当前地点 + 本地时间（实时更新）
- 中间：日期选择器（默认今天）
- 右侧：设备配置下拉菜单

**主内容区**（三栏布局）

#### 左栏 - 配置面板（30%宽度，可折叠）

1. **位置卡片**
   - 自动定位按钮（GPS图标）
   - 经纬度输入框（度分秒/十进制切换）
   - 常用地点快速切换

2. **设备卡片**
   - 预设组合下拉菜单
   - 传感器尺寸选择器
   - 焦距输入框 + FOV实时预览

3. **可视区域卡片**
   - 天空图缩略图（点击展开全屏）
   - 当前区域列表（角度范围）
   - 编辑/删除按钮

#### 中栏 - 天空图（40%宽度，核心交互区）

- 大型Canvas天空图（360°方位角 × 90°高度角）
- 地平线参考线
- 八大方位标注
- 黄道线、天赤道线
- 深空目标实时位置标记（颜色编码：星系/星云/星团）
- 时间轴滑块（底部）
- 实时时钟显示
- 全屏模式按钮

#### 右栏 - 推荐列表（30%宽度）

- Tab切换："今晚黄金" | "后半夜" | "黎明前"
- 目标卡片内容：
  - 目标名称（M42 - 猎户座大星云）
  - 类型标签（星云/星系/星团）
  - 星等 + 视大小
  - 最佳时段（20:30-23:45）
  - 当前高度角（实时更新）
  - 推荐指数（数字 + 颜色条）
  - 方位角 + 高度角
- 排序选项：推荐指数 / 最佳时段 / 亮度

### 4.2 推荐指数颜色编码

- **绿色**（>80分）：强烈推荐
- **黄色**（60-80分）：推荐
- **橙色**（<60分）：可考虑

### 4.3 交互细节

**天空图**
- 单击：显示目标详细信息浮层
- 拖拽：绘制/编辑可视区域多边形
- 滚轮：缩放高度角

**推荐列表**
- 悬停：天空图中高亮对应目标
- 点击：滚动天空图到目标位置

**实时更新**
- 每分钟自动刷新目标位置
- 可见性状态变化时动画提示

### 4.4 移动端适配

- 垂直布局：配置 → 天空图 → 推荐
- 天空图支持触摸手势（双指缩放、单指拖拽）
- 横屏模式：天空图全屏，配置和列表侧边滑出

---

## 5. 数据模型

### 5.1 深空天体数据

```javascript
{
  id: "M42",
  name: "猎户座大星云",
  type: "emission-nebula",
  // 类型：emission-nebula | galaxy | cluster | planetary-nebula
  ra: 83.633,        // 赤经（度）
  dec: -5.391,       // 赤纬（度）
  magnitude: 4.0,    // 视星等
  size: 85,          // 视大小（角分）
  optimalFov: { min: 100, max: 400 },
  constellation: "Orion",
  difficulty: 1      // 1-5级，1为最易
}
```

**数据库规模**
- Messier天体：110个
- NGC天体：约150个常见目标
- IC天体：约40个明亮目标
- **总计：约300个目标**

### 5.2 用户配置

```javascript
{
  location: {
    name: "常用观测点",
    lat: 39.9042,
    lng: 116.4074,
    timezone: "Asia/Shanghai"
  },
  equipment: {
    sensorSize: "full-frame",
    sensorWidth: 36,    // mm
    sensorHeight: 24,   // mm
    focalLength: 200,   // mm
    fovH: 10.5,         // 度
    fovV: 7.0           // 度
  },
  visibleZones: [
    {
      id: "zone-1",
      name: "东侧空地",
      polygon: [
        [90, 20],  // [方位角, 高度角]
        [120, 20],
        [120, 60],
        [90, 60]
      ],
      priority: 1
    }
  ]
}
```

### 5.3 IndexedDB存储结构

**ObjectStore: `deepsky_objects`**
- 深空天体数据库（静态，约300条）
- 索引：`id`, `type`, `constellation`

**ObjectStore: `user_configs`**
- 用户配置（可保存多套）
- 索引：`name`, `lastUsed`

**ObjectStore: `cached_calculations`**
- 缓存的计算结果
- Key: `${date}_${location.lat}_${location.lng}`
- Value: 当天所有目标的可见性窗口
- TTL: 24小时

---

## 6. 关键算法实现

### 6.1 可见性计算

```javascript
function calculateVisibilityWindow(target, location, date, visibleZones) {
  const samples = generateTimeSamples(date, 5); // 5分钟间隔

  for (const zone of visibleZones) {
    let inWindow = false;
    let windowStart, windowEnd;
    let maxAltitude = 0;

    for (const time of samples) {
      const { alt, az } = calculateTargetPosition(target, location, time);
      const isInZone = pointInPolygon([az, alt], zone.polygon);

      if (isInZone && alt > 15) { // 高度>15度
        if (!inWindow) {
          windowStart = time;
          inWindow = true;
        }
        windowEnd = time;
        maxAltitude = Math.max(maxAltitude, alt);
      }
    }

    if (windowStart && windowEnd) {
      return {
        zoneId: zone.id,
        windowStart,
        windowEnd,
        maxAltitude
      };
    }
  }
  return null;
}
```

### 6.2 FOV匹配度评分

```javascript
function calculateFovMatchScore(targetSize, fovInArcmin) {
  const ratio = targetSize / Math.min(fovInArcmin.h, fovInArcmin.v);

  if (ratio < 0.1) return 5;        // 太小
  if (ratio > 1.5) return 3;        // 太大
  if (ratio >= 0.2 && ratio <= 0.7) return 20; // 理想
  if (ratio >= 0.1 && ratio < 0.2) return 15;
  if (ratio > 0.7 && ratio <= 1.0) return 12;

  return 8;
}
```

### 6.3 高度得分

```javascript
function calculateAltitudeScore(maxAltitude) {
  if (maxAltitude < 30) {
    return Math.max(0, (maxAltitude - 15) / 15 * 40);
  }
  if (maxAltitude < 60) {
    return 40 + (maxAltitude - 30) / 30 * 10;
  }
  return 50; // 满分
}
```

### 6.4 亮度得分

```javascript
function calculateBrightnessScore(magnitude) {
  if (magnitude <= 2) return 30;
  if (magnitude <= 4) return 25;
  if (magnitude <= 6) return 18;
  if (magnitude <= 8) return 10;
  return 5;
}
```

---

## 7. 技术实现要点

### 7.1 天体位置计算

使用 `astronomy-engine` 库：

```javascript
import { makeObserver, searchRiseSet, Body } from 'astronomy-engine';

function calculateTargetPosition(target, location, time) {
  const observer = makeObserver(
    location.lat,
    location.lng,
    0 // 海拔高度
  };

  const equiJ2000 = {
    ra: target.ra,
    dec: target.dec,
    dist: 1000 // 忽略距离
  };

  const pos = geometryOfHourAngle(
    observer,
    equiJ2000,
    time
  );

  return {
    alt: pos.altitude,  // 高度角（度）
    az: pos.azimuth     // 方位角（度）
  };
}
```

### 7.2 可视区域多边形判断

使用射线法判断点是否在多边形内：

```javascript
function pointInPolygon(point, polygon) {
  const [x, y] = point;
  let inside = false;

  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[j];

    const intersect = ((yi > y) !== (yj > y)) &&
      (x < (xj - xi) * (y - yi) / (yj - yi) + xi);

    if (intersect) inside = !inside;
  }

  return inside;
}
```

### 7.3 Service Worker离线策略

```javascript
// 缓存策略：Cache First
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});

// 预缓存核心资源
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('skywatcher-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/index.html',
        '/app.js',
        '/deepsky-data.json'
      ]);
    })
  );
});
```

---

## 8. 开发计划

### 8.1 阶段划分

**Phase 1: 核心功能（MVP）**
- [x] 需求分析和设计
- [ ] 地理定位模块
- [ ] 天体位置计算
- [ ] 简化版推荐算法（仅基于高度和亮度）
- [ ] 基础UI（配置面板 + 推荐列表）

**Phase 2: 交互增强**
- [ ] Canvas交互式天空图
- [ ] 可视区域多边形编辑
- [ ] 完整评分算法
- [ ] 时段分组展示

**Phase 3: 离线支持**
- [ ] IndexedDB数据持久化
- [ ] Service Worker配置
- [ ] PWA清单文件

**Phase 4: 优化和打磨**
- [ ] 移动端适配
- [ ] 性能优化
- [ ] 用户体验打磨

### 8.2 技术难点

1. **天文计算精度**：需要确保天体位置计算误差<0.1°
2. **Canvas性能**：绘制300+个目标标记时保持60fps
3. **离线数据更新**：设计合理的缓存失效策略
4. **多边形编辑交互**：提供直观的拖拽和缩放体验

---

## 9. 后续扩展可能

### 9.1 高级功能
- 光污染级别评估（基于位置数据）
- 月亮影响计算（避开受月光干扰的目标）
- 天气数据集成（云量预报）
- 拍摄计划导出（ICS日历格式）

### 9.2 社区功能
- 用户拍摄作品分享
- 目标评分和反馈
- 观测点数据库

---

## 附录

### A. 参考资源

**天文计算库**
- [astronomy-engine](https://github.com/cosinekitty/astronomy)
- [satellite.js](https://github.com/shashwatak/satellite.js)

**深空天体数据源**
- [Messier Objects Database](https://en.wikipedia.org/wiki/Messier_object)
- [NGC/IC Project](http://ngcicproject.org/)

### B. 术语表

- **FOV (Field of View)**：视场角，镜头能拍摄到的角度范围
- **赤经 (RA)**：天球经度，单位为小时或度
- **赤纬 (Dec)**：天球纬度，单位为度
- **视星等 (Magnitude)**：天体亮度，数值越小越亮
- **视大小**：天体在天球上的角直径，单位为角分
- **方位角**：从正北顺时针测量的角度（0-360°）
- **高度角**：天体相对于地平线的仰角（0-90°）

---

**文档版本**: 1.0
**最后更新**: 2025-01-21
