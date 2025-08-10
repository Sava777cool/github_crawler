# GitHub Crawler

> Script for scraping search data by keywords.

![python](https://img.shields.io/badge/python-3.11-BLUE)

## Content
- [Installation](#installation)
- [Description](#description)

## Installation
- Ubuntu
- Python3.11

#### Virtualenv
```shell script
$ sudo apt install virtualenv
```
## Clone
`https://github.com/Sava777cool/github_crawler.git`

## Setup
Install virtualenv in project folder.
```shell script
[project_folder]$ virtualenv -p $(which python3.11) venv
```
**Don't change the name "venv", the path to the virtual environment is used when creating services.** 

**If you want to change the name, make the appropriate changes to the file `[project_folder]/services/install.sh`**
```shell script
...
touch "$ENV_PRJ_SRC"
echo "VENV_PATH=${PWD}/venv" >> "${ENV_PRJ_SRC}"
...
```
Activate virtualenv
```shell script
[project_folder]$ source venv/bin/activate
```
Install python packages from requirements.txt
```shell script
(venv)[project_folder]$ pip install -r requirements.txt
```
Create the source.json file in the root `[project_folder]`
and enter the appropriate data for crawling, example data in file source.json:
```source.json
# [project_folder]/source.json

{
  "keywords": ["django", "html", "css"],
  "proxies": ["82.208.33.96", "47.236.163.74:8080", "32.223.6.94:80"],
  "type": "Repositories"
}

```

## Description
The program consists of the following packages:
#### main.py
- main file for start crawling;

#### source.json
- file with configuration data for start crawling (proxy, keywords, type of search);

#### result.json
- file with result of crawling;

#### tests/test_scraper.py
-file with tests for scraper;

#### Run scripts

`python main.py` - start crawling with default configuration and save data in result.json in current folder.

`python main.py -f, --file source.json` - start crawling with custom file name with source data and save data in result.json in current folder.

`pytest` - run tests.

`pytest -v` - run tests with details.


