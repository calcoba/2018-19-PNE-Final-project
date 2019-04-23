import http.server
import socketserver
import requests
import sys
import termcolor
import json
from Seq import Seq


def species_connect(endpoint, para):
    server = "http://rest.ensembl.org"
    if 'specie' in para.keys():
        specie = para['specie']
        try:
            chromo = para['chromo']
        except KeyError:
            chromo = ""
        url_link = server + endpoint + specie + "/" + chromo
        r = requests.get(url_link, headers={"Content-Type": "application/json"})
        print(server + endpoint + specie + "/" + chromo)
        if not r.ok:
            if r.status_code == 400:
                error = "Error 400 Client Error: Bad Request for url: "+'<a href="{}">{}</a>'.format(url_link, url_link)
                return {'length': error, 'karyotype': error}
            else:
                error = "Error " + r.status_code()
                return {'length': error, 'karyotype': error}

        try:
            length = r.json()['length']
            return {'length': length}
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
            return {'karyotype': list_karyotype}

    else:
        try:
            limit = int(para['limit'])
        except KeyError:
            limit = 199
        except ValueError:
            limit = 199
        r = requests.get(server + endpoint, headers={"Content-Type": "application/json"})

        if not r.ok:
            r.raise_for_status()
            sys.exit()

        data_species = r.json()['species']
        if type(limit) is int:
            list_species = "<ul>"
            try:
                for i in range(limit):
                    list_species += "<li>"+str(i+1)+" "+str(data_species[i]['name'])+"</li>"
                list_species += "<ul>"
            except IndexError:
                list_species = "The limit can't be superior to 199"
        else:
            list_species = "The limit must be an integer"
        return {'list_species': list_species}


def get_id(name):
    server = "http://rest.ensembl.org"
    endpoint = "/xrefs/symbol/homo_sapiens/" + name['gene']
    url_link = server + endpoint
    r = requests.get(url_link, headers={"Content-Type": "application/json"})
    if not r.ok:
        if r.status_code == 400:
            return "Error 400 Client Error: Bad Request for url: " + '<a href="{}">{}</a>'.format(url_link, url_link)
        else:
            return "Error " + r.status_code()
    try:
        gene_id = r.json()[0]['id']
    except IndexError:
        return
    return {'gene_id': gene_id}


def get_gene_data(gene_id):
    server = "http://rest.ensembl.org"
    endpoint = "/sequence/id/" + gene_id
    data = {"ids": [gene_id]}
    data = json.dumps(data)
    print(data)
    r = requests.get(server + endpoint, headers={"Content-Type": "application/json"}, data=data)
    if not r.ok:
        if r.status_code == 400:
            return "Error 400 Client Error: Bad Request for url:", server + endpoint
        else:
            return "Error", r.status_code()
    gene_data = r.json()
    print(type(gene_data))
    return {'gene_data': gene_data}


def gene_calc(gene_seq):
    seq_calc = Seq(gene_seq)
    bases = set(seq_calc.strbases)
    p_bases = {}
    c_bases = {}
    print(1)
    for base in bases:
        p_bases.update({base: str(seq_calc.perc(base)) + "%"})
        c_bases.update({base: seq_calc.count(base)})

    p_table = "{:<5} : {:<5}".format('Base', 'Percentage')
    for k, v in p_bases.items():
        p_table += "<p>{:<5} : {:<5}</p>".format(k, v)

    c_table = "{:<5} : {:<5}".format('Base', 'Count')
    for k, v in c_bases.items():
        c_table += "<p>{:<5} : {:<5}</p>".format(k, v)

    return p_table, c_table


def gene_list(parameters):
    gene = parameters['chromo']
    start = parameters['start']
    end = parameters['end']
    server = "http://rest.ensembl.org"
    endpoint = "/overlap/region/human/{}:{}-{}?feature=gene".format(gene, start, end)
    url_link = server + endpoint
    r = requests.get(url_link, headers={"Content-Type": "application/json"})
    if not r.ok:
        if r.status_code == 400:
            return "Error 400 Client Error: Bad Request for url: " + '<a href="{}">{}</a>'.format(url_link, url_link)
        else:
            return "Error", r.status_code()
    decoded = r.json()
    if 'error' in decoded[0].keys():
        return decoded['error']
    else:
        list_gene = "<ul>"
        for i in range(len(decoded)):
            list_gene += "<li>"+str(i+1)+" "+str(decoded[i]['external_name'])+"</li>"
        list_gene += "</ul>"
        return {'list_gene': list_gene}


class TestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        # Printing the request line
        contents = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>EnsemblRequest</title></head>"""
        termcolor.cprint(self.requestline, 'blue')
        total_request = self.path.split('?')
        request = total_request.pop(0)
        try:
            r_para = total_request[0].split('&')
            para = dict()
            for i in r_para:
                i = i.split("=")
                para.update({i[0]: i[1]})
            if 'json' in para.keys():
                del para['json']
                json_para = True
            else:
                json_para = False
        except IndexError:
            para = ""

        if request == "/":
            f = open("form.html", 'r')
            contents = f.read()
            f.close()

        else:
            if request == "/listSpecies":
                endpoint = "/info/species"
                if total_request:
                    try:
                        list_species = species_connect(endpoint, para)['list_species']
                    except ValueError:
                        para = dict()
                        list_species = species_connect(endpoint, para)['list_species']
                else:
                    para = dict()
                    list_species = species_connect(endpoint, para)['list_species']
                if type(list_species) is str:
                    contents += """<body><h1>List of species</h1>{}""".format(list_species)

            elif request == "/karyotype":
                endpoint = "/info/assembly/"
                if not para['specie']:
                    contents += """<body><h1> Something went wrong</h1>You must fill the specie form"""
                else:
                    karyotype = species_connect(endpoint, para)['karyotype']
                    if type(karyotype) == str:
                        contents += """<body><h1>Karyotype information of {}</h1>{}""".format(para['specie'], karyotype)
                    else:
                        contents += """<body><h2>Something went wrong in the request</h2>
                        {}""".format(" ".join(karyotype))

            elif request == "/chromosomeLength":
                endpoint = "/info/assembly/"
                if not para['specie'] or not para['chromo']:
                    contents += """<body><h1>Something went wrong</h1>Must fill the chromosome and the specie form"""
                else:
                    length = species_connect(endpoint, para)['length']
                    if type(length) is int:
                        contents += """<body><h2>Chromosome length</h2>
                        Chromosome {} of {} specie is {} length""".format(para['chromo'], para['specie'], length)
                    else:
                        contents += """<body><h2>Something went wrong in the request</h2>{}""".format(" ".join(length))

            elif request.startswith("/gene"):
                gene_request = request.lstrip("/gene")

                if gene_request == "List":
                    list_gene = gene_list(para)['list_gene']
                    contents += """<body><h2>Genes list</h2>
                             <p>{}</p>""".format(list_gene)
                else:
                    gene_id = get_id(para)['gene_id']
                    if gene_id:
                        g_data = get_gene_data(gene_id)['gene_data']
                        # noinspection PyTypeChecker
                        g_seq = g_data['seq']

                        if gene_request == "Seq":
                            contents += """<body><h2>Gene sequence</h2>
                             <p style='word-break: break-all'>{}</p>""".format(g_seq)

                        elif gene_request == "Info":
                            # noinspection PyTypeChecker
                            desc_data = g_data['desc'].split(":")
                            # noinspection PyTypeChecker
                            contents += """<body><h2>Gene sequence</h2>
                             <p>Gene Id: {}</p>
                             <p>Start Position: {}</p>
                             <p>End Position: {}</p>
                             <p>Chromosome: {}</p>
                    <p>Length: {}</p>""".format(g_data['id'], desc_data[3], desc_data[4], desc_data[2], len(g_seq))

                        elif gene_request == "Calc":
                            p_table, c_table = gene_calc(g_seq)
                            contents += """<body><h2> {} Gene Calculations</h2>
                             <p>{}</p>
                             <p>{}</p>""".format(para['gene'], p_table, c_table)

                    else:
                        f = open("error.html", 'r')
                        contents = f.read()
                        f.close()

            else:
                f = open("error.html", 'r')
                contents = f.read()
                f.close()
            contents += """<p><a href="/">Main page</a></p></body></html>"""
        if not json_para:
            self.send_response(200)

            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(str.encode(contents)))
            self.end_headers()

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
