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
python code/main.py > output.txt 2>&1

If using Jupyter with Visual Studio Code, you can run the .py files cell by cell as separated by the #%% characters. I'm not sure how the #%% thing works outside of Visual Studio Code.

## Documentation
There are some documentation files in ./documentation/. They can be used in addition to the Wiki.

## Folder structure
./code/ - inside here are the files you need to run the model. 
./other_code/ - inside here is extra code that is useful to use for visualisation of the outputs, creation of input data and some kinds of analysis/exploration files. 
./config/ - general configurations you can set, other than those that are in the integrate.py file.

## State of this repository:
It's really messy and im sorry. Trying to keep up with schedule means ive had to prioritise getting things working over clean code and documentation. I will try to clean it up after it's all done.

## Integration with transport data system:
This repo makes use of a repo i also designed which is a data system for transport data. It is called transport_data_system and is available on my own Github page. I havent added it to APERC account because of it's use of the Large File System (LFS) which is not supported by APERC, yet. 

Useful code:
git rm --cached -r .

## Public vs master branch:
Because this is an APERC project, there is a chance that some data should be kept relatively confidential, so I have created a public branch and repo which is a stripped down version of the private branch. Note that the private branch and repo is private to all except me, it really just acts as a backup. The public branch and repo does not contain any data besides what is needed to run it, and is for the purpose of sharing the code with the public and potentially running a lightweight webapp. Therefore the scenarios presented dont represent the scenarios in production on the private branch and repo as the private branch and repo is the one that is used for development and contains all the data/charts/outputs etc from our modelling work.

To manage this public branch and the private branch I keep two working trees (just folders, they dont use the git tree methods) on my local machine. One for the public branch and one for the private branch. I then work on the private branch and merge those changes into the public branch by pushing them to the private repo, then pulling them on the public tree's prviate branch, then merging them (and vice versa). This is to try reduce the risk of accidentally deleting data on the private branch that is not stored in the public branch.

Specifically, on my public branch working tree i have two branches: 
-public_master: This is the branch that is used by the public branch.
-private_master: this is the private branch, which is private and contains all the data on the private repo.

Then on my private branch working tree i just have the branches associated with development of the master branch, e.g. private_master, dev, feature branches etc.

# Management of branches
When you set up a public tree folder you will want to do this:
```bash
git branch --set-upstream-to=public/public_master public_master
git branch --set-upstream-to=private/private_masterprivate_master
```
This will allow you to push and pull from the correct branches on the correct trees while minimising the risk of accidentally pushing to the wrong repo.