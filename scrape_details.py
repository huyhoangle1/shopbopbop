"""
Script để lấy chi tiết từng đơn hàng từ file JSON hiện có
Không cần login lại, chỉ cần session còn hợp lệ
"""
import json
import requests
from bs4 import BeautifulSoup
import time
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Tắt SSL warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DetailScraper:
    def __init__(self, base_url="https://shopbopbop.vn"):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Cấu hình retry
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        })
    
    def scrape_order_detail(self, order_code, order_type='accounts-v2'):
        """
        Lấy TẤT CẢ dữ liệu từ trang chi tiết đơn hàng
        """
        detail_url = f"{self.base_url}/account/orders/{order_type}/{order_code}"
        print(f"  Đang lấy chi tiết đơn hàng {order_code}...")
        
        try:
            response = self.session.get(detail_url, timeout=15, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chỉ lưu thông tin cần thiết
            detail_data = {
                'ma_don': order_code,
                'loai': order_type,
                'url': detail_url
            }
            
            # Chỉ lấy input để tìm tài khoản và mật khẩu
            inputs = soup.find_all('input')
            
            # TRÍCH XUẤT TÀI KHOẢN VÀ MẬT KHẨU
            tai_khoan = None
            mat_khau = None
            
            # Cách 1: Tìm label "Tài Khoản" và input tương ứng
            labels = soup.find_all('label')
            for label in labels:
                label_text = label.get_text(strip=True)
                label_for = label.get('for', '')
                
                # Tìm input tương ứng với label
                input_elem = None
                
                if label_for:
                    # Tìm input có id hoặc name trùng với label_for
                    input_elem = soup.find('input', id=label_for) or soup.find('input', attrs={'name': label_for})
                
                # Nếu không tìm thấy, tìm trong cấu trúc HTML gần label
                if not input_elem:
                    # Tìm trong parent của label
                    parent = label.parent
                    if parent:
                        # Tìm input trong cùng parent
                        input_elem = parent.find('input')
                        
                        # Nếu không có, tìm trong div con
                        if not input_elem:
                            divs = parent.find_all('div', recursive=False)
                            for div in divs:
                                input_elem = div.find('input')
                                if input_elem:
                                    break
                        
                        # Nếu vẫn không có, tìm trong div kế tiếp
                        if not input_elem:
                            next_div = parent.find_next_sibling('div')
                            if next_div:
                                input_elem = next_div.find('input')
                                if not input_elem:
                                    # Tìm trong div con của next_div
                                    inner_divs = next_div.find_all('div', recursive=False)
                                    for div in inner_divs:
                                        input_elem = div.find('input')
                                        if input_elem:
                                            break
                
                if input_elem:
                    input_value = input_elem.get('value', '')
                    if input_value:
                        if 'tài khoản' in label_text.lower() or 'username' in label_text.lower() or label_for == 'username':
                            tai_khoan = input_value
                        elif 'mật khẩu' in label_text.lower() or 'password' in label_text.lower() or label_for == 'password':
                            mat_khau = input_value
            
            # Cách 2: Tìm input có value và tìm label gần đó (tìm ngược lại)
            if not tai_khoan or not mat_khau:
                for inp in inputs:
                    input_value = inp.get('value', '')
                    if not input_value:
                        continue
                    
                    input_id = inp.get('id', '')
                    input_name = inp.get('name', '')
                    
                    # Tìm label liên quan
                    related_label = None
                    
                    # Tìm label có for trùng với id
                    if input_id:
                        related_label = soup.find('label', attrs={'for': input_id})
                    
                    # Nếu không có, tìm label trong cấu trúc HTML gần input
                    if not related_label:
                        # Tìm trong parent
                        parent = inp.parent
                        if parent:
                            # Tìm label trước input trong cùng parent
                            related_label = parent.find('label')
                            
                            # Nếu không có, tìm trong div cha
                            if not related_label:
                                grandparent = parent.parent
                                if grandparent:
                                    related_label = grandparent.find('label')
                    
                    if related_label:
                        label_text = related_label.get_text(strip=True)
                        if 'tài khoản' in label_text.lower() or 'username' in label_text.lower():
                            if not tai_khoan:
                                tai_khoan = input_value
                        elif 'mật khẩu' in label_text.lower() or 'password' in label_text.lower():
                            if not mat_khau:
                                mat_khau = input_value
                    else:
                        # Dựa vào id hoặc name của input
                        if 'user' in input_id.lower() or 'user' in input_name.lower() or input_id == 'username' or input_name == 'username':
                            if not tai_khoan:
                                tai_khoan = input_value
                        elif 'pass' in input_id.lower() or 'pass' in input_name.lower() or input_id == 'password' or input_name == 'password':
                            if not mat_khau:
                                mat_khau = input_value
            
            # Lưu tài khoản và mật khẩu vào detail_data
            if tai_khoan:
                detail_data['tai_khoan'] = tai_khoan
            if mat_khau:
                detail_data['mat_khau'] = mat_khau
            
            print(f"  ✓ Đã lấy chi tiết đơn hàng {order_code}")
            if tai_khoan:
                print(f"    - Tài khoản: {tai_khoan}")
            if mat_khau:
                print(f"    - Mật khẩu: {'*' * len(mat_khau)}")
            
            return detail_data
            
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Lỗi khi lấy chi tiết đơn hàng {order_code}: {e}")
            return None
    
    def scrape_details_from_json(self, input_file='shopbopbop_data.json', output_file='shopbopbop_details.json'):
        """
        Đọc file JSON, lấy chi tiết từng đơn hàng và lưu vào file mới
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
        
        details = []
        total_count = 0
        
        # Xử lý accounts
        if 'accounts' in data and data['accounts']:
            print(f"\nXử lý {len(data['accounts'])} đơn hàng từ accounts...")
            for account in data['accounts']:
                if 'ma_don' in account and account['ma_don']:
                    total_count += 1
                    detail = self.scrape_order_detail(account['ma_don'], 'accounts')
                    if detail:
                        detail['account_info'] = account
                        details.append(detail)
                    time.sleep(1)
        
        # Xử lý accounts_v2
        if 'accounts_v2' in data and data['accounts_v2']:
            print(f"\nXử lý {len(data['accounts_v2'])} đơn hàng từ accounts-v2...")
            for account in data['accounts_v2']:
                if 'ma_don' in account and account['ma_don']:
                    total_count += 1
                    detail = self.scrape_order_detail(account['ma_don'], 'accounts-v2')
                    if detail:
                        detail['account_info'] = account
                        details.append(detail)
                    time.sleep(1)
        
        # Lưu kết quả
        output_data = {
            'total': len(details),
            'details': details
        }
        
        print(f"\nĐang lưu vào {output_file}...")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Đã lưu {len(details)}/{total_count} chi tiết đơn hàng vào {output_file}")
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
    print("SCRAPE ORDER DETAILS")
    print("=" * 50)
    print("\nLưu ý: Script này cần session đã đăng nhập.")
    print("Nếu chưa đăng nhập, hãy chạy scrape_shopbopbop.py trước.\n")
    
    input_file = input("Nhập tên file JSON đầu vào (mặc định: shopbopbop_data.json): ").strip()
    if not input_file:
        input_file = 'shopbopbop_data.json'
    
    output_file = input("Nhập tên file JSON đầu ra (mặc định: shopbopbop_details.json): ").strip()
    if not output_file:
        output_file = 'shopbopbop_details.json'
    
    scraper = DetailScraper()
    scraper.scrape_details_from_json(input_file, output_file)
    
    print("\n" + "=" * 50)
    print("HOÀN TẤT!")
    print("=" * 50)


if __name__ == "__main__":
    main()

