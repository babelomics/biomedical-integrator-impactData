import logging

from aiohttp import web
import aiohttp_cors
from aiohttp_middlewares.cors import DEFAULT_ALLOW_HEADERS


#from .auth import bearer_required
from integrator import load_logger
from integrator.request.routes import routes


LOG = logging.getLogger(__name__)


async def initialize(app):
    """Initialize server."""
    LOG.info("Initialization done.")

async def destroy(app):
    """Upon server close, close the DB connections."""
    LOG.info("Shutting down.")
    

def main(path=None):    
    # Configure the permissions server
    server = web.Application()
    server.on_startup.append(initialize)
    server.on_cleanup.append(destroy)
    
    load_logger()
    
    # Configure the endpoints
    server.add_routes(routes) 

    cors = aiohttp_cors.setup(server, defaults={
        "https://beacon-network-test.ega-archive.org": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_methods=("POST", "PATCH", "GET", "OPTIONS"),
                allow_headers=DEFAULT_ALLOW_HEADERS
            )
    })

    for route in list(server.router.routes()):
            cors.add(route, {
            "http://localhost:3000":
                aiohttp_cors.ResourceOptions(allow_credentials=True,
                expose_headers="*",
                allow_methods=("POST", "PATCH", "GET", "OPTIONS"),
                allow_headers=DEFAULT_ALLOW_HEADERS),
            "https://192.168.150.147:3000":
                aiohttp_cors.ResourceOptions(allow_credentials=True,
                expose_headers="*",
                allow_methods=("POST", "PATCH", "GET", "OPTIONS"),
                allow_headers=DEFAULT_ALLOW_HEADERS),
            "*":
                aiohttp_cors.ResourceOptions(allow_credentials=True,
                expose_headers="*",
                allow_methods=("POST", "PATCH", "GET", "OPTIONS"),
                allow_headers=DEFAULT_ALLOW_HEADERS)                
        })

    web.run_app(server,
                host='0.0.0.0',
                port=5052,
                shutdown_timeout=0, ssl_context=None)

if __name__ == '__main__':
    main()


