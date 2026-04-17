import logging
import os
from logging.handlers import RotatingFileHandler

def get_logger(name: str) -> logging.Logger:
    """Configure and return a customized logger that writes to stdout and a file."""
    logger = logging.getLogger(name)
    
    # If the logger already has handlers, avoid adding duplicates
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Ensure logs directory exists
    log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Formatting
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    
    # File Handler (Rotating logs at 5MB, keep 3 backups)
    log_file = os.path.join(log_dir, 'pipeline.log')
    fh = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    fh.setFormatter(formatter)
    
    logger.addHandler(ch)
    logger.addHandler(fh)
    
    return logger
