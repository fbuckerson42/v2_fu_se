from playwright.sync_api import sync_playwright, Page, Browser
import logging
import time
import os
from typing import Optional
from config.settings import settings
from database.connection import DatabaseConnection
from database.token_queries import TokenQueries

logger = logging.getLogger(__name__)


class KeyCRMAuth:
    
    def __init__(self, login: Optional[str] = None, password: Optional[str] = None, db: Optional[DatabaseConnection] = None):
        self.login = login or settings.KEYCRM_LOGIN
        self.password = password or settings.KEYCRM_PASSWORD
        self.web_url = settings.KEYCRM_WEB_URL
        self.db = db
        
        if not self.login or not self.password:
            raise ValueError("Login and password are required. Set KEYCRM_LOGIN and KEYCRM_PASSWORD in .env")
    
    def extract_bearer_token(self) -> str:
        logger.info("Starting authentication process...")
        
        is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=is_github_actions)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='uk-UA',
                timezone_id='Europe/Kiev',
                extra_http_headers={
                    'Accept-Language': 'uk,en-US;q=0.9,en;q=0.8',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                }
            )
            page = context.new_page()
            
            errors = []
            responses = []
            
            def log_response(response):
                if 'login' in response.url.lower() or 'auth' in response.url.lower() or 'api' in response.url.lower():
                    responses.append(f"{response.status} {response.url}")
                    if response.status >= 400:
                        errors.append(f"Error response: {response.status} {response.url}")
            
            page.on('response', log_response)
            
            try:
                logger.info(f"Navigating to {self.web_url}/login")
                page.goto(f"{self.web_url}/login", wait_until="load")
                
                if os.getenv('GITHUB_ACTIONS') == 'true':
                    page.screenshot(path='01_login_page.png')
                    with open('01_login_page.html', 'w', encoding='utf-8') as f:
                        f.write(page.content())
                    logger.info("Saved screenshot and HTML: 01_login_page.png, 01_login_page.html")
                
                logger.info("Waiting for login form...")
                page.wait_for_selector('input', timeout=10000)
                
                if os.getenv('GITHUB_ACTIONS') == 'true':
                    page.screenshot(path='02_form_visible.png')
                    logger.info("Saved screenshot: 02_form_visible.png")
                
                logger.info("Filling login form...")
                email_input = page.locator('input').first
                password_input = page.locator('input[type="password"]').first
                
                email_input.fill(self.login)
                password_input.fill(self.password)
                
                if os.getenv('GITHUB_ACTIONS') == 'true':
                    page.screenshot(path='03_credentials_filled.png')
                    logger.info("Saved screenshot: 03_credentials_filled.png")
                
                logger.info("Submitting login form...")
                page.locator('input[type="password"]').press('Enter')
                
                logger.info("Waiting for response...")
                page.wait_for_timeout(5000)
                
                current_url = page.url
                logger.info(f"Current URL after login: {current_url}")
                
                for resp in responses:
                    logger.info(f"API Response: {resp}")
                
                if errors:
                    for err in errors:
                        logger.error(err)
                
                if '/login' in current_url:
                    page.screenshot(path='04_login_failed.png')
                    with open('04_login_failed.html', 'w', encoding='utf-8') as f:
                        f.write(page.content())
                    
                    page_content = page.content()
                    with open('04_login_failed_full.html', 'w', encoding='utf-8') as f:
                        f.write(page_content)
                    
                    error_elem = page.locator('text=Помилка, text=Error, text=Invalid, text=Невірн').first
                    if error_elem.count() > 0:
                        error_msg = error_elem.text_content()
                    else:
                        error_msg = "No visible error message"
                    
                    logger.error(f"Still on login page. Error: {error_msg}")
                    logger.info(f"Page content length: {len(page_content)} chars")
                    raise Exception(f"Login failed: {error_msg}")
                
                logger.info("Login successful, waiting for API requests...")
                time.sleep(3)
                
                logger.info("Trying to extract token from network requests first...")
                token = self._extract_token_from_network(page)
                token_key = "from_network"
                
                if not token:
                    logger.info("Network extraction failed, trying localStorage...")
                    token = self._extract_token_from_storage(page)
                    token_key = "from_storage"
                
                if not token:
                    raise Exception("Failed to extract Bearer token")
                
                logger.info("Successfully extracted Bearer token")
                logger.info(f"Token key: {token_key}, length: {len(token) if token else 0}")
                return token
                
            except Exception as e:
                logger.error(f"Authentication failed: {e}")
                raise
            finally:
                browser.close()
    
    def _extract_token_from_storage(self, page: Page) -> Optional[str]:
        try:
            logger.info("Trying to extract token from localStorage...")
            
            all_keys = page.evaluate("() => Object.keys(localStorage)")
            logger.info(f"localStorage keys: {all_keys}")
            
            all_storage = page.evaluate("() => { const r = {}; for(const k of Object.keys(localStorage)) { try { r[k] = localStorage.getItem(k)?.slice(0,100) || 'N/A' } catch(e) { r[k] = 'ERROR' } } return r; }")
            logger.info(f"localStorage content preview: {all_storage}")
            
            token = None
            token_key = None
            
            for key in all_keys:
                if any(kw in key.lower() for kw in ['token', 'auth', 'access', 'bearer']):
                    value = page.evaluate(f"(k) => localStorage.getItem(k)", key)
                    if value:
                        token = value
                        token_key = key
                        logger.info(f"Found token in key: {key}")
                        break
            
            if not token:
                for key in all_keys:
                    value = page.evaluate(f"(k) => localStorage.getItem(k)", key)
                    if value and len(value) > 20:
                        try:
                            import base64
                            decoded = base64.b64decode(value[:50]).decode('utf-8', errors='ignore')
                            if 'eyJ' in value or 'jwt' in decoded.lower():
                                token = value
                                token_key = key
                                logger.info(f"Found JWT-like token in key: {key}")
                                break
                        except:
                            pass
            
            if token:
                logger.info(f"Token extracted from key: {token_key}")
                return token
            
        except Exception as e:
            logger.warning(f"Failed to extract token from localStorage: {e}")
        
        return None
    
    def _extract_token_from_network(self, page: Page) -> Optional[str]:
        try:
            logger.info("Trying to extract token from network requests...")
            
            captured_token = None
            captured_requests = []
            
            def handle_request(request):
                nonlocal captured_token
                auth_header = request.headers.get('authorization', '')
                if auth_header.startswith('Bearer '):
                    captured_token = auth_header.replace('Bearer ', '')
                    captured_requests.append(f"Bearer request: {request.method} {request.url}")
            
            def handle_response(response):
                if response.status == 200 and 'api.keycrm.app' in response.url:
                    try:
                        body = response.text()
                        if body and len(body) > 100:
                            captured_requests.append(f"200 response from {response.url}: {body[:200]}")
                    except:
                        pass
            
            page.on('request', handle_request)
            page.on('response', handle_response)
            
            logger.info("Navigating to orders page to capture API requests...")
            page.goto(f"{self.web_url}/orders", wait_until="load")
            time.sleep(3)
            
            logger.info(f"Captured {len(captured_requests)} relevant requests")
            for req in captured_requests[:5]:
                logger.info(f"  {req[:200]}")
            
            if captured_token:
                logger.info(f"Token found in Authorization header: length {len(captured_token)}")
                return captured_token
            
        except Exception as e:
            logger.warning(f"Failed to extract token from network: {e}")
        
        return None
    
    def save_token_to_db(self, token: str) -> None:
        if not self.db:
            logger.warning("No database connection provided, skipping token save to DB")
            return
        
        try:
            token_queries = TokenQueries(self.db)
            token_queries.save_token(token, token_type='bearer_token')
            logger.info("Bearer token saved to database")
        except Exception as e:
            logger.error(f"Failed to save token to database: {e}")
            raise
    
    def save_token_to_env(self, token: str) -> None:
        try:
            env_file = '.env'
            
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            token_found = False
            for i, line in enumerate(lines):
                if line.startswith('KEYCRM_BEARER_TOKEN='):
                    lines[i] = f'KEYCRM_BEARER_TOKEN={token}\n'
                    token_found = True
                    break
            
            if not token_found:
                lines.append(f'\nKEYCRM_BEARER_TOKEN={token}\n')
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            logger.info(f"Bearer token saved to {env_file}")
            
        except Exception as e:
            logger.error(f"Failed to save token to .env: {e}")
            raise


def authenticate_and_save(db: Optional[DatabaseConnection] = None) -> str:
    auth = KeyCRMAuth(db=db)
    token = auth.extract_bearer_token()
    
    if db:
        auth.save_token_to_db(token)
    else:
        auth.save_token_to_env(token)
    
    return token
