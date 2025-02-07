import base64
import aiohttp
import asyncio

async def upload_media_app_password(url, headers, file_path):
    upload_endpoint = f"{url.rstrip('/')}/wp-json/wp/v2/media"
    
    # Prepare file data
    file_name = file_path.split('/')[-1]
    with open(file_path, 'rb') as f:
        file_data = f.read()

    form = aiohttp.FormData()
    form.add_field(
        "file",
        file_data,
        filename=file_name,
        content_type="image/jpeg"  # or the correct MIME type
    )

    async with aiohttp.ClientSession() as session:
        async with session.post(upload_endpoint, headers=headers, data=form) as resp:
            resp.raise_for_status()
            return await resp.json()

async def main():
    url = "https://roshel.az/roverland"
    username = "canilgu@roshel.az"        # The WP username
    app_password = "3VVJ Ox3z 6Lrc cZHU MX5z VW7s"   # The 24-char application password
    file_path = "small.jpg"

    auth_str = f"{username}:{app_password}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {b64_auth}"}

    result = await upload_media_app_password(url, headers, file_path)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
