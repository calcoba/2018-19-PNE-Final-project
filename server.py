import http.server
import socketserver
import requests
import sys
import termcolor


def species_connect(endpoint, limit=162, specie="", chromo=""):
    server = "http://rest.ensembl.org"
    if specie:
        r = requests.get(server + endpoint + specie + "/" + chromo, headers={"Content-Type": "application/json"})
        if not r.ok:
            if r.status_code == 400:
                return "Error 400 Client Error: Bad Request for url:", server + endpoint + specie
            else:
                return "Error", r.status_code()

        try:
            length = r.json()['length']
            return length
        except KeyError:
            data_karyotype = r.json()['karyotype']
            print(data_karyotype, 1)
            if data_karyotype:
                list_karyotype = "<ul>"
                for i in range(len(data_karyotype)):
                    list_karyotype += "<li>" + data_karyotype[i] + "</li>"
                list_karyotype += "<ul>"
            else:
                list_karyotype = "<ul> There is no available information for the karyotype of this specie <ul>"
            return list_karyotype

    else:
        r = requests.get(server + endpoint, headers={"Content-Type": "application/json"})

        if not r.ok:
            r.raise_for_status()
            sys.exit()

        data_species = r.json()['species']
        if type(limit) is int:
            list_species = "<ul>"
            try:
                for i in range(limit):
                    list_species += "<li>"+str(data_species[i]['name'])+"</li>"
                list_species += "<ul>"
            except IndexError:
                list_species = "The limit can't be superior to 162"
        else:
            list_species = "The limit must be an integer"
        return list_species


def get_id(name):
    server = "http://rest.ensembl.org"
    endpoint = "/xrefs/symbol/homo_sapiens/" + name
    r = requests.get(server + endpoint, headers={"Content-Type": "application/json"})
    if not r.ok:
        if r.status_code == 400:
            return "Error 400 Client Error: Bad Request for url:", server + endpoint
        else:
            return "Error", r.status_code()
    gene_id = r.json()[0]['id']
    return gene_id


def gene_seq(gene_id):
    server = "http://rest.ensembl.org"
    endpoint = "/sequence/id/" + gene_id
    r = requests.get(server + endpoint, headers={"Content-Type": "application/json"})
    if not r.ok:
        if r.status_code == 400:
            return "Error 400 Client Error: Bad Request for url:", server + endpoint
        else:
            return "Error", r.status_code()


class TestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        # Printing the request line
        contents = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>EnsemblRequest</title></head>"""
        termcolor.cprint(self.requestline, 'blue')
        total_request = self.path.split('?')
        request = total_request.pop(0)
        try:
            r_para = total_request[0].split('&')
        except IndexError:
            r_para = ""

        if request == "/":
            f = open("form.html", 'r')
            contents = f.read()
            f.close()

        else:
            if request == "/listSpecies":
                endpoint = "/info/species"
                if total_request:
                    try:
                        limit = int(r_para[0].split('=')[-1])
                        list_species = species_connect(endpoint, limit)
                    except ValueError:
                        list_species = species_connect(endpoint)
                else:
                    list_species = species_connect(endpoint)
                if type(list_species) is str:
                    contents += """<body><h1>List of species</h1>{}""".format(list_species)

            elif request == "/karyotype":
                endpoint = "/info/assembly/"
                specie = r_para[0].split('=')[-1]
                if not specie:
                    contents += """<body><h1> Something went wrong</h1>You must fill the specie form"""
                else:
                    karyotype = species_connect(endpoint, specie=specie)
                    if type(karyotype) == str:
                        contents += """<body><h1>Karyotype information of {}</h1>{}""".format(specie, karyotype)
                    else:
                        contents += """<body><h2>Something went wrong in the request</h2>{}""".format(" ".join(karyotype))

            elif request == "/chromosomeLength":
                endpoint = "/info/assembly/"
                specie = r_para[0].split('=')[-1]
                chromo = r_para[-1].split('=')[-1]
                if not specie or not chromo:
                    contents += """<body><h1>Something went wrong</h1>Must fill the chromosome and the specie form"""

                else:
                    length = species_connect(endpoint, specie=specie, chromo=chromo)
                    if type(length) is int:
                        contents += """<body><h2>Chromosome length</h2>Chromosome {} of {} specie is {} length""".format(chromo, specie, length)
                    else:
                        contents += """<body><h2>Something went wrong in the request</h2>{}""".format(" ".join(length))

            elif request.startswith("/gene"):
                gene_request = request.lstrip("/gene")
                gene_name = r_para[0].split('=')[-1]
                gene_id = get_id(gene_name)

                if gene_request == "Seq":
                    print(gene_id)
                elif gene_request == "Info":
                    pass
                elif gene_request == "Cal:":
                    pass
                elif gene_request == "List":
                    pass

            else:
                f = open("error.html", 'r')
                contents = f.read()
                f.close()
            contents += """<p><a href="/">Main page</a></p></body></html>"""

        self.send_response(200)

        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(str.encode(contents)))
        self.end_headers()
        print(contents)

        # -- Sending the body of the response message
        self.wfile.write(str.encode(contents))


PORT = 8000
socketserver.TCPServer.allow_reuse_address = True


# -- Main program
with socketserver.TCPServer(("", PORT), TestHandler) as httpd:
    print("Serving at PORT: {}".format(PORT))

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

print("")
print("Server Stopped")
