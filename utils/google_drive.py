import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO
import logging
import mimetypes

logger = logging.getLogger('faceswap_api')

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_google_drive_service():
    """獲取 Google Drive service"""
    try:
        creds = None
        # token.pickle 儲存使用者的存取權杖
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
                
        # 如果沒有可用的憑證或已過期
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # 儲存憑證
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return build('drive', 'v3', credentials=creds)
        
    except Exception as e:
        logger.error(f"獲取 Google Drive service 失敗: {str(e)}")
        raise Exception(f"Google Drive 服務初始化失敗: {str(e)}")

def check_google_auth():
    """檢查是否已經授權 Google Drive"""
    try:
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
                if creds and creds.valid:
                    return True
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        with open('token.pickle', 'wb') as token:
                            pickle.dump(creds, token)
                        return True
                    except:
                        return False
        return False
    except Exception:
        return False

def get_mime_type(filename):
    """獲取檔案的 MIME 類型"""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'

def upload_to_google_drive(file_obj, filename):
    """上傳檔案到 Google Drive 並返回可共享的 URL"""
    try:
        logger.info(f"開始上傳檔案: {filename}")
        service = get_google_drive_service()
        
        # 讀取檔案內容
        try:
            file_data = BytesIO(file_obj.read())
            file_obj.seek(0)
        except Exception as e:
            logger.error(f"讀取檔案失敗: {str(e)}")
            raise Exception(f"讀取檔案失敗: {str(e)}")
        
        # 設定檔案資訊
        file_metadata = {
            'name': filename,
            'mimeType': get_mime_type(filename)
        }
        
        # 創建上傳物件
        try:
            media = MediaIoBaseUpload(
                file_data,
                mimetype=get_mime_type(filename),
                resumable=True,
                chunksize=1024*1024  # 1MB chunks
            )
        except Exception as e:
            logger.error(f"創建上傳物件失敗: {str(e)}")
            raise Exception(f"準備上傳失敗: {str(e)}")
        
        # 執行上傳
        try:
            logger.debug("開始執行檔案上傳")
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webContentLink'
            ).execute()
            logger.info(f"檔案上傳成功，ID: {file.get('id')}")
        except Exception as e:
            logger.error(f"檔案上傳失敗: {str(e)}")
            raise Exception(f"檔案上傳失敗: {str(e)}")
        
        # 設定權限
        try:
            logger.debug("設定檔案權限")
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            service.permissions().create(
                fileId=file['id'],
                body=permission
            ).execute()
            logger.info("檔案權限設定成功")
        except Exception as e:
            logger.error(f"設定檔案權限失敗: {str(e)}")
            raise Exception(f"設定檔案權限失敗: {str(e)}")
        
        # 獲取並返回檔案連結
        if 'webContentLink' in file:
            logger.info("成功獲取檔案連結")
            return file['webContentLink']
        else:
            logger.error("無法獲取檔案連結")
            raise Exception("無法獲取檔案連結")
        
    except Exception as e:
        logger.error(f"Google Drive 上傳過程發生錯誤: {str(e)}")
        raise Exception(f"Google Drive 上傳失敗: {str(e)}")
        