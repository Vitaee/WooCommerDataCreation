import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from googletrans import Translator
import json
import re
from urllib.parse import urljoin

# Constants
BASE_URL = "https://aurora-parts.ru"  # Base URL of the website
TARGET_PATH = "/land-rover/range-rover/range-rover-iv-2013/"  # Target path for Range Rover IV 2013


# Headers for HTTP requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36"
}

# Initialize the translator
translator = Translator()

async def fetch(session, url):
    """Fetch the content of the URL asynchronously."""
    try:
        async with session.get(url, headers=HEADERS) as response:
            response.raise_for_status()
            await asyncio.sleep(3)  # Add a delay to avoid overloading the server
            return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def parse_total_pages(html):
    """Parse the HTML to find the total number of pagination pages."""
    soup = BeautifulSoup(html, 'html.parser')
    pagination = soup.find('div', class_='pagination')  # Adjust based on actual pagination container
    if not pagination:
        return 1  # If no pagination found, assume only one page

    page_links = pagination.find_all('a', href=True)
    page_numbers = []
    for link in page_links:
        href = link['href']
        match = re.search(r'/page-(\d+)/', href)
        if match:
            page_numbers.append(int(match.group(1)))

    total_pages = max(page_numbers) if page_numbers else 1
    return total_pages

async def scrape_images(url, session):
    """Scrape the images from the product page."""
    html = await fetch(session, url)
    if not html:
        print(f"Failed to retrieve images for {url}.")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    imgs = soup.find_all('img', class_='good-slider__img js-zoom-img')
    image_urls = []
    for img in imgs:
        image_url = img.get('src')
        if image_url:
            image_urls.append(BASE_URL+ image_url)

    return image_urls
    
async def parse_products(html, session):
    """Parse the HTML and extract product details."""
    soup = BeautifulSoup(html, 'html.parser')
    products = []

    items_list = soup.find('div', class_='items-list__list is-active')
    if not items_list:
        print("No products list found on the page.")
        return products

    items = items_list.find_all('div', class_='items-list__item')
    for item in items:
        

        # Extract product name in Russian
        name_tag = item.find('a', class_='item__title')
        product_name_ru = name_tag.get_text(strip=True) if name_tag else ""
        product_href = name_tag['href'] if  name_tag else ""

        # Extract price in Russian
        price_tag = item.find('div', class_='item__price')
        price_ru = price_tag.get_text(strip=True) if price_tag else ""
        
        # Extract image URL

        imgs = await scrape_images(BASE_URL + product_href, session)
        

        products.append({
            "product_name_ru": product_name_ru,
            "product_price_ru": price_ru,
            "product_photo_url": imgs,
            "product_href": product_href
        })

    return products

async def translate_text(text, dest_language='az'):
    """Translate text to the destination language."""
    try:
        translated =  await translator.translate(text, dest=dest_language)
        return translated
    except Exception as e:
        print(f"Translation error for '{text}': {e}")
        return ""

def convert_price(price_str):
    """Convert price from RUB to AZN."""
    # Extract numeric value from price string
    match = re.search(r'([\d\s]+)', price_str)
    if match:
        rub = int(match.group(1).replace(' ', ''))
        azn = rub * 0.0171 
        azn = azn * 2
        # Format to two decimal places with comma as decimal separator
        return f"{azn:,.2f} AZN".replace(',', ' ').replace('.', ',')
    return ""

async def process_product(session, product):
    """Translate product details and convert price."""
    product_name_az =  await translate_text(product["product_name_ru"])
    product_name_az = product_name_az.text  
    product_price_az = convert_price(product["product_price_ru"])

    return {
        "product_name_ru": product["product_name_ru"],
        "product_price_ru": product["product_price_ru"],
        "product_photo_url": product["product_photo_url"],
        "product_name_az": product_name_az,
        "product_price_az": product_price_az,
        "product_href": product["product_href"]
    }

async def scrape_page(session, page_number, url):
    """Scrape a single page given the page number."""
    if page_number != 1:
        url = urljoin(url, f"page-{page_number}/?list_type=")
    
    print(f"Scraping page {page_number}: {url}")
    html = await fetch(session, url)
    if not html:
        print(f"Failed to retrieve page {page_number}.")
        return []

    products = await parse_products(html, session)
    print(f"Found {len(products)} products on page {page_number}.")
    return products


async def main():

    
    async with aiohttp.ClientSession() as session:

        brands = [
            {'href': 'https://aurora-parts.ru/land-rover/defender/defender-ii-2019-2023/', 'name': 'defender'},
            {'href': 'https://aurora-parts.ru/land-rover/discovery/discovery-iv-2009/', 'name': 'discovery'},
            {'href': 'https://aurora-parts.ru/land-rover/discovery/discovery-v-2017/', 'name': 'discovery_2017'},
            {'href': 'https://aurora-parts.ru/land-rover/land-rover-discovery-sport-14-/discovery-sport-2014/', 'name': 'discovery_sport'},
            {'href': 'https://aurora-parts.ru/land-rover/range-rover/range-rover-iv-2013/', 'name': 'range-rover'},
            {'href': 'https://aurora-parts.ru/land-rover/range-rover/range-rover-evoque-2011/', 'name': 'range-rover-evoque'},
            {'href': 'https://aurora-parts.ru/land-rover/range-rover-evoque/range-rover-evoque-ii-l551-2019/', 'name': 'range-rover_evoque_2019'},
            {'href': 'https://aurora-parts.ru/land-rover/range-rover-sport/range-rover-sport-1-l320-2005-2013/', 'name': 'range-rover-sport_2013'},
            {'href': 'https://aurora-parts.ru/land-rover/range-rover-sport/range-rover-sport-2013/', 'name': 'range-rover-sport_2013'},
            {'href': 'https://aurora-parts.ru/land-rover/range-rover-velar/range-rover-velar-l560-2017-/', 'name': 'range-rover-sport_2018'},
        ]

        for item in brands:
            brand_name = item['name']
            url = item['href']

            # Generate all page numbers
            page_numbers = list(range(1,  5))

            all_products = []

            # Create tasks for scraping all pages
            scrape_tasks = [scrape_page(session, page, url) for page in page_numbers]

            # Gather all scraped products
            pages_products = await asyncio.gather(*scrape_tasks)

            # Flatten the list of lists
            for products in pages_products:
                all_products.extend(products)

            if not all_products:
                print("No products found across all pages.")
                return

            print(f"Total products found: {len(all_products)}")

            # Process each product asynchronously
            process_tasks = [process_product(session, product) for product in all_products]
            processed_products = await asyncio.gather(*process_tasks)

            # Save to JSON file
            with open(f'products_auro_{brand_name}_new.json', 'w+', encoding='utf-8') as f:
                json.dump(processed_products, f, ensure_ascii=False, indent=4)

            break

        print("Data has been saved to products.json")


if __name__ == "__main__":
    asyncio.run(main())
