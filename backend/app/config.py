"""Application configuration"""
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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
