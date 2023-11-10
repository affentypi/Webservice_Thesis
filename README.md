# Bachelor Thesis Webservice by Jacob Fehn

## Usage
### Installation
After cloning the project, a virtual environment has to be created.
If the IDE does not automatically offer to create one, the terminal can be used
for that. The command depends on the installed Python version (in some cases python3 is needed).
```bash
python -m venv venv
```

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the required packages.
```bash
pip install -r requirements.txt
```
After that the web service is ready to go!

### Run the Webservice
If the IDE does not automatically recognize the flask framework and offers to run the Webservice,
either run the main.py file or use the terminal command (in some cases python3): 
```bash
python -m flask run
```

The Webservice then runs on local host and can be accessed under http://127.0.0.1:5000.
To terminate the Webservice "Press CTRL+C to quit" or use the "terminate" button in your IDE.

For further deployment or configuration, follow the steps of [deploying flask](https://flask.palletsprojects.com/en/2.0.x/deploying/).
Another useful tutorial is found [here](https://code.visualstudio.com/docs/python/tutorial-flask#_optional-activities).

## Functionality
The backend consists of html_processing.py and nlp.processing.py. Given a set of two documents (old and new)
they will gather all the changes and modifications and output them as return nlp_processing.process_nlp(...)
and simultaneously write an HTML file in folder templates which can be rendered by flask.
More details in the thesis paper itself.