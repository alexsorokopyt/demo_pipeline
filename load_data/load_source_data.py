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

    config = Config(path=root / 'config.yaml', schema_path=root / 'load_data/configs/config_schema.yaml').load()

    db = Database(url=config['dwh_url'])

    with db.connection as conn:
       
        source_folder = pathlib.Path(config['source_folder'])
        
        files = os.listdir(source_folder)

        for item in files:

            file_path = source_folder / item

            file_name, file_extension = os.path.splitext(item)

            error_file_path = pathlib.Path(config['error_folder']) / item
            backup_file_path = pathlib.Path(config['backup_folder']) / f'{file_name}_{datetime.now().strftime("_%Y-%m-%d_%H-%M-%S")}{file_extension}'
            
            for source in config['sources']:
                
                current_source_config = config['sources'][source]
                
                if file_name.startswith(current_source_config['file_mask']):
                    
                    try:
                        os.rename(file_path, file_path)
                    except PermissionError as exc:
                        logging.warning(f'Файл используется другим процессом: {file_path}', exc_info=True)
                        continue
        
                    source_data = read_excel_table(
                        file_path=str(file_path), 
                        sheet_name=current_source_config['sheet_name'],
                        is_smart_table=False,
                        promote_headers=True, 
                        rename=current_source_config['rename'], 
                        convert=current_source_config.get('convert', {}), 
                        metadata={
                            'loaded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'source_file': backup_file_path.__str__()
                        }
                    )
                    
                    if not source_data is None:
                        
                        schema = current_source_config['dwh_schema']
                        table = current_source_config['dwh_table']
                        
                        try:
                            db.insert_data(table=table, data=source_data, schema=schema)                     
                        except Exception as e:
                            os.rename(file_path, error_file_path)
                            continue

                        try:
                            os.rename(file_path, backup_file_path)
                            logging.info(f'Файл перемещен: {file_path} >> {backup_file_path}')
                        except FileExistsError as e:
                            logging.warning(f'Ошибка при попытке перемещения файла (файл уже существует): {backup_file_path}', exc_info=True)
                            continue