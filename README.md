# GPTEngineer

### Setup
Create and activate virtual environment.
```
python -m venv evadb-venv
source evadb-venv/bin/activate
```
Install dependencies
```
pip install -r requirements.txt
```

### Usage
Create an empty sub-directory with a file `prompt`.
Example:
```
mkdir calculator
echo "Make a calculator in python. Inputs will be a string. Addition, multiplication, subtraction and division should be supported." > calculator/prompt
```
Run the script
```
python main.py
```

### Demo
Print the included demo:
```
cat example_session.txt
```
