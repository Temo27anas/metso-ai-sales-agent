# Sales Assistant CLI

CLI chat assistant for a mining industry salesperson. It answers product, service-cost and flotation questions using inputted data.
Author: [@Temo27anas]

## Setup

```
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY
python parse_reports.py   # one-time: turns the 50 service reports into data/processed/reports.csv
```

## Use

```
python main.py                      # chat
python main.py --once "question"    # one question
```

## How it works

The model only handles language. Every fact and number comes from one of three tools;

- **get_brochure** – product facts from the brochures, cited by page
- **estimate_service_cost** – costs, hours and rates from past service reports
- **assess_flotation** – compares silica/iron grades against hourly data from a reference plant

If the data doesn't have the answer (prices, competitors, missing products), the assistant says so.

## Files

- `main.py` – chat loop (OpenAI Responses API)
- `tools.py` – the three tools
- `prompts.py` – system prompt and report-extraction prompt
- `parse_reports.py` – extracts the messy service reports with the LLM, checks the numbers add up
- `config.py` – paths and model settings
