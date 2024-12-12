
import logging
from aiohttp import web
from aiohttp.web_request import Request

LOG = logging.getLogger(__name__)

async def handler(request: Request):    
    LOG.setLevel(logging.DEBUG)

    response_data = {
    "meta": {
        "beaconId": "SARS-CoV-2-beacon.integrator.clinbioinfosspa.es",
        "apiVersion": "v2.0.0",
        "returnedSchemas": []
    },
    "response": {
        "endpointSets": {
        "biosample": {
            "entryType": "biosample",
            "openAPIEndpointsDefinition": "https://raw.githubusercontent.com/ga4gh-beacon/beacon-v2/main/models/json/beacon-v2-default-model/biosamples/endpoints.json",
            "rootUrl": "https://virus-beacon.clinbioinfosspa.es/api/biosamples",
        },
        "genomicVariant": {
            "entryType": "genomicVariant",
            "openAPIEndpointsDefinition": "https://raw.githubusercontent.com/ga4gh-beacon/beacon-v2/main/models/json/beacon-v2-default-model/genomicVariations/endpoints.json",
            "rootUrl": "https://virus-beacon.clinbioinfosspa.es/api/g_variants",
        },
        "individual": {
            "entryType": "individual",
            "openAPIEndpointsDefinition": "https://raw.githubusercontent.com/ga4gh-beacon/beacon-v2/main/models/json/beacon-v2-default-model/individuals/endpoints.json",
            "rootUrl": "https://virus-beacon.clinbioinfosspa.es/api/individuals",
            "filteringTermsUrl": "https://virus-beacon.clinbioinfosspa.es/api/filtering_terms",            
        },
        "occurences": {
            "entryType": "occurences",            
            "rootUrl": "https://virus-beacon.clinbioinfosspa.es/api/occurrences",
            "filteringTermsUrl": "https://virus-beacon.clinbioinfosspa.es/api/images/filtering_terms",            
        },

        }
    }
    }

    return web.json_response(response_data)