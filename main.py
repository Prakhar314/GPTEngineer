import evadb
import os

from dotenv import load_dotenv

DEBUG = False

def read_prompt_from_dir(prompt_dir: str) -> str:
    prompt = ""
    with open(os.path.join(prompt_dir, "prompt"), "r") as f:
        prompt = f.read()
    return prompt

def print_colored(text: str, color: str, end: str = "\n"):
    if color == "red":
        print("\033[91m {}\033[00m".format(text), end=end)
    elif color == "green":
        print("\033[92m {}\033[00m".format(text), end=end)
    elif color == "yellow":
        print("\033[93m {}\033[00m".format(text), end=end)
    elif color == "blue":
        print("\033[94m {}\033[00m".format(text), end=end)
    elif color == "magenta":
        print("\033[95m {}\033[00m".format(text), end=end)
    else:
        print(text,end=end)

def colored_input(text: str, color: str = "red", end: str = "") -> str:
    print_colored(text, color, end=end)
    return input()

def save_files(project_dir: str, output:str):
    lines = output.split("\n")
    i = 0
    while i < len(lines):
        if lines[i].startswith("```") and i>0:
            filename = os.path.join(project_dir,lines[i-1].strip())
            # create directory if it doesn't exist
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            # collect code
            j = i+1
            code = ""
            while j < len(lines):
                if lines[j].startswith("```"):
                    break
                else:
                    code += lines[j] + "\n"
                j += 1
            i = j + 1

            # write code to file
            with open(filename, "w") as f:
                f.write(code)
        else:
            i += 1


class EvaDB:
    def __init__(self, reset=False):
        self.cursor = evadb.connect().cursor()
        if reset:
            self.drop_table()
        self.cursor.query("CREATE TABLE IF NOT EXISTS prompts (project TEXT(20) UNIQUE, prompt TEXT(20));").execute()
        self.cursor.query("CREATE FUNCTION IF NOT EXISTS TunedGPT IMPL 'chatgpt_tuned.py';").execute()

    def get_prompt(self, project: str) -> str:
        query = f"""SELECT prompt FROM prompts WHERE project = \"{project}\";"""
        ans = self.cursor.table("prompts").select("prompt").filter(f"project = \"{project}\"").df()
        if len(ans) == 0:
            return ""
        else:
            return ans.iloc[0,0]
        
    def insert_prompt(self, project: str, prompt: str):
        # escape single quotes
        prompt = prompt.replace("'", "\'")
        
        query = ""
        if self.get_prompt(project) != "":
            query = f"""DELETE FROM prompts WHERE project = \"{project}\";"""
            self.cursor.query(query).execute()

        query = f"""INSERT INTO prompts (project, prompt) VALUES (\"{project}\", \"{prompt}\");"""
        self.cursor.query(query).execute()

    def add_clarification(self, project: str, clarification: str):
        current_prompt = self.get_prompt(project)
        new_prompt = current_prompt + "\n" + clarification
        self.insert_prompt(project, new_prompt)
    
    def drop_table(self):
        self.cursor.drop_table("prompts").execute()

    def ask_gpt(self, prompt:str, user_input: str) -> str:
        # swap single quotes with double quotes
        prompt = prompt.replace("\'", "\"")
        user_input = user_input.replace("\'", "\"")

        query = f"SELECT TunedGPT(\'{user_input}\', \'{prompt}\');"
        if DEBUG:
            print_colored(query, "yellow")

        return self.cursor.query(query).df()["tunedgpt.response"][0]

    def get_preprompt(self, preprompt:str)->str:
        f = open(os.path.join("pre_prompts", preprompt), "r")
        ret = f.read()
        return ret
    
if __name__ == "__main__":
    load_dotenv()
    
    #Take project directory as input from user
    project_dir = colored_input("Enter project directory: ")

    prompt = read_prompt_from_dir(project_dir)

    evaDB = EvaDB(reset=False)
    
    #Insert prompt into database
    evaDB.insert_prompt(project_dir, prompt)

    gpt_query = evaDB.get_preprompt("clarify_req") 
    user_input = "Project Description: \n" + evaDB.get_prompt(project_dir)

    while True:
        gpt_ans = evaDB.ask_gpt(gpt_query, user_input)
        print_colored(gpt_ans, "green")
        if gpt_ans.lower().startswith("nothing"):
            break

        # check if the user wants to add a clarification
        clarification = colored_input("Clarify? (y/n): ")
        if clarification.lower() == "y" or clarification.lower() == "yes":
            clarification = colored_input("Enter clarification: ")
            user_input += "\n" + gpt_ans + "\n" + clarification
            gpt_query = evaDB.get_preprompt("clarify_opt") 
        else:
            gpt_query = evaDB.get_preprompt("clarify_end")
            break
    
    # generate code
    print_colored("Generating code...", "yellow")
    gpt_query = gpt_query + evaDB.get_preprompt("generate").replace("FILE_FORMAT", evaDB.get_preprompt("file_format"))

    gpt_ans = evaDB.ask_gpt(gpt_query, user_input)
    print_colored(gpt_ans, "green")

    # ask user if they want to save the code
    save = colored_input("Save code? (y/n): ")
    if save.lower() == "y" or save.lower() == "yes":
        save_files(project_dir, gpt_ans)
        print_colored("Code saved!", "red")
    