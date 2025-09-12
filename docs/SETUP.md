# HackMerlin Agent – Setup Guide

## 1. Clone repo: https://github.com/ShikhaAtGitHub/hackermerlin-agent.git

## 2. Create Virtual Environment
python3 -m venv hackervenv

## 3. Activate
source hackervenv/bin/activate

## 4. Install Requirements:
pip install --upgrade pip
pip install -r requirements.txt

## 5. Install Playwright Browser
playwright install

## 6. Run Agent
python -m src.run_agent



