from aiohttp import web
from integrator.response import redirect, info, map, handlers  as integrator_handlers

routes = [

    ########################################
    # CONFIG
    ########################################
    
    web.get('/api/info', info.handler),

    web.get('/api/maps', map.handler),

    web.get('/api/images/filtering_terms', integrator_handlers.filtering_terms_img_handler),

    web.get('/api/filtering_terms', integrator_handlers.filtering_terms_handler),


    ########################################
    # GET
    ########################################

    web.get('/api/biosamples', integrator_handlers.biosamples_handler),

    web.get('/api/g_variants', integrator_handlers.g_variants_handler),

    web.get('/api/individuals', integrator_handlers.individuals_handler),

    web.get('/api/{tail:.*}', redirect.handler),
    web.get('/{tail:.*}', redirect.handler),
        
    ########################################
    # POST
    ########################################

    web.post('/api/biosamples', integrator_handlers.biosamples_handler),

    web.post('/api/g_variants', integrator_handlers.g_variants_handler),
   
    web.post('/api/individuals', integrator_handlers.individuals_handler),

    web.post('/api/occurrences', integrator_handlers.occurrences_handler),


    web.post('/api/{tail:.*}', redirect.handler),
    web.post('/{tail:.*}', redirect.handler)
]
