import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = 'uploads'

# 確保上傳目錄存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, filename):
    """保存上傳的檔案並返回檔案路徑"""
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    file.save(filepath)
    return filepath 