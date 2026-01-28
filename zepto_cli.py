


import argparse
import sys
from zepto_scraper_enhanced import EnhancedZeptoScraper


def main():
    parser = argparse.ArgumentParser(description='Scrape product data from Zepto mobile app')

    parser.add_argument(
        '-c', '--category',
        nargs='+',
        help='Category/categories to scrape (e.g., fruits vegetables)'
    )
    
    parser.add_argument(
        '-l', '--list-categories',
        action='store_true',
        help='List all available categories'
    )

    parser.add_argument(
        '--lat',
        type=float,
        help='Latitude for location-based products'
    )
    
    parser.add_argument(
        '--lon',
        type=float,
        help='Longitude for location-based products'
    )

    parser.add_argument(
        '-f', '--format',
        choices=['json', 'csv', 'both'],
        default='both',
        help='Output format (default: both)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='./output/',
        help='Output directory (default: ./output/)'
    )
    parser.add_argument(
        '--download-images', 
        action='store_true',
        help='Download product images'
    )
    
    parser.add_argument(
        '--image-dir',
        default='./images/',
        help='Directory to save images (default: ./images/)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay between requests in seconds (default: 0.5)'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=0,
        help='Maximum pages to scrape per category (0 = unlimited)'
    )
    parser.add_argument(
        '--config',
        default='config.ini',
        help='Configuration file path (default: config.ini)'
    )

    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Show analysis after scraping'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )
    args = parser.parse_args()

    try:
        scraper = EnhancedZeptoScraper(args.config)

        if args.lat:
            scraper.latitude = args.lat
        if args.lon:
            scraper.longitude = args.lon
        if args.format:
            scraper.output_format = args.format
        if args.output:
            scraper.output_directory = args.output
        if args.delay:
            scraper.rate_limit_delay = args.delay
        if args.max_pages:
            scraper.config['DEFAULT']['max_pages'] = str(args.max_pages)
        if args.download_images:
            scraper.download_images = True
        if args.image_dir:
            scraper.image_directory = args.image_dir
    except Exception as e:
        print(f"Error initializing scraper: {e}")
        sys.exit(1)

    if args.list_categories:
        print("\nAvailable categories:\n")
        categories = scraper.get_categories()
        
        if categories:
            for i, cat in enumerate(categories, 1):
                print(f"{i:3}. {cat.get('name', 'Unknown')}")
            print(f"\nTotal: {len(categories)} categories")
        else:
            print("Failed to fetch categories")
        
        sys.exit(0)

    if args.category:
        print("\nStarting scraping...")
        
        results = {}
        for category in args.category:
            print(f"\nScraping: {category}")
            
            products = scraper.scrape_category(category)
            results[category] = products
            
            print(f"Scraped {len(products)} products from {category}")
            

            if args.analyze and products:
                scraper.print_analysis(products)
        
        print("\nSummary:")
        
        total_products = sum(len(products) for products in results.values())
        print(f"Total categories scraped: {len(results)}")
        print(f"Total products scraped: {total_products}")
        
        for category, products in results.items():
            print(f"  {category}: {len(products)} products")
        
        print("\nData saved to: " + str(scraper.output_directory))
        
        if scraper.download_images:
            print("Images saved to: " + str(scraper.image_directory))
        
        print("")
    else:
        parser.print_help()
        print("\nPlease specify --category or --list-categories")
        sys.exit(1)

if __name__ == "__main__":
    main()
