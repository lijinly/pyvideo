
from datetime import timedelta
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件

# config.py
class Config:
    project_root = Path(__file__).parent.parent  # 根据实际文件位置调整层级
    sql_lite_dir = project_root / ".asset_space" / ".dbs"
    sql_lite_dir.mkdir(parents=True, exist_ok=True)    
    sql_lite_path = sql_lite_dir / "sqlite3.db"
    
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)  # Access Token 过期时间
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)     # Refresh Token 过期时间
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' +str(sql_lite_path)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False