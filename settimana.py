import fitz  # PyMuPDF
import json


def ottengo_settimane():
    giorni = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
    doc = fitz.open("CAL_PRIME.pdf")

    # C'è solo una pagina, quindi va bene anche così
    page = doc[0]
    settimane = {}

    # è la prima settimana di settembre
    rect = fitz.Rect(19, 67, 130, 137)

    testo = page.get_textbox(rect).splitlines()

    # Offset_x e offset_y mi dicono quando sarà la prima settimana di scuola, considerando che
    # inizia sempre di lunedì, basta vedere quale sia il primo giorno di settembre
    offset_x = int(testo[len(testo) - 2]) + giorni.index(testo[len(testo) - 1])

    offset_y = offset_x + 6

    n_settimana_b = 0

    # Ho sempre pensato che fossero 9 i mesi di scuola e invece sono 10
    for i in range(10):
        max_giorni = 30

        # Non tutti i mesi finisco per 31, quindi si limita il while
        if i == 1 or i == 3 or i == 6 or i == 8:
            max_giorni = 31
        elif i == 5:
            max_giorni = 29
        elif i == 3:
            # Serve per dicembre
            max_giorni = 23
        elif i == 6:
            # Vacanze pasquali
            max_giorni = 27

        if i != 0 and i != 4 and i != 7:
            if testo[len(testo) - 2] == 'A' or testo[len(testo) - 2] == 'B':
                offset_x = 6 - giorni.index(testo[len(testo) - 1])
            else:
                offset_x = 6 - giorni.index(testo[len(testo) - 2])

            # Controlla se la settimana è finita
            if offset_x > 1:
                offset_x = 0
                offset_y = 5 - giorni.index(testo[len(testo) - 2])
            else:
                offset_y = offset_x + 6

        # Sia aprile che gennaio incominciano dopo per via delle vacanze
        elif i == 4:
            offset_x = 7
            offset_y = offset_x + 6
        elif i == 7:
            offset_x = 2
            offset_y = 6

        while offset_x < max_giorni and "Fine delle " not in testo:
            # Prende la settimana
            rect = fitz.Rect(19 + (116 * i), 70 + (10 * offset_x), 130 + (115 * i), 80 + (10 * offset_y))

            testo = page.get_textbox(rect).splitlines()

            # 0 -> Settimana A
            # 1 -> Settimana B
            # 2 -> Settimana B solo per le prime
            if "A" in testo:
                settimane[str(offset_x + 1) + "-" + str(offset_y) + "-" + str(i)] = 0
                n_settimana_b = 0

            elif "B" in testo:
                if n_settimana_b != 0:
                    settimane[str(offset_x + 1) + "-" + str(offset_y) + "-" + str(i)] = 1
                else:
                    settimane[str(offset_x + 1) + "-" + str(offset_y) + "-" + str(i)] = 2

                n_settimana_b = n_settimana_b + 1

            offset_x = offset_y + 1

            # Controlla se il mese è finito
            if offset_y + 7 < max_giorni:
                offset_y = offset_x + 6
            else:
                offset_y = max_giorni

    doc.close()

    salvo_json(settimane)


def salvo_json(dati):
    json_file = json.dumps(dati, indent=4)
    with open("settimane.json", "w") as outfile:
        outfile.write(json_file)


if __name__ == "__main__":
    ottengo_settimane()
