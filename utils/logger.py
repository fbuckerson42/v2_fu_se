import logging
import sys
from pathlib import Path
from datetime import datetime
import pytz
from config.settings import settings

KYIV_TZ = pytz.timezone('Europe/Kyiv')

def setup_logger(name: str = 'keycrm_scraper') -> logging.Logger:
    logger = logging.getLogger(name)
    
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    logger.handlers.clear()
    
    def KyivTimeFormatter(fmt=None, datefmt=None):
        class Formatter(logging.Formatter):
            def formatTime(self, record, datefmt=None):
                dt = datetime.now(KYIV_TZ)
                return dt.strftime(datefmt or '%Y-%m-%d %H:%M:%S')
        return Formatter(fmt=fmt, datefmt=datefmt)
    
    detailed_formatter = KyivTimeFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    if settings.LOG_FILE:
        log_file = Path(settings.LOG_FILE)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger


logger = setup_logger()
