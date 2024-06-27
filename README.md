Please view the Wiki here for contextual information:

https://github.com/H3yfinn/transport_model_9th_edition/wiki

## SETUP
### Install Anaconda
run:
conda env create --prefix ./env_transport_model --file ./config/env_transport_model.yml

Then:
conda activate ./env_transport_model

Note that installing those libraries in the yml files will result in a few other dependencies also being installed.

## Run the model
Simply put, if using the command line, just use:
python workflow/main.py > output.txt 2>&1

If using Jupyter with Visual Studio Code, you can run the .py files cell by cell as separated by the #%% characters. I'm not sure how the #%% thing works outside of Visual Studio Code.

## Documentation
There are some documentation files in ./documentation/. They can be used in addition to the Wiki.

## Folder structure
./workflow/ - inside here are the files you need to run the model. 
./other_code/ - inside here is extra code that is useful to use for visualisation of the outputs, creation of input data and some kinds of analysis/exploration files. 
./config/ - general configurations you can set, other than those that are in the integrate.py file.

## State of this repository:
It's really messy and im sorry. Trying to keep up with schedule means ive had to prioritise getting things working over clean code and documentation. I will try to clean it up after it's all done.

## Integration with transport data system:
This repo makes use of a repo i also designed which is a data system for transport data. It is called transport_data_system and is available on my own Github page. I havent added it to APERC account because of it's use of the Large File System (LFS) which is not supported by APERC, yet. 