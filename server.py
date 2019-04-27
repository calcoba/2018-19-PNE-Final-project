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
        if not r.ok:
            if r.status_code == 400:
                error = "Error 400 Client Error: Bad Request for url: "+'<a href="{}">{}</a>'.format(url_link, url_link)
                return {'length': "", 'karyotype': "", 'error': error}
            else:
                error = "Error " + r.status_code()
                return {'length': "", 'karyotype': "", 'error': error}

        try:
            length = r.json()['length']
            return {'length': length}
        except KeyError:
            data_karyotype = r.json()['karyotype']
            return {'karyotype': data_karyotype}

    else:
        r = requests.get(server + endpoint, headers={"Content-Type": "application/json"})

        if not r.ok:
            r.raise_for_status()
            sys.exit()

        data_species = r.json()['species']
        return {'list_species': data_species}


def get_id(name):
    server = "http://rest.ensembl.org"
    endpoint = "/xrefs/symbol/homo_sapiens/" + name['gene']
    url_link = server + endpoint
    r = requests.get(url_link, headers={"Content-Type": "application/json"})

    try:
        gene_id = r.json()[0]['id']
    except IndexError:
        error = "Bad Request for url: " + '<a href="{}">{}</a>'.format(url_link, url_link)
        return {'gene_id': error}
    return {'gene_id': gene_id}


def get_gene_data(gene_id):
    server = "http://rest.ensembl.org"
    try:
        endpoint = "/sequence/id/" + gene_id['gene_id']
    except TypeError:
        return {'gene_data': {'seq': gene_id['gene_id']}}
    data = {"ids": [gene_id]}
    data = json.dumps(data)
    r = requests.get(server + endpoint, headers={"Content-Type": "application/json"}, data=data)
    if not r.ok:
        if r.status_code == 400:
            return {'gene_data': {'seq': gene_id['gene_id']}}
        else:
            error = "Error" + str(r.status_code())
            return {'gene_data': {'seq': error}}
    gene_data = r.json()
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
    bases_data = {'p_bases': p_bases, 'c_bases': c_bases}
    return bases_data


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
            error = "Error 400 Client Error: Bad Request for url: " + '<a href="{}">{}</a>'.format(url_link, url_link)
            return {'list_gene': error}
        else:
            error = "Error" + str(r.status_code())
            return {'list_gene': error}
    list_gene = r.json()
    if not list_gene:
        return {'list_gene': "The chromosome {} isn't between positions {} and {}". format(gene, start, end)}
    return {'list_gene': list_gene}


class TestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        # Printing the request line
        contents = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>EnsemblRequest</title></head>"""
        termcolor.cprint(self.requestline, 'blue')
        total_request = self.path.split('?')
        request = total_request.pop(0)
        json_para = False
        try:
            r_para = total_request[0].split('&')
            para = dict()
            for i in r_para:
                i = i.split("=")
                para.update({i[0]: i[1]})
            if 'json' in para.keys():
                del para['json']
                json_para = True
        except IndexError:
            para = dict()

        if request == "/":
            f = open("form.html", 'r')
            contents = f.read()
            f.close()

        else:
            if request == "/listSpecies":
                endpoint = "/info/species"
                try:
                    limit = int(para['limit'])
                except KeyError:
                    limit = 199
                except ValueError:
                    limit = 199
                except TypeError:
                    limit = 199
                data = species_connect(endpoint, para)
                if type(limit) is int:
                    list_species = list()
                    try:
                        for i in range(limit):
                            list_species.append(data['list_species'][i]['name'])
                    except IndexError:
                        list_species = "The limit can't be superior to 199"
                else:
                    list_species = "The limit must be an integer"
                if type(data['list_species'][i]['name']) is str:
                    contents += """<body><h1>List of species</h1>
                    <ul><li>{}</li><ul>""".format("</li><li>".join(list_species))
                    data = {'list_species': list_species}
                print(data)

            elif request == "/karyotype":
                endpoint = "/info/assembly/"
                if not para['specie']:
                    contents += """<body><h1> Something went wrong</h1>You must fill the specie form"""
                else:
                    data = species_connect(endpoint, para)
                    if data:
                        list_karyotype = "<ul>"
                        for i in range(len(data['karyotype'])):
                            list_karyotype += "<li>" + data['karyotype'][i] + "</li>"
                        list_karyotype += "<ul>"
                    else:
                        list_karyotype = "<ul> There is no available information for the karyotype of this specie <ul>"
                    if type(data['karyotype']) == list:
                        print('OK')
                        contents += """<body><h1>Karyotype information of {}</h1>{}""".format(para['specie'], list_karyotype)
                    else:
                        contents += """<body><h2>Something went wrong in the request</h2>
                        {}""".format(data['error'])

            elif request == "/chromosomeLength":
                endpoint = "/info/assembly/"
                if not para['specie'] or not para['chromo']:
                    contents += """<body><h1>Something went wrong</h1>Must fill the chromosome and the specie form"""
                else:
                    data = species_connect(endpoint, para)
                    if type(data['length']) is int:
                        contents += """<body><h2>Chromosome length</h2>
                        Chromosome {} of {} specie is {} length""".format(para['chromo'], para['specie'], data['length'])
                    else:
                        contents += """<body><h2>Something went wrong in the request</h2>{}""".format(data['error'])

            elif request.startswith("/gene"):
                gene_request = request.lstrip("/gene")

                if gene_request == "List":
                    if not (para['chromo'] or para['start'] or para['end']):
                        contents += """<body><h1> Something went wrong</h1>You must fill the form"""
                    else:
                        data = gene_list(para)
                        list_gene = list()
                        try:
                            for i in range(len(data['list_gene'])):
                                list_gene.append(data['list_gene'][i]['external_name'])
                        except TypeError:
                            list_gene.append(data['list_gene'])
                        contents += """<body><h2>Genes list</h2>
                        <h3>Chromosome {}. Start position: {}. End position: {}</h3>
                        <p><li>{}</p>""".format(para['chromo'], para['start'], para['end'], "</li><li>".join(list_gene))
                        data = {'list_gene': list_gene}

                elif not para['gene']:
                    contents += """<body><h1> Something went wrong</h1>You must fill the form"""

                else:
                    gene_id = get_id(para)
                    if gene_id:
                        g_data = get_gene_data(gene_id)['gene_data']
                        # noinspection PyTypeChecker
                        data = g_data['seq']

                        if gene_request == "Seq":
                            contents += """<body><h2>Gene sequence</h2>
                             <p style='word-break: break-all'>{}</p>""".format(data)
                            data = {'gene_seq': data}

                        elif gene_request == "Info":
                            # noinspection PyTypeChecker
                            try:
                                desc_data = g_data['desc'].split(":")
                                data = {'gene_id': g_data['id'], 'start': desc_data[3], 'end': desc_data[4],
                                        'chromosome': desc_data[2], 'length': len(data)}
                                # noinspection PyTypeChecker
                                contents += """<body><h2>Gene information</h2>
                                 <p>Gene Id: {}</p><p>Start Position: {}</p>
                                 <p>End Position: {}</p><p>Chromosome: {}</p><p>Length: {}
                                 </p>""".format(data['gene_id'], data['start'],
                                                data['end'], data['chromosome'], data['length'])

                            except KeyError:
                                contents += """<body><h2>Gene information</h2>
                            <p style='word-break: break-all'>{}</p>""".format(data)

                        elif gene_request == "Calc":
                            if len(set(data)) <= 4:
                                data = gene_calc(data)
                                p_table = "{:<5} : {:<5}".format('Base', 'Percentage')
                                for k, v in data['p_bases'].items():
                                    p_table += "<p>{:<5} : {:<5}</p>".format(k, v)

                                c_table = "{:<5} : {:<5}".format('Base', 'Count')
                                for k, v in data['c_bases'].items():
                                    c_table += "<p>{:<5} : {:<5}</p>".format(k, v)
                                contents += """<body><h2> {} Gene Calculations</h2>
                                 <p>{}</p>
                                 <p>{}</p>""".format(para['gene'], p_table, c_table)
                            else:
                                contents += """<body><h2>Gene calculation</h2>
                            <p style='word-break: break-all'>{}</p>""".format(data)

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
        else:
            contents = json.dumps(data)
            self.send_response(200)

            self.send_header('Content-Type', 'application/json')
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
