import os
import pathlib
from custom_functions import get_emails
import sys

import logging

from dotenv import load_dotenv

from common_library.notification import EmailNotification
from common_library.loggers import set_logger
from common_library.custom_configs import env_var, Config, CustomTemplate


LOG_FORMAT_START = '>> '
LOG_FORMAT_DELIMITER = ' -- '


if __name__ == '__main__':

    root = pathlib.Path(sys.executable).parent.parent.parent

    load_dotenv(root / '.env')

    loggers = set_logger(root / 'load_data/configs/logging.yaml')

    config = Config(path=root / 'config_new.yaml', schema_path=root / 'load_data/configs/config_schema.yaml').load()

    notificator = EmailNotification(host=env_var('smtp_host'), port=env_var('smtp_port'), address_from=env_var('email_address'), password=env_var('email_password'))

    logs_tmp = loggers['handlers']['tmp']['filename']
    logs_info = loggers['handlers']['info']['filename']
    
    with open(logs_tmp, 'r', encoding='utf-8') as f:
        document = f.read()
        # Split logs file by a separator at the begging of each log entry
        split_logs = list(map(lambda line: line.split(LOG_FORMAT_DELIMITER), document.split(LOG_FORMAT_START)))
        # Split each log entry by a new line symbol to get log name and description
        split_log_name = [[part.split('\n') if i == 5 else part for i, part in enumerate(log)] for log in split_logs]
        errors = [log for log in split_log_name if log[0] == 'ERROR']
        warnings = [log for log in split_log_name if log[0] == 'WARNING']


    emails = get_emails(config['mappings_path'])
    send_to = (emails['Success']['To'] if len(errors) == 0 else emails['All']['To'])
    send_cc = (emails['Success']['Cc'] if len(errors) == 0 else emails['All']['Cc'])

    notificator.send_email(
        address_to=send_to, 
        address_cc=send_cc,
        subject=config['email_header'], 
        template_path=root / 'load_data/configs/email_template.html', 
        template_dict={
            'exceptions': errors,
            'warnings': warnings,
            'logs': logs_info
        }
    )
    
    logging.info(f'Оправлены e-mail на следующие адреса: {", ".join(send_to + send_cc)}')

    logs_file_to_clear = open(logs_tmp,'w')
    logs_file_to_clear.close()