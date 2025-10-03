import aiohttp
import asyncio
import os
import json
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

class Spider:
    def __init__(self):
        self.domains = self.init_domains()
        self.headers = {
            'Authorization': f'Bearer {os.getenv("SPIDER_API_KEY")}',
            'Content-Type': 'application/json',
        }

    def init_domains(self):
        with open("data/domains.json", "r") as f:
            domains = json.load(f)["domains"]
            f.close()
        return domains

    async def crawl_domain(self, session, domain):
        params = {
            "url": domain,
            "limit": 250, # Maximum number of pages to crawl
            "depth": 4, # Reasonable depth for small sites
            "request": "smart",
            "return_format": "markdown",
            "metadata": True,
            "country_code":"nl",
            "locale":"nl-NL"
        }

        async with session.post(
            'https://api.spider.cloud/crawl',
            headers=self.headers,
            json=params
        ) as response:
            # Get the response text first
            response_text = await response.text()
            
            try:
                # Try to parse as JSON
                response_data = json.loads(response_text)
            except json.JSONDecodeError:
                # If it's not JSON, save the raw text
                response_data = {"raw_content": response_text}
            
            # Extract domain name for filename
            domain_name = urlparse(domain).netloc.replace('www.', '')
            filename = f"data/spider_{domain_name}.json"
            
            # Create data directory if it doesn't exist
            os.makedirs("data", exist_ok=True)
            
            with open(filename, "w") as f:
                json.dump(response_data, f, indent=2)

    async def crawl_all(self):
        async with aiohttp.ClientSession() as session:
            tasks = [self.crawl_domain(session, domain) for domain in self.domains]
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    spider = Spider()
    asyncio.run(spider.crawl_all())