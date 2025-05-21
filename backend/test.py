from googlesearch import search
from duckduckgo_search import DDGS
import time
company_names = [
    "Vattenfall AB",
    "E.ON Sverige",
    "Svenska Kraftnät",  # and so on...
]

for company_name in company_names:
    query = f"{company_name} electricity Sweden official site"
    print(f"Searching for {company_name} athletics official site...")
    site_names = {}
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query)
            for result in results:
                site_names[company_name] = result['href']
                break
    except Exception as e:
        print(f"Error searching for {company_name} athletics site: {e}")
        continue
    time.sleep(1)
