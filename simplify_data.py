"""
Script để giản lược dữ liệu JSON, chỉ giữ lại:
- Tài khoản/mật khẩu đăng nhập
- Tài khoản/mật khẩu từ account và account_v2
"""
import json
import os
import glob

def simplify_account_data(data):
    """
    Giản lược dữ liệu của một tài khoản
    """
    simplified = {
        'username': data.get('username', ''),
        'password': data.get('password', ''),
        'status': data.get('status', ''),
        'accounts': [],
        'accounts_v2': []
    }
    
    if data.get('status') == 'success' and data.get('data'):
        account_data = data['data']
        
        # Lấy tài khoản/mật khẩu từ account_details
        if account_data.get('account_details'):
            for detail in account_data['account_details']:
                account_info = {
                    'tai_khoan': detail.get('tai_khoan', ''),
                    'mat_khau': detail.get('mat_khau', ''),
                    'ma_don': detail.get('ma_don', ''),
                    'loai': detail.get('loai', '')
                }
                
                # Chỉ thêm nếu có tài khoản hoặc mật khẩu
                if account_info['tai_khoan'] or account_info['mat_khau']:
                    if detail.get('loai') == 'accounts':
                        simplified['accounts'].append(account_info)
                    elif detail.get('loai') == 'accounts-v2':
                        simplified['accounts_v2'].append(account_info)
    
    return simplified

def simplify_json_file(input_file, output_file=None):
    """
    Giản lược file JSON
    """
    if not output_file:
        # Tạo tên file output tự động
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_simplified.json"
    
    print(f"Đang đọc file: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"✗ Không tìm thấy file {input_file}")
        return
    except json.JSONDecodeError as e:
        print(f"✗ Lỗi khi đọc JSON: {e}")
        return
    
    # Giản lược dữ liệu
    simplified_data = {
        'base_names': data.get('base_names', []),
        'total_accounts': data.get('total_accounts', 0),
        'success_count': data.get('success_count', 0),
        'fail_count': data.get('fail_count', 0),
        'results': []
    }
    
    # Giản lược từng kết quả
    for result in data.get('results', []):
        simplified_result = simplify_account_data(result)
        simplified_data['results'].append(simplified_result)
    
    # Lưu file mới
    print(f"Đang lưu vào: {output_file}")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(simplified_data, f, ensure_ascii=False, indent=2)
        print(f"✓ Đã lưu file giản lược: {output_file}")
        
        # Thống kê
        total_accounts_found = 0
        total_accounts_v2_found = 0
        for result in simplified_data['results']:
            total_accounts_found += len(result['accounts'])
            total_accounts_v2_found += len(result['accounts_v2'])
        
        print(f"\nThống kê:")
        print(f"  - Tổng số tài khoản đăng nhập: {simplified_data['total_accounts']}")
        print(f"  - Tài khoản từ accounts: {total_accounts_found}")
        print(f"  - Tài khoản từ accounts_v2: {total_accounts_v2_found}")
        
    except Exception as e:
        print(f"✗ Lỗi khi lưu file: {e}")

def main():
    import sys
    import io
    # Fix encoding cho Windows console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    print("=" * 50)
    print("GIẢN LƯỢC DỮ LIỆU JSON")
    print("=" * 50)
    
    # Tìm các file JSON có thể giản lược
    json_files = glob.glob('shopbopbop_all_accounts_*.json')
    
    if not json_files:
        print("Không tìm thấy file JSON nào để xử lý")
        input_file = input("\nNhập đường dẫn file JSON: ").strip()
        if not input_file:
            return
    else:
        print("\nTìm thấy các file:")
        for i, f in enumerate(json_files, 1):
            print(f"  {i}. {f}")
        
        choice = input("\nChọn file (số) hoặc nhập đường dẫn file khác: ").strip()
        
        try:
            file_index = int(choice) - 1
            if 0 <= file_index < len(json_files):
                input_file = json_files[file_index]
            else:
                print("✗ Số không hợp lệ!")
                return
        except ValueError:
            # Không phải số, coi như đường dẫn file
            input_file = choice
    
    output_file = input("Nhập tên file output (Enter để tự động): ").strip()
    if not output_file:
        output_file = None
    
    simplify_json_file(input_file, output_file)
    
    print("\n" + "=" * 50)
    print("HOÀN TẤT!")
    print("=" * 50)

if __name__ == "__main__":
    main()

