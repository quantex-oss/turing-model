import os


class Config(object):  # 默认配置
    DEBUG = False

    # get attribute
    def __getitem__(self, key):
        return self.__getattribute__(key)


class ProductionConfig(Config):  # 生产环境
    K8S_MASTER = "10.0.0.167"
    K8S_USERNAME = "root"
    K8S_PASSWD = "abcd@1234"


class DevelopmentConfig(Config):  # 开发环境
    K8S_MASTER = "192.168.0.162"
    K8S_USERNAME = "root"
    K8S_PASSWD = "root"


# 环境映射关系
mapping = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 一键切换环境
APP_ENV = os.environ.get('APP_ENV', 'default').lower()  # 设置环境变量为default
config = mapping[APP_ENV]()  # 获取指定的环境
