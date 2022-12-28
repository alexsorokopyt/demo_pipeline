import inspect
import importlib

from sqlalchemy import create_engine
from sqlalchemy import insert
from sqlalchemy import MetaData
from sqlalchemy import Column
from sqlalchemy import Table
from sqlalchemy.engine import Connection
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import InterfaceError
from sqlalchemy.exc import ArgumentError

from typing import List
from typing import Dict
from typing import Any

import logging


class Database():
    
    def __init__(self, url: str):
        
        self._url = url
        try:
            self._db_engine = create_engine(self._url) 
            self._connection = self._db_engine.connect()
        except (OperationalError, ArgumentError) as ex:
            logging.error('Не удалось подключиться к базе данных с указанным URL', exc_info=True)
            raise
        except InterfaceError as ex:
            logging.error('Не удалось подключиться к базе данных с указанным драйвером', exc_info=True)
            raise
        except Exception as ex:
            logging.error('Непредвиденная ошибка', exc_info=True)
            raise


    @property
    def connection(self):
        return self._connection

    
    @property
    def db_engine(self):
        return self._db_engine


    @property
    def url(self):
        return self._url


    def insert_data(self, schema: str, table: str, data: dict, truncate: bool=False) -> int:
    
        meta = MetaData(bind=self._db_engine, schema=schema)
        meta.reflect(bind=self._db_engine)

        full_table_name = f'{schema}.{table}'

        try:
            table_obj =  meta.tables[full_table_name]
        except KeyError as exc:
            logging.error(f'Не найдена таблица в базе данных: {schema}.{table}', exc_info=True)
            raise
        
        if truncate: self._connection.execute(f'TRUNCATE TABLE {full_table_name}')
        
        insertion_obj = insert(table_obj)
        
        try:
            self._connection.execute(insertion_obj, data)
            logging.info(f'Успешно вставлены данные в таблицу {schema}.{table}')  
        except Exception as ex:
            logging.error(f'Ошибка при вставке строк в таблицу {schema}.{table}', exc_info=True)
            raise