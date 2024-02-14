use std::error::Error;
use std::fs::File;
use std::io::Read;
use teloxide::{prelude::*, utils::command::BotCommands};
use serde_json::{Value};
use lazy_static::lazy_static;
use std::sync::Mutex;
use regex::Regex;
use time::OffsetDateTime;

// My beloved global variables <3
lazy_static! {
    static ref CLASSI: Mutex<Vec<String>> = Mutex::new(vec![]);
    static ref JSON: Value = leggo_json("orario.json".to_string()).unwrap();

}

#[tokio::main]
async fn main() {
    pretty_env_logger::init();
    log::info!("Starting command bot...");

    // Devo trovare un metodo migliore per inzializzare JSON
    println!("{}", JSON.is_boolean());

    let bot = Bot::from_env();
    Command::repl(bot, answer).await;

}

/*
    Robe da fare:
        Cerca classe
        Vedi orario di un giorno particolare -> Come?
        Help -> Fatto
        Segnala un bug
 */

fn leggo_json(path: String) -> Result<Value, Box<dyn Error>> {

    let mut file = File::open(path)?;

    let mut content = String::new();
    file.read_to_string(&mut content)?;

    let parsed_json: Value = serde_json::from_str(&content)?;

    if let Some(object) = parsed_json.as_object() {
        for (chiave, _) in object {
            CLASSI.lock().unwrap().push(chiave.to_string());
        }
    } else {
        panic!("JSON non valido");
    }

    Ok(parsed_json)
}

#[derive(BotCommands, Clone)]
#[command(rename_rule = "lowercase", description = "These commands are supported:")]
enum Command {
    #[command(description = "Fa partire il bot e manda questo messaggio")]
    Start,
    #[command(description = "Mostra questo messaggio")]
    Help,
    #[command(description = "Cerca una classe e mostro l'orario di oggi.")]
    Cerca(String),
    #[command(description = "handle a username and an age.", parse_with = "split")]
    UsernameAndAge { username: String, age: u8 },
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
        Command::UsernameAndAge { username, age } => {
            bot.send_message(msg.chat.id, format!("Your username is @{username} and age is {age}."))
                .await?
        }
    };
    Ok(())
}
fn cerco_la_classe(mut classe: String) -> String {
    // Toglie gli spazi da classe
    let regex = Regex::new(r"(?m)\s+").unwrap();

    classe = regex.replace_all(&*classe.to_uppercase(), "").to_string();

    let mut trovato = false;
    let mut i = 0;

    while !trovato && i < CLASSI.lock().unwrap().len() {
        if CLASSI.lock().unwrap()[i] == classe
        {
            trovato = true;
        } else
        {
            i += 1;
        }
    }

    if trovato {
        return stampo_classe(i);
    } else {
        return "La classe non esiste, devi cercarla così: ex 3A AFM".to_string();
    }
}

fn stampo_classe(pos: usize) -> String {
    let giorni = vec!["lunedi", "martedi", "mercoledi", "giovedi", "venerdi"];
    let layout = vec!["materie", "professori", "aule"];

    let oggi: usize = (OffsetDateTime::weekday(OffsetDateTime::now_utc()).number_from_monday() - 1) as usize;

    let orario = &JSON[CLASSI.lock().unwrap()[pos].to_string()][giorni[oggi]];

    if orario.as_object().unwrap().len() > 0 {
        let mut s = String::new();

        for i in 0..6
        {
            s += &*format!("Materia: {} - Professore: {} - Aula: {} \n", orario[layout[0]][i], orario[layout[1]][i], orario[layout[2]][i]);
        }

        return s;
    } else {
        return "Mi dispiace, ma l'orario è vuoto. Puoi segnarlarlo come bug con /segnala".to_string();
    }


}
