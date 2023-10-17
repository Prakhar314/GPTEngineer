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
        print(text, end=end)


def colored_input(text: str, color: str = "red", end: str = "") -> str:
    print_colored(text, color, end=end)
    return input()


def save_files(project_dir: str, output: str):
    lines = output.split("\n")
    i = 0
    while i < len(lines):
        if lines[i].startswith("```") and i > 0:
            filename = os.path.join(project_dir, lines[i-1].strip())
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

def cleanse(text: str) -> str:
    """
    Cleanses query inputs by replacing double quotes with single quotes.
    """
    return text.replace("\"", "\'")


class EngineerState:

    class PREPROMPT:
        CLARIFY_REQ = "clarify_req"
        CLARIFY_OPT = "clarify_opt"
        CLARIFY_END = "clarify_end"
        GENERATE = "generate"
        FILE_FORMAT = "file_format"

    def __init__(self, reset=False):
        self.cursor = evadb.connect().cursor()
        if reset:
            self.cursor.query("DROP TABLE IF EXISTS prompts;").execute()
            self.cursor.query("DROP TABLE IF EXISTS pre_prompts;").execute()
            self.cursor.query("DROP TABLE IF EXISTS clarifications;").execute()
            self.cursor.query("DROP FUNCTION IF EXISTS TunedGPT;").execute()

        self.cursor.query(
            "CREATE TABLE IF NOT EXISTS prompts (project TEXT(20) UNIQUE, prompt TEXT(200));").execute()

        # create TunedGPT function
        self.cursor.query(
            "CREATE FUNCTION IF NOT EXISTS TunedGPT IMPL 'chatgpt_tuned.py';").execute()

        # create pre-prompts table
        self.cursor.query(
            "CREATE TABLE IF NOT EXISTS pre_prompts (name TEXT(20) UNIQUE, prompt TEXT(2000));").execute()

        # create clarifications table
        self.cursor.query(
            "CREATE TABLE IF NOT EXISTS clarifications (project TEXT(20), question TEXT(2000), clarification TEXT(2000));").execute()

        # load pre-prompts
        self.load_preprompts()

    def get_prompt(self, project: str) -> str:
        """
        Returns the prompt for the given project.
        """
        
        ans = self.cursor.table("prompts").select(
            "prompt").filter(f"project = \"{project}\"").df()
        if len(ans) == 0:
            return ""
        else:
            return ans.iloc[0, 0]

    def insert_prompt(self, project: str, prompt: str):
        """
        Inserts the prompt into the database.
        """
        # escape single quotes
        project = cleanse(project)
        prompt = cleanse(prompt)

        query = ""
        if self.get_prompt(project) != "":
            query = f"""DELETE FROM prompts WHERE project = \"{project}\";"""
            self.cursor.query(query).execute()

            query = f"""DELETE FROM clarifications WHERE project = \"{project}\";"""
            self.cursor.query(query).execute()

        query = f"""INSERT INTO prompts (project, prompt) VALUES (\"{project}\", \"{prompt}\");"""
        self.cursor.query(query).execute()

    def drop_table(self):
        """
        Drops the prompts table.
        """
        self.cursor.drop_table("prompts").execute()

    def ask_gpt(self, gpt_prompt: str, gpt_context: str) -> str:
        """
        Asks GPT the given prompt and user input.
        """
        # swap single quotes with double quotes
        gpt_prompt = cleanse(gpt_prompt)
        gpt_context = cleanse(gpt_context)

        query = f"SELECT TunedGPT(\"{gpt_context}\", \"{gpt_prompt}\");"
        if DEBUG:
            print_colored(query, "yellow")

        return self.cursor.query(query).df()["tunedgpt.response"][0]

    def get_consolidated_prompt(self, project_dir: str) -> tuple[str, int]:
        """
        Returns the consolidated prompt for the given project.
        """
        # get prompt
        prompt = self.get_prompt(project_dir)
        if prompt == "":
            return ""

        # get all past clarifications
        clarifications = self.cursor.table("clarifications").select(
            "question, clarification").filter(f"project = \"{project_dir}\"").df()

        consolidated_prompt = "User description:\n" + prompt + "\n\n"
        if len(clarifications) > 0:
            consolidated_prompt += "Clarifications:\n"

        for i in range(len(clarifications)):
            consolidated_prompt += clarifications.iloc[i,
                                                       0] + "\n" + clarifications.iloc[i, 1] + "\n\n"
            
        return consolidated_prompt, len(clarifications)

    def ask_clarification(self, project_dir: str) -> str:
        """
        Asks the user for clarification.
        """

        # get consolidated prompt
        consolidated_prompt, clarification_count = self.get_consolidated_prompt(
            project_dir)

        # get clarification prompt
        clarification_prompt = ""
        if clarification_count == 0:
            clarification_prompt = self.get_preprompt(
                EngineerState.PREPROMPT.CLARIFY_REQ)
        else:
            clarification_prompt = self.get_preprompt(
                EngineerState.PREPROMPT.CLARIFY_OPT)

        if clarification_prompt == "":
            return ""

        # ask GPT
        return self.ask_gpt(clarification_prompt, consolidated_prompt)

    def save_clarification(self, project_dir: str, gpt_que: str, clarification: str):
        """
        Saves the clarification into the database.
        """
        project_dir = cleanse(project_dir)
        gpt_que = cleanse(gpt_que)
        clarification = cleanse(clarification)

        self.cursor.query(
            f"""INSERT INTO clarifications (project, question, clarification) VALUES (\"{project_dir}\", \"{gpt_que}\", \"{clarification}\");""").execute()

    def ask_generate(self, project_dir: str) -> str:
        # get consolidated prompt
        consolidated_prompt, _ = self.get_consolidated_prompt(project_dir)

        # get generate prompt
        generate_prompt = self.get_preprompt(EngineerState.PREPROMPT.GENERATE).replace(
            "FILE_FORMAT", self.get_preprompt(EngineerState.PREPROMPT.FILE_FORMAT))

        # ask GPT
        return self.ask_gpt(generate_prompt, consolidated_prompt)

    def get_preprompt_from_disk(self, preprompt: str) -> str:
        """
        Returns the pre-prompt from the pre_prompts directory.
        """
        with open(os.path.join("pre_prompts", preprompt), "r") as f:
            return f.read()

    def get_preprompt(self, preprompt: str) -> str:
        """
        Returns the pre-prompt from the database.
        """

        preprompt = cleanse(preprompt)

        ans = self.cursor.table("pre_prompts").select(
            "prompt").filter(f"name = \"{preprompt}\"").df()
        if len(ans) == 0:
            return ""
        else:
            return ans.iloc[0, 0]

    def load_preprompts(self):
        """
        Loads all pre-prompts from the pre_prompts directory.
        """
        for preprompt in os.listdir("pre_prompts"):
            if self.get_preprompt(preprompt) != "":
                # delete pre-prompt from database
                self.cursor.query(
                    f"""DELETE FROM pre_prompts WHERE name = \"{preprompt}\";""").execute()
            preprompt_text = cleanse(self.get_preprompt_from_disk(preprompt))
            
            self.cursor.query(
                f"""INSERT INTO pre_prompts (name, prompt) VALUES (\"{preprompt}\", \"{preprompt_text}\");""").execute()

def gpt_engineer(project_dir:str, reset:bool=False) -> None:
    load_dotenv()

    engineer = EngineerState(reset=reset)

    if not os.path.exists(project_dir):
        raise Exception(f"Project directory {project_dir} does not exist.")

    prompt = read_prompt_from_dir(project_dir)

    # Insert prompt into database
    engineer.insert_prompt(project_dir, prompt)

    while True:
        gpt_ans = engineer.ask_clarification(project_dir)
        print_colored(gpt_ans, "green")
        if gpt_ans.lower().startswith("nothing"):
            break

        # check if the user wants to add a clarification
        clarification = colored_input("Clarify? (y/n): ")
        if clarification.lower() == "y" or clarification.lower() == "yes":
            clarification = colored_input("Enter clarification: ")
            engineer.save_clarification(project_dir, gpt_ans, clarification)
        else:
            break

    # generate code
    print_colored("Generating code...", "yellow")

    gpt_ans = engineer.ask_generate(project_dir)
    print_colored(gpt_ans, "green")

    # ask user if they want to save the code
    save = colored_input("Save code? (y/n): ")
    if save.lower() == "y" or save.lower() == "yes":
        save_files(project_dir, gpt_ans)
        print_colored("Code saved!", "red")


if __name__ == "__main__":
    project_dir = colored_input("Enter project directory: ")
    gpt_engineer(project_dir, reset=True)
