import os
import pathlib

from socket import gaierror

from typing import List
from typing import Dict

from smtplib import SMTP_SSL, SMTP
from smtplib import SMTPAuthenticationError

import mimetypes
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.multipart import MIMEMultipart
from email.header import Header 

from common_library.custom_configs import CustomTemplate

import logging

import html2text


class EmailNotification():
    
    def __init__(self, host: str, port: int, address_from: str, password: str=None):
        self._host = host
        self._port = port
        self._address_from = address_from
        self._password = password
        
        try:
            self._server = SMTP_SSL(self._host, self._port)
            self._server.login(self._address_from, self._password)
        except gaierror as exc:
            logging.error(f'Указан неверный хост: {self._host}', exc_info=True)
            raise
        except TimeoutError as exc:
            logging.error(f'Не удалось подключиться к хосту: {self._host}:{self._port}', exc_info=True)
            raise
        except Exception as exc:
            logging.error('Непредвиденная ошибка', exc_info=True) 
            raise
    

    def send_email(self, address_to: List[str], subject: str=None, template_path: str=None, template_dict: Dict=None, address_cc: List[str]=None, attachments: List[str]=None):
        
        self._msg = MIMEMultipart('alternative')
        self._attachments = attachments
        
        self._msg['From'] = self._address_from
        self._msg['To'] = (', '.join(address_to or []) if isinstance(address_to, list) else address_to)
        self._msg['Cc'] = (', '.join(address_cc or []) if isinstance(address_cc, list) else address_cc)
        self._msg['Subject'] = Header(subject, 'utf-8')
            
        self.__process_attachement()
        
        if not template_path is None:
            
            if os.path.exists(template_path):
                
                if template_dict is None:
                    logging.error('Недопустимый словарь для заполнения шаблона')
                    raise ValueError()
                
                maintype, subtype = self.__check_file_type(template_path)
                
                template = CustomTemplate(template_path).render(**template_dict)

                if maintype == 'text':
                    
                    self._msg.attach(MIMEText(template, subtype, 'utf-8'))
                    
                    # Конвертация HTML в обычный текст для тех пользователей, у кого почта не поддерживает HTML
                    if subtype == 'html':
                        html_converter = html2text.HTML2Text()
                        html_converter.ignore_links = True
                        plain_text = html_converter.handle(template)
                        
                        self._msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
            else:
                logging.error('Указан неверный путь к шаблону email')
                raise FileNotFoundError()
        
        if not self._password is None:
            try:
                self._server.login(self._address_from, self._password)
            except SMTPAuthenticationError as exc:
                logging.error('Не удалось подключиться с указанными данными', exc_info=True)
                raise 
            except Exception as exc:
                logging.error('Непредвиденная ошибка', exc_info=True)
                raise
        
        self._server.send_message(self._msg)
        self._server.quit()
        
    
    def __process_attachement(self):
        if not self._attachments is None:
            for f in self._attachments:
                if os.path.isfile(f):
                    self.__attach_file(f)
                elif os.path.exists(f):
                    folder_files = os.listdir(f)
                    folder = pathlib.Path(f)
                    for inner_file in folder_files:
                        self.__attach_file(folder / inner_file)


    def __attach_file(self, filepath: str):
       
        maintype, subtype = self.__check_file_type(filepath)
        
        if maintype == 'text':
            with open(filepath) as fp:
                file = MIMEText(fp.read(), _subtype=subtype)
        
        elif maintype == 'image':
            with open(filepath, 'rb') as fp:
                file = MIMEImage(fp.read(), _subtype=subtype)
        
        elif maintype == 'audio':
            with open(filepath, 'rb') as fp:
                file = MIMEAudio(fp.read(), _subtype=subtype)
        
        else:
            with open(filepath, 'rb') as fp:
                file = MIMEBase(maintype, subtype)
                file.set_payload(fp.read())
                encoders.encode_base64(file)
        
        file.add_header('Content-Disposition', 'attachment', filename=filename)
        
        self._msg.attach(file)
    
    
    @staticmethod
    def __check_file_type(filepath: str):
        filename = os.path.basename(filepath)
        ctype, encoding = mimetypes.guess_type(filepath)
        
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        
        maintype, subtype = ctype.split('/', 1)
        
        return maintype, subtype