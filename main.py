import sys
import os
import argparse
from typing import Optional, Dict, Any
from utils.logger import logger
from config.settings import settings
from database.connection import DatabaseConnection
from database.queries import OrderQueries
from scraper.auth import authenticate_and_save
from scraper.api_client import KeyCRMClient, OrdersScraper
from scraper.parser import OrderParser
from scraper.url_parser import URLParser


def run_migration(db: DatabaseConnection) -> None:
    logger.info("Running database migrations...")
    
    migrations = [
        'database/migrations/001_create_orders_table.sql',
        'database/migrations/002_create_tokens_table.sql'
    ]
    
    try:
        for migration_file in migrations:
            logger.info(f"Running {migration_file}...")
            db.run_migration(migration_file)
        logger.info("All migrations completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def authenticate() -> str:
    logger.info("Starting authentication...")
    try:
        with DatabaseConnection() as db:
            token = authenticate_and_save(db=db)
            logger.info("Authentication successful")
            return token
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise


def scrape_orders(max_pages: Optional[int] = None, filters_url: Optional[str] = None, max_retries: int = 1) -> None:
    if not settings.validate():
        logger.error("Invalid configuration. Please check .env file")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("KeyCRM Scraper Started")
    logger.info("=" * 60)
    
    filters_url = filters_url or os.getenv('KEYCRM_FILTERS_URL')
    
    if not filters_url:
        logger.error("=" * 60)
        logger.error("ERROR: KEYCRM_FILTERS_URL is required!")
        logger.error("=" * 60)
        sys.exit(1)
    
    logger.info(f"Parsing filters from URL...")
    custom_filters = URLParser.parse_keycrm_url(filters_url)
    filter_summary = URLParser.get_filter_summary(filters_url)
    logger.info(f"Filters: {filter_summary}")
    
    stats = {
        'total_fetched': 0,
        'inserted': 0,
        'updated': 0,
        'errors': 0
    }
    
    for attempt in range(max_retries + 1):
        try:
            logger.info("Connecting to database...")
            with DatabaseConnection() as db:
                queries = OrderQueries(db)
                
                logger.info("Connecting to KeyCRM API...")
                with KeyCRMClient(db=db) as client:
                    logger.info("Loading statuses from API...")
                    OrderParser.load_statuses_from_api(client)
                    
                    scraper = OrdersScraper(client)
                    
                    logger.info(f"Starting to scrape orders (max_pages={max_pages or 'all'})...")
                    orders_json = scraper.scrape_all_orders(max_pages=max_pages, custom_filters=custom_filters)
                    stats['total_fetched'] = len(orders_json)
                    
                    if not orders_json:
                        logger.warning("No orders fetched")
                        return
                    
                    logger.info(f"Processing {len(orders_json)} orders...")
                    all_orders_data = []
                    for i, order_json in enumerate(orders_json, 1):
                        try:
                            order_data = OrderParser.parse_order(order_json)
                            all_orders_data.append(order_data)
                            
                            if (i + 1) % 100 == 0:
                                logger.info(f"Parsed {i + 1}/{len(orders_json)} orders...")
                        
                        except Exception as e:
                            stats['errors'] += 1
                            order_id = order_json.get('id', 'unknown')
                            logger.error(f"Failed to parse order {order_id}: {e}")
                            continue
                    
                    logger.info(f"Saving {len(all_orders_data)} orders to database...")
                    batch_stats = queries.batch_upsert_orders(all_orders_data)
                    stats['inserted'] = 0
                    stats['updated'] = batch_stats.get('updated', len(all_orders_data))
                    stats['errors'] += batch_stats.get('errors', 0)
                    
                    db.commit()
                    logger.info("All orders saved to database")
            
            logger.info("=" * 60)
            logger.info("Scraping completed successfully!")
            logger.info("=" * 60)
            logger.info(f"Total fetched: {stats['total_fetched']}")
            logger.info(f"Inserted: {stats['inserted']}")
            logger.info(f"Updated: {stats['updated']}")
            logger.info(f"Errors: {stats['errors']}")
            logger.info("=" * 60)
            return
            
        except Exception as e:
            error_str = str(e)
            is_401 = '401' in error_str or 'Unauthorized' in error_str
            
            if is_401 and attempt < max_retries:
                logger.warning(f"401 Unauthorized received (attempt {attempt + 1}/{max_retries + 1}). Running authentication...")
                try:
                    with DatabaseConnection() as db:
                        token = authenticate_and_save(db=db)
                        logger.info(f"New token obtained, retrying scrape...")
                except Exception as auth_err:
                    logger.error(f"Authentication failed: {auth_err}")
                    if attempt == max_retries:
                        raise
            else:
                logger.error(f"Scraping failed: {e}")
                raise


def show_statistics() -> None:
    logger.info("Fetching database statistics...")
    
    try:
        with DatabaseConnection() as db:
            queries = OrderQueries(db)
            stats = queries.get_statistics()
            
            logger.info("=" * 60)
            logger.info("Database Statistics")
            logger.info("=" * 60)
            logger.info(f"Total orders: {stats['total_orders']}")
            logger.info(f"Orders with PRP: {stats['orders_with_prp']}")
            logger.info(f"Orders without PRP: {stats['orders_without_prp']}")
            logger.info(f"Total amount: {stats['total_amount']:.2f} UAH")
            logger.info(f"Last scraped: {stats['last_scraped']}")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error(f"Failed to fetch statistics: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description='KeyCRM Scraper - Scrape orders from KeyCRM to PostgreSQL'
    )
    
    parser.add_argument(
        'command',
        choices=['scrape', 'auth', 'migrate', 'stats'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=None,
        help='Maximum pages to scrape (default: all)'
    )
    
    parser.add_argument(
        '--url',
        type=str,
        default=None,
        help='KeyCRM URL with filters (e.g., "https://your-company.keycrm.app/orders?filters[manager_id]=120")'
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == 'auth':
            authenticate()
            
        elif args.command == 'migrate':
            with DatabaseConnection() as db:
                run_migration(db)
        
        elif args.command == 'scrape':
            scrape_orders(max_pages=args.max_pages, filters_url=args.url)
        
        elif args.command == 'stats':
            show_statistics()
        
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
