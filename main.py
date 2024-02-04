import fitz
import json
import re

settimana = ["lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato"]

classi_json = {}

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

def riempio_json(blocco, giorno):
    if len(blocco) < 6:
       for i in range(len(blocco)):
           blocco.append(blocco[i])

    k = 0

    for i in range(2):
        template_json[settimana[giorno]]["materie"].append(blocco[0 + k])
        template_json[settimana[giorno]]["professori"].append(blocco[1 + k])

        if(not "(" in blocco[2 + k] and (not "PALESTRA" in blocco[2 + k]) and blocco[2 + k] != "Tesauro LAB.INFORMATICA"):
            template_json[settimana[giorno]]["professori"][len(template_json[settimana[giorno]]["professori"]) - 1] = template_json[settimana[giorno]]["professori"][len(template_json[settimana[giorno]]["professori"]) - 1] + "," + blocco[2 + k]
            k = k + 1
        template_json[settimana[giorno]]["aule"].append(blocco[2 + k])

        if (len(blocco) / 2 == 5):
            template_json[settimana[giorno]]["aule"][len(template_json[settimana[giorno]]["aule"]) - 1] = template_json[settimana[giorno]]["aule"][len(template_json[settimana[giorno]]["aule"]) - 1] + "," + blocco[3 + k]
            k = k + 1

        k = k + 3


def ottengo_dati():
    doc = fitz.open("orario.pdf")

    for n_pagina in range(66,67):
        print(n_pagina)

        page = doc[n_pagina]

        #template_json_pulito = template_json

        #fizt.React(Left, Bot, Right, Top)
        intestazione = (page.get_textbox(fitz.Rect(300,20,550,50))
              .replace("<<SABATI CHIUSI>>", "")
              .strip()
              .splitlines())

        classe = intestazione[0]



        for i in range(5):
            prima_e_seconda = (page.get_textbox(fitz.Rect((60 + (125 * i)), 90, (180 + (126 * i)), 230)))
            terza_e_quarta = (page.get_textbox(fitz.Rect((60 + (125 * i)), 240, (180 + (126 * i)), 380)))
            quinta_e_sesta = (page.get_textbox(fitz.Rect((60 + (125 * i)), 400, (180 + (126 * i)), 550)))

            prima_e_seconda = re.sub(r'\uea1e', "", prima_e_seconda).strip().splitlines()
            terza_e_quarta = re.sub(r'\uea1e', "", terza_e_quarta).strip().splitlines()
            quinta_e_sesta = re.sub(r'\uea1e', "", quinta_e_sesta).strip().splitlines()


            if(len(prima_e_seconda) != 0):
                riempio_json(prima_e_seconda, i)
                riempio_json(terza_e_quarta, i)
                riempio_json(quinta_e_sesta, i)

                classi_json.update({classe: template_json})
                #template_json = template_json_pulito


def salvo_json():
    json_file = json.dumps(classi_json,indent=4)
    with open("orario.json", "w") as outfile:
        outfile.write(json_file)

if __name__ == "__main__":
    ottengo_dati()
    #salvo_json()
