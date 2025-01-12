import logging
import asyncio
from fastapi import FastAPI, Header, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import Union, Literal, Annotated
from microdata_scraper import Parser
from fastapi.concurrency import run_in_threadpool
import traceback
from config import API_KEY
from translator.translator import translate_text
import gc
from config import DEEPL_API_KEY
import deepl
import requests

logger = logging.getLogger('__main__.' + __name__)

class Selector(BaseModel):
    name: str
    type: Union[Literal['text'], Literal['html'], Literal['list']]
    xpath: str


class SubmitGeneral(BaseModel):
    url: str
    selectors: list[Selector]


app = FastAPI()
@app.get("/pars-url")
async def hello():
    # translator = deepl.Translator('cafecf8d-ed9e-408b-b330-f1e5f0877a52:fx')
    # result = translator.translate_text("Hello, world!", target_lang="FR")
    # print(result.text)  # "Bonjour, le monde !"
    
    r = requests.post(
        url="https://api.deepl.com/v2/translate",
        data={
            "target_lang": "EN",
            # "auth_key": 'cafecf8d-ed9e-408b-b330-f1e5f0877a52:fx',
            "auth_key": 'cafecf8d-ed9e-408b-b330-f1e5f0877a52',
            "text": 'Привет Мир',
        },
    )
    print(r.status_code)
    print('HELLO')
    
@app.post("/pars-url")
async def scrape(data: SubmitGeneral, x_api_key: Annotated[str | None, Header(convert_underscores=True)] = None,):
    if x_api_key and x_api_key == API_KEY:
        try:
            data = jsonable_encoder(data)
            parser = Parser()

            try:
                result = await asyncio.wait_for(parser.process_url(
                    url=data['url'],
                    selectors=data['selectors']
                ), timeout=15.0)
            except asyncio.TimeoutError:
                logger.debug(f'Timeout ERROR processing result!')
                # when time out happen program will break from the test function and execute code here
                print('timeout!')
                print('lets continue to do other things')
                error = 'Timeout error'
                raise HTTPException(status_code=500, detail=error)
            parser = None
            gc.collect()

            logger.debug(f'Processing finished: {result}')
            return result
        except Exception as ex:
            error = ''.join(traceback.TracebackException.from_exception(ex).format())
            logger.error(f'Error in scrape. {error}')
            raise HTTPException(status_code=500, detail=error)
    else:
        logger.error('Wrong / missing API key!')
        raise HTTPException(status_code=403, detail="X-api-key not correct")
