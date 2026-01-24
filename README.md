# AI Skywatcher - 天文观测助手

**AI-powered deep sky target recommender for astrophotography**

[![Frontend Status](https://img.shields.io/badge/frontend-✅%20成功-green)
![Backend Status](https://img.shields.io/badge/backend-✅%20成功-blue)
![Integration](https://img.shields.io/badge/integration-✅%20完成-success)
![Version](https://img.shields.io/badge/version-2.4.0-orange)

---

## 项目简介

AI Skywatcher 是一个专为天文摄影师设计的智能深空拍摄目标推荐工具。它根据您的位置、设备参数和可视区域，为您推荐最佳的深空天体拍摄目标。

**✨ 核心特性**:
- 🌍 **智能定位**: 支持真实浏览器 GPS 定位和手动设置观测地点
- 🔭 **设备配置**: 预设常见设备组合，自定义传感器和焦距参数，实时 FOV 计算
- 📐 **FOV 视野框**: 可视化设备视野范围，支持拖动定位，实时反馈拍摄构图
- 🗓️ **日期规划**: 选择任意日期评估未来观测目标，智能推荐时段
- 🎯 **可视区域编辑**: 矩形区域标注遮挡物，灵活管理观测范围
- 🗺️ **交互式天空图**: 3D 天球投影，实时显示深空目标位置
- ⭐ **智能推荐**: 基于多维度评分的拍摄目标推荐
- ⏰ **时段筛选**: 今晚黄金、后半夜、黎明前时段推荐
- 📱 **响应式设计**: 支持桌面、平板、移动设备
- 💾 **本地存储**: 位置、设备、可视区域、FOV 框位置自动保存

---

## 技术栈

### 前端
- **框架**: Vanilla JavaScript + HTML5
- **构建工具**: Vite 5.4
- **样式**: CSS Variables + Custom CSS
- **图表**: Canvas API
- **状态管理**: Pub/Sub 模式

### 后端
- **框架**: FastAPI 0.109
- **Python**: 3.11+
- **数据验证**: Pydantic 2.5
- **服务器**: Uvicorn
- **天文计算**: Skyfield, Astroquery

---

## 快速开始

### 项目结构

```
ai-skywatcher/
├── frontend/              # 前端应用 (Vite + Vanilla JS)
│   ├── src/
│   │   ├── index.html
│   │   ├── styles/
│   │   └── scripts/
│   ├── package.json
│   └── vite.config.js
├── backend/               # 后端 API (FastAPI)
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── models/        # Pydantic 模型
│   │   ├── services/      # 业务逻辑
│   │   └── utils/
│   ├── requirements.txt
│   └── main.py
├── docs/                  # 项目文档
│   ├── plans/            # 设计文档
│   └── progress/         # 开发进展
└── README.md
```

### 安装依赖

**前端**:
```bash
cd frontend
npm install
```

**后端**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 启动服务

**启动后端** (终端 1):
```bash
cd backend
source venv/bin/activate
python -m app.main
```

后端将运行在: **http://localhost:8000**
- API 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

**启动前端** (终端 2):
```bash
cd frontend
npm run dev
```

前端将运行在: **http://localhost:3000**

访问 http://localhost:3000 开始使用应用！

---

## 功能特性

### ✅ 已实现功能

#### 位置管理
- 自动定位 (Mock 北京/上海)
- 手动输入经纬度
- 保存常用地点

#### 设备配置
- 5 个预设配置 (全画幅/APS-C + 不同焦距)
- 自定义传感器尺寸和焦距
- 自动计算 FOV (视场角)

#### 可视区域编辑
- 矩形区域创建（输入坐标）
- 可视区域列表管理
- 区域删除功能
- 默认全天空区域
- 与推荐引擎集成

#### FOV 视野框
- 实时显示设备视野范围
- 拖动定位（方位角/高度角）
- 点击高亮效果
- 显示/隐藏切换
- 位置重置功能
- 自动保存位置

#### 智能推荐
- **评分算法** (100分制):
  - 高度得分: 50分
  - 亮度得分: 30分
  - FOV匹配: 20分
  - 时长得分: 10分
- 时段筛选:
  - 今晚黄金 (日落后2小时至午夜)
  - 后半夜 (午夜至凌晨3点)
  - 黎明前 (凌晨3点至天文晨光)
- 实时位置计算
- 可见性窗口分析

#### 数据管理
- 10+ 个深空天体 Mock 数据
- 支持按类型、星座过滤
- 关键词搜索

### 🔄 待开发功能

- 目标详情弹窗
- 数据持久化 (IndexedDB)
- PWA 离线支持
- 用户系统
- 导出功能 (PDF/图片)
- 多语言支持

---

## API 文档

### 基础信息

**Base URL**: `http://localhost:8000/api/v1`

**响应格式**:
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 核心 API 端点

#### 位置管理
- `POST /locations/geolocate` - 自动定位
- `POST /locations/validate` - 验证位置
- `GET /locations` - 获取保存的地点
- `POST /locations` - 保存地点
- `DELETE /locations/{id}` - 删除地点

#### 设备配置
- `GET /equipment/presets` - 获取预设配置
- `POST /equipment/calculate-fov` - 计算 FOV
- `GET /equipment` - 获取保存的设备配置
- `POST /equipment` - 保存设备配置

#### 深空目标
- `GET /targets` - 获取所有目标 (支持分页、过滤)
- `GET /targets/{id}` - 获取目标详情
- `GET /targets/search?q=` - 搜索目标

#### 可见性计算
- `POST /visibility/position` - 计算实时位置
- `POST /visibility/windows` - 计算可见性窗口
- `POST /visibility/positions-batch` - 批量计算位置

#### 推荐引擎
- `POST /recommendations` - 获取推荐目标
- `POST /recommendations/by-period` - 按时段获取推荐
- `POST /recommendations/summary` - 获取推荐统计

**完整 API 文档**: http://localhost:8000/docs

---

## 设计系统

### 颜色

- 主背景: `#121212` (深空主题)
- 次要背景: `#1A1A2E`
- 主强调色: `#10B981` (绿色, 成功/推荐)
- 次强调色: `#3B82F6` (蓝色, 链接/选中)

### 字体

- 基础: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto`
- 等宽: `'SF Mono', Monaco, 'Cascadia Code', monospace`

### 间距

- 基础单位: 4px
- 系列: 4px, 8px, 12px, 16px, 20px, 24px...


---

## 开发进展

### ✅ 已完成 (2025-01-24)

#### 前端开发 (v2.4.0)
- ✅ 完整的 UI 界面 (HTML + CSS)
- ✅ Canvas 交互式天空图（3D 天球投影）
- ✅ 状态管理系统
- ✅ API 接口封装
- ✅ Mock 数据支持
- ✅ 响应式设计
- ✅ 真实浏览器 GPS 定位
- ✅ 设备预设切换功能
- ✅ 日期选择器
- ✅ **本地存储功能**（位置、设备、日期）
- ✅ **时间轴交互控制**（拖动调整观测时间）
- ✅ **3D 天球优化**（中心视角，球面投影）
- ✅ **可视区域编辑器**（矩形区域创建与管理）
- ✅ **FOV 视野框**（可视化设备视野，拖动定位）

#### 后端开发
- ✅ FastAPI 项目结构
- ✅ 20+ API 端点
- ✅ Pydantic 数据模型
- ✅ 天体位置计算服务
- ✅ 可见性分析服务
- ✅ 智能推荐引擎
- ✅ Mock 数据服务
- ✅ **天空图 API 路由**（新增）

#### 前后端对接
- ✅ Vite 代理配置
- ✅ API 调用集成
- ✅ 数据流验证
- ✅ 错误处理
- ✅ 加载状态

**详细文档**:
- [前后端对接总结](./docs/progress/frontend-backend-integration-summary.md)
- [功能增强开发总结](./docs/progress/feature-enhancement-summary.md)
- [本地存储功能](./docs/progress/local-storage-feature-summary.md)
- [时间轴交互功能](./docs/progress/timeline-interactive-feature-summary.md)
- [3D 天球优化](./docs/progress/3d-celestial-sphere-summary.md)
- **[FOV 视野框功能](./docs/progress/2025-01-24-fov-frame-feature.md)**（最新）

### 🚧 进行中

- [ ] 目标详情弹窗
- [ ] 可视区域编辑器
- [ ] 数据持久化（IndexedDB）
- [ ] 更多天体数据（目标 300+）

### 📋 计划中

- [ ] 用户系统
- [ ] 数据同步
- [ ] PWA 支持
- [ ] 多语言支持

---

## Docker 部署

### 后端部署

```bash
cd backend
docker build -t deep-sky-api .
docker run -p 8000:8000 deep-sky-api
```

### Docker Compose

```bash
docker-compose up -d
```

---

## 测试

### 后端测试
```bash
cd backend
pytest tests/
```

### 前端测试
```bash
cd frontend
npm run lint
npm run format
```

---

## 贡献指南

欢迎贡献代码、报告 Bug 或提出新功能建议！

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: add some amazing feature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 许可证

MIT License

---

## 致谢

- [astronomy-engine](https://github.com/cosinekitty/astronomy) - 天文计算库
- [FastAPI](https://fastapi.tiangolo.com/) - 现代高性能 Web 框架
- [Vite](https://vitejs.dev/) - 快速的前端构建工具
- 设计稿基于 MasterGo

---

## 联系方式

- 项目主页: [GitHub Repository](#)
- 问题反馈: [Issues](#)

---

**版本**: 2.4.0
**最后更新**: 2025-01-24
**状态**: ✅ FOV 视野框功能完成，系统正常运行
**访问地址**:
- 前端: http://localhost:3000
- 后端: http://localhost:8000/docs

**最新功能**:
- ✅ FOV 视野框（可视化设备视野）
- ✅ 可视区域编辑器（矩形区域创建）
- ✅ 3D 天球优化（中心视角投影）
- ✅ 时间轴交互控制（拖动调整时间）
- ✅ 本地存储功能（位置、设备、日期）
- ✅ 真实浏览器 GPS 定位
- ✅ 设备预设智能切换
- ✅ 日期规划功能
- ✅ 实时 FOV 计算

