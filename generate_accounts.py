"""
Script tự động tạo danh sách tài khoản và mật khẩu
"""
import json

def generate_accounts(base_name):
    """
    Tạo danh sách tài khoản và mật khẩu từ base_name
    
    Ví dụ: "hoang" -> 29 bộ tài khoản/mật khẩu:
    - hoang1997 đến hoang2010 (14 bộ)
    - hoang hoang (1 bộ)
    - hoang 123456 (1 bộ)
    - hoang + các số khác (13 bộ) để đủ 29
    """
    accounts = []
    
    # 1. Tạo từ năm 1997 đến 2010 (14 bộ)
    for year in range(1997, 2011):
        username = f"{base_name}{year}"
        password = f"{base_name}{year}"
        accounts.append({
            'username': username,
            'password': password
        })
    
    # 2. hoang hoang (1 bộ)
    accounts.append({
        'username': base_name,
        'password': base_name
    })
    
    # 3. hoang 123456 (1 bộ)
    accounts.append({
        'username': base_name,
        'password': '123456'
    })
    
    # 4. Thêm các năm từ 2011 đến 2023 để đủ 29 bộ (13 bộ)
    for year in range(2011, 2024):
        username = f"{base_name}{year}"
        password = f"{base_name}{year}"
        accounts.append({
            'username': username,
            'password': password
        })
    
    # Đảm bảo đúng 29 bộ
    if len(accounts) > 29:
        accounts = accounts[:29]
    elif len(accounts) < 29:
        # Nếu thiếu, thêm các biến thể khác
        remaining = 29 - len(accounts)
        for i in range(1, remaining + 1):
            accounts.append({
                'username': f"{base_name}{2000 + i}",
                'password': f"{base_name}{2000 + i}"
            })
    
    return accounts

def save_accounts_to_file(accounts, filename='generated_accounts.json'):
    """
    Lưu danh sách tài khoản vào file JSON
    """
    data = {
        'total': len(accounts),
        'accounts': accounts
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Đã tạo {len(accounts)} tài khoản và lưu vào {filename}")

def save_accounts_to_txt(accounts, filename='generated_accounts.txt'):
    """
    Lưu danh sách tài khoản vào file text (format: username:password)
    """
    with open(filename, 'w', encoding='utf-8') as f:
        for acc in accounts:
            f.write(f"{acc['username']}:{acc['password']}\n")
    
    print(f"✓ Đã lưu {len(accounts)} tài khoản vào {filename}")

def main():
    import sys
    import io
    # Fix encoding cho Windows console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    print("=" * 50)
    print("TẠO TÀI KHOẢN TỰ ĐỘNG")
    print("=" * 50)
    
    base_name = input("Nhập từ khóa (ví dụ: hoang): ").strip()
    
    if not base_name:
        print("✗ Từ khóa không được để trống!")
        return
    
    print(f"\nĐang tạo tài khoản từ '{base_name}'...")
    accounts = generate_accounts(base_name)
    
    print(f"\nĐã tạo {len(accounts)} bộ tài khoản/mật khẩu:")
    print("\nMột số ví dụ:")
    for i, acc in enumerate(accounts[:5]):
        print(f"  {i+1}. {acc['username']} / {acc['password']}")
    print("  ...")
    for i, acc in enumerate(accounts[-3:], len(accounts)-2):
        print(f"  {i}. {acc['username']} / {acc['password']}")
    
    # Lưu vào file
    save_accounts_to_file(accounts)
    save_accounts_to_txt(accounts)
    
    print("\n" + "=" * 50)
    print("HOÀN TẤT!")
    print("=" * 50)

if __name__ == "__main__":
    main()

