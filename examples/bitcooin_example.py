import requests
import json

data = """
{"url": "https://bitcoin.pl/decentralizacja-sieci-bitcoin-jest-zagrozonah",
"selectors" : [
    {"name": "text", "type": "html", "xpath": "//div[h2]"}, 
    {"name": "text_content", "type": "text", "xpath": "//div[h2]"},
    {"name": "page_title", "type": "text", "xpath": "//h1"},
    {"name": "article_lang", "type": "text", "xpath": "//html/@lang"},
    {"name": "publication_date", "type": "text", "xpath": "//span[contains(@class, 'i-heroicons:calendar')]/following-sibling::span"},
    {"name": "article_author", "type": "text", "xpath": "//div[div[div[@class='relative']//span[.='Autor']]]//a[contains(@href, '/author/')][contains(@class, 'text')]"},
    {"name": "tags", "type": "list", "xpath": "//div[@class='single-post-new__tags']/a"},
    {"name": "category", "type": "list", "xpath": "(//div[span/span[contains(@class, 'i-heroicons:calendar')]])[1]/following-sibling::a"}
]
}
"""

r = requests.post(
    url='http://localhost:8000/scrape',
    data=data,
    headers={
        'Content-Type': 'application/json',
        'X-API-Key': 'AIzaSyDaGmWKa4JsXZ-HjGw7ISLn_3namBGewQe',
    }
)

data = json.loads(r.text)

print(r.text)