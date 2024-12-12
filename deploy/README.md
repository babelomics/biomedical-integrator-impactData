# Deployment instructions


## Prerequisites

You should have installed:

- [Docker](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3](https://www.python.org/downloads/)

## Installation

All of the commands should be executed from the deploy directory.

```bash
cd deploy
```


#### Up the containers

If you are using a build with all the services in the same cluster, you can use:

```bash
docker-compose up -d --build
```


#### Check the logs

Check the logs until the beacon is ready to be queried:

```bash
docker-compose logs -f beacon
```

## Usage

You can query the beacon using GET or POST. Below, you can find some examples of usage:

> For simplicity (and readability), we will be using [HTTPie](https://github.com/httpie/httpie).


### Using GET



Querying this endpoit it should return the variants of the beacon (paginated):

```bash
http GET http://localhost:5050/api/g_variants
```

You can also add [request parameters](https://github.com/ga4gh-beacon/beacon-v2-Models/blob/main/BEACON-V2-Model/genomicVariations/requestParameters.json) to the query, like so:

```bash
http GET http://localhost:5050/api/individuals?filters=NCIT:C16576,NCIT:C42331
```

### Using POST

You can use POST to make the previous query. With a `request.json` file like this one:

```json
{
    "meta": {
        "apiVersion": "2.0"
    },
    "query": {
        "requestParameters": {
    "alternateBases": "G" ,
    "referenceBases": "A" ,
    "start": [ 16050074 ],
            "end": [ 16050568 ],
	    "variantType": "SNP"
        },
        "filters": [],
        "includeResultsetResponses": "HIT",
        "pagination": {
            "skip": 0,
            "limit": 10
        },
        "testMode": false,
        "requestedGranularity": "record"
    }
}

```

You can execute:

```bash
curl \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "meta": {
        "apiVersion": "2.0"
    },
    "query": {
        "requestParameters": {
    "alternateBases": "G" ,
    "referenceBases": "A" ,
"start": [ 16050074 ],
            "end": [ 16050568 ],
	    "variantType": "SNP"
        },
        "filters": [],
        "includeResultsetResponses": "HIT",
        "pagination": {
            "skip": 0,
            "limit": 10
        },
        "testMode": false,
        "requestedGranularity": "record"
    }
}' \
  http://localhost:5050/api/g_variants


```

But you can also use complex filters:

```json
{
    "meta": {
        "apiVersion": "2.0"
    },
    "query": {
        "filters": [
            {
                "id": "UBERON:0000178",
                "scope": "biosample",
                "includeDescendantTerms": false
            }
        ],
        "includeResultsetResponses": "HIT",
        "pagination": {
            "skip": 0,
            "limit": 10
        },
        "testMode": false,
        "requestedGranularity": "count"
    }
}
```

