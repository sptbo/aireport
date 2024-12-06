import os
import logging
import yaml

def load_config(config_path='config.yaml'):
    """
    加载配置文件
    :param config_path: 配置文件路径
    :return: 配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 设置日志配置
    logging.basicConfig(
        level=config['logging']['level'], 
        format=config['logging']['format'],
        handlers=[
            logging.FileHandler("log.log"),  # 将日志输出到文件
            logging.StreamHandler()  # 同时将日志输出到控制台
        ]
    )
    
    # 设置凭证信息
    os.environ["QIANFAN_AK"] = config['credentials']['QIANFAN_AK']
    os.environ["QIANFAN_SK"] = config['credentials']['QIANFAN_SK']
    
    return config

config = load_config()