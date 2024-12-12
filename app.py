from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
from utils.logger import setup_logger
from utils.file_handler import allowed_file
from services.faceswap_service import FaceSwapService
import requests
from io import BytesIO
from utils.image_storage import upload_image
import time
import json

app = Flask(__name__, static_url_path='/img', static_folder='img')

# 確保 img 目錄存在
if not os.path.exists('img'):
    os.makedirs('img')

# 設定
#API_KEY = "340d75eb35d0e2a69758a7d7e31f8fcdcb70a466689aff29580f526b7ef0386f"
API_KEY = "b6b9bad9655675f5de02121216e7b13715147011f840b9ece8f51a425899e16c"
PIAPI_URL = "https://api.piapi.ai/api/v1/task"

# 初始化
logger = setup_logger()
faceswap_service = FaceSwapService(API_KEY, PIAPI_URL)

@app.route('/')
def index():
    """首頁"""
    return render_template('index.html')

@app.route('/test')
def test_page():
    """測試頁面"""
    return render_template('test.html')

@app.route('/test-url')
def test_url_page():
    """URL測試頁面"""
    return render_template('test_url.html')

@app.route('/api/test-faceswap', methods=['POST'])
def test_faceswap():
    """處理換臉請求"""
    try:
        logger.info(f'request.files {request.files} ')
        # 檢查檔案
        source_file = request.files.get('source')
        target_file = request.files.get('target')
        
        if not source_file or not target_file:
            return jsonify({'error': '請上傳兩張圖片'}), 400
            
        if not (allowed_file(source_file.filename) and allowed_file(target_file.filename)):
            return jsonify({'error': '不支援的文件格式'}), 400
        #logger.info(f'request.files {} ')
        # 使用 FaceSwap 服務處理圖片
        try:
            result_url = faceswap_service.process_images(source_file, target_file)
            # 上傳圖片到 imgbb
            try:
                image_response = requests.get(result_url)
                if image_response.status_code == 200:
                    image_content = image_response.content
                    # 使用前時間作為檔案名
                    #filename = f"success_{int(time.time())}.jpg"
                    # 上傳圖片到 imgbb
                    ftime=int(time.time())
                    imgbb_url = upload_image(BytesIO(image_content), f"success_{ftime}.jpg")
                    # 從檔名中提取時間戳記
                    timestamp = ftime
                    filename = f"success_{timestamp}.jpg"
                    
                    # 準備要記錄的資料
                    record = {
                        'timestamp': timestamp,
                        'url': imgbb_url
                    }
                    
                    try:
                        # 讀取現有的 JSON 檔案，如果不存在則創建新的
                        try:
                            with open('image_records.json', 'r') as f:
                                records = json.load(f)
                        except FileNotFoundError:
                            records = []
                        
                        # 添加新記錄
                        records.append(record)
                        
                        # 寫入 JSON 檔案
                        with open('image_records.json', 'w') as f:
                            json.dump(records, f, indent=4)
                            
                        logger.info(f"成功記錄圖片資訊: {record}")
                    except Exception as e:
                        logger.error(f"記錄圖片資訊時發生錯誤: {str(e)}")
                    if imgbb_url:
                        logger.info(f"成功上傳圖片到 imgbb, URL: {imgbb_url}")
                        # 更新回傳的 URL
                        result_url = imgbb_url
                    else:
                        logger.error("無法上傳圖片到 imgbb")
                else:
                    logger.error(f"下載圖片失敗, 狀態碼: {image_response.status_code}")
            except Exception as e:
                logger.error(f"上傳圖片到 imgbb 過程發生錯誤: {str(e)}")
            return jsonify({
                'success': True,
                'result': result_url
            })
        except Exception as e:
            logger.error(f"FaceSwap 處理失敗: {str(e)}")
            return jsonify({'error': f'圖片處理失敗: {str(e)}'}), 500
            
    except Exception as e:
        logger.exception("處理請求時發生異常")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-faceswap-url', methods=['POST'])
def test_faceswap_url():
    """處理換臉請求 (URL版本)"""
    try:
        data = request.json
        source_url = data.get('source_url')
        target_url = data.get('target_url')
        
        if not source_url or not target_url:
            return jsonify({'error': '請提供兩個圖片URL'}), 400
            
        # 下載圖片
        try:
            source_response = requests.get(source_url)
            target_response = requests.get(target_url)
            
            if source_response.status_code != 200 or target_response.status_code != 200:
                return jsonify({'error': '無法下載圖片'}), 400
                
            # 將圖片轉換為 file-like 物件
            source_file = BytesIO(source_response.content)
            target_file = BytesIO(target_response.content)
            
            # 設定檔案名稱
            source_file.filename = 'source.jpg'
            target_file.filename = 'target.jpg'
            
            # 使用現有的處理邏輯
            result_url = faceswap_service.process_images(source_file, target_file)
            return jsonify({
                'success': True,
                'result': result_url
            })
            
        except Exception as e:
            logger.error(f"下載圖片失敗: {str(e)}")
            return jsonify({'error': f'下載圖片失敗: {str(e)}'}), 500
            
    except Exception as e:
        logger.exception("處理請求時發生異常")
        return jsonify({'error': str(e)}), 500

@app.route('/api/fetch-task-result', methods=['POST'])
def fetch_task_result():
    """根據任務 ID 獲取結果"""
    try:
        data = request.json
        task_id = data.get('task_id')
        
        if not task_id:
            return jsonify({'error': '請提供任務 ID'}), 400
            
        try:
            # 使用 FaceSwap 服務查詢結果
            result_url = faceswap_service.fetch_task_result(task_id)
            return jsonify({
                'success': True,
                'result': result_url
            })
            
        except Exception as e:
            logger.error(f"獲取任務結果失敗: {str(e)}")
            return jsonify({'error': f'獲取任務結果失敗: {str(e)}'}), 500
            
    except Exception as e:
        logger.exception("處理請求時發生異常")
        return jsonify({'error': str(e)}), 500

@app.route('/imgbb-search')
def imgbb_search_page():
    """ImgBB 搜尋頁面"""
    return render_template('imgbb_search.html')

@app.route('/api/search-imgbb', methods=['POST'])
def search_imgbb():
    """搜尋 ImgBB 圖片"""
    try:
        data = request.json
        filename = data.get('Id')
        logger.info(f'filename:{filename}')
        if not filename:
            return jsonify({'error': '請提供檔案名稱'}), 400
        # 讀取 image_records.json 檔案
        try:
            with open('image_records.json', 'r') as f:
                records = json.load(f)
            
            # 搜尋符合的記錄
            result_url = None
            for record in records:
                if str(record['timestamp']) == filename:
                    result_url = record['url']
                    break
                    
            if result_url:
                return jsonify({
                    'success': True,
                    'result': result_url
                })
            else:
                return jsonify({'error': '找不到對應的圖片記錄'}), 404
                
        except FileNotFoundError:
            return jsonify({'error': '找不到記錄檔'}), 500
    except json.JSONDecodeError:
        return jsonify({'error': '記錄檔格式錯誤'}), 500
        
        
        '''    
        try:
            # 使用 ImgBB API 搜尋圖片
            headers = {
                'Content-Type': 'application/json',
            }
            
            params = {
                'key': IMGBB_API_KEY,
                'name': filename
            }
            
            response = requests.get(
                'https://api.imgbb.com/1/account/images',
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                images = data.get('data', [])
                
                results = []
                for image in images:
                    if filename.lower() in image['name'].lower():
                        results.append({
                            'url': image['url'],
                            'filename': image['name'],
                            'timestamp': image['datetime']
                        })
                
                return jsonify({
                    'success': True,
                    'results': results
                })
            else:
                raise Exception(f"搜尋失敗: {response.status_code}")
            
             
        except Exception as e:
            logger.error(f"搜尋圖片失敗: {str(e)}")
            return jsonify({'error': f'搜尋失敗: {str(e)}'}), 500
        '''  
    except Exception as e:
        logger.exception("處理請求時發生異常")
        return jsonify({'error': str(e)}), 500

@app.route('/camera')
def camera_page():
    """相機拍照頁面"""
    return render_template('camera.html')

@app.route('/api/upload-photo', methods=['POST'])
def upload_photo():
    """處理相機拍照上傳"""
    try:
        if 'photo' not in request.files:
            return jsonify({'error': '沒有收到照片'}), 400
            
        photo = request.files['photo']
        if not photo:
            return jsonify({'error': '照片為空'}), 400
            
        if not allowed_file(photo.filename):
            return jsonify({'error': '不支援的檔案格式'}), 400

        # 上傳到 imgbb
        try:
            image_url = upload_image(photo, f"camera_{int(time.time())}.jpg")
            return jsonify({
                'success': True,
                'url': image_url
            })
        except Exception as e:
            logger.error(f"上傳照片失敗: {str(e)}")
            return jsonify({'error': f'上傳失敗: {str(e)}'}), 500
            
    except Exception as e:
        logger.exception("處理照片上傳時發生異常")
        return jsonify({'error': str(e)}), 500

@app.route('/api/list-images')
def list_images():
    """列出已上傳的圖片"""
    try:
        # 讀取 image_records.json 檔案
        try:
            with open('image_records.json', 'r') as f:
                records = json.load(f)
            
            # 整理圖片資訊
            images = []
            for record in records:
                images.append({
                    'url': record['url'],
                    'filename': f"image_{record['timestamp']}.jpg",
                    'timestamp': record['timestamp']
                })
            
            return jsonify({
                'success': True,
                'images': images
            })
                
        except FileNotFoundError:
            return jsonify({
                'success': True,
                'images': []
            })
            
    except Exception as e:
        logger.exception("獲取圖片列表時發生異常")
        return jsonify({'error': str(e)}), 500

@app.route('/api/list-local-images')
def list_local_images():
    """列出本機圖片目錄下的圖片"""
    try:
        img_folder = 'img'
        logger.info(f"正在讀取圖片目錄: {img_folder}")
        
        if not os.path.exists(img_folder):
            logger.info("圖片目錄不存在，正在創建...")
            os.makedirs(img_folder)
        
        # 獲取圖片列表
        images = []
        for filename in os.listdir(img_folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(img_folder, filename)
                logger.info(f"找到圖片: {filename}, 完整路徑: {full_path}")
                images.append({
                    'filename': filename,
                    'path': full_path
                })
        
        logger.info(f"找到 {len(images)} 張圖片")
        return jsonify({
            'success': True,
            'images': images
        })
            
    except Exception as e:
        logger.exception("獲取本機圖片列表時發生異常")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-local-photo', methods=['POST'])
def upload_local_photo():
    """處理本機圖片上傳"""
    try:
        filename = request.form.get('filename')
        if not filename:
            return jsonify({'error': '未指定檔案名稱'}), 400
            
        filepath = os.path.join('img', filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '找不到指定檔案'}), 404
            
        # 讀取檔案並上傳到 imgbb
        with open(filepath, 'rb') as f:
            image_url = upload_image(f, f"local_{int(time.time())}.jpg")
            
        return jsonify({
            'success': True,
            'url': image_url
        })
            
    except Exception as e:
        logger.exception("處理本機圖片上傳時發生異常")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("啟動 Face Swap API 服務")
    app.run(debug=True)