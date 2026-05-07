import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Chỉ cấp quyền quản lý các file do app này tạo ra để bảo mật
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    creds = None
    # Kiểm tra xem token.json đã tồn tại chưa
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Nếu chưa có token hoặc token hết hạn, tiến hành xác thực lại
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Lưu thông tin xác thực vào token.json cho lần sau
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(file_obj, file_name, mime_type):
    service = get_drive_service()
    file_metadata = {'name': file_name}
    media = MediaIoBaseUpload(file_obj, mimetype=mime_type, resumable=True)
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    return file.get('id')

def list_drive_files():
    service = get_drive_service()
    results = service.files().list(
        pageSize=10, fields="files(id, name, size, mimeType, createdTime)", orderBy="createdTime desc"
    ).execute()
    return results.get('files', [])