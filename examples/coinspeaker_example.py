import requests
import json

data = """
{"url": "https://www.coinspeaker.com/ripple-win-sec-altcoin-surge/",
"selectors" : [
    {"name": "text", "type": "html", "xpath": "//div[@class='content']"}, 
    {"name": "text_content", "type": "text", "xpath": "//div[@class='content']"}, 
    {"name": "disclaimer_bottom", "type": "text", "xpath": "//p[@class='disclaimer']"},
    {"name": "tags", "type": "list", "xpath": "//span[@class='meta-tags']/a"},
    {"name": "article_lang", "type": "text", "xpath": "//html/@lang"}
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