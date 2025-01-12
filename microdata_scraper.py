import requests
import asyncio
import zendriver as uc
#nodriver==0.38.post1
import extruct
from w3lib.html import get_base_url
from lxml import html, etree
import logging
from transform import convert_to_yyyy_mm_dd, get_file_path_from_url
from translator.translator import translate_text
import traceback
import gc


logger = logging.getLogger('__main__.' + __name__)

class Scraper():

    def __init__(self, wait_delay=10):
        self.wait_delay = wait_delay
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Brave";v="129", "Not-A.Brand";v="8", "Chromium";v="129"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Linux"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Gpc': '1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive'
        }

    async def get_html(self, url, selector_to_wait='h1', headers=None):
        logger.info(f'Trying to get html for {url}')
        loop = asyncio.get_running_loop()
        content = await loop.create_task(self.get_content_using_nodriver(url, selector_to_wait=selector_to_wait))
        return content

    def get_content_using_requests(self, url, custom_headers=None):
        headers = self.headers
        if custom_headers:
            for key in custom_headers.keys():
                headers[key] = custom_headers[key]

        response = requests.get(url, headers=headers)
        if str(response.status_code).startswith('4') or str(response.status_code).startswith('5'):
            logger.error(f"Ошибка при запросе страницы {url}. Ошибка: {response}")
            return None
        logger.info(f"response: {response.status_code} | url: {url}")
        return response.text

    async def get_content_using_nodriver(self, url, selector_to_wait='h1', retries=20):
        browser = None
        try:
            browser = await uc.start(
                # headless=True,
                # browser_args=['--headless=new'],
            )
            page = await browser.get(url)
            await browser.sleep(2)
            await self.get_with_retry(page, selector_to_wait, browser, retries)
            content = await asyncio.wait_for(page.get_content(), 15)
            return content
        except asyncio.TimeoutError:
            logger.error(f'Timeout while waiting for content for URL: {url}')
            return None
        except Exception as ex:
            error = ''.join(traceback.TracebackException.from_exception(ex).format())
            logger.error(f'Error in get_content_using_nodriver for URL: {url}. {error}')
            return None
        finally:
            if browser:
                browser.stop()
            else:
                browser = None
            page = None
            gc.collect()


    async def get_with_retry(self, page, selector, browser, n_retry=5):
        while n_retry > 0:
            try:
                el = await page.select(selector, timeout=5)
                if el:
                    return el
                logger.info('I am waiting <H1>')
                await browser.sleep(1)
            except TimeoutError:
                await browser.sleep(1)
                n_retry -= 1
        raise TimeoutError()

class Parser():

    def __init__(self):
        self.fields = [
            'articleAuthor',
            'disclaimerTop',
            'disclaimerBottom',
            'text',
            'publicationDate',
            'articleLocale',
            'pageTitle',
            'pageTitleEng',
            'tags',
            'category',
            'urlCategory',
        ]
        self.scraper = Scraper()
        pass

    async def process_url(self, url, selectors=[]):
        scraper = self.scraper
        content = await scraper.get_html(url)
        if content:
            base_url = get_base_url(content, url)
            data = extruct.extract(content, base_url=base_url)
            
            record = {}
            if data['json-ld'] != []:
                # Самый полный формат JSON-LD
                for entry in data['json-ld']:
                    if '@graph' in entry:
                        for graph_entry in entry['@graph']:
                            if ('@type' in graph_entry) and (('Article' in graph_entry['@type']) or ('BlogPosting' in graph_entry['@type'])):
                                record = self._parse_record(graph_entry)
                                break
                    else:
                        if ('@type' in entry) and (('Article' in entry['@type']) or ('BlogPosting' in entry['@type'])):
                            record = self._parse_record(entry)
                            break

            if data['opengraph'] != []:
                # Пробуем заполнить пустующие значения
                entry = data['opengraph'][0]
                if 'properties' in entry:
                    try:
                        if record['articleLocale'] is None:
                            record['articleLocale'] = self._get_opengraph_article_lang(entry)
                    except:
                        pass
                    try:
                        if record['pageTitle'] is None:
                            record['pageTitle'] = self._get_opengraph_page_title(entry)
                    except:
                        pass
                    try:
                        if record['category'] is None:
                            record['category'] = self._get_opengraph_category(entry)
                    except:
                        pass
                    try:
                        if record['publicationDate'] is None:
                            record['publicationDate'] = self._get_opengraph_date_publication(entry)
                    except:
                        pass
            if data['rdfa'] != []:
                logger.info(f'Found RDFA section for URL: {url}!')
            if data['microformat'] != []:
                logger.info(f'Found MICROFORMAT section for URL: {url}!')

            if selectors:
                record = self._process_selectors(record, selectors, content)
            record = self._postprocess(record, url)
            scraper = None
            gc.collect()
            return record
        else:
            logger.error(f'Error processing URL: {url}')
            raise ValueError(f'Empty HTML for the {url}')

    def _postprocess(self, record, url):
        try:
            if record['publicationDate'] and record['articleLocale']:
                record['publicationDate'] = convert_to_yyyy_mm_dd(record['publicationDate'], record['articleLocale'])
        except:
            pass
        record['urlCategory'] = get_file_path_from_url(url=url)

        try:
            if record['articleLocale'] != 'en' and record['articleLocale'] != 'en-US':
                record['pageTitleEng'] = translate_text(record['pageTitle'], record['articleLocale'])
            else:
                record['pageTitleEng'] = record['pageTitle']
        except:
            pass

        try:
            record['articleLocale'] = record['articleLocale'].split('-')[0]
        except:
            pass

        # Инициализируем все поля по умолчанию
        for field in self.fields:
            if field not in record:
                record[field] = None

        return record

    def _process_selectors(self, record, selectors, content):
        tree = html.fromstring(content)
        for selector in selectors:
            value = self._get_selector_value(tree, selector['xpath'], selector['type'])
            if (selector['name'] not in record) or (not(record[selector['name']])):
                if value:
                    record[selector['name']] = value
                else:
                    record[selector['name']] = 'Not Found'
        return record

    def _get_selector_value(self, tree, xpath, type):
        value = None
        if type == 'text':
            value = tree.xpath(f'normalize-space({xpath})')
        if type == 'html':
            try:
                content_node = tree.xpath(xpath)[0]
                value = etree.tostring(content_node, pretty_print=True).decode('utf-8')
            except:
                pass
        if type == 'list':
            values =  []
            for node in tree.xpath(xpath):
                node_value = node.xpath('normalize-space(.)')
                values.append(node_value)
            value = ', '.join(values)
        return value

    def _parse_record(self, entry):
        record = {}
        record['articleAuthor'] = self._get_json_ld_author(entry)
        record['text'] = self._get_json_ld_text(entry)
        record['publicationDate'] = self._get_json_ld_date_publication(entry)
        record['articleLocale'] = self._get_json_ld_article_lang(entry)
        record['pageTitle'] = self._get_json_ld_page_title(entry)
        record['tags'] = self._get_json_ld_tags(entry)
        record['category'] = self._get_json_ld_category(entry)
        return record

    def _get_json_ld_author(self, row):
        author = None
        # TODO @type == 'Person' ?
        if 'author' in row:
            if isinstance(row['author'], list):
                for author_item in row['author']:
                    if '@type' in author_item and author_item['@type'] == 'Person':
                        author = author_item['name']
            elif ('name' in row['author']):
                author = row['author']['name']
        return author

    def _get_json_ld_text(self, row):
        text = None
        if 'articleBody' in row:
            text = row['articleBody']
        return text

    def _get_json_ld_date_publication(self, row):
        date_publication = None
        if 'datePublished' in row:
            date_publication = row['datePublished']
        return date_publication

    def _get_json_ld_article_lang(self, row):
        article_lang = None
        if 'inLanguage' in row:
            article_lang = row['inLanguage']
        return article_lang

    def _get_json_ld_page_title(self, row):
        page_title = None
        if 'headline' in row:
            page_title = row['headline']
        return page_title

    def _get_json_ld_tags(self, row):
        tags = None
        if 'keywords' in row:
            tags = row['keywords']

        if isinstance(tags, list):
            tags = ', '.join(tags)
        return tags

    def _get_json_ld_category(self, row):
        category = None
        if 'articleSection' in row:
            category = row['articleSection']

        if isinstance(category, list):
            category = ', '.join(category)
        return category

    def _get_opengraph_article_lang(self, row):
        article_lang = self._get_opengraph_property(row, 'og:locale')
        if article_lang:
            article_lang = article_lang.replace('_', '-')
        return article_lang

    def _get_opengraph_page_title(self, row):
        page_title = self._get_opengraph_property(row, 'og:title')
        return page_title

    def _get_opengraph_category(self, row):
        category = self._get_opengraph_property(row, 'article:section')
        return category

    def _get_opengraph_date_publication(self, row):
        date_publication = self._get_opengraph_property(row, 'article:published_time')
        return date_publication

    def _get_opengraph_property(self, row, target_property_name):
        value = None
        if 'properties' in row:
            for (property_name, property_value) in row['properties']:
                if property_name == target_property_name:
                    value = property_value
                    break
        return value

if __name__ == '__main__':

    # url = 'https://www.analyticsinsight.net/cryptocurrency-analytics-insight/cryptocurrencies-to-buy-under-1-top-5-picks-for-september'
    # url = 'https://blockchainreporter.net/solana-expands-cross-chain-connectivity-with-router-protocol-integration/'
    # url = 'https://www.crypto-news-flash.com/breaking-billion-dollar-bank-bny-set-to-custody-bitcoin-btc-as-the-first-bank-in-u-s-history/'
    # url = 'https://journalducoin.com/defi/airdrop-hamster-kombat-131-millions-adresses-eligibles/'
    url = 'https://www.coinspeaker.com/ripple-win-sec-altcoin-surge/'

    parser = Parser()
    data = parser.process_url(
        url=url,
        selectors=[
            {'name': 'text', 'type': 'html', 'xpath': '//div[@class="content"]'},
            {'name': 'disclaimerBottom', 'type': 'text', 'xpath': '//p[@class="disclaimer"]'},
            {'name': 'tags', 'type': 'list', 'xpath': '//span[@class="meta-tags"]/a'},
            {'name': 'articleLocale', 'type': 'text', 'xpath': '//html/@lang'},
        ]
    )

    print('Done!')
