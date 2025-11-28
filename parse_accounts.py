"""
Script để parse lại file JSON và chỉ lấy những mục có thông tin "Tài Khoản:"
"""
import json
import re

def parse_account_data(text_content):
    """
    Parse dữ liệu tài khoản từ text có định dạng: "Mã Số:|#49000|Mã Đơn:|Y2-XXX|Tài Khoản:|username|Ngày Mua:|date"
    """
    if not text_content or 'Tài Khoản:' not in text_content:
        return None
    
    # Tách các phần bằng dấu |
    parts = text_content.split('|')
    account_data = {}
    
    i = 0
    while i < len(parts):
        part = parts[i].strip()
        if not part:
            i += 1
            continue
        
        # Kiểm tra xem có phải là label không (có dấu :)
        if ':' in part and i + 1 < len(parts):
            label = part.replace(':', '').strip()
            value = parts[i + 1].strip() if i + 1 < len(parts) else ''
            
            # Lưu vào dictionary
            if label == 'Tài Khoản':
                account_data['tai_khoan'] = value
            elif label == 'Mã Số':
                account_data['ma_so'] = value
            elif label == 'Mã Đơn':
                # Mã đơn có thể có giá tiền, tách ra
                if '/' in value:
                    order_parts = value.split('/')
                    account_data['ma_don'] = order_parts[0].strip()
                    if len(order_parts) > 1:
                        account_data['gia'] = order_parts[1].strip()
                else:
                    account_data['ma_don'] = value
            elif label == 'Ngày Mua':
                account_data['ngay_mua'] = value
            else:
                # Lưu các trường khác
                account_data[label.lower().replace(' ', '_')] = value
            
            i += 2  # Bỏ qua cả label và value
        else:
            i += 1
    
    # Chỉ trả về nếu có thông tin tài khoản
    if 'tai_khoan' in account_data:
        return account_data
    return None

def filter_accounts_from_json(input_file='shopbopbop_data.json', output_file='shopbopbop_accounts_filtered.json'):
    """
    Đọc file JSON, lọc và parse chỉ những mục có "Tài Khoản:"
    """
    print(f"Đang đọc file {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"✗ Không tìm thấy file {input_file}")
        return
    except json.JSONDecodeError as e:
        print(f"✗ Lỗi khi đọc JSON: {e}")
        return
    
    filtered_data = {
        'accounts': [],
        'accounts_v2': []
    }
    
    # Xử lý accounts
    if 'accounts' in data and data['accounts']:
        print(f"Đang xử lý {len(data['accounts'])} mục trong accounts...")
        for item in data['accounts']:
            if 'content' in item:
                parsed = parse_account_data(item['content'])
                if parsed:
                    filtered_data['accounts'].append(parsed)
            elif isinstance(item, dict):
                # Kiểm tra xem có chứa thông tin tài khoản không
                item_text = '|'.join([f"{k}:{v}" for k, v in item.items()])
                if 'Tài Khoản:' in item_text or 'tai_khoan' in str(item).lower():
                    parsed = parse_account_data(item_text)
                    if parsed:
                        filtered_data['accounts'].append(parsed)
                    elif any('tài khoản' in str(v).lower() or 'tai_khoan' in str(k).lower() for k, v in item.items()):
                        filtered_data['accounts'].append(item)
    
    # Xử lý accounts_v2
    if 'accounts_v2' in data and data['accounts_v2']:
        print(f"Đang xử lý {len(data['accounts_v2'])} mục trong accounts_v2...")
        for item in data['accounts_v2']:
            if 'content' in item:
                parsed = parse_account_data(item['content'])
                if parsed:
                    filtered_data['accounts_v2'].append(parsed)
            elif isinstance(item, dict):
                # Kiểm tra xem có chứa thông tin tài khoản không
                item_text = '|'.join([f"{k}:{v}" for k, v in item.items()])
                if 'Tài Khoản:' in item_text or 'tai_khoan' in str(item).lower():
                    parsed = parse_account_data(item_text)
                    if parsed:
                        filtered_data['accounts_v2'].append(parsed)
                    elif any('tài khoản' in str(v).lower() or 'tai_khoan' in str(k).lower() for k, v in item.items()):
                        filtered_data['accounts_v2'].append(item)
    
    # Lưu file mới
    print(f"Đang lưu vào {output_file}...")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Đã lọc và lưu:")
        print(f"  - Accounts: {len(filtered_data['accounts'])} tài khoản")
        print(f"  - Accounts V2: {len(filtered_data['accounts_v2'])} tài khoản")
        print(f"  - File output: {output_file}")
    except Exception as e:
        print(f"✗ Lỗi khi lưu file: {e}")

if __name__ == "__main__":
    import sys
    import io
    # Fix encoding cho Windows console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    print("=" * 50)
    print("PARSE ACCOUNTS FROM JSON")
    print("=" * 50)
    filter_accounts_from_json()

