import fitz  # PyMuPDF
import json
import re  # Le fantastiche Regex
import sys
from os.path import exists

settimana = ["lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato"]

classi_json = {}


def riempio_json(blocco, giorno, template_json, ora_singola=0):
    # Questa if serve in caso ci sia un blocco da due ore, li scende e li mette nel json
    # come se fossero 2h separate

    if len(blocco) < 6 and ora_singola == 0:
        for i in range(len(blocco)):
            blocco.append(blocco[i])

    k = 0

    for i in range(2 - ora_singola):
        template_json[giorno]["materie"].append(blocco[0 + k])
        template_json[giorno]["professori"].append(blocco[1 + k])

        # Se non c'è scritto l'aula dopo il nome del prof, significa che ce ne deve essere un altro che fa compresenza
        if ("(" not in blocco[2 + k] and ("PALESTRA" not in blocco[2 + k]) and blocco[
            2 + k] != "Tesauro LAB.INFORMATICA" and "HOME" not in blocco[2 + k]):
            template_json[giorno]["professori"][len(template_json[giorno]["professori"]) - 1] = \
                template_json[giorno]["professori"][
                    len(template_json[giorno]["professori"]) - 1] + "," + blocco[2 + k]
            k = k + 1
        template_json[giorno]["aule"].append(blocco[2 + k])

        # Stesso ragionamento di prima, ma con le aule
        if len(blocco) / 2 == 5:
            template_json[giorno]["aule"][len(template_json[giorno]["aule"]) - 1] = \
                template_json[giorno]["aule"][len(template_json[giorno]["aule"]) - 1] + "," + \
                blocco[
                    3 + k]
            k = k + 1

        # Mi serve per scorrere il vettore
        k = k + 3


def controllo_file():
    if len(sys.argv) != 2:
        print("Non mi hai passato il path del file")
    elif exists(sys.argv[1]):
        doc = fitz.open(sys.argv[1])

        orario_b = controllo_sabato(doc)
        if orario_b == 'B':
            ottengo_dati_b(doc)
        elif orario_b == 'C':
            ottengo_dati_c(doc)
        else:
            ottengo_dati(doc)
    else:
        print("Il file non esiste")


def controllo_sabato(doc):
    page = doc[0]
    intestazione = page.get_textbox(fitz.Rect(320, 20, 550, 50))
    # Chiusi -> Settimana A -> A
    # Aperti -> File con soltanto la settimana B per le prime -> C
    # Se non c'è nulla, è il file con la settimana B per tutti, comprese le prime -> B

    if "APERTI" in intestazione:
        return 'C'
    elif "CHIUSI" in intestazione:
        return 'A'
    else:
        return 'B'


# Dato che i blocchi delle ore sono più grossi nel file della settimana b per tutti
# Ho deciso di modificare solo le coordinate, visto che il resto è uguale
def ottengo_dati_b(doc):
    giorni = 6

    # len(doc) indica il numero di pagine totali
    for n_pagina in range(len(doc)):
        template_json = {
            "lunedi": {
                "materie": [],
                "professori": [],
                "aule": []
            },
            "martedi": {
                "materie": [],
                "professori": [],
                "aule": []
            },
            "mercoledi": {
                "materie": [],
                "professori": [],
                "aule": []
            },
            "giovedi": {
                "materie": [],
                "professori": [],
                "aule": []
            },
            "venerdi": {
                "materie": [],
                "professori": [],
                "aule": []
            },
            "sabato": {
                "materie": [],
                "professori": [],
                "aule": []
            }
        }
        page = doc[n_pagina]

        # fizt.Rect(Left, Bot, Right, Top)
        intestazione = (page.get_textbox(fitz.Rect(380, 20, 425, 50))
                        .splitlines())

        # Prende il numero, sezione, indirizzo e il numero di alunni di quella classe
        classe = re.sub(r'\s+', "", intestazione[0])

        if "LIC" in classe:
            giorni -= 1
            template_json.pop("sabato")

        for i in range(giorni):
            ora_singola1 = 0
            ora_singola2 = 0
            ora_singola3 = 0

            offset_y = 0
            offset_x = 0

            blocco4 = None

            # Prende le prime due ore iniziali
            blocco1 = (page.get_textbox(fitz.Rect((60 + (126 * i)), 80, (180 + (126 * i)), 230)))

            blocco1 = tolgo_unicode(blocco1)

            # Questa if esiste per via della 3A AFM che hanno l'orario vuoto
            if len(blocco1) != 0:

                # Se alla fine non c'è l'aula, significa che la seconda e terza ora sono un blocco unico,
                # per cui devo prendere solo la prima
                if "(" not in blocco1[len(blocco1) - 1] and "PALESTRA" not in blocco1[len(blocco1) - 1] and blocco1[
                    len(blocco1) - 1] != "Tesauro LAB.INFORMATICA" and "HOME" not in blocco1[len(blocco1) - 1]:
                    blocco1 = page.get_textbox(fitz.Rect((60 + (125 * i)), 80, (180 + (126 * i)), 150))
                    blocco1 = tolgo_unicode(blocco1)

                    ora_singola1 = 1

                    offset_y = 80
                    offset_x = 60

                blocco2 = (
                    page.get_textbox(
                        fitz.Rect((70 + (125 * i)), (230 - offset_x), (180 + (126 * i)), (380 - offset_y))))

                blocco2 = tolgo_unicode(blocco2)

                if "(" not in blocco2[len(blocco2) - 1] and "PALESTRA" not in blocco2[len(blocco2) - 1] and blocco2[
                    len(blocco2) - 1] != "Tesauro LAB.INFORMATICA" and "HOME" not in blocco2[len(blocco2) - 1]:
                    blocco2 = page.get_textbox(fitz.Rect((60 + (125 * i)), 240, (180 + (126 * i)), 310))
                    blocco2 = tolgo_unicode(blocco2)
                    ora_singola2 = 1

                    offset_y = 80
                    offset_x = 60

                blocco3 = page.get_textbox(
                    fitz.Rect((60 + (125 * i)), (380 - offset_x), (180 + (126 * i)), (550 - offset_y)))

                blocco3 = tolgo_unicode(blocco3)

                if ("(" not in blocco3[len(blocco3) - 1] and "PALESTRA" not in blocco3[len(blocco3) - 1] and blocco3[
                    len(blocco3) - 1] != "Tesauro LAB.INFORMATICA") and "HOME" not in blocco3[
                    len(blocco3) - 1] or ora_singola2 == 1:

                    # Se la 3h è singola, significa che la quarta e la quinta possono essere insieme e l'ultima è
                    # singola
                    if ora_singola2 == 0:
                        ora_singola3 = 1
                        offset_x = 80
                        blocco3 = page.get_textbox(fitz.Rect((60 + (125 * i)), 320, (180 + (126 * i)), 380))
                        blocco3 = tolgo_unicode(blocco3)

                    blocco4 = page.get_textbox(fitz.Rect((60 + (125 * i)), (480 - offset_x), (180 + (126 * i)), 550))
                    blocco4 = tolgo_unicode(blocco4)

                riempio_json(blocco1, settimana[i], template_json, ora_singola1)
                riempio_json(blocco2, settimana[i], template_json, ora_singola2)
                riempio_json(blocco3, settimana[i], template_json, ora_singola3)

                # Non perforza il blocco4 può esistere, perchè la giornata magari è composta da 6 ore singole
                if blocco4 is not None:
                    riempio_json(blocco4, settimana[i], template_json)

        classi_json.update({classe: template_json})
        giorni = 6

    doc.close()

    salvo_json('B')


def ottengo_dati_c(doc):
    giorni = 6
    classe = "1"
    n_pagina = 0

    while "1" in classe:
        page = doc[n_pagina]

        template_json = {
            "lunedi": {
                "materie": [],
                "professori": [],
                "aule": []
            },
            "martedi": {
                "materie": [],
                "professori": [],
                "aule": []
            },
            "mercoledi": {
                "materie": [],
                "professori": [],
                "aule": []
            },
            "giovedi": {
                "materie": [],
                "professori": [],
                "aule": []
            },
            "venerdi": {
                "materie": [],
                "professori": [],
                "aule": []
            },
            "sabato": {
                "materie": [],
                "professori": [],
                "aule": []
            }
        }

        # fizt.Rect(Left, Bot, Right, Top)
        intestazione = (page.get_textbox(fitz.Rect(300, 20, 350, 50))
                        .splitlines())

        # Prende il numero, sezione, indirizzo e il numero di alunni di quella classe
        classe = re.sub(r'\s+', "", intestazione[0])

        if "INF" in classe or "ELT" in classe or "MEC" in classe:

            for i in range(giorni):

                ora_singola1 = 0
                ora_singola2 = 0
                ora_singola3 = 0

                offset_y = 0
                offset_x = 0

                blocco4 = None

                blocco1 = (page.get_textbox(fitz.Rect((60 + (125 * i)), 90, (180 + (126 * i)), 230)))

                blocco1 = tolgo_unicode(blocco1)

                if len(blocco1) != 0:

                    if "(" not in blocco1[len(blocco1) - 1] and "PALESTRA" not in blocco1[len(blocco1) - 1] and blocco1[
                        len(blocco1) - 1] != "Tesauro LAB.INFORMATICA":
                        blocco1 = page.get_textbox(fitz.Rect(fitz.Rect((60 + (125 * i)), 90, (180 + (126 * i)), 150)))
                        blocco1 = tolgo_unicode(blocco1)

                        ora_singola1 = 1

                        offset_y = 80
                        offset_x = 60

                    blocco2 = (
                        page.get_textbox(
                            fitz.Rect((60 + (125 * i)), (240 - offset_x), (180 + (126 * i)), (380 - offset_y))))

                    blocco2 = tolgo_unicode(blocco2)

                    if "(" not in blocco2[len(blocco2) - 1] and "PALESTRA" not in blocco2[len(blocco2) - 1] and blocco2[
                        len(blocco2) - 1] != "Tesauro LAB.INFORMATICA" and "HOME" not in blocco2[len(blocco2) - 1]:
                        blocco2 = page.get_textbox(fitz.Rect((60 + (125 * i)), 240, (180 + (126 * i)), 310))
                        blocco2 = tolgo_unicode(blocco2)
                        ora_singola2 = 1

                        offset_y = 80
                        offset_x = 60

                    blocco3 = (page.get_textbox(
                        fitz.Rect((60 + (125 * i)), (400 - offset_x), (180 + (126 * i)), (550 - offset_y))))

                    blocco3 = tolgo_unicode(blocco3)

                    if "(" not in blocco3[len(blocco3) - 1] and "PALESTRA" not in blocco3[len(blocco3) - 1] and blocco3[
                        len(blocco3) - 1] != "Tesauro LAB.INFORMATICA":
                        if ora_singola2 == 0:
                            ora_singola3 = 1
                            offset_x = 80
                            blocco3 = page.get_textbox(
                                fitz.Rect(fitz.Rect((60 + (125 * i)), 320, (180 + (126 * i)), 380)))
                            blocco3 = tolgo_unicode(blocco3)

                        blocco4 = (page.get_textbox(fitz.Rect((60 + (125 * i)), (480-offset_x), (180 + (126 * i)), 550)))
                        blocco4 = tolgo_unicode(blocco4)

                    riempio_json(blocco1, settimana[i], template_json, ora_singola1)
                    riempio_json(blocco2, settimana[i], template_json)
                    riempio_json(blocco3, settimana[i], template_json, ora_singola3)
                    if blocco4 is not None:
                        riempio_json(blocco4, settimana[i], template_json)

            classi_json.update({classe: template_json})

        n_pagina = n_pagina + 1

    doc.close()

    salvo_json('C')


def ottengo_dati(doc):
    giorni = 5
    # len(doc) indica il numero di pagine totali
    for n_pagina in range(len(doc)):
        page = doc[n_pagina]

        template_json = {
            "lunedi": {
                "materie": [],
                "professori": [],
                "aule": []
            },
            "martedi": {
                "materie": [],
                "professori": [],
                "aule": []
            },
            "mercoledi": {
                "materie": [],
                "professori": [],
                "aule": []
            },
            "giovedi": {
                "materie": [],
                "professori": [],
                "aule": []
            },
            "venerdi": {
                "materie": [],
                "professori": [],
                "aule": []
            }
        }

        # fizt.Rect(Left, Bot, Right, Top)
        intestazione = (page.get_textbox(fitz.Rect(320, 20, 370, 50))
                        .splitlines())

        # Prende il numero, sezione, indirizzo e il numero di alunni di quella classe
        classe = re.sub(r'\s+', "", intestazione[0])

        for i in range(giorni):

            ora_singola1 = 0
            ora_singola2 = 0
            ora_singola3 = 0

            offset_y = 0
            offset_x = 0

            blocco4 = None

            blocco1 = (page.get_textbox(fitz.Rect((60 + (125 * i)), 90, (180 + (126 * i)), 230)))

            blocco1 = tolgo_unicode(blocco1)

            if len(blocco1) != 0:

                if "(" not in blocco1[len(blocco1) - 1] and "PALESTRA" not in blocco1[len(blocco1) - 1] and blocco1[
                    len(blocco1) - 1] != "Tesauro LAB.INFORMATICA":
                    blocco1 = page.get_textbox(fitz.Rect(fitz.Rect((60 + (125 * i)), 90, (180 + (126 * i)), 150)))
                    blocco1 = tolgo_unicode(blocco1)

                    ora_singola1 = 1

                    offset_y = 80
                    offset_x = 60

                blocco2 = (
                    page.get_textbox(
                        fitz.Rect((60 + (125 * i)), (240 - offset_x), (180 + (126 * i)), (380 - offset_y))))

                blocco2 = tolgo_unicode(blocco2)

                if "(" not in blocco2[len(blocco2) - 1] and "PALESTRA" not in blocco2[len(blocco2) - 1] and blocco2[
                    len(blocco2) - 1] != "Tesauro LAB.INFORMATICA" and "HOME" not in blocco2[len(blocco2) - 1]:
                    blocco2 = page.get_textbox(fitz.Rect((60 + (125 * i)), 240, (180 + (126 * i)), 310))
                    blocco2 = tolgo_unicode(blocco2)
                    ora_singola2 = 1

                    offset_y = 80
                    offset_x = 60

                blocco3 = (page.get_textbox(
                    fitz.Rect((60 + (125 * i)), (400 - offset_x), (180 + (126 * i)), (550 - offset_y))))

                blocco3 = tolgo_unicode(blocco3)

                if "(" not in blocco3[len(blocco3) - 1] and "PALESTRA" not in blocco3[len(blocco3) - 1] and blocco3[
                    len(blocco3) - 1] != "Tesauro LAB.INFORMATICA":
                    if ora_singola2 == 0:
                        ora_singola3 = 1
                        offset_x = 80
                        blocco3 = page.get_textbox(
                            fitz.Rect(fitz.Rect((60 + (125 * i)), 320, (180 + (126 * i)), 380)))
                        blocco3 = tolgo_unicode(blocco3)

                    blocco4 = (page.get_textbox(fitz.Rect((60 + (125 * i)), (480 - offset_x), (180 + (126 * i)), 550)))
                    blocco4 = tolgo_unicode(blocco4)

                riempio_json(blocco1, settimana[i], template_json, ora_singola1)
                riempio_json(blocco2, settimana[i], template_json)
                riempio_json(blocco3, settimana[i], template_json, ora_singola3)
                if blocco4 is not None:
                    riempio_json(blocco4, settimana[i], template_json)

        classi_json.update({classe: template_json})

    doc.close()

    salvo_json(orario_b)


def salvo_json(orario_b):
    json_file = json.dumps(classi_json, indent=4)

    with open("orario_" + orario_b + ".json", "w") as outfile:
        outfile.write(json_file)


def tolgo_unicode(blocco):
    blocco = re.sub(r'(\s+\uea1e)|(\uea1e)', "", blocco).strip().splitlines()

    # Con le regex non funzia
    while "a" in blocco:
        blocco.remove("a")

    while "s" in blocco:
        blocco.remove("s")

    return blocco

if __name__ == "__main__":
    controllo_file()
