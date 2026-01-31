import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(root_dir="./.logs", max_size=5*1024*1024, backup_count=5,name :str=None):
    """
    配置按大小轮转的日志系统
    
    参数:
        root_dir: 日志文件根目录（默认 ./logs）
        max_size: 单个日志文件最大大小（字节），默认5MB
        backup_count: 最多保留的备份文件数，默认5个
    """
    # 1. 确保根目录存在
    os.makedirs(root_dir, exist_ok=True)
    
    # 2. 定义日志格式（与需求一致）
    log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    
    # 3. 定义基础日志文件名（根目录+基础名称）
    base_log_name = "app.log"
    log_file_path = os.path.join(root_dir, base_log_name)
    
    # 4. 创建RotatingFileHandler：按大小轮转，文件名带序号
    # 当文件超过max_size时，自动重命名为 app.log.1, app.log.2...（序号即level）
    handler = RotatingFileHandler(
        log_file_path,
        maxBytes=max_size,  # 单个文件最大大小
        backupCount=backup_count,  # 最多保留的备份文件数
        encoding="utf-8"  # 支持中文
    )
    handler.setFormatter(log_format)
    handler.setLevel(logging.INFO)  # 日志级别
    
    # 5. 配置根日志器
    logger = logging.getLogger(name=name)
    logger.setLevel(logging.INFO)  # 全局日志级别
    logger.addHandler(handler)
    
    # 可选：添加控制台输出（同时在控制台打印日志）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    return logger