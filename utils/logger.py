import logging
import os
from datetime import datetime

def setup_logger():
    logger = logging.getLogger('faceswap_api')
    logger.setLevel(logging.DEBUG)
    
    # 創建 logs 目錄
    logs_folder = 'logs'
    os.makedirs(logs_folder, exist_ok=True)
    
    # 創建檔案處理器，每天一個新的日誌檔案
    log_filename = os.path.join(logs_folder, f'faceswap_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 創建控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 設定日誌格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加處理器到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 