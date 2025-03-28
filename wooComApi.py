import aiohttp, base64, json
from urllib.parse import urlencode
from urllib.parse import urlparse


WC_STORE_URL_TEST= "https://roshel.az/roverland"
WC_CONSUMER_KEY_TEST= "ck_4116194af66bf4d80091b60a226faa391c8d7197"
WC_CONSUMER_SECRET_TEST= "cs_333d5dd5d873f7a5595826517732de7a5d1c9429"

WC_CONSUMER_KEY_PROD = "ck_b31d454694883481517f89f8981a3580537be5fc"
WC_CONSUMER_SECRET_PROD = "cs_6a7990739f059ce07a4b87b1f6b22437f2451ca5"
WC_STORE_URL_PROD = "https://roverland.az"


class WooCommerceClient:
    def __init__(self):
        self.base_url = f"{WC_STORE_URL_PROD}/wp-json/wc/v3"
        self.auth = aiohttp.BasicAuth(WC_CONSUMER_KEY_PROD, WC_CONSUMER_SECRET_PROD)
        self.wp_media_url = f"{WC_STORE_URL_PROD}/wp-json/wp/v2/media"

        self.timeout =  aiohttp.ClientTimeout(
            total=220,  # Total timeout (in seconds)
            connect=180,  # Connection timeout (in seconds)
            sock_connect=140,  # Socket connection timeout (in seconds)
            sock_read=140  # Socket read timeout (in seconds)
        )

    async def upload_media(self, image_url):
        """Upload image to  media library and return media ID"""
        async with aiohttp.ClientSession() as session:
            try:
                # Download the image
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        print(f"Failed to download image: {resp.status}")
                        return None
                    image_data = await resp.read()
                
                # Extract filename from URL
                parsed_url = urlparse(image_url)
                filename = parsed_url.path.split("/")[-1]

                print(f"Uploading image: {filename}")

                # Upload to WordPress media library
                username_test = "canilgu@roshel.az"        # The WP username
                app_password_test = "3VVJ Ox3z 6Lrc cZHU MX5z VW7s"   # The 24-char application password

                username = "can@roshel.az"
                #app_password = "gFyY UoWl vRaq aGoo M8YR yM1O"
                app_password = "xVki HQku CEkJ rNsY a71S yD8a"
                
                auth_str = f"{username}:{app_password}"
                
                b64_auth = base64.b64encode(auth_str.encode()).decode()
                headers = {
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Content-Type": "image/jpeg",  # Adjust if you know the exact MIME type
                    "Authorization": f"Basic {b64_auth}"
                }

                print(headers)
                
                async with session.post(
                    self.wp_media_url,
                    data=image_data,
                    headers=headers,
                    timeout = self.timeout
                ) as resp:
                    resp.raise_for_status()
                    media_data = await resp.json()
                    return media_data['id']
                    
            except aiohttp.ClientResponseError as e:
                print(f"Media upload HTTP Error: {e.status}, {e.message}")
            except Exception as e:
                print(f"Media upload Error: {e}")
            return None

    async def create_product(self, data):
        if "images" in data:
            new_images = []
            a = 0
            for img in data["images"]:
                if a == 4:
                    break
                
                if "src" in img and "id" not in img:
                    media_id = await self.upload_media(img["src"])
                    if media_id:
                        new_images.append({"id": media_id})
                
               
                a += 1
                
            data["images"] = new_images

       
        url = f"{self.base_url}/products"
        async with aiohttp.ClientSession(auth=self.auth, timeout=self.timeout) as session:
            async with session.post(url, json=data) as resp:
                resp.raise_for_status()
                return await resp.json()
            
    async def get_all_products(self):
        url = f"{self.base_url}/products"
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_product(self, product_id):
        url = f"{self.base_url}/products/{product_id}"
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def update_product(self, product_id, data):
        url = f"{self.base_url}/products/{product_id}"
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async with session.put(url, json=data) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def delete_product(self, product_id):
        params = {'force': True}
        url = f"{self.base_url}/products/{product_id}"
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async with session.delete(url, params=params) as resp:
                resp.raise_for_status()
                return await resp.json()


async def main():
    wc_client = WooCommerceClient()
    
    # Load JSON data
    with open("0_withcode_carro.json", "r", encoding="utf-8") as file:
        products = json.load(file)
    
    for product in products[0:2]:
        product_name = product.get("product_name_az")
        product_price = product.get("product_price_az", "")
        product_photo_url = product.get("product_photo_url")
        
        
        # Skip products without an image URL
        if not product_photo_url:
            continue
        
        print(f"Creating product: {product_name}")
        
        new_product_data = {
            "name": product_name,
            "type": "simple",
            "regular_price": product_price,
            "description": f"<p>{product_name} - CODE: {product.get('product_code')}</p>",
            "short_description": f"Qısa təsviri, {product_name} \n orginal url: <a href='{product.get('product_href')}'> link </a> ",
            "categories": [{"id": 196}],  # Replace with the actual category ID
            "images": [{"src": product_photo} for product_photo in product_photo_url]
        }
        
       
        try:
            created_product = await wc_client.create_product(new_product_data)
            print(f"Created product: {created_product}")
        except:
            pass
        
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())