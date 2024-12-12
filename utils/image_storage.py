import requests
import logging
import base64
from io import BytesIO

logger = logging.getLogger('faceswap_api')

IMGBB_API_KEY = "e9083f753faa8543dd09a4a916a7a4a3"  # 需要從 imgbb.com 獲取
IMGBB_API_URL = "https://api.imgbb.com/1/upload"

def upload_image(file_obj, filename):
    """上傳圖片到 imgbb 並返回 URL"""
    try:
        logger.info(f"開始上傳圖片: {filename}")
        
        # 讀取圖片內容並轉換為 base64
        image_data = file_obj.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # 準備請求參數
        payload = {
            'key': IMGBB_API_KEY,
            'image': base64_image,
            'name': filename
        }
        
        # 發送上傳請求
        response = requests.post(IMGBB_API_URL, data=payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                image_url = result['data']['url']
                logger.info(f"圖片上傳成功: {image_url}")
                return image_url
            else:
                logger.error("圖片上傳失敗: API 返回失敗")
                raise Exception("圖片上傳失敗")
        else:
            logger.error(f"圖片上傳失敗: HTTP {response.status_code}")
            raise Exception(f"圖片上傳失敗: HTTP {response.status_code}")
            
    except Exception as e:
        logger.error(f"圖片上傳過程發生錯誤: {str(e)}")
        raise Exception(f"圖片上傳失敗: {str(e)}") 