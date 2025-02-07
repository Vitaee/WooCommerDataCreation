import asyncio
import aiohttp
import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup
import json
import re
from googletrans import Translator


# Initialize global translator
translator = Translator()

async def fetch_html(session: ClientSession, url: str) -> str:
    """Fetch the HTML text of a given URL using an aiohttp session."""
    async with session.get(url) as response:
        await asyncio.sleep(4)
        response.raise_for_status()
        return await response.text()

def extract_products_from_soup(soup: BeautifulSoup) -> list:
    """
    Extract product data (Russian name, Russian price, image URL) from the soup
    and return as a list of dicts.
    """
    products_data = []

    # Each product block has 'div' with class 'parts-list-item'
    product_divs = soup.find_all('div', class_='parts-list-item')

    
    for product in product_divs:
        # Product name (ru)
        name_div = product.find('div', class_='font-weight-bold mb-0')
        if not name_div:
            continue
        product_name_ru = name_div.get_text(strip=True)

        # Product href 
        product_href = product.find('a', class_='link-dark')['href']

        
        # Product price (ru)
        price_block = product.find('div', class_='price-main')
        if price_block:
            price_ru_raw = price_block.get_text(strip=True)
        else:
            price_ru_raw = ""



        
        # For images
        imgs = product.find('div',class_='media').find_all('div', class_='d-none')
        product_photo_url = []

        for item in imgs:
            for img in item.find_all('img'):
                try:
                    product_photo_url.append(img['data-src'])
                except: 
                    pass

        # Clean up the price text (e.g. "53 BYN" -> "53 BYN")
        product_price_ru = re.sub(r'\s+', ' ', price_ru_raw)

        products_data.append({
            "product_name_ru": product_name_ru,
            "product_price_ru": product_price_ru,
            "product_photo_url": product_photo_url,
            "product_href": product_href
        })
        
    return products_data

def convert_price(price_str):
    """Convert price from RUB to AZN."""
    # Extract numeric value from price string
    match = re.search(r'([\d\s]+)', price_str)
    if match:
        rub = int(match.group(1).replace(' ', ''))
        azn = rub *0.0171
        azn = azn * 2
        # Format to two decimal places with comma as decimal separator
        return f"{azn:,.2f} AZN".replace(',', ' ').replace('.', ',')
    return ""

async def translate_text(text, dest_language='az'):
    """Translate text to the destination language."""
    try:
        translated =  await translator.translate(text, dest=dest_language)
        return translated
    except Exception as e:
        print(f"Translation error for '{text}': {e}")
        return ""

async def process_product_data(product_data: dict) -> dict:
    """
    Translate Russian product name to Azerbaijani, 
    convert and "translate" the price into Azerbaijani, and return the enriched dict.
    """
    # Translate product name (ru -> az)
    product_name_ru = product_data["product_name_ru"]
    product_price_ru = product_data["product_price_ru"]
    product_photo_url = product_data["product_photo_url"]

    # We attempt translation. If there's an issue, we'll use the original text.
    product_name_az =  await translate_text(product_data["product_name_ru"])
    product_name_az = product_name_az.text  

    # Convert price RU -> AZN
    product_price_az = convert_price(product_price_ru)

    # Build final record
    return {
        "product_name_ru": product_name_ru,
        "product_price_ru": product_price_ru,
        "product_photo_url": product_photo_url,
        "product_name_az": product_name_az,
        "product_price_az": product_price_az,
        "product_href": product_data["product_href"]
    }

async def scrape_page(session: ClientSession, page_url: str) -> list:
    """Fetch the page, parse out products, and return processed product dictionaries."""
    html = await fetch_html(session, page_url)
    soup = BeautifulSoup(html, 'html.parser')

    # Extract basic product data
    products_data = extract_products_from_soup(soup)

    # Enrich each product (translation + currency conversion)
    tasks = [process_product_data(p) for p in products_data]
    processed_products = await asyncio.gather(*tasks)
    return processed_products

async def main():
    base_url_list = [
        "https://carro.by/parts/brand_land-rover/",
        "https://carro.by/parts/brand_land-rover/model_defender",
        "https://carro.by/parts/brand_land-rover/model_discovery-sport",
        "https://carro.by/parts/brand_land-rover/model_range-rover",
        "https://carro.by/parts/brand_land-rover/model_range-rover-sport",
        "https://carro.by/parts/brand_land-rover/model_discovery",
        "https://carro.by/parts/brand_land-rover/model_freelander",
        "https://carro.by/parts/brand_land-rover/model_range-rover-evoque",
        "https://carro.by/parts/brand_land-rover/model_range-rover-velar"

    ]
    params = {
        "page": 1,
        "per-page": 30
    }

    all_results = []
    page_limit = 30

    async with aiohttp.ClientSession() as session:
        for base_url in base_url_list:
            # Construct page URL with current pagination
            page_url = f"{base_url}?page={params['page']}&per-page={params['per-page']}"

            print(f"Scraping page {params['page']}...")

            # Scrape current page
            products_on_page = await scrape_page(session, page_url)

            if not products_on_page:
                print("No more products found or end of pages.")
                break

            all_results.extend(products_on_page)

            # Increment page for next iteration
            params["page"] += 1

            # Safety limit if you don't want to scrape too many pages:
            if params["page"] > page_limit:
                print("Reached page limit, moving on next category.")
                continue

            await asyncio.sleep(4)


    # Save all results to JSON
    with open("products_land_rover_carro_new.json", "w+", encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(all_results)} products to products_land_rover.json")

if __name__ == "__main__":
    asyncio.run(main())
