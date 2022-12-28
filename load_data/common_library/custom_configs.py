from jinja2 import Environment, FileSystemLoader
import os
import yaml
import logging
import sys
import pathlib

from dotenv import load_dotenv

from common_library.validation import FinbyValidator
from datetime import datetime


root = pathlib.Path(sys.executable).parent.parent.parent
load_dotenv(root / '.env')

    
def env_var(name: str) -> str:
    return os.getenv(name)  

def today() -> str:
    return datetime.today().strftime('%Y-%m-%d')

def info_logger() -> str:
    return str(root / f'logs/info/info_log_{today()}.log')

def error_logger() -> str:
    return str(root / f'logs/error/error_log_{today()}.log')

def tmp_logger() -> str:
    return str(root / f'logs/error/error_log_{today()}.log')


class CustomTemplate():

    def __init__(self, path: str):
        
        if os.path.exists(path):
            self.path = path
        else:
            logging.error(f'Указан неверный путь к файлу: {path}')
            raise FileNotFoundError
        
        self.__func_dict = {
            "env_var": env_var,
            "today": today,
            "info_logger": info_logger,
            'error_logger': error_logger,
            'tmp_logger': tmp_logger
        }         
        
    
    def render(self, **kwargs) -> str:
        folder_path, file_path = os.path.dirname(self.path), os.path.basename(self.path)
        
        env = Environment(loader=FileSystemLoader(folder_path))
        
        template = env.get_template(file_path)
        
        template.globals.update(self.__func_dict)
        
        template_string = template.render(**kwargs)
        
        return template_string


class Config():
    
    def __init__(self, path: str, schema_path: str=None):
        
        if os.path.exists(path):
            self.path = path
        else:
            logging.error('Указан неверный путь к config файлу')
            raise FileNotFoundError()
        
        if not schema_path is None:
            if os.path.exists(path):
                self.schema_path = schema_path
            else:
                logging.error('Указан неверный путь к схеме config файла')
                raise FileNotFoundError()
        else:
            self.schema_path = None


    def load(self) -> dict:
        
        config = self.__load_rendered_yaml(self.path)
            
        if not self.schema_path is None:
            schema = self.__load_rendered_yaml(self.schema_path)
            
            validator = FinbyValidator()
            is_valid = validator.validate(config, schema)
            config = validator.validated(config, schema)
            
            self.errors = validator.errors
            
            if not is_valid: 
                logging.error(f'Были обнаружены ошибки при проверке схемы config файла: {self.path}\n{validator.errors}')
                raise ValueError()
            
        return config
    
    
    @staticmethod
    def __load_rendered_yaml(path: str):
        
        yaml.add_constructor(u'!ref', __class__.__ref_constructor)
        
        with open(path) as f:
            result = yaml.load( CustomTemplate(path).render(), Loader=yaml.Loader )
        
        return result
    
    
    @staticmethod
    def __get_nested_key(dct, keys):
        
        for key in keys:
            dct = dct.get(key)
        
        return dct


    @staticmethod
    def __ref_constructor(loader, node):
        
        value = loader.construct_scalar(node)
        
        try:
            config_path, nodes = value.split(':')
        except Exception as exc:
            logging.error('Input value must contain both file path and list of nested YAML nodes', exc_info=True)
            raise
        
        node_path = nodes.split('..')
        
        nested_yaml = __class__.__load_rendered_yaml(config_path)
        
        value = __class__.__get_nested_key(nested_yaml, node_path)
        
        return value