use std::error::Error;
use serde_json::{Value};
use lazy_static::lazy_static;
use std::sync::Mutex;

lazy_static!{ 
    static ref PROVA: Mutex<Vec<String>> =  Mutex::new(vec![]);
    static ref TEST: Value = untyped_example().unwrap();
}


fn main() {
    println!("Please call {} at the number {}", TEST["name"], TEST["phones"][0]);
    println!("{}", PROVA.lock().unwrap()[0]);
}

fn untyped_example() -> Result<Value, Box<dyn Error>> {
    // Some JSON input data as a &str. Maybe this comes from the user.
    let data = r#"
        {
            "name": "John Doe",
            "age": 43,
            "phones": [
                "+44 1234567",
                "+44 2345678"
            ]
        }"#;

    // Parse the string of data into serde_json::Value.
    let v: Value = serde_json::from_str(data)?;

    // Access parts of the data by indexing with square brackets.

    PROVA.lock().unwrap().push("A A A CERCASI CERCASI".to_string());

    Ok(v)
}
