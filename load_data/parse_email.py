import sys
import pathlib
import logging

from dotenv import load_dotenv

from common_library.loggers import set_logger
from common_library.custom_configs import Config
from common_library.fetch_email import FetchEmail
from common_library.custom_configs import env_var
from common_library.fetch_email import get_mail_config

if __name__ == '__main__':
    
    root = pathlib.Path(sys.executable).parent.parent.parent

    set_logger(root / 'load_data/configs/logging.yaml')

    load_dotenv(root / '.env')

    config = Config(path=root / 'config_new.yaml', schema_path=root / 'load_data/configs/config_schema.yaml').load()

    inbox = FetchEmail(host=env_var('imap_host'), port=env_var('imap_port'), address=env_var('email_address'), password=env_var('email_password'))

    inbox.get_email_uids(folder='INBOX')

    mail_config = get_mail_config(config)
            
    inbox.save_attachments(
        folder=config['source_folder'],
        part_types=config['data_files_type'],
        mail_config=mail_config
    )
    
    inbox.close_connection()