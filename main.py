import fitz
import json
import re

settimana = ["lunedi", "martedi", "mercoledi", "giovedi", "venerdi"]

classi_json = {}


def riempio_json(blocco, giorno, template_json, ora_singola=0):
    if len(blocco) < 6 and ora_singola == 0:
        for i in range(len(blocco)):
            blocco.append(blocco[i])

    k = 0

    for i in range(2 - ora_singola):
        template_json[settimana[giorno]]["materie"].append(blocco[0 + k])
        template_json[settimana[giorno]]["professori"].append(blocco[1 + k])

        if ("(" not in blocco[2 + k] and ("PALESTRA" not in blocco[2 + k]) and blocco[
            2 + k] != "Tesauro LAB.INFORMATICA"):
            template_json[settimana[giorno]]["professori"][len(template_json[settimana[giorno]]["professori"]) - 1] = \
                template_json[settimana[giorno]]["professori"][
                    len(template_json[settimana[giorno]]["professori"]) - 1] + "," + blocco[2 + k]
            k = k + 1
        template_json[settimana[giorno]]["aule"].append(blocco[2 + k])

        if len(blocco) / 2 == 5:
            template_json[settimana[giorno]]["aule"][len(template_json[settimana[giorno]]["aule"]) - 1] = \
                template_json[settimana[giorno]]["aule"][len(template_json[settimana[giorno]]["aule"]) - 1] + "," + \
                blocco[
                    3 + k]
            k = k + 1

        k = k + 3


def ottengo_dati():
    doc = fitz.open("orario.pdf")

    for n_pagina in range(71,72):

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

        page = doc[n_pagina]

        # fizt.React(Left, Bot, Right, Top)
        intestazione = (page.get_textbox(fitz.Rect(300, 20, 550, 50))
                        .replace("<<SABATI CHIUSI>>", "")
                        .strip()
                        .splitlines())

        classe = intestazione[0]

        for i in range(3, 4):

            ora_singola1 = 0
            ora_singola3 = 0

            offset_y = 0
            offset_x = 0

            blocco4 = None

            blocco1 = (page.get_textbox(fitz.Rect((60 + (125 * i)), 90, (180 + (126 * i)), 230)))

            blocco1 = tolgo_unicode(blocco1).splitlines()

            if len(blocco1) != 0:

                if "(" not in blocco1[len(blocco1) - 1] and "PALESTRA" not in blocco1[len(blocco1) - 1] and blocco1[
                    len(blocco1) - 1] != "Tesauro LAB.INFORMATICA":
                    blocco1 = page.get_textbox(fitz.Rect(fitz.Rect((60 + (125 * i)), 90, (180 + (126 * i)), 150)))
                    blocco1 = tolgo_unicode(blocco1).splitlines()

                    ora_singola1 = 1

                    offset_y = 80
                    offset_x = 60

                blocco2 = (
                    page.get_textbox(
                        fitz.Rect((60 + (125 * i)), (240 - offset_x), (180 + (126 * i)), (380 - offset_y))))

                blocco2 = tolgo_unicode(blocco2).splitlines()

                blocco3 = (page.get_textbox(
                    fitz.Rect((60 + (125 * i)), (400 - offset_x), (180 + (126 * i)), (550 - offset_y))))

                blocco3 = tolgo_unicode(blocco3).splitlines()

                print(blocco3)

                if "(" not in blocco3[len(blocco3) - 1] and "PALESTRA" not in blocco3[len(blocco3) - 1] and blocco3[
                    len(blocco3) - 1] != "Tesauro LAB.INFORMATICA":
                    blocco3 = page.get_textbox(fitz.Rect(fitz.Rect((60 + (125 * i)), 320, (180 + (126 * i)), 380)))
                    blocco3 = tolgo_unicode(blocco3).splitlines()
                    ora_singola3 = 1

                    blocco4 = (page.get_textbox(fitz.Rect((60 + (125 * i)), 400, (180 + (126 * i)), 550)))
                    blocco4 = tolgo_unicode(blocco4).splitlines()

                print(blocco3)

                riempio_json(blocco1, i, template_json, ora_singola1)
                riempio_json(blocco2, i, template_json)
                riempio_json(blocco3, i, template_json, ora_singola3)
                if blocco4 is not None:
                    riempio_json(blocco4, i, template_json)

        classi_json.update({classe: template_json})


def salvo_json():
    json_file = json.dumps(classi_json, indent=4)
    with open("orario.json", "w") as outfile:
        outfile.write(json_file)


def tolgo_unicode(blocco):
    return re.sub(r'(\s+\uea1e)|\uea1e', "", blocco).strip()


def test():
    doc = fitz.open("orario.pdf")
    page = doc[22]

    page.set_cropbox(fitz.Rect((60 + (125 * 4)), (400 - 20), (180 + (126 * 4)), 550))

    doc.save("test.pdf")


if __name__ == "__main__":
    #test()
    ottengo_dati()
    #salvo_json()
