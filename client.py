import requests

# -- API information
HOSTNAME = "http://localhost:8000"
ENDPOINTS = "/listSpecies?limit=10&json=1", "/listSpecies?json=1", "/karyotype?specie=mouse&json=1", \
            "/chromosomeLength?specie=mouse&chromo=18&json=1", "/geneSeq?gene=FRAT1&json=1", \
            "/geneInfo?gene=FRAT1&json=1", "/geneCalc?gene=FRAT1&json=1", \
            "/geneList?chromo=1&start=0&end=30000&json=1", "/listSpecies?limeit=10&json=1", \
            "/listSpecies?limit=1e0&json=1", "/karyotype?speecie=mouese&json=1", \
            "/chromosomeLength?specie=moeuse&chromo=18&json=1", "/geneSeq?gene=FReAT1&json=1", \
            "/geneInfo?gene=FeRAT1&json=1", "/geneCalc?gene=FReAT1&json=1", \
            "/geneList?chromo=1&start=0&end=300000&json=1", "/geneList?chromo=e&start=0&end=30000&json=1", \
            "/geneList?chromo=1&start=30001&end=30000&json=1", "/geneList?chromo=1&start=10&end=500000000&json=1", \
            "/geneList?chromo=1&start=2000000000000&end=2000000000001&json=1"
headers = {'User-Agent': 'http-client'}
for endpoint in ENDPOINTS:
    url_link = HOSTNAME + endpoint

    r = requests.get(url_link, headers={"Content-Type": "application/json"})

    text_json = r.json()

    print(text_json)
