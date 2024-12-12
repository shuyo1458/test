import requests
import logging
import time
import http.client
import json
from utils.image_storage import upload_image

logger = logging.getLogger('faceswap_api')

class FaceSwapService:
    def __init__(self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url
        #self.api_url="https://api.piapi.ai/api/v1/task"

    def process_images(self, source_file, target_file):
        """處理圖片換臉請求"""
        logger.info(f"source file: {type(source_file)}")
        try:
            # 上傳圖片到圖床服務
            source_url = upload_image(source_file, f"source_{int(time.time())}.jpg")
            target_url = upload_image(target_file, f"target_{int(time.time())}.jpg")
            
            # 準備 API 請求
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                "model": "Qubico/image-toolkit",
                "task_type": "face-swap",
                "input": {
                    "swap_image": source_url,
                    "target_image": target_url,
                    
                }
            }
            '''
            payload = json.dumps({
                 "target_image": source_url,
                 "swap_image": target_url,
                 "result_type": "url"
            })
            '''
            logger.info(f"發送請求到 PIAPI，payload: {payload}")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            # 檢查特定的錯誤狀態
            if response.status_code == 402:
                logger.error("PIAPI 額度不足")
                raise Exception("API 額度不足，請充值後再試")
            if response.status_code == 200:
                response_data = response.json()
                task_id = response_data.get('data', {}).get('task_id')
                if not task_id:
                    logger.error("無法獲取任務 ID")
                    raise Exception("無法獲取任務 ID")
                logger.info(f"成功創建任務，task_id: {task_id}")
            logger.info(f"PIAPI 響應狀態碼: {response.status_code}")
            logger.info(f"PIAPI 響應內容: {response.text}")
            #logger.info(f"PIAPI 圖片id:{task_id}")
          
            return self._handle_api_response(response)
            
        except Exception as e:
            logger.exception("處理請求時發生異常")
            raise

    def _handle_api_response(self, response):
        """處理 API 響應"""
        try:
            response_data = response.json()
            
            # 檢查錯誤訊息
            if response.status_code != 200:
                error_message = response_data.get('message', '未知錯誤')
                if 'insufficient credits' in error_message:
                    raise Exception("API 額度不足，請充值後再試")
                raise Exception(f"API 錯誤: {error_message}")
            
            task_id = response_data.get('data', {}).get('task_id')
            status_id=response_data.get('data',{}).get('status')
            logger.info(f'responses 響應內容: {response_data}')
            if not task_id:
                raise Exception("無法獲取任務 ID")
                
            logger.info(f"成功創建任務，task_id: {task_id}")
            return self._poll_task_status(task_id)
            
        except Exception as e:
            logger.error(f"處理 API 響應失敗: {str(e)}")
            raise

    def _poll_task_status(self, task_id):
        """輪詢任���狀態"""
        headers = {
            'x-api-key': self.api_key
        }
        #------------
        '''
        fetch_url = "https://api.piapi.ai/api/face_swap/v1/fetch"
        fetch_headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json'
            }
        fetch_payload = {
                "task_id": task_id
            }
            
        fetch_response = requests.post(
                fetch_url,
                headers=fetch_headers,
                json=fetch_payload
            )
        logger.info(f"PIAPI 響應狀態碼: {fetch_response.text}")
        if fetch_response.status_code == 200:
            fetch_data = fetch_response.json()
            image_url = fetch_data.get('data', {}).get('image')
            if not image_url:
                logger.error("無法獲取圖片 URL")
                raise Exception("無法獲取圖片 URL")
                
            logger.info(f"成功獲取圖片 URL: {image_url}")
                # 下載圖片
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                image_content = image_response.content
                logger.info("圖片下載成功")
                 # 上傳圖片到 imgbb
                sucess_url = upload_image(image_content, f"sucess_{int(time.time())}.jpg")
                if not sucess_url:
                    logger.error("無法獲取 imgbb 圖片 URL")
                    raise Exception("無法獲取 imgbb 圖片 URL")
                else:
                    logger.info(f"成功上傳圖片到 imgbb, URL: {sucess_url}")
            else:
                logger.error(f"下載圖片失敗, 狀態碼: {image_response.status_code}")
                raise Exception("下載圖片失敗")         
        else:
            logger.error(f"獲取圖片 錯誤：{fetch_response.status_code}")
        
        '''
        #-------------

        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                logger.debug(f"正在檢查任務狀態，第 {attempt + 1} 次嘗試")
                status_response = requests.get(
                    f"{self.api_url}/{task_id}",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('data', {}).get('status')
                    logger.info(f'status :{status_data}')
                    if status == 'completed':
                        result_url = status_data.get('data', {}).get('output', {}).get('image_url')
                        if result_url:
                            logger.info(f"任務完成，結果 URL: {result_url}")
                            return result_url
                        raise Exception("無法獲取結果 URL")
                    elif status == 'failed':
                        error_msg = status_data.get('data', {}).get('error', {}).get('message', '處理失敗，無具體錯誤信息')
                        raise Exception(f"處理失敗: {error_msg}")
                    elif status == 'insufficient_credits':
                        raise Exception("API 額度不足，請充值後再試")
                    
                    logger.debug(f"任務狀態: {status}")
                elif status_response.status_code == 402:
                    raise Exception("API 額度不足，請充值後再試")
                else:
                    logger.error(f"檢查任務狀態失敗: {status_response.status_code}")
                
            except Exception as e:
                logger.error(f"輪詢任務狀態時發生錯誤: {str(e)}")
                raise
                
            time.sleep(2)
        
        raise Exception("處理超時") 

    def fetch_task_result(self, task_id):
        """根據任務 ID 獲取結果"""
        try:
            fetch_url = "https://api.piapi.ai/api/face_swap/v1/fetch"
            fetch_headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json'
            }
            fetch_payload = {
                "task_id": task_id
            }
            
            fetch_response = requests.post(
                fetch_url,
                headers=fetch_headers,
                json=fetch_payload
            )
            
            if fetch_response.status_code == 200:
                fetch_data = fetch_response.json()
                image_url = fetch_data.get('data', {}).get('image')
                if not image_url:
                    raise Exception("無法獲取圖片 URL")
                
                return image_url
            else:
                raise Exception(f"獲取任務結果失敗: {fetch_response.status_code}")
                
        except Exception as e:
            logger.error(f"獲取任務結果失敗: {str(e)}")
            raise 