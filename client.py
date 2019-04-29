
import requests

# -- API information
HOSTNAME = "http://localhost:8000"
ENDPOINTS = "/listSpecies?limit=10&json=1", "/listSpecies?json=1", \
    "/karyotype?specie=mouse&json=1", "/chromosomeLength?specie=mouse&chromo=18&json=1", "/geneSeq?gene=FRAT1&json=1", \
            "/geneInfo?gene=FRAT1&json=1", "/geneCalc?gene=FRAT1&json=1", "/geneList?chromo=1&start=0&end=30000&json=1"
headers = {'User-Agent': 'http-client'}
for endpoint in ENDPOINTS:
    url_link = HOSTNAME + endpoint + "&json=1"

    r = requests.get(url_link, headers={"Content-Type": "application/json"})

    text_json = r.json()

    print(text_json)
