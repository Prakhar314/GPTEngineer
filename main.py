import evadb
import os

from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    print(os.environ["OPENAI_KEY"])
    # Connect to EvaDB and get a database cursor for running queries
    cursor = evadb.connect().cursor()

    # create table with text and response columns
    cursor.query("DROP TABLE IF EXISTS qa;").execute()
    cursor.query("CREATE TABLE qa (text TEXT(50), response TEXT(50));").execute()
    cursor.query("INSERT INTO qa (text, response) VALUES ('Hello', 'Hi');").execute()
    cursor.query("INSERT INTO qa (text, response) VALUES ('I hate you', 'Hi');").execute()
    print(cursor.table("qa").select(f"ChatGPT('Analyze the sentiment here. Answer in 1 word', text)").df()["chatgpt.response"])