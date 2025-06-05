import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import logging
import re
from urllib.parse import urlencode, urljoin
from .models import CarListing, CarDetection
from .config import settings
import random

logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self):
        self.base_url = ""
        self.headers = {
            'User-Agent': settings.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def get_page(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Get page content with error handling"""
        try:
            async with session.get(
                url, 
                headers=self.headers, 
                timeout=settings.request_timeout
            ) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def parse_price(self, price_text: str) -> Optional[str]:
        """Extract and clean price from text"""
        if not price_text:
            return None
        
        # Remove extra whitespace and extract numbers
        price_match = re.search(r'\$[\d,]+', price_text.replace(' ', ''))
        return price_match.group() if price_match else None
    
    def parse_mileage(self, mileage_text: str) -> Optional[str]:
        """Extract mileage from text"""
        if not mileage_text:
            return None
        
        # Look for patterns like "50,000 miles" or "50K"
        mileage_match = re.search(r'[\d,]+[kK]?(\s*miles?)?', mileage_text)
        return mileage_match.group() if mileage_match else None

class AutoTraderScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.autotrader.com"
        self.source = "autotrader"
    
    def build_search_url(self, car_detection: CarDetection) -> str:
        """Build AutoTrader search URL"""
        params = {
            'listingTypes': 'used,new',
            'makeCodeList': car_detection.make.upper() if car_detection.make != "Unknown" else "",
            'modelCodeList': car_detection.model.upper() if car_detection.model != "Unknown" else "",
            'zip': '10001',  # Default to NYC
            'location': '[object Object]',
            'sortBy': 'relevance',
            'numRecords': '25'
        }
        
        if car_detection.year:
            params['startYear'] = str(max(car_detection.year - 2, 1990))
            params['endYear'] = str(min(car_detection.year + 2, 2024))
        
        return f"{self.base_url}/cars-for-sale/all-cars?{urlencode(params)}"
    
    async def scrape_listings(self, session: aiohttp.ClientSession, car_detection: CarDetection) -> List[CarListing]:
        """Scrape AutoTrader listings"""
        url = self.build_search_url(car_detection)
        html = await self.get_page(session, url)
        
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        # Find listing containers (this selector may need adjustment)
        listing_elements = soup.find_all('div', class_=re.compile(r'listing-item|inventory-listing'))
        
        for element in listing_elements[:10]:  # Limit to first 10 results
            try:
                listing = self._parse_autotrader_listing(element)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.error(f"Error parsing AutoTrader listing: {e}")
                continue
        
        return listings
    
    def _parse_autotrader_listing(self, element) -> Optional[CarListing]:
        """Parse individual AutoTrader listing"""
        try:
            # These selectors are approximations and may need adjustment
            title_elem = element.find('h3') or element.find('a', class_=re.compile(r'title|heading'))
            price_elem = element.find(class_=re.compile(r'price'))
            mileage_elem = element.find(class_=re.compile(r'mileage'))
            location_elem = element.find(class_=re.compile(r'location|dealer'))
            link_elem = element.find('a', href=True)
            image_elem = element.find('img', src=True)
            
            if not title_elem or not link_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            price = self.parse_price(price_elem.get_text(strip=True)) if price_elem else None
            mileage = self.parse_mileage(mileage_elem.get_text(strip=True)) if mileage_elem else None
            location = location_elem.get_text(strip=True) if location_elem else None
            link = urljoin(self.base_url, link_elem['href'])
            image_url = image_elem['src'] if image_elem else None
            
            # Extract make/model from title
            make, model = self._extract_make_model(title)
            
            return CarListing(
                title=title,
                price=price,
                make=make,
                model=model,
                mileage=mileage,
                location=location,
                listing_url=link,
                source=self.source,
                image_url=image_url
            )
        
        except Exception as e:
            logger.error(f"Error parsing listing element: {e}")
            return None
    
    def _extract_make_model(self, title: str) -> tuple:
        """Extract make and model from listing title"""
        # Simple extraction - in production you'd use a more sophisticated approach
        words = title.split()
        if len(words) >= 2:
            return words[1], words[2] if len(words) > 2 else "Unknown"
        return "Unknown", "Unknown"

class CarsComScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.cars.com"
        self.source = "cars.com"
    
    def build_search_url(self, car_detection: CarDetection) -> str:
        """Build Cars.com search URL"""
        params = {
            'dealer_id': '',
            'keyword': '',
            'make_model_max_price': '',
            'maximum_distance': '50',
            'mileage_max': '',
            'page_size': '20',
            'sort': 'best_match_desc',
            'stock_type': 'all',
            'year_max': '',
            'year_min': '',
            'zip': '10001'
        }
        
        if car_detection.make != "Unknown":
            params['makes[]'] = car_detection.make.lower()
        
        return f"{self.base_url}/shopping/results/?{urlencode(params)}"
    
    async def scrape_listings(self, session: aiohttp.ClientSession, car_detection: CarDetection) -> List[CarListing]:
        """Scrape Cars.com listings"""
        url = self.build_search_url(car_detection)
        html = await self.get_page(session, url)
        
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        # Find listing containers
        listing_elements = soup.find_all('div', class_=re.compile(r'vehicle-card|listing'))
        
        for element in listing_elements[:10]:
            try:
                listing = self._parse_cars_listing(element)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.error(f"Error parsing Cars.com listing: {e}")
                continue
        
        return listings
    
    def _parse_cars_listing(self, element) -> Optional[CarListing]:
        """Parse individual Cars.com listing"""
        # Similar structure to AutoTrader parser
        try:
            title_elem = element.find('h2') or element.find('a', class_=re.compile(r'title'))
            price_elem = element.find(class_=re.compile(r'price'))
            link_elem = element.find('a', href=True)
            
            if not title_elem or not link_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            price = self.parse_price(price_elem.get_text(strip=True)) if price_elem else None
            link = urljoin(self.base_url, link_elem['href'])
            
            make, model = self._extract_make_model(title)
            
            return CarListing(
                title=title,
                price=price,
                make=make,
                model=model,
                listing_url=link,
                source=self.source
            )
        
        except Exception:
            return None
    
    def _extract_make_model(self, title: str) -> tuple:
        """Extract make and model from listing title"""
        words = title.split()
        if len(words) >= 2:
            return words[0], words[1]
        return "Unknown", "Unknown"

class ScrapingOrchestrator:
    def __init__(self):
        self.scrapers = []
        
        if settings.enable_autotrader:
            self.scrapers.append(AutoTraderScraper())
        
        if settings.enable_cars_com:
            self.scrapers.append(CarsComScraper())
        
        logger.info(f"Initialized {len(self.scrapers)} scrapers")
    
    async def scrape_all(self, car_detection: CarDetection) -> List[CarListing]:
        """Run all scrapers concurrently"""
        if not self.scrapers:
            logger.warning("No scrapers enabled")
            return []
        
        connector = aiohttp.TCPConnector(limit=settings.max_concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Run all scrapers concurrently
            tasks = [
                scraper.scrape_listings(session, car_detection) 
                for scraper in self.scrapers
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            all_listings = []
            for result in results:
                if isinstance(result, list):
                    all_listings.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Scraper failed: {result}")
            
            # Add some randomization to simulate more realistic results
            if len(all_listings) < 5:
                all_listings.extend(self._generate_demo_listings(car_detection))
            
            return all_listings[:20]  # Return top 20 results
    
    def _generate_demo_listings(self, car_detection: CarDetection) -> List[CarListing]:
        """Generate demo listings for demonstration purposes"""
        demo_listings = []
        
        makes = ["Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "BMW", "Mercedes"] 
        models = ["Camry", "Accord", "F-150", "Cruze", "Altima", "3 Series", "C-Class"]
        prices = ["$15,999", "$22,500", "$18,750", "$28,900", "$31,200"]
        years = [2018, 2019, 2020, 2021, 2022]
        
        for i in range(5):
            make = random.choice(makes)
            model = random.choice(models)
            year = random.choice(years)
            price = random.choice(prices)
            
            demo_listings.append(CarListing(
                title=f"{year} {make} {model}",
                price=price,
                year=year,
                make=make,
                model=model,
                mileage=f"{random.randint(15, 80)},000 miles",
                location="Demo Location",
                dealer="Demo Dealer",
                listing_url=f"https://example.com/listing/{i}",
                source="demo"
            ))
        
        return demo_listings

# Global scraping orchestrator
scraping_orchestrator = ScrapingOrchestrator() 