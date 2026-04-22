from pathlib import Path

def format_size(size_in_bytes):
    """Hàm hỗ trợ chuyển đổi dung lượng từ Byte sang KB, MB, GB..."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0

def get_file_properties(file_path):
    """Hàm trích xuất thông tin chi tiết của một file"""
    path = Path(file_path)
    
    # Kiểm tra xem đường dẫn có tồn tại và có phải là file không
    if not path.is_file():
        return {"error": "Đường dẫn không hợp lệ hoặc không phải là file."}
        
    # 1. Lấy tên file (Bao gồm cả đuôi)
    file_name = path.name
    
    # 2. Lấy định dạng file (Đuôi file, ví dụ: .mp4, .docx)
    # Dùng .lower() để đồng bộ, ví dụ .JPG hay .jpg đều thành .jpg
    file_extension = path.suffix.lower() 
    
    # 3. Lấy kích thước file
    size_bytes = path.stat().st_size
    size_formatted = format_size(size_bytes)
    
    return {
        "name": file_name,
        "extension": file_extension,
        "size_formatted": size_formatted,
        "size_bytes": size_bytes 
    }

if __name__ == "__main__":
    # Thay đường dẫn này bằng một file thực tế trên máy bạn để test
    test_file = r"C:\ThuMucCuaBan\file_test.txt" 
    
    ket_qua = get_file_properties(test_file)
    print(ket_qua)
    from pathlib import Path
import datetime

def format_size(size_in_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes} B"

def get_recent_files(directory_path, limit=4):
    """Quét một thư mục và trả về danh sách các file"""
    path = Path(directory_path)
    if not path.is_dir():
        return []
    
    files_data = []
    # Duyệt qua các mục trong thư mục
    for p in path.iterdir():
        if p.is_file():
            # Lấy thông tin file
            stat = p.stat()
            files_data.append({
                "name": p.name,
                "size": format_size(stat.st_size),
                # Tạm thời để ngày mặc định cho giống giao diện
                "date_str": "Hôm nay", 
            })
            
    # Lấy ra số lượng file theo limit (ví dụ: 4 file)
    return files_data[:limit]