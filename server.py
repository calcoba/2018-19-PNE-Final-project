import http.server
import socketserver
import requests
import sys


def connection(endpoint, limit=162, specie=""):
    server = "http://rest.ensembl.org"
    if specie:
        r = requests.get(server + endpoint + specie, headers={"Content-Type": "application/json"})

        if not r.ok:
            r.raise_for_status()
            sys.exit()

        decoded = r.json()
        data_karyotype = decoded['karyotype']
        if data_karyotype:
            list_karyotype = "<ul>"
            for i in range(len(data_karyotype)):
                list_karyotype += "<li>" + data_karyotype[i] + "</li>"
            list_karyotype += "<ul>"
        else:
            list_karyotype= "<ul> There is no available information for the karyotyoe of this specie <ul>"
        return list_karyotype

    else:
        r = requests.get(server + str(endpoint), headers={"Content-Type": "application/json"})

        if not r.ok:
            r.raise_for_status()
            sys.exit()

        decoded = r.json()
        data_species = decoded['species']
        list_species = "<ul>"
        for i in range(limit):
            list_species += "<li>"+str(data_species[i]['name'])+"</li>"
        list_species += "<ul>"
        return list_species


class TestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        # Printing the request line
        print(self.requestline, 'blue')
        total_request = self.path.split('?')
        request = total_request.pop(0)
        print(total_request)

        if request == "/":
            f = open("form.html", 'r')
            contents = f.read()
            f.close()

        elif request == "/listSpecies":
            endpoint = "/info/species"
            if total_request:
                try:
                    limit = int(total_request[-1].split('=')[-1])
                    list_species = connection(endpoint, limit)
                except ValueError:
                    list_species = connection(endpoint)
            else:
                list_species = connection(endpoint)
            contents = """<!DOCTYPE html>
                                <html lang="en">
                                <head>
                                    <meta charset="UTF-8">
                                    <title>SeqAnalysis</title>
                                </head>
                                <body>
                                 <h1>List of species</h1>
                                  {}
                                  <a href="/">Main page</a>
                                </body>
                                </html>""".format(list_species)

        elif request == "/karyotype":
            endpoint = "/info/assembly/"
            specie = total_request[-1].split('=')[-1]
            karyotype = connection(endpoint, specie=specie)
            contents = """<!DOCTYPE html>
                                <html lang="en">
                                <head>
                                    <meta charset="UTF-8">
                                    <title>SeqAnalysis</title>
                                </head>
                                <body>
                                 <h1> information about the karyotype of {}</h1>
                                  {}
                                  <a href="/">Main page</a>
                                </body>
                                </html>""".format(specie, karyotype)

        elif request == "/chromosomeLength":
            pass

        else:
            f = open("error.html", 'r')
            contents = f.read()
            f.close()

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
