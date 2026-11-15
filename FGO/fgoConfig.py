"""配置管理系统"""
import json
import os
from FGO.fgoLogging import get_logger

logger = get_logger("Config")

class Config:
    """配置类 — 管理所有用户配置"""

    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.data = {}
        self.load()

    def load(self):
        """从文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info(f"✅ 配置加载成功: {self.config_file}")
            except Exception as e:
                logger.error(f"❌ 配置加载失败: {e}")
                self.data = self.get_default_config()
        else:
            logger.warning(f"⚠️  配置文件不存在，使用默认配置")
            self.data = self.get_default_config()
            self.save()

    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ 配置已保存: {self.config_file}")
        except Exception as e:
            logger.error(f"❌ 配置保存失败: {e}")

    @staticmethod
    def get_default_config():
        """获取默认配置"""
        return {
            "run_count": 0,    # 0 = 无限
            "apple_limit": 0,  # 最多吃几个苹果，0 = 不吃
        }

    def get(self, key, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def __repr__(self):
        return f"<Config: {json.dumps(self.data, ensure_ascii=False, indent=2)}>"

# 全局配置实例
config = Config("config.json")
