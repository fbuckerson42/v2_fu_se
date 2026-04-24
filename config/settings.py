import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Settings:
    DATABASE_URL: str = os.getenv('DATABASE_URL', '')
    
    KEYCRM_BASE_URL: str = os.getenv('KEYCRM_BASE_URL', '')
    KEYCRM_WEB_URL: str = os.getenv('KEYCRM_WEB_URL', '')
    KEYCRM_BEARER_TOKEN: str = os.getenv('KEYCRM_BEARER_TOKEN', '')
    KEYCRM_LOGIN: str = os.getenv('KEYCRM_LOGIN', '')
    KEYCRM_PASSWORD: str = os.getenv('KEYCRM_PASSWORD', '')
    
    GITHUB_TOKEN: str = os.getenv('GITHUB_TOKEN', '')
    GITHUB_REPOSITORY: str = os.getenv('GITHUB_REPOSITORY', '')
    GITHUB_ACTIONS: bool = os.getenv('GITHUB_ACTIONS', 'false') == 'true'
    
    ORDERS_PER_PAGE: int = int(os.getenv('ORDERS_PER_PAGE', '50'))
    REQUEST_TIMEOUT: int = int(os.getenv('REQUEST_TIMEOUT', '30'))
    REQUEST_DELAY: float = float(os.getenv('REQUEST_DELAY', '1'))
    
    AUTO_REFRESH_TOKEN: bool = os.getenv('AUTO_REFRESH_TOKEN', 'true').lower() == 'true'
    
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'scraper.log')
    
    PRP_FIELD_ID: int = 121
    
    def validate(self) -> bool:
        errors = []
        
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is not set")
        
        if not self.KEYCRM_BASE_URL:
            errors.append("KEYCRM_BASE_URL is not set")
        
        if not self.KEYCRM_WEB_URL:
            errors.append("KEYCRM_WEB_URL is not set")
        
        if not os.getenv('KEYCRM_FILTERS_URL'):
            errors.append(
                "KEYCRM_FILTERS_URL is not set. "
                "This is required to specify which orders to scrape. "
                "Example: https://your-company.keycrm.app/orders?filters[manager_id]=312&filters[status_id]=36"
            )
        
        if not self.KEYCRM_LOGIN or not self.KEYCRM_PASSWORD:
            errors.append("KEYCRM_LOGIN and KEYCRM_PASSWORD must be set for authentication")
        
        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def __repr__(self) -> str:
        return (
            f"Settings(\n"
            f"  DATABASE_URL={'***' if self.DATABASE_URL else 'NOT SET'},\n"
            f"  KEYCRM_BASE_URL={self.KEYCRM_BASE_URL or 'NOT SET'},\n"
            f"  KEYCRM_BEARER_TOKEN={'***' if self.KEYCRM_BEARER_TOKEN else 'NOT SET'},\n"
            f"  KEYCRM_LOGIN={'***' if self.KEYCRM_LOGIN else 'NOT SET'},\n"
            f"  AUTO_REFRESH_TOKEN={self.AUTO_REFRESH_TOKEN},\n"
            f"  ORDERS_PER_PAGE={self.ORDERS_PER_PAGE},\n"
            f"  REQUEST_TIMEOUT={self.REQUEST_TIMEOUT},\n"
            f"  LOG_LEVEL={self.LOG_LEVEL}\n"
            f")"
        )


settings = Settings()
