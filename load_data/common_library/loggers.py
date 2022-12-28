import logging
import logging.config

from common_library.custom_configs import Config
      

def set_logger(config_path: str):
    
    config = Config(config_path).load()

    logging.config.dictConfig(config)
    
    return config