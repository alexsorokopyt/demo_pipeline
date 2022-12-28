import os
import pathlib
from datetime import datetime
import sys
import logging

from custom_functions import read_excel_table

from common_library.loggers import set_logger
from common_library.custom_configs import Config
from common_library.dwh import Database


if __name__ == '__main__':

    root = pathlib.Path(sys.executable).parent.parent.parent

    set_logger(root / 'load_data/configs/logging.yaml')

    config = Config(path=root / 'config_new.yaml', schema_path=root / 'load_data/configs/config_schema.yaml').load()

    db = Database(url=config['dwh_url'])
    
    with db.connection as conn:
    
        mappings_path = config['mappings_path']
        
        file_name, file_extension = os.path.splitext(mappings_path)
        
        mappings_config = config['mappings']
       
        for mapping in mappings_config:
            
            mapping_data = read_excel_table(
                file_path=mappings_path, 
                sheet_name=mappings_config[mapping]['sheet_name'],
                is_smart_table=True,
                table_name=mappings_config[mapping]['excel_table'], 
                promote_headers=True, 
                rename=mappings_config[mapping]['rename'],
                metadata={'loaded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            )
            
            db.insert_data(table=mappings_config[mapping]['dwh_table'], data=mapping_data, schema=mappings_config[mapping]['dwh_schema'], truncate=True)