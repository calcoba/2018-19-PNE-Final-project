
import json
import requests

# -- API information
HOSTNAME = "http://localhost:8000"
ENDPOINTS = "/listSpecies?limit=10&json=1", "/listSpecies?json=1", \
    "/karyotype?specie=mouse&json=1", "/chromosomeLength?specie=mouse&chromo=18&json=1","/geneSeq?gene=FRAT1&json=1", \
            "/geneInfo?gene=FRAT1&json=1", "/geneCalc?gene=FRAT1&json=1", "/geneList?chromo=1&start=0&end=30000&json=1"
headers = {'User-Agent': 'http-client'}
for endpoint in ENDPOINTS:
    url_link = HOSTNAME + endpoint + "&json=1"

    r = requests.get(url_link, headers={"Content-Type": "application/json"})
    # -- Read the response's body and close
    # -- the connection
    text_json = r.json()

    # -- Optionally you can print the
    # -- received json file for testing
    # print(text_json)

    # -- Generate the object from the json file

    print(text_json)

