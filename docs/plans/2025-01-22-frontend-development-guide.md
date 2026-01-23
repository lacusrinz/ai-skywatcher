# 深空拍摄目标推荐工具 - 前端开发文档

**文档版本**: 1.1 (已与后端对齐)
**创建日期**: 2025-01-22
**基于设计文档**: 2025-01-21-deep-sky-target-recommender-design.md
**设计稿**: MasterGo - sky-watcher

**对齐说明**: 本文档已与后端设计文档 (`backend-design.md`) 对齐，确保API接口、数据结构、响应格式一致。详见 `api-interface-alignment.md`。

---

## 目录

1. [项目概述](#1-项目概述)
2. [设计系统](#2-设计系统)
3. [组件架构](#3-组件架构)
4. [布局规范](#4-布局规范)
5. [状态管理](#5-状态管理)
6. [Mock 数据接口](#6-mock-数据接口)
7. [Canvas 天空图实现](#7-canvas-天空图实现)
8. [性能优化](#8-性能优化)
9. [开发流程](#9-开发流程)

---

## 1. 项目概述

### 1.1 项目信息

- **项目名称**: 深空拍摄目标推荐工具 (AI Skywatcher)
- **产品类型**: 离线优先的单页面应用（PWA）
- **目标用户**: 有经验的天文摄影师
- **核心功能**: 根据用户位置、镜头参数、可视区域智能推荐深空拍摄目标

### 1.2 技术栈

```yaml
前端框架: Vanilla JavaScript + HTML5 (或可选 React/Vue)
构建工具: Vite
样式方案: CSS Modules + CSS Variables
图表库: Canvas API (天空图)
状态管理: IndexedDB + 自定义 Store
地理定位: Geolocation API
天文计算: astronomy-engine
日期处理: date-fns
离线存储: IndexedDB + Service Worker
```

### 1.3 文件结构

```
src/
├── index.html              # 入口 HTML
├── styles/
│   ├── variables.css       # CSS 变量（设计 tokens）
│   ├── reset.css          # 样式重置
│   ├── components.css     # 组件样式
│   └── layouts.css        # 布局样式
├── scripts/
│   ├── main.js            # 入口文件
│   ├── store.js           # 状态管理
│   ├── api.js             # Mock API 接口
│   ├── utils/
│   │   ├── astronomy.js   # 天文计算工具
│   │   ├── geo.js         # 地理定位工具
│   │   └── canvas.js      # Canvas 绘制工具
│   ├── components/
│   │   ├── Header.js      # 顶部导航栏
│   │   ├── ConfigPanel.js # 左侧配置面板
│   │   ├── SkyMap.js      # 中间天空图
│   │   ├── RecommendList.js # 右侧推荐列表
│   │   └── Modal.js       # 模态框
│   └── services/
│       ├── storage.js     # IndexedDB 存储
│       └── sw.js          # Service Worker
├── data/
│   ├── deepsky-objects.json # 深空天体数据库
│   └── mock-data.json     # Mock 数据
└── manifest.json          # PWA 清单文件
```

---

## 2. 设计系统

### 2.1 设计 Tokens（Design Tokens）

#### 颜色系统（Color Palette）

```css
:root {
  /* 背景色 */
  --bg-primary: #121212;      /* 主背景色（深空主题） */
  --bg-secondary: #1A1A2E;    /* 次要背景色（面板/卡片） */
  --bg-tertiary: #2D2D3A;     /* 三级背景色（子面板） */
  --bg-elevated: #0F172A;     /* 浮起元素背景 */

  /* 文字色 */
  --text-primary: #FFFFFF;    /* 主文字色（标题/正文） */
  --text-secondary: #E0E0E0;  /* 次要文字色（辅助文本） */
  --text-disabled: #9E9E9E;   /* 禁用状态文字色 */
  --text-hint: #94A3B8;       /* 提示文字色 */

  /* 强调色 */
  --accent-primary: #10B981;  /* 主强调色（绿色，成功/推荐） */
  --accent-secondary: #3B82F6;/* 次强调色（蓝色，链接/选中） */
  --accent-warning: #F59E0B;  /* 警告色（橙色） */
  --accent-error: #EF4444;    /* 错误色（红色） */

  /* 边框色 */
  --border-primary: #334155;  /* 主边框色 */
  --border-secondary: #475569;/* 次边框色 */
  --border-focus: #3B82F6;    /* 焦点边框色 */

  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.2);

  /* 天空图专用色 */
  --sky-ground: #1A1A2E;      /* 地面 */
  --sky-horizon: #2D3748;     /* 地平线 */
  --sky-grid: #4A5568;        /* 网格线 */
  --sky-target-galaxy: #F687B3; /* 星系颜色（粉色） */
  --sky-target-nebula: #63B3ED; /* 星云颜色（蓝色） */
  --sky-target-cluster: #FBD38D; /* 星团颜色（橙色） */
}
```

#### 字体系统（Typography）

```css
:root {
  /* 字体族 */
  --font-family-base: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                      'Helvetica Neue', Arial, sans-serif;
  --font-family-mono: 'SF Mono', Monaco, 'Cascadia Code', 'Courier New', monospace;

  /* 字体大小 */
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-md: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  --font-size-3xl: 32px;

  /* 字重 */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* 行高 */
  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;
}
```

#### 间距系统（Spacing）

```css
:root {
  --spacing-0: 0;
  --spacing-1: 4px;
  --spacing-2: 8px;
  --spacing-3: 12px;
  --spacing-4: 16px;
  --spacing-5: 20px;
  --spacing-6: 24px;
  --spacing-8: 32px;
  --spacing-10: 40px;
  --spacing-12: 48px;
}
```

#### 圆角（Border Radius）

```css
:root {
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;
}
```

#### 过渡动画（Transitions）

```css
:root {
  --transition-fast: 150ms ease-in-out;
  --transition-base: 200ms ease-in-out;
  --transition-slow: 300ms ease-in-out;
}
```

### 2.2 响应式断点

```css
/* 移动端优先 */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
@media (min-width: 1536px) { /* 2xl */ }
```

---

## 3. 组件架构

### 3.1 组件层次结构

```
App
├── Header（顶部导航栏）
│   ├── Logo
│   ├── LocationDisplay（位置显示）
│   ├── DateSelector（日期选择器）
│   └── EquipmentSelector（设备选择器）
│
├── Main（主内容区）
│   ├── ConfigPanel（左侧配置面板，可折叠）
│   │   ├── LocationCard（位置卡片）
│   │   ├── EquipmentCard（设备卡片）
│   │   └── VisibleZonesCard（可视区域卡片）
│   │
│   ├── SkyMap（中间天空图）
│   │   ├── Canvas（画布）
│   │   ├── TimeSlider（时间滑块）
│   │   └── TargetTooltip（目标提示框）
│   │
│   └── RecommendPanel（右侧推荐面板）
│       ├── PeriodTabs（时段标签页）
│       ├── TargetList（目标列表）
│       └── TargetCard（目标卡片）
│
└── Modal（模态框组件）
    ├── LocationModal（位置设置模态框）
    ├── EquipmentModal（设备设置模态框）
    └── ZoneEditorModal（可视区域编辑器）
```

### 3.2 核心组件规范

#### 3.2.1 Header（顶部导航栏）

**功能**:
- 显示当前地点和本地时间
- 日期选择器（用于规划未来观测）
  - 点击显示日历选择器
  - 默认显示当前日期
  - 支持选择未来任意日期
  - 选择日期后自动重新加载推荐
  - 格式：YYYY-MM-DD
- 设备配置下拉菜单

**尺寸**:
- 高度: `64px`
- 左右 padding: `--spacing-6 (24px)`

**样式**:
```css
.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-6);
  z-index: 100;
}

.header-left,
.header-center,
.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}
```

**Mock 数据结构**:
```javascript
{
  location: {
    name: "北京天文馆",
    lat: 39.9042,
    lng: 116.4074,
    timezone: "Asia/Shanghai"
  },
  currentDate: "2025-01-22",
  currentTime: "20:30:45",
  equipment: {
    id: "eq-1",
    name: "全画幅 + 200mm",
    fov: { h: 10.3, v: 6.9 }
  }
}
```

#### 3.2.2 ConfigPanel（左侧配置面板）

**功能**:
- 位置设置（自动/手动）
  - 自动定位：使用浏览器 Geolocation API 获取真实位置
  - 手动输入：经纬度输入框
  - 常用地点管理（使用 localStorage 本地存储）
    - 默认为空列表
    - 定位后可以添加到常用地点
    - 支持自定义名称
    - 从常用地点选择加载
    - 删除已保存的地点
    - 数据持久化在浏览器本地，不依赖服务器
- 设备配置（预设/自定义）
  - 预设切换时自动更新传感器尺寸、焦距和 FOV
  - "自定义"预设下可手动输入传感器尺寸和焦距
  - 非自定义预设下输入框禁用（只读）
  - 输入变化时自动计算 FOV
- 可视区域管理

**本地存储策略**:

```javascript
// 使用 localStorage 存储用户配置
const STORAGE_KEYS = {
  SAVED_LOCATIONS: 'skywatcher_saved_locations',  // 常用地点列表
  CURRENT_LOCATION: 'skywatcher_current_location', // 当前位置
  SELECTED_EQUIPMENT: 'skywatcher_equipment',      // 设备配置
  SELECTED_DATE: 'skywatcher_date'                 // 选择的日期
};

// 数据结构
{
  savedLocations: [
    {
      id: 'loc-1',
      name: '家',
      latitude: 39.9042,
      longitude: 116.4074,
      timezone: 'Asia/Shanghai',
      createdAt: '2025-01-22T10:30:00Z'
    },
    {
      id: 'loc-2',
      name: '云南天文台',
      latitude: 25.0339,
      longitude: 102.7895,
      timezone: 'Asia/Shanghai',
      createdAt: '2025-01-22T11:00:00Z'
    }
  ]
}
```

**UI 交互流程**:

1. **初始状态**: 常用地点下拉框显示"常用地点 (0)"
2. **定位后**:
   - 显示"保存到常用地点"按钮
   - 点击按钮弹出名称输入框
   - 保存后更新下拉框
3. **选择地点**:
   - 从下拉框选择已保存的地点
   - 自动填充经纬度并更新推荐
4. **删除地点**:
   - 选中地点后显示删除按钮
   - 确认后从列表中移除

**尺寸**:
- 桌面端: 宽度 `320px`，可折叠
- 平板端: 抽屉模式，宽度 `280px`
- 移动端: 全屏模态框

**布局**:
```css
.config-panel {
  width: 320px;
  height: calc(100vh - 64px);
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-primary);
  padding: var(--spacing-6);
  overflow-y: auto;
  margin-top: 64px;
}

.config-card {
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: var(--spacing-4);
  margin-bottom: var(--spacing-4);
}
```

**Mock 数据**:
```javascript
// 位置配置
{
  locationMode: "auto", // "auto" | "manual"
  savedLocations: [
    { id: "loc-1", name: "家", lat: 39.9042, lng: 116.4074 },
    { id: "loc-2", name: "常用观测点", lat: 40.4461, lng: 79.9822 }
  ],
  currentLocation: {
    lat: 39.9042,
    lng: 116.4074,
    accuracy: 10 // 精度（米）
  }
}

// 设备配置
{
  presets: [
    {
      id: "eq-1",
      name: "全画幅 + 200mm",
      sensor: "full-frame",
      sensorWidth: 36,
      sensorHeight: 24,
      focal: 200,
      fovH: 10.3,
      fovV: 6.9
    },
    {
      id: "eq-2",
      name: "全画幅 + 85mm",
      sensor: "full-frame",
      sensorWidth: 36,
      sensorHeight: 24,
      focal: 85,
      fovH: 23.9,
      fovV: 16.0
    },
    {
      id: "eq-3",
      name: "全画幅 + 50mm",
      sensor: "full-frame",
      sensorWidth: 36,
      sensorHeight: 24,
      focal: 50,
      fovH: 39.6,
      fovV: 26.7
    },
    {
      id: "eq-4",
      name: "APS-C + 85mm",
      sensor: "aps-c",
      sensorWidth: 23.6,
      sensorHeight: 15.6,
      focal: 85,
      fovH: 15.2,
      fovV: 10.1
    },
    {
      id: "eq-5",
      name: "APS-C + 50mm",
      sensor: "aps-c",
      sensorWidth: 23.6,
      sensorHeight: 15.6,
      focal: 50,
      fovH: 25.8,
      fovV: 17.1
    },
    {
      id: "custom",
      name: "自定义",
      sensor: "custom",
      sensorWidth: 0,
      sensorHeight: 0,
      focal: 0,
      fovH: 0,
      fovV: 0
    }
  ],
  currentEquipment: {
    id: "eq-1",
    sensorSize: "full-frame",
    sensorWidth: 36, // mm
    sensorHeight: 24, // mm
    focalLength: 200, // mm
    fovH: 10.3, // 度
    fovV: 6.9   // 度
  }
}

// 可视区域
{
  zones: [
    {
      id: "zone-1",
      name: "东侧空地",
      polygon: [
        [90, 20],  // [方位角, 高度角]
        [120, 20],
        [120, 60],
        [90, 60]
      ]
    }
  ]
}
```

#### 3.2.3 SkyMap（中间天空图）

**功能**:
- 绘制 360° 方位角 × 90° 高度角的天空图
- 显示深空目标位置
- 绘制可视区域多边形
- 时间轴预览和交互
- 交互：点击、拖拽目标

**尺寸**:
- 高度: `calc(100vh - 64px)`
- 宽度: `flex: 1`

**Canvas 配置**:
```javascript
const skyMapConfig = {
  width: 800,
  height: 800,
  centerX: 400,
  centerY: 400,
  maxRadius: 380, // 最大半径（对应90°高度角）
  gridLines: {
    altitude: [0, 15, 30, 45, 60, 75, 90], // 高度角网格
    azimuth: [0, 45, 90, 135, 180, 225, 270, 315] // 方位角网格
  }
};
```

**绘制要素**:
1. 背景和网格
2. 地平线（`alt = 0°`）
3. 方位角标注（N/NE/E/SE/S/SW/W/NW）
4. 高度角圆圈（15°/30°/45°/60°/75°/90°）
5. 黄道线
6. 天赤道线
7. 深空目标标记（不同颜色代表类型）
8. 可视区域多边形（半透明遮罩）

**交互状态**:
```javascript
{
  currentTime: new Date(),
  selectedTarget: null,
  hoveredZone: null,
  isDrawingZone: false,
  currentZonePoints: []
}
```

#### 3.2.4 RecommendPanel（右侧推荐面板）

**功能**:
- Tab 切换（今晚黄金 / 后半夜 / 黎明前）
- 目标列表展示
- 排序和筛选
- 实时更新高度角

**尺寸**:
- 桌面端: 宽度 `360px`
- 平板端: 宽度 `320px`
- 移动端: 全屏

**布局**:
```css
.recommend-panel {
  width: 360px;
  height: calc(100vh - 64px);
  background: var(--bg-secondary);
  border-left: 1px solid var(--border-primary);
  display: flex;
  flex-direction: column;
  margin-top: 64px;
}

.period-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-primary);
}

.tab-button {
  flex: 1;
  padding: var(--spacing-4);
  background: transparent;
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  transition: all var(--transition-base);
}

.tab-button.active {
  color: var(--accent-primary);
  border-bottom: 2px solid var(--accent-primary);
}

.target-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-4);
}
```

**Mock 数据**:
```javascript
{
  currentPeriod: "tonight-golden", // "tonight-golden" | "midnight" | "dawn"
  periods: {
    "tonight-golden": {
      label: "今晚黄金",
      timeRange: "20:00 - 00:00",
      targets: [
        {
          targetId: "M42",
          name: "猎户座大星云",
          type: "emission-nebula",
          magnitude: 4.0,
          size: 85, // 角分
          constellation: "Orion",
          bestTime: { start: "20:30", end: "23:45" },
          currentAltitude: 45.2,
          currentAzimuth: 135.6,
          maxAltitude: 65,
          maxAltitudeTime: "22:15",
          score: 87,
          scoreBreakdown: {
            altitude: 38,
            brightness: 28,
            fovMatch: 15,
            duration: 6
          },
          visibilityWindows: [
            {
              startTime: "2025-01-22T20:30:00+08:00",
              endTime: "2025-01-23T00:45:00+08:00",
              maxAltitude: 65,
              zoneId: "zone-1"
            }
          ]
        },
        // ... 更多目标
      ]
    }
  }
}
```

**目标卡片样式**:
```css
.target-card {
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: var(--spacing-4);
  margin-bottom: var(--spacing-3);
  cursor: pointer;
  transition: all var(--transition-base);
  border-left: 4px solid transparent;
}

.target-card:hover {
  background: var(--bg-elevated);
  transform: translateX(4px);
}

.target-card.score-high {
  border-left-color: var(--accent-primary); /* >80分，绿色 */
}

.target-card.score-medium {
  border-left-color: var(--accent-warning); /* 60-80分，橙色 */
}

.target-card.score-low {
  border-left-color: var(--accent-error); /* <60分，红色 */
}

.target-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-2);
}

.target-name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.target-type {
  font-size: var(--font-size-sm);
  color: var(--text-hint);
  text-transform: uppercase;
}

.target-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-2);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.target-score {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-top: var(--spacing-3);
}

.score-bar {
  flex: 1;
  height: 8px;
  background: var(--bg-primary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: var(--accent-primary);
  transition: width var(--transition-slow);
}
```

---

## 4. 布局规范

### 4.1 整体布局

**桌面端（≥1024px）**:
```
┌─────────────────────────────────────────────────────────┐
│ Header (64px)                                           │
├──────────┬────────────────────────────┬─────────────────┤
│          │                            │                 │
│ Config   │                            │  Recommend      │
│ Panel    │         Sky Map             │  Panel          │
│ (320px)  │         (flex: 1)           │  (360px)        │
│          │                            │                 │
└──────────┴────────────────────────────┴─────────────────┘
```

**平板端（768px - 1023px）**:
```
┌────────────────────────────────────────────────┐
│ Header (64px)                                  │
├───────────┬────────────────────────────────────┤
│           │                                    │
│  Config   │            Sky Map                 │
│  Drawer   │         (flex: 1)                  │
│ (280px)   │                                    │
│           │    + Recommend Panel (Overlay)     │
└───────────┴────────────────────────────────────┘
```

**移动端（<768px）**:
```
┌─────────────────────────┐
│ Header (64px)           │
├─────────────────────────┤
│ Config Panel            │
│ (Full Screen Modal)     │
├─────────────────────────┤
│                         │
│     Sky Map             │
│    (100% width)         │
│                         │
├─────────────────────────┤
│ Recommend Panel         │
│ (Bottom Sheet)          │
└─────────────────────────┘
```

### 4.2 Grid 布局系统

```css
.app-container {
  display: grid;
  grid-template-rows: 64px 1fr;
  grid-template-columns: 320px 1fr 360px;
  height: 100vh;
}

/* 桌面端 */
@media (min-width: 1024px) {
  .app-container {
    grid-template-columns: 320px 1fr 360px;
  }
}

/* 平板端 */
@media (max-width: 1023px) {
  .app-container {
    grid-template-columns: 1fr;
  }
  .config-panel {
    position: fixed;
    left: -320px;
    transition: left var(--transition-slow);
  }
  .config-panel.open {
    left: 0;
  }
}

/* 移动端 */
@media (max-width: 767px) {
  .app-container {
    grid-template-columns: 1fr;
  }
  .recommend-panel {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 50vh;
    transform: translateY(100%);
    transition: transform var(--transition-slow);
  }
  .recommend-panel.open {
    transform: translateY(0);
  }
}
```

---

## 5. 状态管理

### 5.1 状态树结构

```javascript
const state = {
  // 用户配置
  config: {
    location: {
      mode: 'auto', // 'auto' | 'manual'
      current: { lat: 39.9042, lng: 116.4074, name: '北京' },
      saved: []
    },
    equipment: {
      sensor: 'full-frame',
      focalLength: 200,
      fov: { h: 10.5, v: 7.0 }
    },
    visibleZones: []
  },

  // 天空图状态
  skyMap: {
    currentTime: new Date(),
    selectedDate: new Date(), // 用户选择的观测日期（默认今天）
    hoveredTarget: null,
    selectedTarget: null,
    zoom: 1.0,
    pan: { x: 0, y: 0 },
    isDrawingZone: false,
    currentZonePoints: []
  },

  // 推荐数据
  recommendations: {
    currentPeriod: 'tonight-golden',
    sortBy: 'score', // 'score' | 'brightness' | 'time'
    periods: {
      'tonight-golden': [],
      'midnight': [],
      'dawn': []
    }
  },

  // UI 状态
  ui: {
    isConfigPanelOpen: true,
    isRecommendPanelOpen: true,
    activeModal: null,
    isLoading: false,
    error: null
  },

  // 数据库
  db: {
    deepskyObjects: [], // 约300个深空目标
    userConfigs: [],
    cachedCalculations: {}
  }
};
```

### 5.2 状态更新模式

```javascript
// 简单的 Pub/Sub 模式
class Store {
  constructor(initialState) {
    this.state = initialState;
    this.listeners = [];
  }

  getState() {
    return this.state;
  }

  setState(partialState) {
    this.state = { ...this.state, ...partialState };
    this.notify();
  }

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  notify() {
    this.listeners.forEach(listener => listener(this.state));
  }
}

// 使用示例
const store = new Store(state);

store.subscribe((newState) => {
  renderApp(newState);
});

// 更新状态
store.setState({
  config: {
    ...store.state.config,
    equipment: { sensor: 'aps-c', focalLength: 85 }
  }
});
```

---

## 6. Mock 数据接口

### 6.1 API 设计

所有数据使用 Mock 接口，实际开发时使用 `fetch` 或 `axios` 替换。

```javascript
// src/scripts/api.js
const API = {
  // 基础 URL（与后端对齐，使用版本化的 API）
  baseURL: '/api/v1',

  // 请求延迟（模拟网络）
  delay: 100,

  // 通用请求方法
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

    // 统一处理响应格式（后端返回 {success, data, message}）
    if (!result.success) {
      throw new Error(result.error?.message || '请求失败');
    }

    return result.data; // 返回实际数据
  },

  // ===== 地理定位 =====

  // 自动获取位置（改为 POST）
  async getCurrentLocation() {
    return this.request('/locations/geolocate', {
      method: 'POST'
    });
  },

  // 获取保存的地点列表
  async getSavedLocations() {
    return this.request('/locations');
  },

  // 保存地点
  async saveLocation(location) {
    return this.request('/locations', {
      method: 'POST',
      body: JSON.stringify(location)
    });
  },

  // 删除地点（新增）
  async deleteLocation(locationId) {
    return this.request(`/locations/${locationId}`, {
      method: 'DELETE'
    });
  },

  // ===== 设备配置 =====

  // 获取设备预设
  async getEquipmentPresets() {
    return this.request('/equipment/presets');
  },

  // 计算 FOV（新增）
  async calculateFOV(sensorWidth, sensorHeight, focalLength) {
    return this.request('/equipment/calculate-fov', {
      method: 'POST',
      body: JSON.stringify({
        sensor_width: sensorWidth,
        sensor_height: sensorHeight,
        focal_length: focalLength
      })
    });
  },

  // 保存设备配置
  async saveEquipment(equipment) {
    return this.request('/equipment', {
      method: 'POST',
      body: JSON.stringify(equipment)
    });
  },

  // ===== 可视区域 =====

  // 获取保存的可视区域（路径改为 /visible-zones）
  async getVisibleZones() {
    return this.request('/visible-zones');
  },

  // 保存可视区域
  async saveVisibleZone(zone) {
    return this.request('/visible-zones', {
      method: 'POST',
      body: JSON.stringify(zone)
    });
  },

  // 更新可视区域（新增）
  async updateVisibleZone(zoneId, zone) {
    return this.request(`/visible-zones/${zoneId}`, {
      method: 'PUT',
      body: JSON.stringify(zone)
    });
  },

  // 删除可视区域（路径改为 /visible-zones）
  async deleteVisibleZone(zoneId) {
    return this.request(`/visible-zones/${zoneId}`, {
      method: 'DELETE'
    });
  },

  // ===== 深空目标 =====

  // 获取深空目标列表（路径改为 /targets）
  async getDeepskyObjects(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/targets${query ? `?${query}` : ''}`);
  },

  // 获取单个目标详情（路径改为 /targets）
  async getDeepskyObject(targetId) {
    return this.request(`/targets/${targetId}`);
  },

  // 搜索目标（新增）
  async searchTargets(query) {
    return this.request(`/targets/search?q=${encodeURIComponent(query)}`);
  },

  // ===== 推荐 =====

  // 获取推荐目标（改为 POST，使用请求体）
  async getRecommendations(params) {
    return this.request('/recommendations', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  // 按时段获取推荐（新增）
  async getRecommendationsByPeriod(period, params) {
    return this.request('/recommendations/by-period', {
      method: 'POST',
      body: JSON.stringify({
        period: period,
        ...params
      })
    });
  },

  // 获取推荐统计（新增）
  async getRecommendationsSummary(params) {
    return this.request('/recommendations/summary', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  // ===== 可见性计算（新增）=====

  // 获取目标的实时位置（改为 POST）
  async getTargetPosition(targetId, location, timestamp) {
    return this.request('/visibility/position', {
      method: 'POST',
      body: JSON.stringify({
        target_id: targetId,
        location: location,
        timestamp: timestamp.toISOString()
      })
    });
  },

  // 计算目标的可见窗口（新增）
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
  },

  // 批量计算目标位置（新增）
  async getBatchTargetPositions(targetIds, location, timestamp) {
    return this.request('/visibility/positions-batch', {
      method: 'POST',
      body: JSON.stringify({
        target_ids: targetIds,
        location: location,
        timestamp: timestamp.toISOString()
      })
    });
  },

  // ===== 天空图 =====

  // 获取天空图渲染数据（改为 POST）
  async getSkyMapData(params) {
    return this.request('/sky-map/data', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  // 获取时间轴数据（新增）
  async getSkyMapTimeline(params) {
    return this.request('/sky-map/timeline', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  }
};
```

### 6.2 Mock 数据实现

使用 Service Worker 或 MSW（Mock Service Worker）拦截请求：

```javascript
// src/scripts/mock.js
const mockData = {
  // 深空目标数据库
  deepskyObjects: [
    {
      id: "M42",
      name: "猎户座大星云",
      type: "emission-nebula",
      ra: 83.633,
      dec: -5.391,
      magnitude: 4.0,
      size: 85,
      constellation: "Orion",
      difficulty: 1
    },
    {
      id: "M31",
      name: "仙女座星系",
      type: "galaxy",
      ra: 10.684,
      dec: 41.269,
      magnitude: 3.4,
      size: 178,
      constellation: "Andromeda",
      difficulty: 2
    },
    // ... 约300个目标
  ],

  // 设备预设
  equipmentPresets: [
    {
      id: "eq-1",
      name: "全画幅 + 200mm",
      sensor: "full-frame",
      sensorWidth: 36,
      sensorHeight: 24,
      focalLength: 200,
      fovH: 10.3,
      fovV: 6.9
    },
    {
      id: "eq-2",
      name: "APS-C + 85mm",
      sensor: "aps-c",
      sensorWidth: 23.6,
      sensorHeight: 15.6,
      focalLength: 85,
      fovH: 15.2,
      fovV: 10.1
    },
    {
      id: "eq-3",
      name: "M4/3 + 300mm",
      sensor: "m43",
      sensorWidth: 17.3,
      sensorHeight: 13.0,
      focalLength: 300,
      fovH: 4.4,
      fovV: 3.3
    }
  ],

  // 推荐结果
  recommendations: {
    "tonight-golden": [
      {
        targetId: "M42",
        score: 87,
        scoreBreakdown: { altitude: 38, brightness: 28, fovMatch: 15, duration: 6 },
        currentAltitude: 45.2,
        currentAzimuth: 135.6,
        maxAltitude: 65,
        maxAltitudeTime: "22:15",
        bestTime: { start: "20:30", end: "23:45" },
        visibilityWindows: [
          {
            startTime: "2025-01-22T20:30:00+08:00",
            endTime: "2025-01-23T00:45:00+08:00",
            maxAltitude: 65,
            zoneId: "zone-1"
          }
        ]
      },
      // ... 更多推荐
    ],
    "midnight": [],
    "dawn": []
  }
};

// Mock API 响应处理
function mockAPI(url, method, data) {
  // 解析 URL
  const pathname = new URL(url, 'http://localhost').pathname;

  // 路由处理
  if (pathname === '/api/location/current' && method === 'GET') {
    return {
      lat: 39.9042,
      lng: 116.4074,
      name: "北京",
      accuracy: 10
    };
  }

  if (pathname === '/api/equipment/presets' && method === 'GET') {
    return mockData.equipmentPresets;
  }

  if (pathname === '/api/objects' && method === 'GET') {
    return mockData.deepskyObjects;
  }

  if (pathname.startsWith('/api/recommendations') && method === 'GET') {
    const params = new URLSearchParams(url.split('?')[1]);
    const period = params.get('period') || 'tonight-golden';
    return mockData.recommendations[period];
  }

  // ... 更多路由

  return { error: 'Not Found' };
}
```

### 6.3 使用 MSW（推荐）

安装 MSW：
```bash
npm install msw --save-dev
```

配置 Mock Service Worker：
```javascript
// src/scripts/mocks.js
import { setupWorker, rest } from 'msw';

import { mockData } from './mock-data';

const worker = setupWorker(
  // 地理定位
  rest.get('/api/location/current', (req, res, ctx) => {
    return res(
      ctx.delay(100),
      ctx.json(mockData.location.current)
    );
  }),

  // 设备预设
  rest.get('/api/equipment/presets', (req, res, ctx) => {
    return res(
      ctx.delay(100),
      ctx.json(mockData.equipmentPresets)
    );
  }),

  // 深空目标
  rest.get('/api/objects', (req, res, ctx) => {
    return res(
      ctx.delay(100),
      ctx.json(mockData.deepskyObjects)
    );
  }),

  // 推荐
  rest.get('/api/recommendations', (req, res, ctx) => {
    const period = req.url.searchParams.get('period') || 'tonight-golden';
    return res(
      ctx.delay(100),
      ctx.json(mockData.recommendations[period])
    );
  })
);

// 启动 worker
worker.start();
```

---

## 7. Canvas 天空图实现

### 7.1 Canvas 基础配置

```javascript
// src/utils/canvas.js
export class SkyMapCanvas {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');

    // 配置
    this.config = {
      width: 800,
      height: 800,
      centerX: 400,
      centerY: 400,
      maxRadius: 380,
      ...options
    };

    // 状态
    this.state = {
      time: new Date(),
      targets: [],
      zones: [],
      hoveredTarget: null,
      zoom: 1.0,
      pan: { x: 0, y: 0 }
    };

    // 初始化
    this.init();
  }

  init() {
    // 设置 Canvas 尺寸（考虑设备像素比）
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = this.config.width * dpr;
    this.canvas.height = this.config.height * dpr;
    this.canvas.style.width = `${this.config.width}px`;
    this.canvas.style.height = `${this.config.height}px`;
    this.ctx.scale(dpr, dpr);

    // 绑定事件
    this.bindEvents();
  }

  bindEvents() {
    // 鼠标移动
    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      this.handleMouseMove(x, y);
    });

    // 点击
    this.canvas.addEventListener('click', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      this.handleClick(x, y);
    });

    // 滚轮缩放
    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      this.handleZoom(e.deltaY);
    });
  }

  // 渲染
  render() {
    const { ctx, config, state } = this;

    // 清空画布
    ctx.clearRect(0, 0, config.width, config.height);

    // 绘制背景
    this.drawBackground();

    // 绘制网格
    this.drawGrid();

    // 绘制可视区域
    this.drawVisibleZones();

    // 绘制目标
    this.drawTargets();

    // 绘制地平线
    this.drawHorizon();
  }

  drawBackground() {
    const { ctx, config } = this;

    // 背景渐变
    const gradient = ctx.createRadialGradient(
      config.centerX, config.centerY, 0,
      config.centerX, config.centerY, config.maxRadius
    );
    gradient.addColorStop(0, '#1A1A2E');
    gradient.addColorStop(1, '#0F172A');

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, config.width, config.height);
  }

  drawGrid() {
    const { ctx, config } = this;

    ctx.strokeStyle = '#4A5568';
    ctx.lineWidth = 1;

    // 高度角圆圈
    for (let alt of [15, 30, 45, 60, 75, 90]) {
      const radius = (alt / 90) * config.maxRadius;
      ctx.beginPath();
      ctx.arc(config.centerX, config.centerY, radius, 0, Math.PI * 2);
      ctx.stroke();

      // 标注
      ctx.fillStyle = '#94A3B8';
      ctx.font = '12px sans-serif';
      ctx.fillText(`${alt}°`, config.centerX + 5, config.centerY - radius + 15);
    }

    // 方位角线
    for (let az of [0, 45, 90, 135, 180, 225, 270, 315]) {
      const angle = (az - 90) * (Math.PI / 180);
      const x = config.centerX + Math.cos(angle) * config.maxRadius;
      const y = config.centerY + Math.sin(angle) * config.maxRadius;

      ctx.beginPath();
      ctx.moveTo(config.centerX, config.centerY);
      ctx.lineTo(x, y);
      ctx.stroke();

      // 方位标注
      const labels = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '14px sans-serif';
      ctx.fillText(
        labels[az / 45],
        x + Math.cos(angle) * 20 - 10,
        y + Math.sin(angle) * 20 + 5
      );
    }
  }

  drawHorizon() {
    const { ctx, config } = this;

    ctx.strokeStyle = '#2D3748';
    ctx.lineWidth = 2;

    ctx.beginPath();
    ctx.arc(config.centerX, config.centerY, config.maxRadius, 0, Math.PI * 2);
    ctx.stroke();
  }

  drawTargets() {
    const { ctx, config, state } = this;

    state.targets.forEach(target => {
      // 计算位置
      const pos = this.azAltToXY(target.azimuth, target.altitude);

      // 绘制目标标记
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 6, 0, Math.PI * 2);

      // 根据类型设置颜色
      const colors = {
        'emission-nebula': '#63B3ED',
        'galaxy': '#F687B3',
        'cluster': '#FBD38D'
      };
      ctx.fillStyle = colors[target.type] || '#FFFFFF';
      ctx.fill();

      // 高亮
      if (state.hoveredTarget === target.id) {
        ctx.strokeStyle = '#FFFFFF';
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    });
  }

  drawVisibleZones() {
    const { ctx, config, state } = this;

    state.zones.forEach(zone => {
      ctx.fillStyle = 'rgba(16, 185, 129, 0.2)';
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.5)';
      ctx.lineWidth = 2;

      ctx.beginPath();
      zone.polygon.forEach(([az, alt], i) => {
        const pos = this.azAltToXY(az, alt);
        if (i === 0) {
          ctx.moveTo(pos.x, pos.y);
        } else {
          ctx.lineTo(pos.x, pos.y);
        }
      });
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    });
  }

  // 方位角、高度角转 Canvas 坐标
  azAltToXY(azimuth, altitude) {
    const { config } = this;
    const radius = (altitude / 90) * config.maxRadius;
    const angle = (azimuth - 90) * (Math.PI / 180);

    return {
      x: config.centerX + Math.cos(angle) * radius,
      y: config.centerY + Math.sin(angle) * radius
    };
  }

  // Canvas 坐标转方位角、高度角
  xyToAzAlt(x, y) {
    const { config } = this;
    const dx = x - config.centerX;
    const dy = y - config.centerY;
    const radius = Math.sqrt(dx * dx + dy * dy);
    const angle = Math.atan2(dy, dx) * (180 / Math.PI) + 90;

    return {
      azimuth: (angle + 360) % 360,
      altitude: Math.min(90, (radius / config.maxRadius) * 90)
    };
  }

  handleMouseMove(x, y) {
    const pos = this.xyToAzAlt(x, y);

    // 检测是否悬停在目标上
    const hoveredTarget = this.state.targets.find(target => {
      const targetPos = this.azAltToXY(target.azimuth, target.altitude);
      const distance = Math.sqrt(Math.pow(x - targetPos.x, 2) + Math.pow(y - targetPos.y, 2));
      return distance < 10;
    });

    if (hoveredTarget) {
      this.canvas.style.cursor = 'pointer';
    } else {
      this.canvas.style.cursor = 'default';
    }

    this.state.hoveredTarget = hoveredTarget ? hoveredTarget.id : null;
    this.render();
  }

  handleClick(x, y) {
    if (this.state.hoveredTarget) {
      // 触发目标选中事件
      this.onTargetSelect?.(this.state.hoveredTarget);
    }
  }

  handleZoom(delta) {
    const zoomFactor = delta > 0 ? 0.9 : 1.1;
    this.state.zoom = Math.max(0.5, Math.min(2.0, this.state.zoom * zoomFactor));
    this.render();
  }

  // 更新数据
  updateData(data) {
    this.state = { ...this.state, ...data };
    this.render();
  }
}
```

### 7.2 使用示例

```javascript
// 初始化天空图
const canvas = document.getElementById('skyMapCanvas');
const skyMap = new SkyMapCanvas(canvas, {
  width: 800,
  height: 800
});

// 更新目标位置
skyMap.updateData({
  targets: [
    { id: 'M42', type: 'emission-nebula', azimuth: 135.6, altitude: 45.2 },
    { id: 'M31', type: 'galaxy', azimuth: 60.5, altitude: 70.8 }
  ],
  zones: [
    {
      id: 'zone-1',
      polygon: [[90, 20], [120, 20], [120, 60], [90, 60]]
    }
  ]
});

// 监听目标选中
skyMap.onTargetSelect = (targetId) => {
  console.log('Selected target:', targetId);
  // 滚动推荐列表到对应目标
  // ...
};
```

---

## 8. 性能优化

### 8.1 渲染优化

1. **Canvas 优化**
   - 使用 `requestAnimationFrame` 批量更新
   - 离屏 Canvas 预渲染静态元素
   - 脏矩形渲染（只重绘变化区域）

```javascript
// 使用 requestAnimationFrame
function updateSkyMap() {
  requestAnimationFrame(() => {
    skyMap.render();
  });
}

// 防抖
function debounce(fn, delay) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), delay);
  };
}

const debouncedUpdate = debounce(updateSkyMap, 100);
```

2. **列表虚拟化**
   - 推荐列表只渲染可见区域
   - 使用 Intersection Observer API

```javascript
// 虚拟滚动示例
class VirtualList {
  constructor(container, itemHeight, renderItem) {
    this.container = container;
    this.itemHeight = itemHeight;
    this.renderItem = renderItem;
    this.visibleItems = [];
    this.observer = new IntersectionObserver(this.onIntersect.bind(this));
  }

  render(items) {
    const visibleCount = Math.ceil(this.container.clientHeight / this.itemHeight);
    this.visibleItems = items.slice(0, visibleCount * 2);

    this.container.innerHTML = '';
    this.visibleItems.forEach((item, index) => {
      const element = this.renderItem(item, index);
      element.style.height = `${this.itemHeight}px`;
      this.container.appendChild(element);
      this.observer.observe(element);
    });
  }

  onIntersect(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        // 加载更多数据
        this.loadMore();
      }
    });
  }
}
```

### 8.2 数据缓存

1. **IndexedDB 缓存**
   - 缓存深空目标数据库
   - 缓存计算结果（24小时有效期）

```javascript
// src/services/storage.js
class StorageService {
  constructor() {
    this.db = null;
  }

  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('SkyWatcherDB', 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (e) => {
        const db = e.target.result;

        // 深空目标存储
        if (!db.objectStoreNames.contains('deepskyObjects')) {
          const objectStore = db.createObjectStore('deepskyObjects', { keyPath: 'id' });
          objectStore.createIndex('type', 'type', { unique: false });
          objectStore.createIndex('constellation', 'constellation', { unique: false });
        }

        // 计算结果缓存
        if (!db.objectStoreNames.contains('cachedCalculations')) {
          const cacheStore = db.createObjectStore('cachedCalculations', { keyPath: 'key' });
          cacheStore.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
    });
  }

  async getDeepskyObjects() {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['deepskyObjects'], 'readonly');
      const store = transaction.objectStore('deepskyObjects');
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async cacheDeepskyObjects(objects) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['deepskyObjects'], 'readwrite');
      const store = transaction.objectStore('deepskyObjects');

      objects.forEach(obj => store.put(obj));

      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
  }

  async getCachedCalculation(key) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['cachedCalculations'], 'readwrite');
      const store = transaction.objectStore('cachedCalculations');
      const request = store.get(key);

      request.onsuccess = () => {
        const cached = request.result;
        if (cached) {
          const age = Date.now() - cached.timestamp;
          // 24小时有效期
          if (age < 24 * 60 * 60 * 1000) {
            resolve(cached.data);
            return;
          }
        }
        resolve(null);
      };
      request.onerror = () => reject(request.error);
    });
  }

  async setCachedCalculation(key, data) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['cachedCalculations'], 'readwrite');
      const store = transaction.objectStore('cachedCalculations');

      store.put({
        key,
        data,
        timestamp: Date.now()
      });

      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
  }
}
```

2. **Service Worker 缓存**
   - 缓存静态资源
   - 离线访问支持

```javascript
// src/services/sw.js
const CACHE_NAME = 'skywatcher-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/styles/variables.css',
  '/styles/components.css',
  '/scripts/main.js',
  '/data/deepsky-objects.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => {
      return response || fetch(e.request);
    })
  );
});
```

### 8.3 代码分割

```javascript
// 动态导入示例
async function loadSkyMap() {
  const { SkyMapCanvas } = await import('./utils/canvas.js');
  return new SkyMapCanvas(canvas);
}

async function loadRecommendations() {
  const { RecommendPanel } = await import('./components/RecommendPanel.js');
  return new RecommendPanel(container);
}
```

---

## 9. 开发流程

### 9.1 开发阶段划分

#### Phase 1: 基础架构（第1-2周）

- [ ] 项目初始化
  - [ ] 安装依赖（Vite、MSW、astronomy-engine）
  - [ ] 配置构建工具
  - [ ] 设置 Mock API
  - [ ] 创建基础文件结构

- [ ] 设计系统实现
  - [ ] CSS 变量定义
  - [ ] 全局样式重置
  - [ ] 组件基础样式

- [ ] 状态管理
  - [ ] Store 类实现
  - [ ] 状态订阅/发布机制
  - [ ] 持久化存储

#### Phase 2: 核心组件（第3-4周）

- [ ] Header 组件
  - [ ] 位置显示
  - [ ] 日期选择器
  - [ ] 设备选择器

- [ ] ConfigPanel 组件
  - [ ] 位置卡片
  - [ ] 设备卡片
  - [ ] 可视区域卡片

- [ ] Mock 数据
  - [ ] 深空目标数据库（300个）
  - [ ] 设备预设
  - [ ] 推荐算法 Mock

#### Phase 3: 天空图实现（第5-6周）

- [ ] Canvas 基础
  - [ ] 画布初始化
  - [ ] 坐标转换
  - [ ] 网格绘制

- [ ] 目标标记
  - [ ] 位置计算
  - [ ] 颜色编码
  - [ ] 交互（悬停/点击）

- [ ] 可视区域
  - [ ] 多边形绘制
  - [ ] 交互编辑
  - [ ] 保存/加载

- [ ] 时间轴
  - [ ] 时间滑块
  - [ ] 实时更新
  - [ ] 动画

#### Phase 4: 推荐系统（第7-8周）

- [ ] 推荐算法
  - [ ] 高度得分
  - [ ] 亮度得分
  - [ ] FOV 匹配度
  - [ ] 时长得分

- [ ] RecommendPanel 组件
  - [ ] Tab 切换
  - [ ] 目标列表
  - [ ] 排序/筛选

- [ ] 实时更新
  - [ ] 定时刷新
  - [ ] 状态同步

#### Phase 5: 离线支持（第9周）

- [ ] IndexedDB
  - [ ] 数据持久化
  - [ ] 缓存管理

- [ ] Service Worker
  - [ ] 静态资源缓存
  - [ ] 离线访问

- [ ] PWA
  - [ ] manifest.json
  - [ ] 安装提示

#### Phase 6: 优化和测试（第10周）

- [ ] 性能优化
  - [ ] Canvas 优化
  - [ ] 列表虚拟化
  - [ ] 代码分割

- [ ] 移动端适配
  - [ ] 响应式布局
  - [ ] 触摸交互

- [ ] 测试
  - [ ] 单元测试
  - [ ] 集成测试
  - [ ] 用户测试

### 9.2 开发规范

#### 命名规范

```javascript
// 文件命名：PascalCase for components, camelCase for utils
components/Header.js
components/ConfigPanel.js
utils/astronomy.js
utils/storage.js

// 变量命名：camelCase
const currentTime = new Date();
const selectedTarget = null;

// 常量命名：UPPER_SNAKE_CASE
const MAX_ALTITUDE = 90;
const GRID_INTERVAL = 15;

// 类命名：PascalCase
class SkyMapCanvas { }
class StorageService { }

// 函数命名：camelCase
function calculateAltitudeScore(maxAltitude) { }
function formatTime(date) { }
```

#### 代码风格

```javascript
// 使用 const/let，避免 var
const config = { width: 800 };
let count = 0;

// 使用模板字符串
const message = `Current altitude: ${altitude}°`;

// 使用箭头函数
const targets = objects.filter(obj => obj.type === 'galaxy');

// 使用解构
const { latitude, longitude } = location;
const [first, second] = array;

// 使用可选链
const name = target?.name ?? 'Unknown';

// 使用 async/await
async function fetchData() {
  try {
    const data = await API.getDeepskyObjects();
    return data;
  } catch (error) {
    console.error(error);
  }
}
```

#### 注释规范

```javascript
/**
 * 计算目标的高度得分
 * @param {number} maxAltitude - 最大高度角（度）
 * @returns {number} 高度得分（0-50分）
 */
function calculateAltitudeScore(maxAltitude) {
  if (maxAltitude < 30) {
    return Math.max(0, (maxAltitude - 15) / 15 * 40);
  }
  if (maxAltitude < 60) {
    return 40 + (maxAltitude - 30) / 30 * 10;
  }
  return 50;
}

// TODO: 实现可视区域多边形编辑功能
// FIXME: 修复时区转换问题
// NOTE: 使用 Web Workers 优化性能
```

### 9.3 Git 工作流

```bash
# 功能分支
git checkout -b feature/header-component
git checkout -b feature/sky-map-canvas
git checkout -b feature/recommendation-algorithm

# 修复分支
git checkout -b fix/timezone-conversion

# 提交规范
git commit -m "feat: add Header component"
git commit -m "fix: fix timezone conversion issue"
git commit -m "docs: update README"
git commit -m "perf: optimize Canvas rendering"
git commit -m "style: format code with Prettier"
git commit -m "refactor: rewrite storage service"
git commit -m "test: add unit tests for astronomy utils"
```

### 9.4 调试技巧

```javascript
// 开发模式日志
const DEBUG = true;

function debugLog(...args) {
  if (DEBUG) {
    console.log('[DEBUG]', ...args);
  }
}

// 性能监控
performance.mark('calculation-start');
// ... 计算代码
performance.mark('calculation-end');
performance.measure('calculation', 'calculation-start', 'calculation-end');
const measure = performance.getEntriesByName('calculation')[0];
console.log(`Calculation took ${measure.duration}ms`);

// Canvas 调试
function drawDebugInfo(ctx) {
  ctx.fillStyle = '#FFFFFF';
  ctx.font = '12px monospace';
  ctx.fillText(`Targets: ${state.targets.length}`, 10, 20);
  ctx.fillText(`FPS: ${fps}`, 10, 35);
}
```

---

## 附录

### A. API 接口总览

与后端对齐后的完整 API 接口列表:

| 模块 | 功能 | 端点 | 方法 | 说明 |
|------|------|------|------|------|
| **Locations** | 自动定位 | `/locations/geolocate` | POST | 获取当前地理位置 |
| | 获取列表 | `/locations` | GET | 获取保存的地点列表 |
| | 保存地点 | `/locations` | POST | 保存新地点 |
| | 删除地点 | `/locations/{id}` | DELETE | 删除保存的地点 |
| **Equipment** | 获取预设 | `/equipment/presets` | GET | 获取设备预设列表 |
| | 计算 FOV | `/equipment/calculate-fov` | POST | 计算视场角 |
| | 保存配置 | `/equipment` | POST | 保存自定义设备 |
| **Targets** | 获取列表 | `/targets` | GET | 获取深空目标列表 |
| | 获取详情 | `/targets/{id}` | GET | 获取目标详情 |
| | 搜索 | `/targets/search` | GET | 搜索目标 |
| **Visibility** | 计算位置 | `/visibility/position` | POST | 计算目标实时位置 |
| | 计算窗口 | `/visibility/windows` | POST | 计算可见窗口 |
| | 批量位置 | `/visibility/positions-batch` | POST | 批量计算位置 |
| **Zones** | 获取列表 | `/visible-zones` | GET | 获取可视区域列表 |
| | 创建区域 | `/visible-zones` | POST | 创建可视区域 |
| | 更新区域 | `/visible-zones/{id}` | PUT | 更新可视区域 |
| | 删除区域 | `/visible-zones/{id}` | DELETE | 删除可视区域 |
| **Recommend** | 获取推荐 | `/recommendations` | POST | 获取推荐目标 |
| | 按时段 | `/recommendations/by-period` | POST | 按时段获取推荐 |
| | 统计 | `/recommendations/summary` | POST | 获取推荐统计 |
| **SkyMap** | 天空图 | `/sky-map/data` | POST | 获取天空图数据 |
| | 时间轴 | `/sky-map/timeline` | POST | 获取时间轴数据 |

**注意**: 所有端点都使用 `/api/v1` 前缀，完整路径如 `/api/v1/locations`。

### B. 与后端对齐的主要变更

#### B.1 Base URL 变更
```javascript
// 修改前
baseURL: '/api'

// 修改后
baseURL: '/api/v1'
```

#### B.2 响应格式处理
```javascript
// 后端统一返回格式: {success, data, message}
// 前端需要解包 data 字段

async request(endpoint, options = {}) {
  // ...
  const result = await response.json();

  if (!result.success) {
    throw new Error(result.error?.message || '请求失败');
  }

  return result.data; // 返回实际数据
}
```

#### B.3 接口路径变更
```javascript
// 位置接口: /location → /locations
GET /location/current → POST /locations/geolocate
GET /location/saved → GET /locations

// 目标接口: /objects → /targets
GET /objects → GET /targets
GET /objects/{id} → GET /targets/{id}

// 可视区域: /zones → /visible-zones
GET /zones → GET /visible-zones
POST /zones → POST /visible-zones
```

#### B.4 请求方法变更
```javascript
// 推荐接口: GET → POST
// 修改前
GET /recommendations?period=tonight-golden

// 修改后
POST /recommendations
Body: {
  location: {...},
  date: "2025-01-22",
  equipment: {...},
  visible_zones: [...],
  limit: 20
}

// 可见性接口: GET → POST
// 修改前
GET /objects/{id}/position?time=2025-01-22T20:30:00Z

// 修改后
POST /visibility/position
Body: {
  target_id: "M42",
  location: {...},
  timestamp: "2025-01-22T20:30:00Z"
}
```

### C. 数据结构对照表

| 数据类型 | 前端接口 | 后端模型 | 说明 |
|---------|---------|---------|------|
| Location | `{lat, lng, name}` | `Location` | 使用 `latitude`/`longitude` 而非 `lat`/`lng` |
| Equipment | `{sensor, focal, fov}` | `Equipment` | 统一字段命名 |
| Target | `{id, name, type, ...}` | `DeepSkyTarget` | 完全对齐 |
| VisibleZone | `{id, polygon: [[az, alt], ...]}` | `VisibleZone` | 完全对齐 |
| Recommendation | `{target, score, windows, ...}` | `Recommendation` | 完全对齐 |

### D. 迁移检查清单

在将现有前端代码迁移到对齐后的 API 时，请检查以下项目:

- [ ] 更新 `baseURL` 为 `/api/v1`
- [ ] 更新响应处理逻辑，解包 `data` 字段
- [ ] 替换所有 `/location/` 为 `/locations/`
- [ ] 替换所有 `/objects` 为 `/targets`
- [ ] 替换所有 `/zones` 为 `/visible-zones`
- [ ] 更新推荐接口为 POST，使用请求体
- [ ] 更新可见性接口为 POST，使用请求体
- [ ] 更新天空图接口为 POST，使用请求体
- [ ] 添加新增的接口方法 (搜索、统计、FOV计算等)
- [ ] 测试所有接口调用
- [ ] 验证错误处理逻辑

---

## 原有附录

### A. 参考资源

- [astronomy-engine](https://github.com/cosinekitty/astronomy) - 天文计算库
- [MSW](https://mswjs.io/) - Mock Service Worker
- [Vite](https://vitejs.dev/) - 构建工具
- [Canvas API](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API) - Canvas 文档
- [IndexedDB](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API) - IndexedDB 文档
- [Service Worker](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API) - Service Worker 文档

### B. 工具推荐

- **代码编辑器**: VS Code
- **浏览器**: Chrome DevTools
- **设计工具**: MasterGo
- **版本控制**: Git + GitHub
- **包管理器**: npm/pnpm
- **代码格式化**: Prettier
- **代码检查**: ESLint

### C. 常见问题

**Q: 如何处理时区？**
A: 使用 `date-fns-tz` 或 `Intl.DateTimeFormat`：
```javascript
const timeZone = 'Asia/Shanghai';
const formatter = new Intl.DateTimeFormat('zh-CN', {
  timeZone,
  hour: '2-digit',
  minute: '2-digit'
});
```

**Q: 如何优化 Canvas 性能？**
A: 使用 `requestAnimationFrame`、离屏渲染、脏矩形技术。

**Q: 如何实现离线功能？**
A: 使用 Service Worker 缓存静态资源，IndexedDB 存储数据。

**Q: 如何测试天文计算精度？**
A: 与已知的星历表数据对比，确保误差 < 0.1°。

---

**文档版本**: 1.1
**最后更新**: 2025-01-22
**维护者**: 开发团队
