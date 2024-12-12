import json
import logging
from aiohttp import ClientSession, web
from aiohttp.web_request import Request

LOG = logging.getLogger(__name__)


async def handler(request: Request):    
    LOG.setLevel(logging.DEBUG)

    response_data = {
        "result":"No implemented"
    }
    return web.json_response(response_data)
