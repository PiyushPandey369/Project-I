# data_fetching_and_db/services/news_service.py
import urllib.request
import xml.etree.ElementTree as ET
import re

# Curated fallback global environmental & weather news
FALLBACK_NEWS = [
    {
        "title": "Global Temperatures Continue to Set New Monthly Records",
        "link": "https://www.sciencedaily.com/news/earth_climate/earth_science/",
        "date": "July 09, 2026",
        "snippet": "Climatologists report record-breaking sea surface temperatures and land heatwaves across both hemispheres, driving weather extremes.",
        "source": "ScienceDaily"
    },
    {
        "title": "Understanding the Role of Stratospheric Aerosols in Climate Change",
        "link": "https://www.sciencedaily.com/news/earth_climate/earth_science/",
        "date": "July 08, 2026",
        "snippet": "New satellite observations examine how volcanic eruptions and aerosol layers reflect solar radiation, cooling the lower atmosphere.",
        "source": "ScienceDaily"
    },
    {
        "title": "How Changing Wind Patterns Drive Extreme Summer Heatwaves",
        "link": "https://www.sciencedaily.com/news/earth_climate/earth_science/",
        "date": "July 06, 2026",
        "snippet": "Atmospheric research highlights how high-pressure jet stream ridges stall over continents, trapping heat for weeks at a time.",
        "source": "ScienceDaily"
    },
    {
        "title": "New Models Track Global Particulate Matter (PM2.5) Transport",
        "link": "https://www.sciencedaily.com/news/earth_climate/earth_science/",
        "date": "July 05, 2026",
        "snippet": "Advanced meteorology simulations map how forest fire plumes and desert dust cross oceans, affecting international air quality standards.",
        "source": "ScienceDaily"
    }
]

def fetch_local_news():
    url = "https://www.sciencedaily.com/rss/earth_climate/earth_science.xml"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        # 5 second timeout to keep requests snappy
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        items = []
        
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            description = item.find('description').text if item.find('description') is not None else ""
            
            # Clean HTML tags and remove extra whitespace
            clean_desc = re.sub('<[^<]+?>', '', description).strip()
            # Clean headline title
            clean_title = title.strip()
            
            # Extract date string nicely (e.g., Thu, 09 Jul 2026 12:00:00 -> 09 Jul 2026)
            date_match = re.search(r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}', pub_date)
            formatted_date = date_match.group(0) if date_match else pub_date
            
            snippet = clean_desc[:140] + "..." if len(clean_desc) > 140 else clean_desc
            
            items.append({
                "title": clean_title,
                "link": link,
                "date": formatted_date,
                "snippet": snippet,
                "source": "ScienceDaily"
            })
            if len(items) >= 4:
                break
        return items
    except Exception as e:
        print(f"ScienceDaily RSS news fetch exception: {e}")
        return []

def get_weather_news():
    rss_news = fetch_local_news()
    if len(rss_news) < 4:
        needed = 4 - len(rss_news)
        return rss_news + FALLBACK_NEWS[:needed]
    return rss_news
