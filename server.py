import http.server
import socketserver
import requests
import termcolor
import json
from Seq import Seq


def species_connect(server, endpoint, para):
    if 'specie' in para.keys():
        specie = para['specie']
        try:
            chromo = para['chromo']
        except KeyError:
            chromo = ""
        url_link = server + endpoint + specie + "/" + chromo
        r = requests.get(url_link, headers={"Content-Type": "application/json"})
        if not r.ok:
            error = r.json()['error']
            return {'error': error}

        try:
            length = r.json()['length']
            return {'length': length}
        except KeyError:
            data_karyotype = r.json()['karyotype']
            return {'karyotype': data_karyotype}

    else:
        r = requests.get(server + endpoint, headers={"Content-Type": "application/json"})

        if not r.ok:
            error = r.json()['error']
            return {'error': error}

        data_species = r.json()['species']
        return {'list_species': data_species}


def get_id(server, name):
    endpoint = "/xrefs/symbol/homo_sapiens/" + name['gene']
    url_link = server + endpoint
    r = requests.get(url_link, headers={"Content-Type": "application/json"})

    try:
        gene_id = r.json()[0]['id']
    except IndexError:
        error = "Bad Request for url: " + '<a href="{}">{}</a>'.format(url_link, url_link) + " Gene name does not exist"
        return {'error': error}
    return {'gene_id': gene_id}


def get_gene_data(server, gene_id):
    endpoint = "/sequence/id/" + gene_id['gene_id']
    data_id = json.dumps({"ids": [gene_id]})
    r = requests.get(server + endpoint, headers={"Content-Type": "application/json"}, data=data_id)
    gene_data = r.json()
    return {'gene_data': gene_data}


def gene_calc(gene_seq):
    seq_calc = Seq(gene_seq)
    bases = set(seq_calc.strbases)
    p_bases = {}
    c_bases = {}
    for base in bases:
        p_bases.update({base: str(seq_calc.perc(base)) + "%"})
        c_bases.update({base: seq_calc.count(base)})
    bases_data = {'p_bases': p_bases, 'c_bases': c_bases}
    return bases_data


def gene_list(server, parameters):
    chromo = parameters['chromo']
    start = parameters['start']
    end = parameters['end']
    endpoint = "/overlap/region/human/{}:{}-{}?feature=gene".format(chromo, start, end)
    url_link = server + endpoint
    r = requests.get(url_link, headers={"Content-Type": "application/json"})
    if not r.ok:
        error = r.json()['error']
        return {'error': error}
    list_gene = r.json()
    if not list_gene:
        return {'list_gene': "The is no gene between positions {} and {} in chromosome {}". format(start, end, chromo)}
    return {'list_gene': list_gene}


def url_wrong():
    return {'error': "Something went wrong with the parameters"}


class TestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        contents = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>EnsemblRequest</title></head>"""
        server = "http://rest.ensembl.org"
        termcolor.cprint(self.requestline, 'blue')
        total_request = self.path.split('?')
        request = total_request.pop(0)
        json_para = False
        data = ""
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
            data = {'Error': "No endpoint given"}
            f.close()

        else:
            if request == "/listSpecies":
                endpoint = "/info/species"
                if not para:
                    para.update({'limit': 199})
                elif 'limit' not in para.keys():
                    contents += """<body><h1> Something went wrong</h1>The parameters are not correct"""
                    data = {'error': "Parameters are not correct"}
                elif not para['limit']:
                    para.update({'limit': 199})
                if 'limit' in para.keys():
                    try:
                        limit = int(para['limit'])
                    except ValueError:
                        limit = "Limit must be an integer"
                    data = species_connect(server, endpoint, para)
                    if type(limit) is int:
                        list_species = list()
                        try:
                            for i in range(limit):
                                list_species.append(data['list_species'][i]['name'])
                            contents += """<body><h1>List of species</h1>
                                                    <ul><li>{}</li><ul>""".format("</li><li>".join(list_species))
                        except IndexError:
                            list_species = "The limit can't be superior to 199"
                            contents += """<body><h1>List of species</h1>
                                                        <ul>{}<ul>""".format(list_species)

                    else:
                        list_species = "The limit must be an integer"
                        contents += """<body><h1>List of species</h1>
                                                        <ul>{}<ul>""".format(list_species)
                    data = {'list_species': list_species}

            elif request == "/karyotype":
                endpoint = "/info/assembly/"
                if 'specie' not in para.keys():
                    contents += """<body><h1> Something went wrong</h1>The parameters are not correct"""
                    data = {'error': "Parameters are not correct"}
                elif not para['specie']:
                    contents += """<body><h1> Something went wrong</h1>You must fill the specie form"""
                    data = {'error': "Parameters are not correct"}
                else:
                    data = species_connect(server, endpoint, para)
                    if data:
                        list_karyotype = "<ul>"
                        if 'karyotype' in data.keys():
                            for i in range(len(data['karyotype'])):
                                list_karyotype += "<li>" + data['karyotype'][i] + "</li>"
                            list_karyotype += "<ul>"
                        else:
                            list_karyotype += data['error']
                        list_karyotype += "<ul>"
                    else:
                        list_karyotype = "<ul> There is no available information for the karyotype of this specie <ul>"
                    contents += """<body><h1>{} Karyotype information</h1>{}""".format(para['specie'], list_karyotype)

            elif request == "/chromosomeLength":
                endpoint = "/info/assembly/"
                if 'specie' not in para.keys() or 'chromo' not in para.keys():
                    contents += """<body><h1> Something went wrong</h1>The parameters are not correct"""
                    data = {'error': "Parameters are not correct"}
                elif not para['specie'] or not para['chromo']:
                    contents += """<body><h1>Something went wrong</h1>Must fill the chromosome and the specie form"""
                    data = {'error': "Parameters are not correct"}
                else:
                    data = species_connect(server, endpoint, para)
                    if 'length' in data.keys():
                        contents += """<body><h2>Chromosome length</h2>
                        Chromosome {} of {} is {} length""".format(para['chromo'], para['specie'], data['length'])
                    else:
                        contents += """<body><h2>Something went wrong in the request</h2>{}""".format(data['error'])

            elif request.startswith("/gene"):
                gene_request = request.lstrip("/gene")

                if gene_request == "List":
                    if ('chromo' or 'start' or 'end') not in para.keys():
                        contents += """<body><h1> Something went wrong</h1>The parameters are not correct"""
                        data = {'error': "Parameters are not correct"}
                    elif not (para['chromo'] or para['start'] or para['end']):
                        contents += """<body><h1> Something went wrong</h1>You must fill the form"""
                        data = {'error': "Parameters are not correct"}
                    else:
                        data = gene_list(server, para)
                        list_gene = list()
                        if 'list_gene' in data.keys():
                            for i in range(len(data['list_gene'])):
                                list_gene.append(data['list_gene'][i]['external_name'])
                            data = {'list_gene': list_gene}
                        else:
                            list_gene.append(data['error'])
                            data = {'error': list_gene}
                        contents += """<body><h2>Genes list</h2>
                        <h3>    Chromosome {}. Start position: {}. End position: {}</h3>
                        <p><li>{}</p>""".format(para['chromo'], para['start'], para['end'], "</li><li>".join(list_gene))
                elif 'gene' not in para.keys():
                    contents += """<body><h1> Something went wrong</h1>The parameters are not correct"""
                    data = {'error': "Parameters are not correct"}
                elif not para['gene']:
                    contents += """<body><h1> Something went wrong</h1>You must fill the form"""
                    data = {'error': "Parameters are not correct"}

                else:
                    gene_id = get_id(server, para)
                    if 'gene_id' in gene_id.keys():
                        g_data = get_gene_data(server, gene_id)
                        if 'gene_data' in g_data.keys():
                            data = g_data['gene_data']['seq']

                            if gene_request == "Seq":
                                contents += """<body><h2>Gene sequence</h2>
                                 <p style='word-break: break-all'>{}</p>""".format(data)
                                data = {'gene_seq': data}

                            elif gene_request == "Info":
                                    desc_data = g_data['gene_data']['desc'].split(":")
                                    data = {'gene_id': g_data['gene_data']['id'], 'start': desc_data[3],
                                            'end': desc_data[4], 'chromosome': desc_data[2], 'length': len(data)}
                                    # noinspection PyTypeChecker
                                    contents += """<body><h2>Gene information</h2>
                                     <p>Gene Id: {}</p><p>Start Position: {}</p>
                                     <p>End Position: {}</p><p>Chromosome: {}</p><p>Length: {}
                                     </p>""".format(data['gene_id'], data['start'],
                                                    data['end'], data['chromosome'], data['length'])

                            elif gene_request == "Calc":
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
                            data = g_data
                            contents += """<body><h1> Something went wrong</h1><p>{}</p>""".format(data['error'])

                    else:
                        data = gene_id
                        contents += """<body><h1> Something went wrong</h1><p>{}</p>""".format(data['error'])

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
