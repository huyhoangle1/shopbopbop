"""
Phiên bản sử dụng Selenium cho trường hợp website cần JavaScript để render
Cài đặt: pip install selenium beautifulsoup4
Tải ChromeDriver từ: https://chromedriver.chromium.org/
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time
import os

class ShopBopBopScraperSelenium:
    def __init__(self, headless=False):
        self.base_url = "https://shopbopbop.vn"
        self.driver = None
        self.data = {
            'accounts': None,
            'accounts_v2': None
        }
        self.headless = headless
        self._setup_driver()
    
    def _setup_driver(self):
        """
        Thiết lập Chrome WebDriver
        """
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            # Thử tìm chromedriver trong PATH hoặc thư mục hiện tại
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✓ Đã khởi tạo ChromeDriver thành công")
        except Exception as e:
            print(f"✗ Lỗi khi khởi tạo ChromeDriver: {e}")
            print("Vui lòng đảm bảo đã cài đặt ChromeDriver và thêm vào PATH")
            raise
    
    def login(self, username, password):
        """
        Đăng nhập vào hệ thống
        """
        print("Đang đăng nhập...")
        login_url = f"{self.base_url}/login"
        
        try:
            self.driver.get(login_url)
            time.sleep(2)  # Đợi trang load
            
            # Tìm các trường input username và password
            # Có thể là id, name, hoặc class
            username_selectors = [
                (By.ID, 'username'),
                (By.NAME, 'username'),
                (By.ID, 'email'),
                (By.NAME, 'email'),
                (By.CSS_SELECTOR, 'input[type="text"]'),
                (By.CSS_SELECTOR, 'input[type="email"]')
            ]
            
            password_selectors = [
                (By.ID, 'password'),
                (By.NAME, 'password'),
                (By.CSS_SELECTOR, 'input[type="password"]')
            ]
            
            username_field = None
            password_field = None
            
            # Tìm username field
            for by, value in username_selectors:
                try:
                    username_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, value))
                    )
                    break
                except:
                    continue
            
            # Tìm password field
            for by, value in password_selectors:
                try:
                    password_field = self.driver.find_element(by, value)
                    break
                except:
                    continue
            
            if not username_field or not password_field:
                print("✗ Không tìm thấy các trường đăng nhập")
                return False
            
            # Nhập thông tin
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(0.5)
            
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(0.5)
            
            # Tìm và click nút đăng nhập
            login_button_selectors = [
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.CSS_SELECTOR, 'input[type="submit"]'),
                (By.XPATH, '//button[contains(text(), "Đăng nhập")]'),
                (By.XPATH, '//button[contains(text(), "Login")]'),
                (By.XPATH, '//input[@value="Đăng nhập"]'),
                (By.XPATH, '//input[@value="Login")]')
            ]
            
            login_button = None
            for by, value in login_button_selectors:
                try:
                    login_button = self.driver.find_element(by, value)
                    break
                except:
                    continue
            
            if login_button:
                login_button.click()
            else:
                # Thử submit form
                password_field.submit()
            
            time.sleep(3)  # Đợi redirect hoặc load trang mới
            
            # Kiểm tra xem đăng nhập có thành công không
            current_url = self.driver.current_url
            if 'login' not in current_url.lower():
                print("✓ Đăng nhập thành công!")
                return True
            else:
                print("✗ Đăng nhập thất bại - vẫn ở trang login")
                return False
                
        except Exception as e:
            print(f"✗ Lỗi khi đăng nhập: {e}")
            return False
    
    def visit_home(self):
        """
        Truy cập trang chủ
        """
        print("Đang truy cập trang chủ...")
        home_url = f"{self.base_url}/home"
        try:
            self.driver.get(home_url)
            time.sleep(2)  # Đợi trang load
            print("✓ Đã truy cập trang chủ thành công!")
            return True
        except Exception as e:
            print(f"✗ Lỗi khi truy cập trang chủ: {e}")
            return False
    
    def scrape_accounts_page(self, url, page_name):
        """
        Lấy dữ liệu từ trang accounts
        """
        print(f"Đang lấy dữ liệu từ {page_name}...")
        try:
            self.driver.get(url)
            time.sleep(3)  # Đợi trang load và JavaScript render
            
            # Lấy HTML sau khi JavaScript đã render
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            accounts_data = []
            
            # Tìm bảng
            tables = soup.find_all('table')
            if tables:
                for table in tables:
                    rows = table.find_all('tr')
                    headers = []
                    if rows:
                        # Lấy header từ row đầu tiên
                        header_cells = rows[0].find_all(['th', 'td'])
                        headers = [cell.get_text(strip=True) for cell in header_cells]
                    
                    for row in rows[1:]:
                        cells = row.find_all(['td', 'th'])
                        account_info = {}
                        for i, cell in enumerate(cells):
                            text = cell.get_text(strip=True)
                            if i < len(headers) and headers[i]:
                                account_info[headers[i]] = text
                            else:
                                account_info[f'col_{i}'] = text
                        if account_info:
                            accounts_data.append(account_info)
            
            # Nếu không có bảng, tìm các card/item
            if not accounts_data:
                items = soup.find_all(['div', 'li'], class_=lambda x: x and (
                    'card' in x.lower() or 
                    'item' in x.lower() or 
                    'account' in x.lower() or
                    'order' in x.lower()
                ))
                for item in items:
                    text = item.get_text(separator='|', strip=True)
                    if text and len(text) > 10:  # Bỏ qua text quá ngắn
                        accounts_data.append({'content': text})
            
            # Nếu vẫn không có, lấy nội dung chính
            if not accounts_data:
                main_content = soup.find('main') or soup.find('div', class_=lambda x: x and (
                    'content' in x.lower() or 
                    'container' in x.lower() or
                    'account' in x.lower()
                ))
                if main_content:
                    accounts_data.append({
                        'raw_html': str(main_content),
                        'text': main_content.get_text(separator='\n', strip=True)
                    })
            
            print(f"✓ Đã lấy được {len(accounts_data)} mục dữ liệu từ {page_name}")
            return accounts_data
            
        except Exception as e:
            print(f"✗ Lỗi khi lấy dữ liệu từ {page_name}: {e}")
            return None
    
    def scrape_all(self, username, password):
        """
        Thực hiện toàn bộ quy trình: login -> home -> scrape 2 trang
        """
        try:
            # Bước 1: Đăng nhập
            if not self.login(username, password):
                print("Không thể đăng nhập. Dừng quy trình.")
                return False
            
            time.sleep(2)
            
            # Bước 2: Truy cập trang chủ
            if not self.visit_home():
                print("Cảnh báo: Không thể truy cập trang chủ, nhưng vẫn tiếp tục...")
            
            time.sleep(2)
            
            # Bước 3: Lấy dữ liệu từ trang accounts
            accounts_url = f"{self.base_url}/account/orders/accounts"
            self.data['accounts'] = self.scrape_accounts_page(accounts_url, "accounts")
            
            time.sleep(2)
            
            # Bước 4: Lấy dữ liệu từ trang accounts-v2
            accounts_v2_url = f"{self.base_url}/account/orders/accounts-v2"
            self.data['accounts_v2'] = self.scrape_accounts_page(accounts_v2_url, "accounts-v2")
            
            return True
        finally:
            self.close()
    
    def close(self):
        """
        Đóng browser
        """
        if self.driver:
            self.driver.quit()
            print("✓ Đã đóng browser")
    
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


def main():
    """
    Hàm main để chạy script
    """
    print("=" * 50)
    print("SHOPBOPBOP SCRAPER (SELENIUM)")
    print("=" * 50)
    
    # Nhập thông tin đăng nhập
    username = input("Nhập username/email: ").strip()
    password = input("Nhập password: ").strip()
    
    if not username or not password:
        print("✗ Username và password không được để trống!")
        return
    
    # Hỏi có muốn chạy headless không
    headless_input = input("Chạy ở chế độ headless? (y/n, mặc định: n): ").strip().lower()
    headless = headless_input == 'y'
    
    # Tạo scraper và chạy
    scraper = ShopBopBopScraperSelenium(headless=headless)
    
    try:
        if scraper.scrape_all(username, password):
            scraper.save_to_json()
            print("\n" + "=" * 50)
            print("HOÀN TẤT!")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("CÓ LỖI XẢY RA!")
            print("=" * 50)
    except Exception as e:
        print(f"\n✗ Lỗi: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()

