# Integrator Beacon Virus v2.x

This integrator makes use of different components developed in the reference implementation of IMPaCT-Data (https://impact-data-ref-imp.readthedocs.io/es/latest/index.html):

- Beacon v2, for the discovery of genomic data: https://b2ri-documentation.readthedocs.io/en/latest/, adapted to pathogen data, in this case, viral genomes of SARS-CoV-2.
- Beacon-OMOP (B4OMOP), for the discovery of clinical data. This is a development derived from the aforementioned Beacon v2, which allows the integration of a Beacon into any OMOP CDM database. https://gitlab.bsc.es/impact-data/impd-beacon_omopcdm/-/blob/main/README.md
- Beacon4Images, for the discovery of imaging data: https://github.com/EGA-archive/beacon2-ri-api-images

Theys use the implementation of the [Beacon v2.0 Model](https://github.com/ga4gh-beacon/beacon-v2-Models) 

## Urls 

### get
- /api/info (integrator): Displays information about the integrator beacon.
- /api/maps (integrator): Shows the catalog of available urls.
- /api/images/filtering_terms (images): List filters images beacon.
- /api/filtering_terms (clinical): List filters clinical beacon.
- /api/biosamples (genomic)
- /api/g_variants (genomic)
- /api/individuals (clinical)


### post
- /api/biosamples  (genomic)
- /api/g_variants  (genomic)
- /api/individuals (clinical)
- /api/occurrences (images)



> [Local deployment instructions](deploy/README.md)
