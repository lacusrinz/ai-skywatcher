# 深空拍摄目标推荐工具 - 天文数据库资源指南

**创建日期**: 2025-01-22
**目标**: 为深空拍摄目标推荐工具提供开源天文数据库集成方案

---

## 目录

1. [核心数据库推荐](#1-核心数据库推荐)
2. [数据库详细说明](#2-数据库详细说明)
3. [Python 集成方案](#3-python-集成方案)
4. [数据获取策略](#4-数据获取策略)
5. [本地化方案](#5-本地化方案)
6. [性能优化](#6-性能优化)

---

## 1. 核心数据库推荐

### 1.1 深空天体目录 (必需)

| 数据库名称 | 类型 | 覆盖范围 | 许可证 | 推荐用途 |
|-----------|------|---------|--------|---------|
| **SIMBAD** | 在线数据库 | 全天体 | 开源 (学术) | 主要深空天体数据 |
| **OpenNGC** | 静态文件 | NGC/IC | MIT | 本地 NGC/IC 数据 |
| **Messier (SEDS)** | 静态文件 | Messier 110 | 公有领域 | Messier 目录 |
| **skycatalog** | Python包 | M/NGC/IC | 开源 | 快速集成 |
| **VizieR** | 在线目录 | 10000+ 目录 | 多种 | 备用查询源 |

### 1.2 恒星与星团数据 (推荐)

| 数据库名称 | 类型 | 覆盖范围 | 许可证 | 推荐用途 |
|-----------|------|---------|--------|---------|
| **Gaia DR3** | 在线+本地 | 18亿颗恒星 | 开源 | 精确位置/视差 |
| **HIPPARCOS** | 在线+本地 | 11.8万恒星 | 开源 | 历史参考 |
| **UCC** | 在线目录 | 开放星团 | 开源 | 开放星团成员 |

### 1.3 辅助数据库 (可选)

| 数据库名称 | 类型 | 用途 |
|-----------|------|------|
| **DSSD** | 在线 | 深空天体尺寸数据 |
| **Aladin Sky Atlas** | 可视化 | 交互式星空查看 |
| **ESASky** | 多波段 | 图像叠加参考 |

---

## 2. 数据库详细说明

### 2.1 SIMBAD Astronomical Database

**概述**: SIMBAD (Set of Identifications, Measurements, and Bibliography for Astronomical Data) 是由法国斯特拉斯堡天文数据中心(CDS)维护的天文对象数据库。

**特点**:
- ✅ 包含所有 Messier、NGC、IC 深空天体
- ✅ 提供精确坐标 (RA/Dec)
- ✅ 星等、类型、尺寸等基本参数
- ✅ 通过 TAP 协议访问
- ✅ 完全免费，无需注册

**数据覆盖**:
- 深空天体: 星系、星云、星团
- 恒星: 明亮恒星、双星、变星
- 太阳系: 行星、小行星
- 总计超过 400 万个对象

**访问方式**:
```python
from astroquery.simbad import Simbad

# 基础查询
result = Simbad.query_object('M31')

# 自定义字段
custom_simbad = Simbad()
custom_simbad.add_votable_fields(
    'ra(d;ICRS;J2000)',  # 赤经
    'dec(d;ICRS;J2000)', # 赤纬
    'flux(V)',           # V星等
    'flux(B)',           # B星等
    'morphology'         # 形态分类
)
```

**官方网站**: [SIMBAD](http://simbad.u-strasbg.fr/simbad/)
**API 文档**: [astroquery.simbad](https://astroquery.readthedocs.io/en/latest/simbad/simbad.html)

---

### 2.2 OpenNGC

**概述**: OpenNGC 是一个许可证友好的 NGC/IC 对象数据库，包含位置和主要数据。

**特点**:
- ✅ MIT 许可证，可商用
- ✅ 包含 NGC (新总表) 全部天体
- ✅ 包含 IC (索引目录) 主要天体
- ✅ CSV/JSON 格式，易于集成
- ✅ GitHub 活跃维护

**数据内容**:
```json
{
  "name": "NGC 224",
  "type": "G",
  "ra": "00 42 44.4",
  "dec": "+41 16 12",
  "constellation": "And",
  "major_axis": 189.5,
  "minor_axis": 60.5,
  "magnitude": 3.44,
  "surface_brightness": 13.54
}
```

**GitHub**: [mattiaverga/OpenNGC](https://github.com/mattiaverga/OpenNGC)

**推荐用途**: 本地化主要数据源，减少在线查询

---

### 2.3 Gaia DR3 (数据发布 3)

**概述**: 欧洲空间局 Gaia 任务的第三次数据发布，包含约 18 亿颗恒星的精确位置、视差和自行数据。

**特点**:
- ✅ 微角秒级精度 (μas)
- ✅ 包含约 100 万个星系的数据
- ✅ 可通过 ADQL 查询
- ✅ 支持锥形搜索 (cone search)
- ✅ 开源，完全免费

**对深空拍摄的价值**:
- **参考星**: 获取拍摄区域的参考恒星坐标
- **星团成员**: 确定开放星团的成员恒星
- **消光校正**: 提供 A_G (消光) 数据
- **光度数据**: BP/RP 光谱信息

**访问方式**:
```python
from astroquery.gaia import Gaia
from astropy import units as u
from astropy.coordinates import SkyCoord

# 方式1: ADQL 查询
query = """
SELECT TOP 1000
  source_id, ra, dec, pmra, pmdec,
  phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag
FROM gaiadr3.gaia_source
WHERE 1=CONTAINS(
  POINT('ICRS', ra, dec),
  CIRCLE('ICRS', 10.684, 41.269, 0.5)  # M31 位置，半径0.5度
)
AND phot_g_mean_mag < 15
"""
job = Gaia.launch_job(query)
results = job.get_results()

# 方式2: 锥形搜索
coord = SkyCoord(ra=10.684*u.degree, dec=41.269*u.degree, frame='icrs')
radius = 0.5 * u.degree
j = Gaia.cone_search_async(coord, radius)
r = j.get_results()
```

**官方网站**: [Gaia Archive](https://www.cosmos.esa.int/web/gaia/dr3)
**教程**: [如何提取 Gaia 数据](https://www.cosmos.esa.int/web/gaia-users/archive/extract-data)

---

### 2.4 VizieR 目录服务

**概述**: VizieR 提供 10000+ 个天文目录的访问，是 CDS 的核心服务之一。

**特点**:
- ✅ 集成多个目录 (Messier, NGC, IC, PGC 等)
- ✅ 支持区域查询
- ✅ 可导出多种格式
- ✅ UCD 标准化

**常用目录**:
- **VII/118**: Messier 目录
- **VII/119**: NGC 2000.0
- **BDS/2009**: 完整 NGC/IC
- **II/246**: HIPPARCOS 主星表

**访问方式**:
```python
from astroquery.vizier import Vizier

# 查询 Messier 目录
Vizier.ROW_LIMIT = 110  # Messier 有110个天体
catalogs = Vizier.find_catalogs('Messier')
result = Vizier.query_region(
    catalog='VII/118',
    coordinates=SkyCoord(ra=83.633, dec=-5.391, unit='deg'),
    radius=1*u.degree
)
```

**官方网站**: [VizieR](https://vizier.cds.unistra.fr/)
**文档**: [astroquery.vizier](https://astroquery.readthedocs.io/en/stable/vizier/vizier.html)

---

### 2.5 skycatalog Python 包

**概述**: 一个轻量级的 Python 天文数据库包，包含 Messier、NGC、IC 等目录。

**特点**:
- ✅ 纯 Python 实现
- ✅ 无需网络连接
- ✅ 简单的 API
- ✅ 可直接集成到项目

**安装**:
```bash
pip install skycatalog
```

**使用示例**:
```python
from skycatalog import messier, ngc, ic

# 获取 Messier 天体
m31 = messier.M31
print(m31.name)  # "Andromeda Galaxy"
print(m31.ra)    # 赤经
print(m31.dec)   # 赤纬

# 获取 NGC 天体
ngc224 = ngc.NGC224

# 搜索
results = messier.search("andromeda")
```

**GitHub**: [MarScaper/skycatalog](https://github.com/MarScaper/skycatalog)

---

### 2.6 其他有用数据库

#### A. UCC (Unified Cluster Catalog)

**概述**: 统一的开放星团目录，基于 Gaia DR3 数据。

**用途**:
- 获取开放星团的成员恒星列表
- 星团的精确位置和参数
- 年龄、金属丰度等信息

**论文**: [A machine-learning-based tool for open cluster membership](https://www.aanda.org/articles/aa/full_html/2023/07/aa45952-23/aa45952-23.html)
**代码**: [gabriel-p-artcls/23-08_UCC](https://github.com/gabriel-p-artcls/23-08_UCC)

#### B. DSSD (Deep Sky Survey Database)

**概述**: 深空天体的详细尺寸和形状数据。

**用途**:
- 获取天体的精确角大小
- 适合不同焦距的拍摄建议
- 表面亮度数据

---

## 3. Python 集成方案

### 3.1 依赖安装

**requirements.txt**:
```
# 天文数据查询
astroquery>=0.4.7
astropy>=6.0.0

# 坐标和时间
skyfield>=1.49
python-dateutil>=2.8.2

# 数据处理
pandas>=2.1.0
numpy>=1.26.0

# 可视化 (可选)
matplotlib>=3.8.0
```

### 3.2 数据访问服务封装

**文件**: `app/services/astronomy_databases.py`

```python
from typing import List, Optional, Dict, Any
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.simbad import Simbad
from astroquery.gaia import Gaia
from astroquery.vizier import Vizier
import pandas as pd
from pathlib import Path

class AstronomyDatabaseService:
    """天文数据库访问服务"""

    def __init__(self):
        self._simbad = None
        self._local_cache = {}

    def get_simbad(self):
        """获取配置好的 SIMBAD 连接"""
        if self._simbad is None:
            self._simbad = Simbad()
            self._simbad.add_votable_fields(
                'ra(d;ICRS;J2000)',
                'dec(d;ICRS;J2000)',
                'flux(V)',
                'flux(B)',
                'morphology',
                'dimensions'
            )
            self._simbad.ROW_LIMIT = -1  # 无限制
        return self._simbad

    def query_deep_sky_object(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        查询深空天体信息

        Args:
            identifier: 天体标识符 (如 "M31", "NGC224")

        Returns:
            天体信息字典
        """
        try:
            simbad = self.get_simbad()
            result = simbad.query_object(identifier)

            if result is None or len(result) == 0:
                return None

            row = result[0]

            return {
                'id': identifier,
                'ra': float(row['RA_d_ICRS_J2000']),
                'dec': float(row['DEC_d_ICRS_J2000']),
                'magnitude': float(row['FLUX_V']) if 'FLUX_V' in row.colnames else None,
                'b_mag': float(row['FLUX_B']) if 'FLUX_B' in row.colnames else None,
                'type': str(row['MORPHOLOGY']) if 'MORPHOLOGY' in row.colnames else None,
            }
        except Exception as e:
            print(f"Error querying {identifier}: {e}")
            return None

    def query_region(
        self,
        ra: float,
        dec: float,
        radius_deg: float = 1.0,
        max_mag: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        查询指定区域内的天体

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

            simbad = self.get_simbad()
            result = simbad.query_region(coord, radius=radius)

            if result is None:
                return []

            objects = []
            for row in result:
                mag = float(row['FLUX_V']) if 'FLUX_V' in row.colnames else None

                # 应用星等过滤
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
            print(f"Error querying region: {e}")
            return []

    def query_reference_stars(
        self,
        ra: float,
        dec: float,
        radius_deg: float = 1.0,
        max_magnitude: float = 15.0
    ) -> pd.DataFrame:
        """
        从 Gaia DR3 查询参考恒星

        Args:
            ra: 中心赤经
            dec: 中心赤纬
            radius_deg: 搜索半径
            max_magnitude: 最大G星等

        Returns:
            恒星数据 DataFrame
        """
        query = f"""
        SELECT
          source_id, ra, dec, pmra, pmdec,
          phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag,
          parallax
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
            print(f"Error querying Gaia: {e}")
            return pd.DataFrame()

    def load_local_catalog(self, catalog_path: str) -> pd.DataFrame:
        """
        加载本地深空天体目录

        Args:
            catalog_path: 目录文件路径 (CSV/JSON)

        Returns:
            天体数据 DataFrame
        """
        path = Path(catalog_path)

        if not path.exists():
            raise FileNotFoundError(f"Catalog not found: {catalog_path}")

        if path.suffix == '.csv':
            return pd.read_csv(path)
        elif path.suffix == '.json':
            return pd.read_json(path)
        else:
            raise ValueError(f"Unsupported format: {path.suffix}")

    def search_messier(self) -> pd.DataFrame:
        """搜索所有 Messier 天体"""
        try:
            vizier = Vizier()
            vizier.ROW_LIMIT = 110

            catalogs = Vizier.find_catalogs('Messier')
            messier_catalog_key = list(catalogs.keys())[0]

            result = Vizier.query_catalog(messier_catalog_key)
            return result[0].to_pandas()
        except Exception as e:
            print(f"Error searching Messier: {e}")
            return pd.DataFrame()

    def get_ngc_ic_objects(
        self,
        min_magnitude: Optional[float] = None,
        object_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取 NGC/IC 天体列表

        Args:
            min_magnitude: 最小星等 (亮于此值)
            object_type: 天体类型 ('G'=星系, 'PN'=行星状星云, etc.)
        """
        # 从本地 OpenNGC 文件加载
        try:
            # 假设已下载 OpenNGC 数据
            df = self.load_local_catalog('data/opengc.csv')

            # 应用过滤条件
            if min_magnitude is not None:
                df = df[df['magnitude'] <= min_magnitude]

            if object_type is not None:
                df = df[df['type'] == object_type]

            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading NGC/IC: {e}")
            return []
```

### 3.3 本地数据管理器

**文件**: `app/services/local_catalog_manager.py`

```python
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

class LocalCatalogManager:
    """本地天文目录管理器"""

    def __init__(self, data_dir: str = "data/catalogs"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_messier_catalog(self) -> str:
        """下载 Messier 目录"""
        # 从 SEDS 或其他可靠源获取
        url = "https://raw.githubusercontent.com/mattiaverga/OpenNGC/master/openngc.csv"
        output_path = self.data_dir / "messier.csv"

        response = requests.get(url)
        response.raise_for_status()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)

        return str(output_path)

    def load_messier_objects(self) -> List[Dict[str, Any]]:
        """加载 Messier 天体"""
        messier_file = self.data_dir / "messier.csv"

        if not messier_file.exists():
            self.download_messier_catalog()

        objects = []
        with open(messier_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['name'].startswith('M '):  # Messier 对象
                    objects.append({
                        'id': row['name'].replace(' ', ''),
                        'name': row['name'],
                        'type': self._map_object_type(row['type']),
                        'ra': self._hms_to_degrees(row['ra']),
                        'dec': self._dms_to_degrees(row['dec']),
                        'magnitude': float(row['mag']) if row['mag'] else None,
                        'size': float(row['size']) if row['size'] else None,
                        'constellation': row['const'],
                    })

        return objects

    def _map_object_type(self, code: str) -> str:
        """映射天体类型代码"""
        type_map = {
            'G': 'galaxy',
            'PN': 'planetary-nebula',
            'HII': 'emission-nebula',
            'OCL': 'cluster',
            'GCL': 'globular-cluster',
            'NB': 'nebula',
            'DRK': 'dark-nebula',
        }
        return type_map.get(code, 'unknown')

    def _hms_to_degrees(self, hms: str) -> float:
        """转换时分秒为度"""
        # 简化实现
        # 实际应使用 astropy.coordinates
        parts = hms.split()
        h, m, s = map(float, parts[:3])
        return (h + m/60 + s/3600) * 15

    def _dms_to_degrees(self, dms: str) -> float:
        """转换度分秒为度"""
        parts = dms.split()
        sign = -1 if parts[0] == '-' else 1
        d, m, s = map(float, parts[1 if sign == 1 else 0:4])
        return sign * (d + m/60 + s/3600)

    def export_to_json(self, objects: List[Dict], filename: str):
        """导出为 JSON 格式"""
        output_path = self.data_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(objects, f, ensure_ascii=False, indent=2)

        print(f"Exported {len(objects)} objects to {output_path}")
```

---

## 4. 数据获取策略

### 4.1 推荐的数据流程

```
┌─────────────────────┐
│  应用启动时         │
└──────────┬──────────┘
           │
           ├─► 加载本地 Messier/NGC/IC (OpenNGC)
           │   └─→ 快速响应，无需网络
           │
           ├─► 缓存常用对象数据
           │   └─→ Redis / 内存缓存
           │
           └─► 在线查询 (按需)
               ├─► SIMBAD: 遗漏数据
               ├─► Gaia: 参考恒星
               └─► VizieR: 特殊目录
```

### 4.2 分阶段实施

**阶段 1: Mock 数据 (当前)**
- 使用静态 JSON 文件
- 约 300 个精选深空天体
- 快速原型开发

**阶段 2: 本地目录**
- 集成 OpenNGC (完整 NGC/IC)
- 添加 Messier 完整数据
- 静态文件查询

**阶段 3: 在线数据库**
- 集成 SIMBAD 查询
- 添加 Gaia 参考星
- 实时数据更新

**阶段 4: 高级功能**
- 定期数据同步
- 用户贡献数据
- 社区评分系统

---

## 5. 本地化方案

### 5.1 数据文件结构

```
data/catalogs/
├── messier.json              # Messier 110个天体
├── ngc.json                  # NGC 主要天体
├── ic.json                   # IC 主要天体
├── openngc.csv               # OpenNGC 完整数据
├── bright_stars.json         # 亮星目录 (HIPPARCOS)
└── constellations.json       # 星座边界
```

### 5.2 数据格式示例

**messier.json**:
```json
{
  "catalog": "Messier",
  "version": "1.0",
  "last_updated": "2025-01-22",
  "objects": [
    {
      "id": "M31",
      "name": "仙女座星系",
      "name_en": "Andromeda Galaxy",
      "type": "galaxy",
      "subtype": "spiral",
      "ra": 10.684708,
      "dec": 41.268750,
      "magnitude": 3.44,
      "size": 178,
      "surface_brightness": 13.5,
      "distance": 2500000,
      "constellation": "Andromeda",
      "difficulty": 1,
      "optimal_season": ["October", "November", "December"],
      "optimal_fov": {"min": 200, "max": 500},
      "tags": ["galaxy", "bright", "large", "naked-eye"],
      "description": "本星系群中最大的星系...",
      "best_aperture": "50mm+",
      "coordinates": {
        "ra_hms": "00 42 44.4",
        "dec_dms": "+41 16 12"
      }
    }
  ]
}
```

### 5.3 数据生成脚本

**文件**: `scripts/generate_catalogs.py`

```python
#!/usr/bin/env python
"""
生成深空天体目录数据
"""
import json
from pathlib import Path
from app.services.astronomy_databases import AstronomyDatabaseService
from app.services.local_catalog_manager import LocalCatalogManager

def main():
    db_service = AstronomyDatabaseService()
    catalog_mgr = LocalCatalogManager()

    # 1. 获取 Messier 天体
    print("Fetching Messier objects...")
    messier_objects = catalog_mgr.load_messier_objects()

    # 2. 添加 SIMBAD 数据
    for obj in messier_objects:
        simbad_data = db_service.query_deep_sky_object(obj['id'])
        if simbad_data:
            obj.update(simbad_data)

    # 3. 导出 JSON
    catalog_mgr.export_to_json(messier_objects, 'messier.json')

    # 4. 获取 NGC 天体 (可选)
    print("Fetching NGC objects...")
    ngc_objects = db_service.get_ngc_ic_objects(min_magnitude=12)
    catalog_mgr.export_to_json(ngc_objects, 'ngc_bright.json')

    print("Done!")

if __name__ == '__main__':
    main()
```

---

## 6. 性能优化

### 6.1 缓存策略

```python
from functools import lru_cache
import pickle
from pathlib import Path

class CachedAstronomyService:
    """带缓存的天文数据服务"""

    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @lru_cache(maxsize=1000)
    def get_object_data(self, object_id: str) -> dict:
        """获取对象数据 (带 LRU 缓存)"""
        cache_file = self.cache_dir / f"{object_id}.pkl"

        # 尝试从磁盘缓存加载
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)

        # 查询在线数据库
        data = self._query_online(object_id)

        # 保存到磁盘
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)

        return data

    def warm_up_cache(self, popular_objects: list):
        """预热缓存"""
        for obj_id in popular_objects:
            self.get_object_data(obj_id)
```

### 6.2 批量查询优化

```python
def batch_query_objects(object_ids: List[str]) -> Dict[str, dict]:
    """批量查询对象，减少网络往返"""

    # 方式1: 使用 SIMBAD 批量查询
    simbad = Simbad()
    # SIMBAD 支持多个对象用逗号分隔
    identifiers = ','.join(object_ids)
    result = simbad.query_objects(identifiers.split(','))

    # 方式2: 并发查询
    from concurrent.futures import ThreadPoolExecutor

    def query_single(obj_id):
        return obj_id, query_deep_sky_object(obj_id)

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(query_single, object_ids)

    return dict(results)
```

### 6.3 数据库索引

如果使用 SQLite/PostgreSQL 存储目录数据:

```sql
-- 创建索引
CREATE INDEX idx_ra_dec ON deep_sky_objects(ra, dec);
CREATE INDEX idx_magnitude ON deep_sky_objects(magnitude);
CREATE INDEX idx_type ON deep_sky_objects(type);
CREATE INDEX idx_constellation ON deep_sky_objects(constellation);

-- 空间索引 (PostGIS 或 SQLite spatial)
SELECT * FROM deep_sky_objects
WHERE ST_DWithin(
  ST_MakePoint(ra, dec)::geography,
  ST_MakePoint(:target_ra, :target_dec)::geography,
  :radius_deg * 111000  # 转换为米
);
```

---

## 7. 总结与建议

### 7.1 最小可行方案 (MVP)

**必需数据源**:
1. ✅ **OpenNGC** - 本地 NGC/IC/M 数据 (下载一次)
2. ✅ **SIMBAD** - 在线补充查询 (按需)

**实施步骤**:
```bash
# 1. 下载 OpenNGC
wget https://github.com/mattiaverga/OpenNGC/raw/master/openngc.csv

# 2. 转换为应用格式
python scripts/generate_catalogs.py

# 3. 集成到应用
# 在 app/services/mock_data.py 中使用本地数据
```

### 7.2 推荐的完整方案

**数据源**:
- **本地**: OpenNGC + Messier (SEDS)
- **在线**: SIMBAD + Gaia (参考星)
- **备份**: VizieR

**架构**:
```
应用启动
  ↓
加载本地 JSON (OpenNGC + Messier)
  ↓
运行时查询 (SIMBAD + Gaia)
  ↓
结果缓存 (Redis)
```

### 7.3 许可证注意事项

| 数据源 | 许可证 | 商用限制 |
|--------|--------|----------|
| OpenNGC | MIT | ✅ 可商用 |
| SIMBAD | 免费学术使用 | ⚠️ 需引用 |
| Gaia | 开源 | ✅ 可商用 |
| VizieR | 多种 | ⚠️ 按目录而定 |

**建议**:
- ✅ 使用 OpenNGC 作为主要数据源 (MIT 许可)
- ✅ SIMBAD 仅用于补充查询
- ✅ 在应用中添加数据源引用

---

## 8. 参考资源

### 8.1 官方文档

- [SIMBAD](http://simbad.u-strasbg.fr/simbad/)
- [Gaia Archive](https://www.cosmos.esa.int/web/gaia/dr3)
- [VizieR](https://vizier.cds.unistra.fr/)
- [astroquery 文档](https://astroquery.readthedocs.io/)

### 8.2 Python 教程

- [Astronomical Data in Python](https://allendowney.github.io/AstronomicalData/01_query.html)
- [Gaia TAP+ Tutorial](https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access)
- [astroquery.simbad 文档](https://astroquery.readthedocs.io/en/latest/simbad/simbad.html)

### 8.3 开源项目

- [OpenNGC](https://github.com/mattiaverga/OpenNGC)
- [skycatalog](https://github.com/MarScaper/skycatalog)
- [GaiaQuery](https://github.com/Gabriel-p/GaiaQuery)

---

**文档版本**: 1.0
**最后更新**: 2025-01-22
**维护者**: 开发团队

**来源**:
- [OpenNGC GitHub](https://github.com/mattiaverga/OpenNGC)
- [SIMBAD astroquery 文档](https://astroquery.readthedocs.io/en/latest/simbad/simbad.html)
- [Gaia TAP+ 文档](https://astroquery.readthedocs.io/en/latest/gaia/gaia.html)
- [VizieR 文档](https://astroquery.readthedocs.io/en/stable/vizier/vizier.html)
- [ESA Gaia Archive - 程序化访问](https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access)
- [如何提取 Gaia 数据](https://www.cosmos.esa.int/web/gaia-users/archive/extract-data)
