

import requests
import json
import csv
import time
import configparser
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging
from pathlib import Path


class EnhancedZeptoScraper:
    
    def __init__(self, config_file: str = 'config.ini'):

        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        

        self._setup_logging()
        

        self.latitude = float(self.config['DEFAULT']['latitude'])
        self.longitude = float(self.config['DEFAULT']['longitude'])
        self.base_url = self.config['API']['base_url']
        self.rate_limit_delay = float(self.config['DEFAULT']['rate_limit_delay'])
        self.max_retries = int(self.config['DEFAULT']['max_retries'])
        self.timeout = int(self.config['DEFAULT']['timeout'])
        

        self.output_format = self.config['DEFAULT']['output_format']
        self.output_directory = Path(self.config['DEFAULT']['output_directory'])
        self.output_directory.mkdir(exist_ok=True)
        

        self.download_images = self.config['DEFAULT'].getboolean('download_images')
        if self.download_images:
            self.image_directory = Path(self.config['DEFAULT']['image_directory'])
            self.image_directory.mkdir(exist_ok=True)
        

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config['HEADERS']['User-Agent'],
            'Content-Type': self.config['HEADERS']['Content-Type'],
            'Accept': self.config['HEADERS']['Accept'],
            'app-version': self.config['HEADERS']['app-version'],
            'platform': self.config['HEADERS']['platform']
        })
        
        self.logger.info(f"Initialized scraper with config from {config_file}")
        self.logger.info(f"Location: ({self.latitude}, {self.longitude})")
    
    def _setup_logging(self):
        log_level = getattr(logging, self.config['DEFAULT']['log_level'])
        log_file = self.config['DEFAULT']['log_file']
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _make_request(self, url: str, params: dict = None, method: str = 'GET') -> Optional[dict]:
        for attempt in range(self.max_retries):
            try:
                if method == 'GET':
                    response = self.session.get(url, params=params, timeout=self.timeout)
                else:
                    response = self.session.post(url, json=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    time.sleep(self.rate_limit_delay)
                    return response.json()
                elif response.status_code == 429:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        
        return None
    
    def get_categories(self) -> List[Dict]:
        url = f"{self.base_url}{self.config['API']['categories_endpoint']}"
        params = {
            'latitude': self.latitude,
            'longitude': self.longitude
        }
        
        data = self._make_request(url, params)
        
        if data:
            categories = data.get('categories', [])
            self.logger.info(f"Found {len(categories)} categories")
            return categories
        
        return []
    
    def get_products_by_category(self, category_id: str, page: int = 1) -> List[Dict]:
        url = f"{self.base_url}{self.config['API']['products_endpoint']}"
        params = {
            'category_id': category_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'page': page,
            'limit': int(self.config['DEFAULT']['products_per_page'])
        }
        
        data = self._make_request(url, params)
        
        if data:
            products = data.get('products', [])
            self.logger.info(f"Fetched {len(products)} products (page {page})")
            return products
        
        return []
    
    def get_all_products_in_category(self, category_name: str) -> List[Dict]:

        categories = self.get_categories()
        category_id = None
        
        for cat in categories:
            if category_name.lower() in cat.get('name', '').lower():
                category_id = cat['id']
                self.logger.info(f"Found category: {cat['name']} (ID: {category_id})")
                break
        
        if not category_id:
            self.logger.error(f"Category '{category_name}' not found")
            return []
        

        all_products = []
        page = 1
        max_pages = int(self.config['DEFAULT']['max_pages'])
        
        while True:
            products = self.get_products_by_category(category_id, page)
            
            if not products:
                break
            
            all_products.extend(products)
            

            if max_pages > 0 and page >= max_pages:
                self.logger.info(f"Reached max pages limit: {max_pages}")
                break
            

            if len(products) < int(self.config['DEFAULT']['products_per_page']):
                break
            
            page += 1
        
        self.logger.info(f"Total products: {len(all_products)}")
        return all_products
    
    def extract_product_details(self, product: Dict) -> Dict:
        details = {
            'product_id': product.get('id', 'N/A'),
            'name': product.get('name', 'N/A'),
            'brand': product.get('brand', 'N/A'),
            'price': float(product.get('price', 0)),
            'mrp': float(product.get('mrp', 0)),
            'weight': product.get('weight', 'N/A'),
            'unit': product.get('unit', 'N/A'),
            'quantity': product.get('quantity', 'N/A'),
            'availability': product.get('in_stock', True),
            'image_url': product.get('image_url', 'N/A'),
            'thumbnail_url': product.get('thumbnail_url', 'N/A'),
            'category': product.get('category', 'N/A'),
            'subcategory': product.get('subcategory', 'N/A'),
            'description': product.get('description', 'N/A'),
            'rating': float(product.get('rating', 0)),
            'review_count': int(product.get('review_count', 0)),
            'tags': ', '.join(product.get('tags', [])),
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        

        if details['mrp'] > 0:
            details['discount_percent'] = round(
                ((details['mrp'] - details['price']) / details['mrp']) * 100, 2
            )
        else:
            details['discount_percent'] = 0
        

        if self.download_images and details['image_url'] != 'N/A':
            self._download_image(details['product_id'], details['image_url'])
        
        return details
    
    def _download_image(self, product_id: str, image_url):
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                ext = image_url.split('.')[-1].split('?')[0]
                filename = self.image_directory / f"{product_id}.{ext}"
                
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                self.logger.debug(f"Downloaded image: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to download image: {e}")
    
    def scrape_category(self, category_name: str) -> List[Dict]:
        self.logger.info(f"Scraping category: {category_name}")
        
        raw_products = self.get_all_products_in_category(category_name)
        
        if not raw_products:
            return []
        
        products = [self.extract_product_details(p) for p in raw_products]
        

        self._save_products(products, category_name)
        
        return products
    
    def scrape_multiple_categories(self, categories: List[str] = None) -> Dict[str, List[Dict]]:
        if categories is None:
            categories = [c.strip() for c in self.config['DEFAULT']['categories'].split(',')]
        
        results = {}
        
        for category in categories:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Scraping: {category}")
            self.logger.info(f"{'='*60}")
            
            products = self.scrape_category(category)
            results[category] = products
            
            self.logger.info(f"Completed: {len(products)} products from {category}")
        
        return results
    
    def _save_products(self, products: List[Dict], category_name: str):
        if not products:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"zepto_{category_name}_{timestamp}"
        

        if self.output_format in ['json', 'both']:
            json_file = self.output_directory / f"{base_filename}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved JSON: {json_file}")
        

        if self.output_format in ['csv', 'both']:
            csv_file = self.output_directory / f"{base_filename}.csv"
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=products[0].keys())
                writer.writeheader()
                writer.writerows(products)
            self.logger.info(f"Saved CSV: {csv_file}")
    
    def analyze_products(self, products: List[Dict]) -> Dict:
        if not products:
            return {}
        
        analysis = {
            'total_products': len(products),
            'available_products': sum(1 for p in products if p['availability']),
            'unavailable_products': sum(1 for p in products if not p['availability']),
            'average_price': round(sum(p['price'] for p in products) / len(products), 2),
            'average_mrp': round(sum(p['mrp'] for p in products) / len(products), 2),
            'average_discount': round(sum(p['discount_percent'] for p in products) / len(products), 2),
            'max_price': max(p['price'] for p in products),
            'min_price': min(p['price'] for p in products),
            'brands': list(set(p['brand'] for p in products if p['brand'] != 'N/A')),
            'categories': list(set(p['category'] for p in products if p['category'] != 'N/A'))
        }
        

        analysis['price_ranges'] = {
            'under_50': sum(1 for p in products if p['price'] < 50),
            '50_100': sum(1 for p in products if 50 <= p['price'] < 100),
            '100_200': sum(1 for p in products if 100 <= p['price'] < 200),
            'over_200': sum(1 for p in products if p['price'] >= 200)
        }
        
        return analysis
    
    def print_analysis(self, products: List[Dict]):
        analysis = self.analyze_products(products)
        
        print("\nAnalysis:")
        print(f"Total Products: {analysis['total_products']}")
        print(f"Available: {analysis['available_products']}")
        print(f"Unavailable: {analysis['unavailable_products']}")
        print(f"\nPricing:")
        print(f"  Average Price: ₹{analysis['average_price']}")
        print(f"  Average MRP: ₹{analysis['average_mrp']}")
        print(f"  Average Discount: {analysis['average_discount']}%")
        print(f"  Price Range: ₹{analysis['min_price']} - ₹{analysis['max_price']}")
        print(f"\nPrice Distribution:")
        print(f"  Under ₹50: {analysis['price_ranges']['under_50']}")
        print(f"  ₹50-100: {analysis['price_ranges']['50_100']}")
        print(f"  ₹100-200: {analysis['price_ranges']['100_200']}")
        print(f"  Over ₹200: {analysis['price_ranges']['over_200']}")
        print(f"\nBrands: {len(analysis['brands'])}")
        print(f"Categories: {len(analysis['categories'])}")
        print("")


def main():
    print("Starting scraper...")
    print()
    

    scraper = EnhancedZeptoScraper('config.ini')
    

    results = scraper.scrape_multiple_categories()
    

    for category, products in results.items():
        if products:
            scraper.print_analysis(products)
    
    print("\nScraping completed!")


if __name__ == "__main__":
    main()
