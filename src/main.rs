use chrono::{Datelike, NaiveDate};
use lazy_static::lazy_static;
use regex::Regex;
use serde_json::{Map, Value};
use std::error::Error;
use std::fs::File;
use std::io::Read;
use std::sync::{Mutex, MutexGuard};
use teloxide::{
    payloads::SendMessageSetters,
    prelude::*,
    types::{InlineKeyboardButton, InlineKeyboardMarkup, Me},
    utils::command::BotCommands,
};

// Le fantastiche variabili globali <3
lazy_static! {
    static ref CLASSI: Mutex<Vec<String>> = Mutex::new(vec![]);
    static ref JSON_A: Result<Value, Box<dyn Error + Send + Sync>> =
        leggo_json("orario_A.json".to_string());
    static ref JSON_B: Result<Value, Box<dyn Error + Send + Sync>> =
        leggo_json("orario_B.json".to_string());
    static ref JSON_SETTIMANE: Result<Value, Box<dyn Error + Send + Sync>> =
        leggo_json("settimane.json".to_string());
    static ref SETTIMANE: Mutex<Vec<String>> = Mutex::new(vec![]);
    static ref MESI: [String; 12] = [
        "Gennaio".to_string(),
        "Febbraio".to_string(),
        "Marzo".to_string(),
        "Aprile".to_string(),
        "Maggio".to_string(),
        "Giugno".to_string(),
        "".to_string(),
        "".to_string(),
        "Settembre".to_string(),
        "Ottobre".to_string(),
        "Novembre".to_string(),
        "Dicembre".to_string()
    ];
}

#[derive(BotCommands, Clone)]
#[command(rename_rule = "lowercase")]
enum Command {
    #[command(description = "Fa partire il bot e manda questo messaggio")]
    Start,
    #[command(description = "Mostra questo messaggio")]
    Help,
    #[command(description = "Cerca una classe e mostro l'orario di oggi.")]
    Cerca(String),
    #[command(description = "Cerca una classe e mostra l'orario di un determinato giorno.")]
    GiornoSpecifico(String),
    #[command(description = "Cerca una classe e mostra l'orario di domani.")]
    Domani(String),
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    match &*JSON_A {
        Err(e) => println!("{}", e),
        _ => match &*JSON_B {
            Err(e) => println!("{}", e),
            _ => match &*JSON_SETTIMANE {
                Err(e) => println!("{}", e),
                _ => {
                    json_a_vec(
                        SETTIMANE.lock().unwrap(),
                        JSON_SETTIMANE.as_ref().unwrap().as_object(),
                    );
                    json_a_vec(CLASSI.lock().unwrap(), JSON_A.as_ref().unwrap().as_object());

                    let bot = Bot::from_env();

                    let handler = dptree::entry()
                        .branch(Update::filter_message().endpoint(message_handler))
                        .branch(Update::filter_callback_query().endpoint(callback_handler));

                    Dispatcher::builder(bot, handler)
                        .enable_ctrlc_handler()
                        .build()
                        .dispatch()
                        .await;
                }
            },
        },
    }

    Ok(())
}

fn creatore_bottoni(mese: usize, anno: i32) -> InlineKeyboardMarkup {
    let mut bottoni: Vec<Vec<InlineKeyboardButton>> = vec![];

    let mut giorni: Vec<String> = (1..=30).map(|giorno| giorno.to_string()).collect();

    if mese == 0 || mese == 2 || mese == 4 || mese == 9 || mese == 11 {
        giorni.push(31.to_string());
    } else if mese == 1 {
        giorni.pop();
        // Per vedere se un anno è bisestile, si fa così:
        if anno % 400 == 0 {
            giorni.pop();
        }
    }

    giorni.push("Mese dopo".to_string());
    giorni.push("Mese prima".to_string());

    for versions in giorni.chunks(3) {
        let row = versions
            .iter()
            .map(|numero| InlineKeyboardButton::callback(numero.to_string(), numero.to_string()))
            .collect();
        bottoni.push(row);
    }

    InlineKeyboardMarkup::new(bottoni)
}

async fn message_handler(
    bot: Bot,
    msg: Message,
    me: Me,
) -> Result<(), Box<dyn Error + Send + Sync>> {
    if let Some(text) = msg.text() {
        match BotCommands::parse(text, me.username()) {
            Ok(Command::Help) => {
                // Just send the description of all commands.
                bot.send_message(msg.chat.id, Command::descriptions().to_string())
                    .await?;
            }
            Ok(Command::Start) => {
                bot.send_message(msg.chat.id, Command::descriptions().to_string())
                    .await?;
            }

            Ok(Command::Cerca(classe)) => {
                let mut ris = String::new();

                let controllo = controllo_classe(classe.to_uppercase()).await;

                if !controllo {
                    ris = "La classe non è valida, devi darmela così: ex 3A AFM".to_string()
                } else {
                    let pos = cerco_la_classe(classe.to_uppercase()).await;
                    if pos == -1 {
                        ris = "La classe non esiste.".to_string()
                    } else {
                        let orario =
                            stampo_classe(pos as usize, chrono::Utc::now().date_naive()).await;
                        let elenco: Vec<_> = orario.split('\n').collect();

                        if elenco.len() > 1 {
                            for testo in elenco.iter().take(elenco.len() - 2) {
                                bot.send_message(msg.chat.id, testo.to_string()).await?;
                            }
                            ris = elenco[elenco.len() - 2].to_string();
                        }
                    }
                }

                bot.send_message(msg.chat.id, ris).await?;
            }

            Ok(Command::GiornoSpecifico(parametro)) => {
                let mut classe = parametro.to_uppercase();
                let mese = (chrono::Utc::now().month() as usize) - 1;
                let anno = chrono::Utc::now().year();

                if controllo_classe(classe.clone()).await {
                    let regex = Regex::new(r"(?m)\s+").unwrap();

                    classe = regex.replace_all(&classe, "").to_string();

                    let testo = format!(
                        "Scegli un giorno per la {} {} di {} {}",
                        &classe[0..2],
                        &classe[2..5],
                        MESI[mese],
                        anno
                    );

                    let bottoni = creatore_bottoni(mese, anno);

                    bot.send_message(msg.chat.id, testo)
                        .reply_markup(bottoni)
                        .await?;
                } else {
                    bot.send_message(msg.chat.id, "La classe non è valida.")
                        .await?;
                }
            }

            Ok(Command::Domani(classe)) => {
                let mut ris = String::new();

                let controllo = controllo_classe(classe.to_uppercase()).await;

                if !controllo {
                    ris = "La classe non è valida, devi darmela così: ex 3A AFM".to_string()
                } else {
                    let pos = cerco_la_classe(classe.to_uppercase()).await;

                    if pos == -1 {
                        ris = "La classe non esiste.".to_string()
                    } else {
                        let data = chrono::Utc::now()
                            .checked_add_days(chrono::Days::new(1))
                            .unwrap()
                            .date_naive();
                        let orario = stampo_classe(pos as usize, data).await;
                        let elenco: Vec<_> = orario.split('\n').collect();

                        if elenco.len() > 1 {
                            for testo in elenco.iter().take(elenco.len() - 2) {
                                bot.send_message(msg.chat.id, testo.to_string()).await?;
                            }
                            ris = elenco[elenco.len() - 2].to_string();
                        }
                    }
                }

                bot.send_message(msg.chat.id, ris).await?;
            }

            Err(_) => {
                bot.send_message(msg.chat.id, "Comando non trovato").await?;
            }
        }
    }

    Ok(())
}

async fn callback_handler(bot: Bot, q: CallbackQuery) -> Result<(), Box<dyn Error + Send + Sync>> {
    if let Some(scelta) = q.data {
        bot.answer_callback_query(q.id).await?;

        if let Some(Message { id, chat, .. }) = q.message.clone() {
            let testo = q.message.unwrap();

            let mut data = mese_e_anno(testo.text().unwrap().to_string()).await;
            if scelta == "Mese dopo" {
                if data[0] == 11 {
                    data[0] = 0;
                    data[1] += 1;
                } else if data[0] == 5 {
                    data[0] = 8;
                    data[1] -= 1;
                } else {
                    data[0] += 1;
                }

                // So che bisogna evitare che si utilizzi l'hard-coding, ma non mi vengono altre idee
                bot.edit_message_text(
                    chat.id,
                    id,
                    format!(
                        "Scegli un giorno per la {} di {} {}",
                        &testo.text().unwrap()[24..30],
                        MESI[data[0] as usize],
                        data[1]
                    ),
                )
                .await?;
                bot.edit_message_reply_markup(chat.id, id)
                    .reply_markup(creatore_bottoni(data[0] as usize, data[1]))
                    .await?;
            } else if scelta == "Mese prima" {
                if data[0] == 8 {
                    data[0] = 5;
                    data[1] += 1;
                } else if data[0] == 0 {
                    data[0] = 11;
                    data[1] -= 1;
                } else {
                    data[0] -= 1;
                }

                bot.edit_message_text(
                    chat.id,
                    id,
                    format!(
                        "Scegli un giorno per la {} di {} {}",
                        &testo.text().unwrap()[24..30],
                        MESI[data[0] as usize],
                        data[1]
                    ),
                )
                .await?;
                bot.edit_message_reply_markup(chat.id, id)
                    .reply_markup(creatore_bottoni(data[0] as usize, data[1]))
                    .await?;
            } else {
                let classe =
                    testo.text().unwrap()[24..26].to_owned() + &testo.text().unwrap()[27..30];
                let pos = cerco_la_classe(classe).await;

                let mut ris = String::new();

                if pos != -1 {
                    let momento = NaiveDate::parse_from_str(
                        &((scelta.parse::<i32>().unwrap() + 1).to_string()
                            + "-"
                            + &*data[0].to_string()
                            + "-"
                            + &*data[1].to_string()),
                        "%d-%m-%Y",
                    )
                    .unwrap();
                    let orario = stampo_classe(pos as usize, momento).await;
                    let elenco: Vec<_> = orario.split('\n').collect();

                    if elenco.len() > 1 {
                        for text in elenco.iter().take(elenco.len() - 2) {
                            bot.send_message(chat.id, text.to_string()).await?;
                        }
                        ris = elenco[elenco.len() - 2].to_string();
                    }
                } else {
                    ris = "La classe non esiste.".to_string()
                }

                bot.send_message(chat.id, ris).await?;
            }
        }
    }

    Ok(())
}

async fn mese_e_anno(testo: String) -> Vec<i32> {
    let mut vet: Vec<i32> = Vec::new();
    let testo_splittato: Vec<&str> = testo.split(' ').collect();

    vet.push(
        MESI.iter()
            .position(|x| x == &testo_splittato[8].to_string())
            .unwrap() as i32,
    );
    vet.push(testo_splittato[9].parse::<i32>().unwrap());

    vet
}

async fn controllo_classe(classe: String) -> bool {
    let regex = Regex::new(r"(?m)[1-5][A-Z]\s*[A-Z]{3}$").unwrap();
    regex.is_match(&classe)
}

// -1 -> Classe non esiste
async fn cerco_la_classe(mut classe: String) -> i32 {
    let classi = CLASSI.lock().unwrap().to_vec();

    classe = classe.to_uppercase();
    let regex = Regex::new(r"(?m)\s+").unwrap();

    classe = regex.replace_all(&classe, "").to_string();

    match classi.iter().position(|x| x == &*classe) {
        Some(i) => i as i32,
        None => -1,
    }
}

async fn stampo_classe(pos: usize, data: NaiveDate) -> String {
    let classi = CLASSI.lock().unwrap().to_vec();
    let mut tabella = String::new();
    let tab_settimane = SETTIMANE.lock().unwrap();
    let giorni = [
        "lunedi",
        "martedi",
        "mercoledi",
        "giovedi",
        "venerdi",
        "sabato",
    ];
    let layout = ["materie", "professori", "aule"];
    let mut tipo_settimana = String::new();

    let mut giorno = data.day();

    // u8 dovrebbe bastare per contenere il numero del mese
    let mese = data.month() as u8;

    let mut oggi = (data.weekday().number_from_monday() - 1) as usize;

    if oggi == 6 {
        oggi = 0;
        tabella += "Dato che è domenica, ecco l'orario di lunedì \n";
        giorno += 1;
    }

    let mut trovato = false;
    let mut i: usize = 0;

    while !trovato && i < tab_settimane.len() {
        let contenuto: Vec<_> = tab_settimane[i].split('-').collect();
        if contenuto[0].parse::<u32>().unwrap() <= giorno
            && giorno <= contenuto[1].parse::<u32>().unwrap()
            && mese == contenuto[2].parse::<u8>().unwrap()
        {
            tipo_settimana = JSON_SETTIMANE.as_ref().unwrap()[&tab_settimane[i]].to_string();
            trovato = true;
        } else {
            i += 1;
        }
    }

    let orario =
        if tipo_settimana == "0" || (tipo_settimana == "2" && classi[pos].find('1').is_some()) {
            &JSON_A.as_ref().unwrap()[classi[pos].to_string()][giorni[oggi]]
        } else {
            &JSON_B.as_ref().unwrap()[classi[pos].to_string()][giorni[oggi]]
        };

    // Controlla se l'orario è vuoto, grazie 3A AFM per esistere
    if !orario[layout[0]].as_array().unwrap().is_empty() {
        for i in 0..6 {
            tabella += &*format!(
                "Materia: {} - Professore: {} - Aula: {} \n",
                orario[layout[0]][i], orario[layout[1]][i], orario[layout[2]][i]
            );
        }
    } else {
        tabella = "Mi dispiace, ma l'orario è vuoto. Prova a cercare un'altra classe".to_string()
    }

    tabella
}

fn json_a_vec(mut array: MutexGuard<Vec<String>>, json: Option<&Map<String, Value>>) {
    if let Some(object) = json {
        for (chiave, _) in object {
            array.push(chiave.to_string());
        }
    } else {
        panic!("JSON non valido");
    }
}

fn leggo_json(path: String) -> Result<Value, Box<dyn Error + Send + Sync>> {
    if std::path::Path::exists(path.as_ref()) {
        let mut file = File::open(path)?;

        let mut content = String::new();
        file.read_to_string(&mut content)?;

        let parsed_json: Value = serde_json::from_str(&content)?;

        Ok(parsed_json)
    } else {
        Err(Box::from("Il json non esiste"))
    }
}
