"""
DEPRECATED: Mock data service replaced by DatabaseService

This service is kept for backward compatibility during transition.
Use app.services.database.DatabaseService instead.

Migration guide:
- Replace: mock_service = MockDataService()
- With: db_service = DatabaseService()
- All method signatures remain compatible
"""
import warnings
import json
from typing import List, Optional
from pathlib import Path
from app.models.target import DeepSkyTarget

# Issue deprecation warning when module is imported
warnings.warn(
    "MockDataService is deprecated. Use DatabaseService instead.",
    DeprecationWarning,
    stacklevel=2
)


class MockDataService:
    """Mock 数据服务"""

    def __init__(self):
        self.targets_cache = None
        self.data_dir = Path("data")

    def load_targets(self) -> List[DeepSkyTarget]:
        """加载深空天体数据"""
        if self.targets_cache is not None:
            return self.targets_cache

        # 尝试从文件加载
        data_file = self.data_dir / "deepsky_objects.json"

        if data_file.exists():
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.targets_cache = [
                    DeepSkyTarget(**target) for target in data["targets"]
                ]
                return self.targets_cache
            except Exception as e:
                print(f"加载文件失败: {e}")

        # 使用内置的 mock 数据
        self.targets_cache = self._generate_mock_targets()
        return self.targets_cache

    def _generate_mock_targets(self) -> List[DeepSkyTarget]:
        """生成 mock 目标数据"""
        mock_targets = [
            DeepSkyTarget(
                id="M42",
                name="猎户座大星云",
                name_en="Orion Nebula",
                type="emission-nebula",
                ra=83.633,
                dec=-5.391,
                magnitude=4.0,
                size=85,
                constellation="Orion",
                difficulty=1,
                description="全天最明亮的弥漫星云，肉眼可见，位于猎户座腰带下方",
                optimal_season=["December", "January", "February"],
                optimal_fov={"min": 100, "max": 400},
                tags=["nebula", "emission", "bright", "beginner-friendly"]
            ),
            DeepSkyTarget(
                id="M31",
                name="仙女座星系",
                name_en="Andromeda Galaxy",
                type="galaxy",
                ra=10.684,
                dec=41.269,
                magnitude=3.4,
                size=178,
                constellation="Andromeda",
                difficulty=1,
                description="本星系群中最大的星系，距离地球约250万光年",
                optimal_season=["October", "November", "December"],
                optimal_fov={"min": 200, "max": 500},
                tags=["galaxy", "spiral", "bright", "large"]
            ),
            DeepSkyTarget(
                id="M45",
                name="昴星团",
                name_en="Pleiades",
                type="cluster",
                ra=56.38,
                dec=24.07,
                magnitude=1.6,
                size=110,
                constellation="Taurus",
                difficulty=1,
                description="最著名的疏散星团，肉眼可见6-7颗星",
                optimal_season=["November", "December", "January"],
                optimal_fov={"min": 100, "max": 300},
                tags=["cluster", "open", "bright"]
            ),
            DeepSkyTarget(
                id="M57",
                name="环状星云",
                name_en="Ring Nebula",
                type="planetary-nebula",
                ra=283.38,
                dec=33.02,
                magnitude=8.8,
                size=1.4,
                constellation="Lyra",
                difficulty=2,
                description="著名的行星状星云，呈现圆环状结构",
                optimal_season=["July", "August", "September"],
                optimal_fov={"min": 50, "max": 200},
                tags=["planetary-nebula", "small"]
            ),
            DeepSkyTarget(
                id="M27",
                name="哑铃星云",
                name_en="Dumbbell Nebula",
                type="planetary-nebula",
                ra=299.87,
                dec=22.72,
                magnitude=7.5,
                size=8.0,
                constellation="Vulpecula",
                difficulty=2,
                description="最大的行星状星云之一，形状像哑铃",
                optimal_season=["August", "September"],
                optimal_fov={"min": 50, "max": 200},
                tags=["planetary-nebula", "large"]
            ),
            DeepSkyTarget(
                id="M51",
                name="涡状星系",
                name_en="Whirlpool Galaxy",
                type="galaxy",
                ra=202.47,
                dec=47.2,
                magnitude=8.4,
                size=11.2,
                constellation="Canes Venatici",
                difficulty=2,
                description="著名的螺旋星系，与伴星系NGC5195相互作用",
                optimal_season=["April", "May"],
                optimal_fov={"min": 50, "max": 200},
                tags=["galaxy", "spiral", "interacting"]
            ),
            DeepSkyTarget(
                id="M8",
                name="礁湖星云",
                name_en="Lagoon Nebula",
                type="emission-nebula",
                ra=270.91,
                dec=-24.38,
                magnitude=6.0,
                size=90,
                constellation="Sagittarius",
                difficulty=1,
                description="人马座最亮的发射星云，肉眼可见",
                optimal_season=["July", "August", "September"],
                optimal_fov={"min": 100, "max": 300},
                tags=["nebula", "emission", "bright"]
            ),
            DeepSkyTarget(
                id="M16",
                name="鹰星云",
                name_en="Eagle Nebula",
                type="emission-nebula",
                ra=274.69,
                dec=-13.8,
                magnitude=6.4,
                size=30,
                constellation="Serpens",
                difficulty=2,
                description="著名的天体创生之柱所在地",
                optimal_season=["June", "July", "August"],
                optimal_fov={"min": 50, "max": 200},
                tags=["nebula", "emission", "pillars"]
            ),
            DeepSkyTarget(
                id="M1",
                name="蟹状星云",
                name_en="Crab Nebula",
                type="supernova-remnant",
                ra=83.63,
                dec=22.02,
                magnitude=8.4,
                size=7,
                constellation="Taurus",
                difficulty=2,
                description="公元1054年超新星爆发的遗迹",
                optimal_season=["December", "January"],
                optimal_fov={"min": 50, "max": 200},
                tags=["supernova-remnant", "pulsar"]
            ),
            DeepSkyTarget(
                id="M13",
                name="武仙座球状星团",
                name_en="Hercules Globular Cluster",
                type="cluster",
                ra=250.42,
                dec=36.46,
                magnitude=5.9,
                size=23,
                constellation="Hercules",
                difficulty=1,
                description="北天最亮的球状星团之一",
                optimal_season=["May", "June", "July"],
                optimal_fov={"min": 50, "max": 200},
                tags=["cluster", "globular", "bright"]
            )
        ]

        return mock_targets

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
        return [t for t in targets if t.constellation.lower() == constellation.lower()]

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
