import logging
import os
from datetime import datetime

class Logger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Create file handler
        handler = logging.FileHandler(f'logs/{name}.log')
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(handler)

    def log(self, message):
        """Log a message"""
        self.logger.info(message)

    def error(self, message):
        """Log an error"""
        self.logger.error(message)

    def warning(self, message):
        """Log a warning"""
        self.logger.warning(message)
