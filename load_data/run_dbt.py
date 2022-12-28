import sys
import pathlib
import subprocess
import logging

from common_library.loggers import set_logger
from common_library.custom_configs import Config


if __name__ == '__main__':
    
    root = pathlib.Path(sys.executable).parent.parent.parent

    set_logger(root / 'load_data/configs/logging.yaml')

    config = Config(path=root / 'config_new.yaml', schema_path=root / 'load_data/configs/config_schema.yaml').load()

    venv = pathlib.Path(sys.executable).parent / 'activate'
    dbt_folder = config['dbt_folder']

    dbt_output = subprocess.run(
        # Specifying project folder location and profiles.yaml location
        # Redirecting stderr to stdout
        f'{venv} && dbt run --project-dir {dbt_folder} --profiles-dir {dbt_folder} 2>&1', 
        capture_output=True, shell=True,
        cwd=root
    )
    
    dbt_log = '\n\t' + dbt_output.stdout.decode().replace('\r', '').replace('\n', '\n\t')

    if not dbt_output.returncode == 0:
        logging.error(f'Ошибка в процессе запуска транформаций в ХД{dbt_log}')
        raise RuntimeError
    else:
        logging.info(f'Даннные успешно трансформированы в ХД{dbt_log}')