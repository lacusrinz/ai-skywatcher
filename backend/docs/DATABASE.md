# Database Documentation

## 概述

AI Skywatcher使用本地SQLite数据库存储深空天体数据，提供快速查询能力，并在需要时自动回退到SIMBAD API。

## 数据库统计

- **总天体数**: ~13,000
- **数据来源**: OpenNGC (开放NGC/IC/Messier目录)
- **数据库文件**: `backend/app/data/deep_sky.db`
- **文件大小**: ~5-10 MB
- **许可证**: CC-BY-SA-4.0

### 数据分布

| 类型 | 数量 | 说明 |
|------|------|------|
| GALAXY | ~5,000 | 星系 |
| NEBULA | ~4,000 | 各类星云 |
| CLUSTER | ~3,000 | 星团（疏散+球状） |
| PLANETARY | ~1,000 | 行星状星云 |

### 目录覆盖

- Messier目录: 110个天体
- Caldwell目录: 109个天体
- NGC目录: ~7,800个天体
- IC目录: ~5,000个天体
- 覆盖星座: 全部88个星座

## 数据库结构

### 表: objects (天体主表)

存储深空天体的基本信息。

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| id | TEXT | 主键 (NGC/IC编号) | "NGC0224" |
| name | TEXT | 天体名称 | "Andromeda Galaxy" |
| type | TEXT | 类型 (GALAXY/NEBULA/CLUSTER/PLANETARY) | "GALAXY" |
| ra | REAL | 赤经 (度) | 10.6847 |
| dec | REAL | 赤纬 (度) | 41.2687 |
| magnitude | REAL | 视星等 | 3.4 |
| size_major | REAL | 长轴 (角分) | 190.0 |
| size_minor | REAL | 短轴 (角分) | 60.0 |
| constellation | TEXT | 所属星座 | "And" |
| surface_brightness | REAL | 表面亮度 (mag/arcsec²) | 22.5 |

### 表: aliases (别名表)

存储天体的各种编号和别名。

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| object_id | TEXT | 外键 (关联objects.id) | "NGC0224" |
| alias | TEXT | 别名 | "M31", "NGC224", "Andromeda" |

**主键**: (object_id, alias)

**说明**:
- 每个天体可以有多个别名
- 包含Messier编号 (M31)
- 包含NGC/IC交叉引用
- 包含常见名称

### 表: observational_info (观测信息表)

存储观测建议和难度评估。

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| object_id | TEXT | 主键 (关联objects.id) | "NGC0224" |
| best_month | INTEGER | 最佳观测月份 (1-12) | 11 |
| difficulty | TEXT | 难度等级 (EASY/MODERATE/DIFFICULT) | "EASY" |
| min_aperture | REAL | 最小口径 (毫米) | 50.0 |
| min_magnitude | REAL | 最小星等 | 3.0 |
| notes | TEXT | 观测备注 | "Visible to naked eye" |

**主键**: object_id

## 数据导入

### 重新生成数据库

如需重新导入数据，运行导入脚本：

```bash
cd /path/to/ai-skywatcher
python scripts/import_openngc.py
```

该脚本会：
1. 从GitHub下载OpenNGC CSV文件
2. 解析并导入到SQLite数据库
3. 生成观测信息（难度、最佳月份等）

### 数据更新

- **OpenNGC更新**: 重新运行导入脚本
- **SIMBAD查询**: 自动缓存到本地数据库
- **手动同步**: `POST /api/v1/targets/sync`

## 查询示例

### Python代码

```python
from app.services.database import DatabaseService

service = DatabaseService()

# 按ID查询
obj = await service.get_object_by_id("NGC0224")
print(f"{obj.name} - {obj.type}")

# 搜索
results = await service.search_objects("Andromeda", limit=10)
for obj in results:
    print(f"{obj.id}: {obj.name}")

# 按类型查询
galaxies = await service.get_objects_by_type("GALAXY")
print(f"Found {len(galaxies)} galaxies")

# 按星座查询
targets = await service.get_objects_by_constellation("Ori")
print(f"Found {len(targets)} objects in Orion")

# 统计信息
stats = await service.get_statistics()
print(f"Total: {stats.total_objects}")
print(f"By type: {stats.objects_by_type}")
```

### API查询

```bash
# 获取天体详情
curl "http://localhost:8000/api/v1/targets/NGC0224"

# 搜索天体
curl "http://localhost:8000/api/v1/targets/search?q=Orion&limit=10"

# 按类型过滤
curl "http://localhost:8000/api/v1/targets?type=GALAXY&page=1&page_size=20"

# 获取统计信息
curl "http://localhost:8000/api/v1/targets/stats"
```

## SIMBAD API回退

### 工作原理

1. **查询本地数据库**: 首先尝试从SQLite获取数据 (~1-5ms)
2. **未找到**: 如果本地没有，查询SIMBAD API (~200-500ms)
3. **缓存结果**: SIMBAD返回的数据自动保存到本地数据库
4. **后续查询**: 下次查询直接从本地获取

### 回退场景

- **适用**: 新发现的NGC/IC天体、用户自定义天体
- **不适用**: Messier天体（已在本地数据库中）
- **限制**: SIMBAD API有速率限制，不建议大量调用

### 手动同步

```bash
# 同步特定天体
curl -X POST "http://localhost:8000/api/v1/targets/sync" \
  -H "Content-Type: application/json" \
  -d '["IC999", "IC1234"]'
```

## 性能优化

### 查询速度

| 操作 | 速度 | 说明 |
|------|------|------|
| 本地数据库查询 | 1-5 ms | SQLite查询 |
| SIMBAD API查询 | 200-500 ms | 网络延迟 + API处理 |
| 缓存命中 | 1-5 ms | 第二次及后续查询 |

### 索引优化

数据库已创建以下索引以加速查询：

```sql
CREATE INDEX idx_objects_ra_dec ON objects(ra, dec);
CREATE INDEX idx_objects_constellation ON objects(constellation);
CREATE INDEX idx_objects_type ON objects(type);
CREATE INDEX idx_aliases_alias ON aliases(alias);
```

### 批量查询建议

- 使用 `search_objects()` 代替多次调用 `get_object_by_id()`
- 使用 `get_objects_by_type()` 代替过滤所有天体
- 限制返回数量（`limit`参数）

## 数据类型映射

### OpenNGC → 本数据库

| OpenNGC类型 | 本数据库类型 |
|-------------|------------|
| G, GPair, Gtrpl, GGroup | GALAXY |
| PN | PLANETARY |
| OCl, GCl, *Ass, Cl+N | CLUSTER |
| HII, EmN, RfN, Neb, DrkN, SNR | NEBULA |

### 观测难度计算

```
表面亮度 = 星等 + 2.5 × log10(长轴²)
- 表面亮度 < 12: EASY (简单)
- 表面亮度 12-14: MODERATE (中等)
- 表面亮度 > 14: DIFFICULT (困难)
```

### 最小口径估算

| 星等 | 最小口径 |
|------|---------|
| > 10 | 200mm (8英寸) |
| 8-10 | 150mm (6英寸) |
| 6-8 | 100mm (4英寸) |
| < 6 | 50mm (2英寸) |

## 故障排除

### 数据库锁定

如果遇到数据库锁定错误：

```bash
# 检查是否有其他进程占用
lsof backend/app/data/deep_sky.db

# 重启后端服务
# 数据库会自动关闭连接
```

### 数据损坏

如果数据库文件损坏：

```bash
# 重新生成数据库
python scripts/import_openngc.py
```

### SIMBAD API失败

如果SIMBAD查询失败：

```bash
# 检查网络连接
ping simbad.u-strasbg.fr

# 查看错误日志
tail -f backend/app.log

# 使用本地数据（无需SIMBAD）
# 天体仍可从本地数据库查询
```

## 参考资源

- [OpenNGC GitHub](https://github.com/mattiaverga/OpenNGC)
- [SIMBAD](http://simbad.u-strasbg.fr/simbad/)
- [PyOngc](https://github.com/mattiaverga/PyOngc)
- [TAP服务](http://dc.g-vo.org/tap)

## 更新日志

### v2.0.0 (2025-01-24)

- ✅ 集成OpenNGC数据库
- ✅ 实现SIMBAD API回退
- ✅ 添加观测信息
- ✅ 支持别名搜索
- ✅ 性能优化（索引、缓存）
