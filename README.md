## Usage

* Create the environment: `conda env create -f environment.yml`
* Open `issues_to_latex_config.yaml` and configure it the way tou need. Don't forget to 
type your password there. 
* Run `python issues_to_latex.py`, in case you get `JIRAError 403 CAPTCHA_CHALLENGE` open your browser and logout/login again on
Jira. 

After running `python issues_to_latex.py`, a `issues_to_latex.txt` is generated.

The `issues_to_latex.py` script expects a `issues_to_latex_config.yaml` on the same folder, 
so in case need to move the script, don't forget to move the config file as well. 
