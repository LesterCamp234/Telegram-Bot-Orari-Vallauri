## orario_dumper.py

Questo script legge il pdf e genera un json con tutti i dati del file.
Funziona con tutti i tipi di orari, compreso anche le settimane B solo per le prime

### Utilizzo
```
pip install -r requirements.txt
py orario_dumper.py path_del_pdf_dell'orario.pdf
```
----

## settimane.py

Questo script legge il pdf delle settimane e genera un json con tutti i dati del file.

**Limitazioni:**
- Lo script non gestisce dinamicamente le vacanze, per cui già il prossimo anno bisognerà cambiarlo
- Bisogna usare per forza il pdf che mostra le settimane B delle prime

### Utilizzo
```
pip install -r requirements.txt
py settimane.py path_del_pdf_delle_settimane.pdf
```
