
import logging
from aiohttp import web
from aiohttp.web_request import Request

LOG = logging.getLogger(__name__)

async def handler(request: Request):    
    LOG.setLevel(logging.DEBUG)

    response_data = {
        "meta": {
            "beaconId": "SARS-CoV-2-beacon.itegrator.clinbioinfosspa.es",
            "apiVersion": "v2.0.0",
            "returnedSchemas": []
        },
        "response": {
            "id": "SARS-CoV-2-beacon.itegrator.clinbioinfosspa.es",
            "name": "Beacon Integrator SARS-CoV-2",
            "apiVersion": "v2.0.0",
            "environment": "test",
            "organization": {
            "id": "es.clinbioinfosspa",
            "name": "Andalusian Platform for Computational Medicine, Fundacion Progreso y Salud",
            "description": "Andalusian Platform for Computational Medicine (APCM) is one of the research platforms of the Fundación Progreso y Salud (FPS). APCM has  the mission of facilitating and providing the tools for the inclusion of the genomic data of the patient in the electronic health record.",
            "address": "Edificio C.D.C.A.. Hospital Universitario  Virgen del RocioAvenida Manuel Siurot s/n, 41013 Sevilla, Spain",
            "welcomeUrl": "http://www.clinbioinfosspa.es/",
            "contactUrl": "mailto:csvs@clinbioinfosspa.es",
            "logoUrl": "http://www.clinbioinfosspa.es/sites/default/files/logo-fundacion_3.png"
            },
            "description": "This Beacon itegrator beacon clinical, genomic and imagen about SARS-Cov-2.",
            "version": "v2.0-39cc125",
            "welcomeUrl": "https://virus-beacon.clinbioinfosspa.es/info",
            "alternativeUrl": "https://virus-beacon.clinbioinfosspa.es/api",
            "createDateTime": "2024-07-30T12:00:00.000000",
            "updateDateTime": "2024-10-10T13:11:23.241517",
            "datasets": []
        }
    }
    
    return web.json_response(response_data)