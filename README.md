# Mobile App Product Scraper

A complete solution for extracting product data from mobile grocery delivery apps like Zepto and Instamart.

## Files Included

### 1. zepto_cli.py
Command-line interface tool for easy scraping operations.

**Features:**
- Scrape specific product categories (fruits, vegetables, dairy, etc.)
- Multiple output formats (CSV, JSON, or both)
- Location-based scraping with custom coordinates
- Image downloading capability
- Built-in data analysis
- Rate limiting for ethical scraping

**Usage Examples:**
```bash
# Scrape fruits category
python zepto_cli.py --category fruits

# Scrape multiple categories
python zepto_cli.py --category fruits vegetables dairy

# Scrape with custom location (Mumbai)
python zepto_cli.py --category fruits --lat 19.0760 --lon 72.8777

# Download product images
python zepto_cli.py --category fruits --download-images

# Save only as JSON
python zepto_cli.py --category fruits --format json

# Show data analysis
python zepto_cli.py --category fruits --analyze

# List all available categories
python zepto_cli.py --list-categories
```

### 2. zepto_scraper_enhanced.py
Core scraping engine with advanced features and configuration support.

**Features:**
- Configuration file support (config.ini)
- Advanced error handling and retry logic
- Session management with custom headers
- Pagination handling for large datasets
- Structured data extraction
- Comprehensive logging system
- Data analysis and statistics

**Key Classes:**
- `EnhancedZeptoScraper`: Main scraper class with all functionality

## Installation

1. Install required dependencies:
```bash
pip install requests configparser
```

2. Ensure both Python files are in the same directory

3. (Optional) Customize settings in `config.ini`

## Configuration

The scraper uses `config.ini` for settings:
- Location coordinates
- API endpoints
- Rate limiting
- Output preferences
- Header configurations

## Output Data

Both tools extract comprehensive product information:

**Product Details:**
- Product ID and name
- Brand information
- Current price and MRP
- Discount percentage
- Weight/quantity
- Availability status
- Product images
- Category and subcategory
- Ratings and review counts
- Tags and descriptions

**Output Formats:**
- **CSV**: Spreadsheet-friendly format
- **JSON**: Structured data format
- **Images**: Downloaded product images (optional)

## Sample Output

### CSV Format:
```
product_id,name,brand,price,mrp,discount_percent,weight,unit,availability,image_url,category,rating,review_count,scraped_at
12345,Fresh Apples,BrandX,120,150,20.0,1,kg,True,https://image.url,Fruits,4.5,123,2026-01-28 10:30:00
```

### JSON Format:
```json
[
  {
    "product_id": "12345",
    "name": "Fresh Apples",
    "brand": "BrandX",
    "price": 120,
    "mrp": 150,
    "discount_percent": 20.0,
    "weight": "1",
    "unit": "kg",
    "availability": true,
    "image_url": "https://image.url",
    "category": "Fruits",
    "rating": 4.5,
    "review_count": 123,
    "scraped_at": "2026-01-28 10:30:00"
  }
]
```

## Data Analysis Features

The tools provide built-in analysis:
- Total product counts
- Availability statistics
- Price range analysis
- Average pricing information
- Discount distribution
- Brand diversity metrics
- Category breakdown

## Ethical Usage

- Implements rate limiting to avoid server overload
- Respects API terms of service
- Includes appropriate delays between requests
- Handles errors gracefully
- Provides transparent logging

## Error Handling

- Automatic retry logic for failed requests
- Graceful handling of network issues
- Detailed error logging
- Fallback mechanisms for missing data

## Performance

- Efficient pagination handling
- Concurrent request management
- Memory-optimized processing
- Configurable rate limiting

## Requirements

- Python 3.7+
- requests library
- configparser library
- Internet connection
- Valid location coordinates

## Note

This tool is designed for educational and research purposes. Users should:
1. Review the target app's Terms of Service
2. Use responsibly with appropriate rate limits
3. Respect data privacy and usage rights
4. Comply with applicable laws and regulations

## Support

For issues or questions:
1. Check the configuration file settings
2. Verify internet connectivity
3. Confirm location coordinates are valid
4. Review the log files for detailed error information
