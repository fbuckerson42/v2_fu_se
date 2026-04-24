from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)


class URLParser:
    
    @staticmethod
    def normalize_url(url: str) -> str:
        if '.keycrm.app' in url and '.api.keycrm.app' not in url:
            url = url.replace('.keycrm.app', '.api.keycrm.app')
            logger.debug(f"Converted web URL to API URL: {url}")
        
        return url
    
    @staticmethod
    def parse_keycrm_url(url: str) -> Dict[str, Any]:
        url = URLParser.normalize_url(url)
        
        if url.startswith('http'):
            parsed = urlparse(url)
            query_string = parsed.query
        elif '?' in url:
            query_string = url.split('?', 1)[1]
        else:
            query_string = url
        
        if not query_string:
            logger.warning("No query parameters found in URL")
            return {}
        
        params = parse_qs(query_string, keep_blank_values=True)
        
        result = {}
        for key, values in params.items():
            value = values[0] if values else ''
            
            if key in ['page', 'per_page']:
                try:
                    result[key] = int(value)
                except (ValueError, TypeError):
                    result[key] = value
            else:
                result[key] = value
        
        logger.info(f"Parsed {len(result)} parameters from URL")
        logger.debug(f"Parameters: {result}")
        
        return result
    
    @staticmethod
    def extract_filters(params: Dict[str, Any]) -> Dict[str, str]:
        filters = {k: v for k, v in params.items() if k.startswith('filters[')}
        logger.debug(f"Extracted {len(filters)} filter parameters")
        return filters
    
    @staticmethod
    def has_filters(url: str) -> bool:
        params = URLParser.parse_keycrm_url(url)
        return any(k.startswith('filters[') for k in params.keys())
    
    @staticmethod
    def get_filter_summary(url: str) -> str:
        params = URLParser.parse_keycrm_url(url)
        filters = URLParser.extract_filters(params)
        
        if not filters:
            return "No filters"
        
        summary_parts = []
        for key, value in filters.items():
            filter_name = key.replace('filters[', '').replace(']', '')
            summary_parts.append(f"{filter_name}: {value}")
        
        return " | ".join(summary_parts)
