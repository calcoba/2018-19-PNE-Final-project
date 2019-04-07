import http.server
import socketserver
import requests
import sys
import termcolor


# Falta comprobar cualquier error
def connection(endpoint, limit=162, specie="", chromo=""):
    server = "http://rest.ensembl.org"
    if specie:
        if chromo:
            r = requests.get(server + endpoint + specie + "/" + chromo, headers={"Content-Type": "application/json"})
            if not r.ok:
                if r.status_code == 400:
                    return "Error 400 Client Error: Bad Request for url:", server + endpoint + specie
                else:
                    return "Error", r.status_code()

            decoded = r.json()
            length = decoded['length']
            return length
        else:
            r = requests.get(server + endpoint + specie, headers={"Content-Type": "application/json"})

            if not r.ok:
                if r.status_code == 400:
                    return "Error 400 Client Error: Bad Request for url:", server + endpoint + specie
                else:
                    return "Error", r.status_code()

            decoded = r.json()
            data_karyotype = decoded['karyotype']
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

        decoded = r.json()
        data_species = decoded['species']
        if type(limit) is int:
            list_species = "<ul>"
            for i in range(limit):
                list_species += "<li>"+str(data_species[i]['name'])+"</li>"
            list_species += "<ul>"
        else:
            list_species = "The limit must be an integer"
        return list_species


class TestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        # Printing the request line
        contents = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SeqAnalysis</title>
</head>
"""
        termcolor.cprint(self.requestline, 'blue')
        total_request = self.path.split('?')
        request = total_request.pop(0)

        if request == "/":
            f = open("form.html", 'r')
            contents = f.read()
            f.close()

        elif request == "/listSpecies":
            endpoint = "/info/species"
            print("1")
            if total_request:
                try:
                    print(2)
                    limit = total_request[-1].split('=')[-1]
                    list_species = connection(endpoint, limit)
                except ValueError:
                    print(3)
                    list_species = connection(endpoint)
            else:
                print(5)
                list_species = connection(endpoint)
                print(type(list_species))
            if type(list_species) is str:
                print(4)
                contents += """<body>
<h1>List of species</h1>
{}
<p><a href="/">Main page</a></p>
</body>
</html>""".format(list_species)

        elif request == "/karyotype":
            endpoint = "/info/assembly/"
            specie = total_request[-1].split('=')[-1]
            if not specie:
                contents += """<body>
<h1> Something went wrong</h1>
You must fill the specie form
<p><a href="/">Main page</a></p>
</body>
</html>"""
            else:
                karyotype = connection(endpoint, specie=specie)
                if type(karyotype) == str:
                    contents += """<body>
<h1> Information about the karyotype of {}</h1>
{}
<p><a href="/">Main page</a></p>
</body>
</html>""".format(specie, karyotype)
                else:
                    contents += """<body>
                <h2>Something went wrong in the request</h2>
                {}
                <p><a href="/">Main page</a></p>
                </body>
                </html>""".format(" ".join(karyotype))

        elif request == "/chromosomeLength":
            endpoint = "/info/assembly/"
            sp_ch = total_request[0].split('&')
            specie = sp_ch[0].split('=')[-1]
            chromo = sp_ch[-1].split('=')[-1]
            if not specie or not chromo:
                contents += """<body>
<h1> Something went wrong</h1>
You must fill the chromosome and the specie form
<p><a href="/">Main page</a></p>
</body>
</html>"""

            else:
                length = connection(endpoint, specie=specie, chromo=chromo)
                if type(length) is int:
                    contents += """<body>
<h2>Length of the chromosome {} of {} specie</h2>
{}
<p><a href="/">Main page</a></p>
</body>
</html>""".format(chromo, specie, length)
                else:
                    contents += """<body>
<h2>Something went wrong in the request</h2>
{}
<p><a href="/">Main page</a></p>
</body>
</html>""".format(" ".join(length))

        else:
            f = open("error.html", 'r')
            contents = f.read()
            f.close()

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
