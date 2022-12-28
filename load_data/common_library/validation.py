# https://docs.python-cerberus.org/en/stable/index.html
from cerberus import Validator

import yaml
import os 
import re
from pathlib import Path
from sqlalchemy import create_engine
import sys


root = Path(sys.executable).parent.parent.parent


class FinbyValidator(Validator):
        
    def _validate_file_extension(self, constraint, field, value):
        '''
        The rule's arguments are validated against this schema:
        {
            'oneof': 
            [
                {'type': 'string'}, 
                {
                    'type': 'list', 
                    'valuesrules': {'type': 'string'}
                }
            ]
        }
        '''
        if os.path.isdir(value):
            file_extensions = [os.path.splitext(file)[1] for file in os.listdir(value)]
        elif os.path.isfile(value):
            file_extensions = [os.path.splitext(value)[1]]
        else:
            return self._error(field, "Invalid path")
            
        
        if isinstance(constraint, str): constraint = [constraint]
        
        not_allowed_extensions = 0
        for ext in file_extensions:
            if not ext in constraint: not_allowed_extensions += 1
               
        if not_allowed_extensions != 0:          
            self._error(field, "Unallowed file extensions were found") 


    def _validate_is_folder_path(self, is_folder, field, value):
        '''
        The rule's arguments are validated against this schema:
        { 'type': 'boolean' }
        '''
        if is_folder and not os.path.isdir(value) and not os.path.isdir(root / value):
            self._error(field, "Value is not a valid path to a folder")
            
    
    def _validate_is_file_path(self, is_file_path, field, value):
        '''
        The rule's arguments are validated against this schema:
        { 'type': 'boolean' }
        '''
        if is_file_path and not os.path.isfile(value):
            self._error(field, "Value is not a valid path to a file")


    def _validate_is_valid_sqlalchemy_url(self, is_valid_sqlalchemy_url, field, value):
        '''
        The rule's arguments are validated against this schema:
        { 'type': 'boolean' }
        '''
        if is_valid_sqlalchemy_url:
            try:
                engine = create_engine(value)
                connection = engine.connect()
                connection.close()
            except Exception as exs:
                self._error(field, "Value is not a valid SQLAlchemy URL")
                raise
                
    
    def _validate_is_valid_db_column_name(self, is_valid_db_column_name, field, value):
        '''
        The rule's arguments are validated against this schema:
        { 'type': 'boolean' }
        '''
        if is_valid_db_column_name and not re.match('^[a-zA-Z0-9_]*$', value):
            self._error(field, "Value is not a valid database column name")