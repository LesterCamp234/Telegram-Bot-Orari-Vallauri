use std::error::Error;
use std::fs::File;
use std::io::Read;
use teloxide::{prelude::*, utils::command::BotCommands};
use serde_json::{Map, Value};
use lazy_static::lazy_static;
use std::sync::{Mutex, MutexGuard};
use regex::Regex;
use time::OffsetDateTime;

// My beloved global variables <3
lazy_static! {
    static ref CLASSI: Mutex<Vec<String>> = Mutex::new(vec![]);
    static ref JSON_A: Result<Value, Box<dyn Error + Send + Sync>> = leggo_json("orario_A.json".to_string());
    static ref JSON_B: Result<Value, Box<dyn Error + Send + Sync>> = leggo_json("orario_B.json".to_string());
    static ref JSON_SETTIMANE: Result<Value, Box<dyn Error + Send + Sync>> = leggo_json("settimane.json".to_string());
    static ref SETTIMANE: Mutex<Vec<String>> = Mutex::new(vec![]);
}

#[tokio::main]
async fn main(){
    match &*JSON_A {
        Err(e) => println!("{}", e),
        _ => {
            match &*JSON_B {
                Err(e) => println!("{}", e),
                _ => {
                    match &*JSON_SETTIMANE {
                        Err(e) => println!("{}", e),
                        _ => {
                            json_a_vec(SETTIMANE.lock().unwrap(), JSON_SETTIMANE.as_ref().unwrap().as_object());
                            json_a_vec(CLASSI.lock().unwrap(), JSON_A.as_ref().unwrap().as_object());

                            let bot = Bot::from_env();

                            Command::repl(bot, answer).await;
                        }
                    }
                }
            }
        }
    }

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
    GiornoSpecifico,
}

async fn answer(bot: Bot, msg: Message, cmd: Command) -> ResponseResult<()> {
    match cmd {
        Command::Help | Command::Start => bot.send_message(msg.chat.id, Command::descriptions().to_string()).await?,
        Command::Cerca(classe) => {
            let mut ris = cerco_la_classe(classe);
            let elenco: Vec<_> = ris.split("\n").collect();

            if elenco.len() > 1 {
                for i in 0..elenco.len() - 2 {
                    bot.send_message(msg.chat.id, elenco[i]).await?;
                }
                ris = elenco[elenco.len() - 2].to_string();
            }

            bot.send_message(msg.chat.id, ris).await?

        }
        Command::GiornoSpecifico => {
            bot.send_message(msg.chat.id, "TODO").await?
        }
    };
    Ok(())
}

fn cerco_la_classe(mut classe: String) -> String {

    let classi = CLASSI.lock().unwrap();

    // Toglie gli spazi da classe
    classe = classe.to_uppercase();

    let mut regex = Regex::new(r"(?m)\d[A-Z]\s*[A-Z]{3}$").unwrap();

    return if regex.is_match(&classe) {
        regex = Regex::new(r"(?m)\s+").unwrap();

        classe = regex.replace_all(&*classe, "").to_string();

        match classi.iter().position(|x| x == &*classe) {
            Some(i) => stampo_classe(i, classi),
            None => "La classe non esiste".to_string(),
        }

    } else {
        "La classe non è valida, devi darmela così: ex 3A AFM".to_string()
    }

}

fn stampo_classe(pos: usize, classi: MutexGuard<'_, Vec<String>>) -> String {
    let mut tabella = String::new();
    let tab_settimane = SETTIMANE.lock().unwrap();
    let giorni = vec!["lunedi", "martedi", "mercoledi", "giovedi", "venerdi"];
    let layout = vec!["materie", "professori", "aule"];
    let mut tipo_settimana = String::new();

    let giorno = OffsetDateTime::now_utc().day();

    // u8 dovrebbe bastare per contenere il numero del mese
    let mese = OffsetDateTime::now_utc().month() as u8;

    let mut oggi = (OffsetDateTime::weekday(OffsetDateTime::now_utc()).number_from_monday() - 1) as usize;

    let mut trovato = false;
    let mut i: usize = 0;

    while !trovato && i < tab_settimane.len() {
        let contenuto: Vec<_> = tab_settimane[i].split("-").collect();
        if contenuto[0].parse::<u8>().unwrap() <= giorno && giorno <= contenuto[1].parse::<u8>().unwrap() && mese == contenuto[2].parse::<u8>().unwrap(){
            tipo_settimana = JSON_SETTIMANE.as_ref().unwrap()[&tab_settimane[i]].to_string();
            trovato = true;
        } else {
            i += 1;
        }
    }

    let orario;

    if oggi == 6 {
        oggi = 0;
        tabella += "Dato che è domenica, ecco l'orario di lunedì \n";
    }

    if tipo_settimana == "0" || (tipo_settimana == "2" && classi[pos].find("1") != None ) {
        orario = &JSON_A.as_ref().unwrap()[classi[pos].to_string()][giorni[oggi]];
    } else {
        orario = &JSON_B.as_ref().unwrap()[classi[pos].to_string()][giorni[oggi]];
    }

    // Controlla se l'orario è vuoto, grazie 3A AFM per esistere
    if orario[layout[0]].as_array().unwrap().len() > 0 {


        for i in 0..6
        {
            tabella += &*format!("Materia: {} - Professore: {} - Aula: {} \n", orario[layout[0]][i], orario[layout[1]][i], orario[layout[2]][i]);
        }

    } else {
       tabella = "Mi dispiace, ma l'orario è vuoto. Prova a cercare un'altra classe".to_string()
    }

    return tabella;

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

    return if std::path::Path::exists(path.as_ref()) {
        let mut file = File::open(path)?;

        let mut content = String::new();
        file.read_to_string(&mut content)?;

        let parsed_json: Value = serde_json::from_str(&content)?;

        Ok(parsed_json)
    } else {
        Err(Box::from("Il json non esiste"))
    }
}
