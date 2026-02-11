import os
import logging
from datetime import datetime

def setup_logger(log_folder):
    """Initializes a logger with a timestamped filename."""
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    
    # Create timestamp: YYYYMMDD_HHMMSS
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_folder, f"session_{timestamp}.log")
    
    logger = logging.getLogger("TradingApp")
    logger.setLevel(logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler(log_filename)
    # Create console handler for real-time feedback
    console_handler = logging.StreamHandler()
    
    # Formatting
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
