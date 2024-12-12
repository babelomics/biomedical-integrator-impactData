import json
import logging
from aiohttp import ClientSession, web
from aiohttp.web_request import Request

from integrator.request.model import RequestParams
from integrator import conf

LOG = logging.getLogger(__name__)

INDIVIDUALS_BIOSAMPLES = {}

BIOSAMPLES = "biosamples"
INDIVIDUALS = "individuals"

async def get_redirect(url, params_request = {}):
    async with ClientSession() as session:
        async with session.get(
                url,
                headers = {
                        #'Authorization': 'Bearer ' + token,
                        'Accept': 'application/json'},
                params = params_request
        ) as resp:
            if resp.status == 200:
                response_data = await resp.json()
            else:
                response_data = {
                    'error': f'Service error: {resp.status}'
                }
            return response_data    


async def post_redirect(url, json_request, params_request = {}):
    async with ClientSession() as session:
        async with session.post(
                url,
                headers = {
                        #'Authorization': 'Bearer ' + token,
                        'Accept': 'application/json'},
                json = json_request,
                params = params_request
        ) as resp:
            if resp.status == 200:
                response_data = await resp.json()
            else:
                response_data = {
                    'error': f'Service error: {resp.status}'
                }
            return response_data  


async def filtering_terms_handler(request: Request):
    response_data = await get_redirect(conf.uri_clinical + "filtering_terms")
    return web.json_response(response_data)


async def filtering_terms_img_handler(request: Request):
    response_data = await get_redirect(conf.uri_imagen + "filtering_terms?limit=999")
    return web.json_response(response_data)


async def biosamples_handler(request: Request): 
    json_body = await request.json() if request.method == "POST" and request.has_body and request.can_read_body else {}  
    query = request.query if request.query else {}
    qparams = RequestParams(**json_body).from_request(request)

    response_data = await biosamples(request.method, json_body, query)    
    return web.json_response(response_data)


async def individuals_handler(request: Request):    
    json_body = await request.json() if request.method == "POST" and request.has_body and request.can_read_body else {}
    response_data = default_response(json_body, "count")
    query = request.query if request.query else {}
    qparams = RequestParams(**json_body).from_request(request)

    # 1. Filters individuals
    LOG.debug("----------------------------STEP 1 ----------------------------------")
    list_individuals_ids = []
    if qparams.query.filters:
        list_individuals_ids = await get_ids_individuals(json_body, query, qparams.query.filters)
        if len(list_individuals_ids) == 0: 
            response_data["responseSummary"]['numTotalResults'] = 0
            response_data["responseSummary"]['exists'] = False
            return web.json_response(response_data)
    else:
        list_individuals_ids = await get_ids_individuals(json_body, query, [])

    LOG.debug(list_individuals_ids)

    # 2. Filters individuals img
    LOG.debug("----------------------------STEP 2 ----------------------------------")
    list_individuals_img_ids = []
    if qparams.query.filtersImg:
        list_individuals_img_ids = await get_ids_individuals_img_intersec(json_body, query, qparams.query.filtersImg)    
        if len(list_individuals_img_ids) == 0: 
            response_data["responseSummary"]['numTotalResults'] = 0
            response_data["responseSummary"]['exists'] = False
            return web.json_response(response_data)

    LOG.debug(list_individuals_img_ids)

    # 3. ids individuals final
    LOG.debug("----------------------------STEP 3 ----------------------------------")
    list_individuals_ids_final = [] 
    if len(qparams.query.filters)> 0 and qparams.query.filtersImg and  len(list_individuals_img_ids) > 0:
        list_individuals_ids_final = list(set(list_individuals_ids).intersection(set(list_individuals_img_ids)))
    elif len(qparams.query.filters)> 0:
        list_individuals_ids_final = list_individuals_ids        
    elif list_individuals_img_ids and len(list_individuals_img_ids) > 0:
        list_individuals_ids_final = list_individuals_img_ids        
    else:
        list_individuals_ids_final = list_individuals_ids
        
    LOG.debug(list_individuals_ids_final)

    # 4. Filter individuals_biosamples
    LOG.debug("----------------------------STEP 4 ----------------------------------")
    list_individuals_biosamples_tmp = []
    # Get all biosamples_individuals
    await get_all_individuals_biosamples()
    #  Get all biosamples_individuals filter by individuals
    list_individuals_biosamples_tmp = await filter_individuals_biosamples(INDIVIDUALS, list_individuals_ids_final)
    
    LOG.debug(list_individuals_biosamples_tmp)

    # 5. Filter variants with biosamples
    LOG.debug("----------------------------STEP 5 ----------------------------------")
    list_biosamples_ids_variants = []
    if qparams.query.request_parameters and len(qparams.query.request_parameters) > 0:        
        filters_variants = {
            "meta": {
                "beaconId": "SARS-CoV-2-beacon.clinbioinfosspa.es",
                "apiVersion": "v2.0"
            },
            "query": {
                    "pagination": {"limit": 999},
                    "requestedGranularity": "record"
            } 
        }        
        filters_variants['query']['requestParameters'] = qparams.query.request_parameters

        # 5.1 Get variants
        LOG.debug("5.1")        
        response_variants = await g_variants("POST", filters_variants, query)
        exists_variants = response_variants['responseSummary']['exists']
        list_variants = response_variants['response']['resultSets'][0]["results"] if exists_variants else []
        LOG.debug(response_variants['response'] if exists_variants else "null")
        LOG.debug(exists_variants)

        # 5.2. Get ids biosamples in variants
        LOG.debug("5.2")
        list_biosamples_ids_variants = [elem['caseLevelData'][0]['biosampleId'] for elem in list_variants] if exists_variants and list_variants else []
        LOG.debug(list_biosamples_ids_variants)

    # 6. Intersection 4.individuals_biosamples & 5. variants_biosamples
    LOG.debug("----------------------------STEP 6 ----------------------------------")
    count = 0
    if qparams.query.request_parameters and len(qparams.query.request_parameters) > 0:
        if len(list_biosamples_ids_variants) == 0  or len(list_individuals_biosamples_tmp) == 0:
            count = 0
        else:    

            # Get list indv-biosamples filter by list ids biosamples in variants
            list_individuals_biosamples_aux_tmp = await filter_individuals_biosamples(BIOSAMPLES, list_biosamples_ids_variants)
            LOG.debug("Get list indv-biosamples filter by list ids biosamples in variants: ")
            LOG.debug(list_individuals_biosamples_aux_tmp)

            # intersect individuals with indv-biosamples
            list_intersec = list(set(list_individuals_biosamples_aux_tmp.keys()).intersection(set(list_individuals_biosamples_tmp))) if len(list_individuals_biosamples_aux_tmp) > 0 and len(list_individuals_biosamples_tmp) > 0 else []
            count = len(list_intersec)
            LOG.debug(list_intersec)        
    else:
        if qparams.query.filtersImg:
            LOG.debug(list_individuals_biosamples_tmp)
            count = len(list_individuals_biosamples_tmp) if len(list_individuals_biosamples_tmp) > 0 else 0
        else:
            LOG.debug(list_individuals_ids_final)
            count = len(list_individuals_ids_final)


    response_data["responseSummary"]['numTotalResults'] = count
    response_data["responseSummary"]['exists'] =  True if count > 0 else False

    return web.json_response(response_data)


async def g_variants_handler(request: Request): 
    json_body = await request.json() if request.method == "POST" and request.has_body and request.can_read_body else {}  
    response_data = default_response(json_body, "records")
    query = request.query if request.query else {}
    qparams = RequestParams(**json_body).from_request(request)

    # 1. Filters individuals
    LOG.debug("----------------------------STEP 1 ----------------------------------")
    list_individuals_ids = []
    if qparams.query.filters:
        # Get individuals ids        
        list_individuals_ids = await get_ids_individuals(json_body, query, qparams.query.filters)
        if len(list_individuals_ids) == 0: 
            response_data["responseSummary"]['numTotalResults'] = 0
            response_data["responseSummary"]['exists'] = False
            return web.json_response(response_data)        

    LOG.debug(list_individuals_ids)
    
    # 2. Filters individuals img
    LOG.debug("----------------------------STEP 2 ----------------------------------")
    list_individuals_img_ids = []
    if qparams.query.filtersImg:
        list_individuals_img_ids = await get_ids_individuals_img_intersec(json_body, query, qparams.query.filtersImg)
        if len(list_individuals_img_ids) == 0: 
            response_data["responseSummary"]['numTotalResults'] = 0
            response_data["responseSummary"]['exists'] = False
            return web.json_response(response_data)

    LOG.debug(list_individuals_img_ids)

    # 3. ids individuals final
    LOG.debug("----------------------------STEP 3 ----------------------------------")
    list_individuals_ids_final = [] 
    if qparams.query.filters and len(qparams.query.filters)> 0 and  len(list_individuals_img_ids) > 0:
        list_individuals_ids_final = list(set(list_individuals_ids).intersection(set(list_individuals_img_ids)))
    elif qparams.query.filters and len(qparams.query.filters)> 0:
        list_individuals_ids_final = list_individuals_ids
    elif list_individuals_img_ids and len(list_individuals_img_ids) > 0:
        list_individuals_ids_final = list_individuals_img_ids

    LOG.debug(list_individuals_ids_final)

    # 4. Filter individuals_biosamples
    LOG.debug("----------------------------STEP 4 ----------------------------------")
    list_individuals_biosamples_tmp = []
    if qparams.query.filters or qparams.query.filtersImg:
        # Get all biosamples_individuals
        await get_all_individuals_biosamples()

        #  Get all biosamples_individuals filter by individuals
        list_individuals_biosamples_tmp = await filter_individuals_biosamples(INDIVIDUALS, list_individuals_ids_final)
        LOG.debug(list_individuals_biosamples_tmp)

    # 5. Filter variants with biosamples
    LOG.debug("----------------------------STEP 5 ----------------------------------")
    list_biosamples_ids_variants = []
    filters_variants = {
        "meta": {
            "beaconId": "SARS-CoV-2-beacon.clinbioinfosspa.es",
            "apiVersion": "v2.0"
        },
        "query": {
                "pagination": {"limit": 999},
                "requestedGranularity": "record"
        } 
    }     
    if qparams.query.request_parameters and len(qparams.query.request_parameters) > 0:
        #if 'requestParameters' in request:
        filters_variants['query']['requestParameters'] = qparams.query.request_parameters
    
    # 5.1 Get variants
    LOG.debug("5.1")    
    response_variants = await g_variants("POST", filters_variants, query)

    # 5.2. Filter variants with biosamples
    exists_variants = response_variants['responseSummary']['exists']
    list_variants = response_variants['response']['resultSets'][0]["results"] if exists_variants else []
    num_total_result = response_variants['responseSummary']['numTotalResults'] if exists_variants else 0
    LOG.debug(exists_variants)

    # 6. Intersection 4.individuals_biosamples & 5. variants_biosamples
    LOG.debug("----------------------------STEP 6 ----------------------------------")
    count = 0
    LOG.debug(len(qparams.query.filters) > 0 or len(qparams.query.filtersImg) > 0)
    if len(qparams.query.filters) > 0 or len(qparams.query.filtersImg) > 0:
        LOG.debug(len(list_variants))
        if len(list_variants) > 0 and len(list_individuals_biosamples_tmp) > 0 :
            
            # filter variants
            list_biosamples_tmp = []
            for elem in list_individuals_biosamples_tmp.keys():
                list_biosamples_tmp.extend(list_individuals_biosamples_tmp[elem])
            
            LOG.debug(list_biosamples_tmp)
            LOG.debug(list_variants[0]['caseLevelData'])

            #list_variants_final =  [elem for elem in list_variants if elem['caseLevelData'][0]['biosampleId'] in list_biosamples_tmp]
            list_variants_final = []
            for elem in list_variants:
                if elem['caseLevelData'][0]['biosampleId'] in list_biosamples_tmp:
                    list_variants_final.append(elem)
            
            count = len(list_variants_final)  

            if count > 0 :
                response_data['response'] = {
                    'resultSets' : [{
                            "results" : list_variants_final[:100],
                            "resultsCount" : count ,
                    }]
                }
            else:                
                filters_variants['query']['filters'] = [
                    {"id":"caseLevelData.biosampleId", "value": list_biosamples_tmp[0]}
                ]
                response_variants = await g_variants("POST", filters_variants, query)

                # 5.2. Filter variants with biosamples
                exists_variants = response_variants['responseSummary']['exists']
                if list_individuals_biosamples_tmp == 1:
                    num_total_result = response_variants['responseSummary']['numTotalResults'] if exists_variants else 0
                else:
                    num_total_result = response_variants['responseSummary']['numTotalResults'] + 1 if exists_variants else 1

                if exists_variants :
                    response_data['response'] = {
                        'resultSets' : [{
                                "results" :  response_variants['response']['resultSets'][0]["results"][:100] if exists_variants else [],
                                "resultsCount" : num_total_result ,
                        }]
                    }
    else:
        count = num_total_result
        LOG.debug(count)
        if count > 0 :
            response_data['response']={
                'resultSets': [{
                        "results" : list_variants[:100],
                        "resultsCount" : count,
                }]
            }
    
    response_data["responseSummary"]['numTotalResults'] = count
    response_data["responseSummary"]['exists'] =  True if response_data["responseSummary"]['numTotalResults'] > 0 else False

    return web.json_response(response_data)


async def occurrences_handler(request: Request):     
    json_body = await request.json() if request.method == "POST" and request.has_body and request.can_read_body else {}  
    response_data = default_response(json_body, "count")
    query = request.query if request.query else {}
    qparams = RequestParams(**json_body).from_request(request)

    # 1. Filters individuals
    LOG.debug("----------------------------STEP 1 ----------------------------------")
    list_individuals_ids = []
    if qparams.query.filters:
        # Get individuals ids        
        list_individuals_ids = await get_ids_individuals(json_body, query, qparams.query.filters)
        if len(list_individuals_ids) == 0: 
            response_data["responseSummary"]['numTotalResults'] = 0
            response_data["responseSummary"]['exists'] = False
            return web.json_response(response_data)
        
    LOG.debug(list_individuals_ids)

    # 2. Filters individuals img
    LOG.debug("----------------------------STEP 2 ----------------------------------")
    list_individuals_img_ids = []
    if qparams.query.filtersImg:
        list_individuals_img_ids = await get_ids_individuals_img_intersec(json_body, query, qparams.query.filtersImg)
        if len(list_individuals_img_ids) == 0: 
            response_data["responseSummary"]['numTotalResults'] = 0
            response_data["responseSummary"]['exists'] = False
            return web.json_response(response_data)
    else:
        list_individuals_img_ids = await get_ids_individuals_img_intersec(json_body, query, [])

    LOG.debug(list_individuals_img_ids)

    # 3. ids individuals final
    LOG.debug("----------------------------STEP 3 ----------------------------------")
    list_individuals_ids_final = [] 
    if qparams.query.filters and len(qparams.query.filters)> 0 and len(list_individuals_img_ids) > 0:
        list_individuals_ids_final = list(set(list_individuals_ids).intersection(set(list_individuals_img_ids)))
    elif qparams.query.filters and len(qparams.query.filters)> 0:
        list_individuals_ids_final = list_individuals_ids
    elif list_individuals_img_ids and len(list_individuals_img_ids) > 0:
        list_individuals_ids_final = list_individuals_img_ids
    
    LOG.debug(list_individuals_ids_final)

    # 4. Filter individuals_biosamples
    LOG.debug("----------------------------STEP 4 ----------------------------------")
    list_individuals_biosamples_tmp = []
    
    # Get all biosamples_individuals
    await get_all_individuals_biosamples()

    # filter
    list_individuals_biosamples_tmp = await filter_individuals_biosamples(INDIVIDUALS, list_individuals_ids_final)
    LOG.debug(list_individuals_biosamples_tmp)

    # 5. Filter variants with biosamples
    LOG.debug("----------------------------STEP 5 ----------------------------------")
    list_biosamples_ids_variants = []
    if qparams.query.request_parameters and len(qparams.query.request_parameters) > 0:        
        filters_variants = {
            "meta": {
                "beaconId": "SARS-CoV-2-beacon.clinbioinfosspa.es",
                "apiVersion": "v2.0"
            },
            "query": {
                    "pagination": {"limit": 999},
                    "requestedGranularity": "record"
            } 
        }  
        #if 'requestParameters' in request:
        filters_variants['query']['requestParameters'] = qparams.query.request_parameters
        LOG.debug(filters_variants)

        # 5.1 Get variants
        LOG.debug("5.1")        
        response_variants = await g_variants("POST", filters_variants, query)
        exists_variants = response_variants['responseSummary']['exists']
        list_variants = response_variants['response']['resultSets'][0]["results"] if exists_variants else []
        LOG.debug(exists_variants)

        # 5.2. Filter variants with biosamples        
        LOG.debug("5.2")        
        list_biosamples_ids_variants = [elem['caseLevelData'][0]['biosampleId'] for elem in list_variants] if exists_variants and list_variants else []                
        LOG.debug(list_biosamples_ids_variants)

    # 6. Intersection 4.individuals_biosamples & 5. variants_biosamples
    LOG.debug("----------------------------STEP 6 ----------------------------------")
    count = 0
    LOG.debug(qparams.query.request_parameters and len(qparams.query.request_parameters) > 0)
    LOG.debug(list_biosamples_ids_variants)
    LOG.debug(list_individuals_biosamples_tmp)
    if qparams.query.request_parameters and len(qparams.query.request_parameters) > 0:
        if len(list_biosamples_ids_variants) == 0  or len(list_individuals_biosamples_tmp) == 0:
            count = 0
        else:
            LOG.debug(list_individuals_biosamples_tmp)            

            # filter by individuals            
            list_individuals_biosamples_aux_tmp = await filter_individuals_biosamples(BIOSAMPLES, list_biosamples_ids_variants)
            LOG.debug(list_individuals_biosamples_aux_tmp)

            list_intersec = list(set(list_individuals_biosamples_aux_tmp.keys()).intersection(set(list_individuals_biosamples_tmp))) if len(list_individuals_biosamples_aux_tmp) > 0 and len(list_individuals_biosamples_tmp) > 0 else []
            count = len(list_intersec)
            LOG.debug(list_intersec)
    else:        
        count = len(list_individuals_biosamples_tmp) if len(list_individuals_biosamples_tmp) > 0 else 0
        LOG.debug(list_individuals_biosamples_tmp)

    response_data["responseSummary"]['numTotalResults'] = count
    response_data["responseSummary"]['exists'] =  True if count > 0 else False

    return web.json_response(response_data)


# 1. Get only ids individuals
async def get_ids_individuals(json_body, query, qparams):
    list_individuals_ids = []
    
    filter_individuals = {
        "meta": {
            "beaconId": "SARS-CoV-2-beacon.clinbioinfosspa.es",
            "apiVersion": "v2.0"
        },
        "query": {
            'filters': ["query"]["filters"] if "query" in json_body and "filters" in json_body["query"] else [],
            'pagination': {'skip': 0, 'limit': 999},
            "requestedGranularity": "record",                
        }
    }    
    LOG.info("filter_individuals")
    LOG.info(filter_individuals)

    # individuals
    response_individuals = await individuals("POST", filter_individuals, {})
    LOG.debug(response_individuals['responseSummary'])
    
    exists_individuals = response_individuals['responseSummary']['exists']
    
    if exists_individuals:
        list_individuals = response_individuals['response']['resultSets'][0]['results']
    
        # get ids individuals
        list_individuals_ids = [elem['id'] for elem in list_individuals] if exists_individuals and list_individuals else []
        LOG.debug("list_individuals_id")
        LOG.debug(list_individuals_ids)
        
    return list_individuals_ids



# 2. Get only ids individuals img
async def get_ids_individuals_img(json_body, action, query, qparams):
    list_individuals_ids = []
    filter_individuals = {
        #"meta": qparams.meta,
        # TODO
        "meta": {
            "beaconId": "SARS-CoV-2-beacon.clinbioinfosspa.es",
            "apiVersion": "v2.0"
        },
        "query": {
            # TODO: remove test
            # 'filters': list(qparams),
            'filters': json_body["query"]["filtersImg"] if "filtersImg" in json_body["query"] else [],
            'pagination': {'skip': 0, 'limit': 999},
            "requestedGranularity": "record",
        }
    }    
    LOG.debug("filter_individuals_img")
    LOG.debug(action)
    LOG.debug(filter_individuals)

    # individuals
    response_individuals = await individuals_img("POST", action, filter_individuals, {})
    exists_individuals = response_individuals['responseSummary']['exists']
    
    if exists_individuals:
        list_individuals = response_individuals['response']['resultSets'][0]['results']
    
        # get ids individuals
        list_individuals_ids = [elem['person_id'] for elem in list_individuals] if exists_individuals and list_individuals else []
        LOG.debug("list_individuals_ids")
        LOG.debug(list_individuals_ids)
        
    return list_individuals_ids



# 2.1 Get only ids individuals itersect all filters
async def get_ids_individuals_img_intersec(json_body, query, qparams):
    list_individuals_ids = []

    if len(qparams) == 0:
        list_individuals_ids = await get_ids_individuals_img(json_body, "occurrences", query, qparams)
        LOG.debug("list_individuals_ids")
        LOG.debug(list_individuals_ids)
    else:
        list_individuals_ids_itersec = []
        LOG.debug(qparams)
        index = 0
        for qp in qparams:            
            LOG.debug(qparams[index])
            json_body['query']['filtersImg'] = [qp]
            ids = await get_ids_individuals_img(json_body, qparams[index]["scope"], query, [qp])
            LOG.debug(ids)
            if index > 1:
                list_individuals_ids_itersec = list(set(list_individuals_ids_itersec).intersection(set(ids)))
            else:
                list_individuals_ids_itersec = ids.copy()
            index = index + 1
            LOG.debug(list_individuals_ids_itersec)
            LOG.debug("index")
            LOG.debug(index)
        list_individuals_ids =  list_individuals_ids_itersec.copy()                
        
    return list_individuals_ids




# 4.2. Get filter biosamples_id
async def filter_individuals_biosamples(option, list_ids):
    LOG.debug("filter_individuals_biosamples")
    list_filter_individuals_biosamples_ids = {}
    LOG.debug(option)
    if option == BIOSAMPLES:
        if INDIVIDUALS_BIOSAMPLES and len(INDIVIDUALS_BIOSAMPLES) > 0:
            for biosample_id in list_ids:
                for key in INDIVIDUALS_BIOSAMPLES:
                    if biosample_id in INDIVIDUALS_BIOSAMPLES[key]:
                        list_filter_individuals_biosamples_ids[key] = INDIVIDUALS_BIOSAMPLES[key]
                        break    
    else:
        if INDIVIDUALS_BIOSAMPLES and len(INDIVIDUALS_BIOSAMPLES) > 0:
            for individual_id in INDIVIDUALS_BIOSAMPLES.keys():
                if individual_id in list_ids:
                    list_filter_individuals_biosamples_ids[individual_id] =  INDIVIDUALS_BIOSAMPLES[individual_id]
    
    LOG.debug(list_filter_individuals_biosamples_ids)
    return list_filter_individuals_biosamples_ids


# 4.3. Get filter biosamples_id
async def individuals_biosamples(option, individuals_biosamples):
    results = []
    if option == BIOSAMPLES:
        for bi in individuals_biosamples:
            results.extend(individuals_biosamples[bi])           
    else:
        results = individuals_biosamples.keys()

    return results 


# 4.1. Get all individuals_biosamples
async def get_all_individuals_biosamples():
    LOG.debug(INDIVIDUALS_BIOSAMPLES)
    if not INDIVIDUALS_BIOSAMPLES or len(INDIVIDUALS_BIOSAMPLES) == 0:
        response_biosamples = await biosamples("GET", {'limit':999}, {})
        exists_biosamples = response_biosamples['responseSummary']['exists']
        list_biosamples = response_biosamples['response']['resultSets'][0]['results']    

        if exists_biosamples and list_biosamples:
            for elem in list_biosamples:                
                individual_id = elem['individualId']
                #LOG.debug(individual_id)
                if individual_id in INDIVIDUALS_BIOSAMPLES:
                    INDIVIDUALS_BIOSAMPLES[individual_id].append(elem['id'])
                else:
                    INDIVIDUALS_BIOSAMPLES[individual_id] = [elem['id']]

    LOG.debug(INDIVIDUALS_BIOSAMPLES)


def default_response(json_body, granularity):
    return {
            "meta":{
                "beaconId":"SARS-CoV-2-beacon.clinbioinfosspa.es",
                "apiVersion":"v2.0.0",
                "returnedGranularity": granularity,
                "receivedRequestSummary": {
                    "apiVersion":"v2.0.0",
                    "requestedSchemas":[],
                    "filters": json_body["query"]["filters"] if "query" in json_body and "filters" in json_body["query"] else [],
                    "requestParameters": json_body["query"]["requestParameters"] if "query" in json_body and "requestParameters" in json_body["query"] else {},
                    "includeResultsetResponses": "HIT",
                    "pagination": json_body["pagination"] if "pagination" in json_body else {},
                    "requestedGranularity": granularity,
                    "testMode": False
                },
                "returnedSchemas":[],
                },                
            "responseSummary": {
                "exists": False,
                "numTotalResults": 0
                },
            "resultsHandover":{},
        }

async def individuals(method, json_body, query):  
    LOG.info("individuals")
    
    if method == 'POST':        
        response_data = await post_redirect(conf.uri_clinical+ "individuals", json_body, query)        
    else:
        response_data = await get_redirect(conf.uri_clinical+ "individuals", query)

    return response_data


async def g_variants(method, json_body, query):  
    if method == 'POST':
        # if "requestParameters" in json_body["query"] and json_body["query"]["requestParameters"] and len(json_body["query"]["requestParameters"]) > 0:
        response_data = default_response(json_body, json_body["query"]["requestedGranularity"])            
        
        condition = True
        skip = 0
        limit = 4
        num_variant_processed = 0
        while condition:
            LOG.debug("-----------skip---------")
            LOG.debug(skip)
            json_body['query']['pagination']['skip'] = skip
            response_variants = await post_redirect(conf.uri_genomic + "g_variants", json_body, query)
            
            exists_variants = response_variants["responseSummary"]["exists"] if "responseSummary" in response_variants else []
            LOG.debug(exists_variants)
            
            list_variants = response_variants['response']['resultSets'][0]['results'] if exists_variants else []
            numTotalResults = response_variants["responseSummary"]['numTotalResults'] if exists_variants else 0
            
            if skip == 0 and exists_variants:
                response_data['responseSummary']['exists'] = exists_variants
                response_data['responseSummary']['numTotalResults'] = numTotalResults
                if exists_variants:
                    response_data['response'] = {
                        "resultSets": [                                
                            { 
                                # "id": "SARS-CoV-2",
                                # "setType":"dataset",
                                # "exists": exists_variants,
                                "results" : [],
                                "resultsCount" : numTotalResults,
                            }
                        ]
                    }
            if exists_variants:
                response_data['response']["resultSets"][0]["results"].extend(list_variants) 

            num_variant_processed = num_variant_processed + len(list_variants)                
            
            if skip > limit or num_variant_processed == numTotalResults:
                condition = False

            skip = skip + 1
    else:
        response_data = await get_redirect(conf.uri_genomic + "g_variants", query)

    return response_data


async def biosamples(method, json_body, query):    
    if method == 'POST':      
        response_data = await post_redirect(conf.uri_genomic + "biosamples", json_body, query)
    else:
        response_data = await get_redirect(conf.uri_genomic + "biosamples?limit=999", query)
    
    return response_data


async def individuals_img(method, action, json_body, query):    
    if method == 'POST':      
        response_data = await post_redirect(conf.uri_imagen + action, json_body, query)
    else:
        response_data = await get_redirect(conf.uri_imagen + action, query)
    
    return response_data
