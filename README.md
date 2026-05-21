# Audit Universe Manager
# AI Service - Audit Universe Manager

This AI service is the Flask-based microservice for the Audit Universe Manager capstone project. It provides AI-powered audit text analysis features through REST APIs running on port 5000. 

## Features

The service currently exposes the following endpoints:
- `POST /describe` - generates a plain-language description of an audit issue.
- `POST /recommend` - returns 3 structured recommendations as JSON.
- `POST /generate-report` - returns a structured audit report as JSON.
- `GET /health` - returns service health, model, uptime, and response metrics. 

## Tech Stack

The AI service uses the following stack:
- Python 3.11
- Flask 3.x
- Groq API
- LLaMA-3.3-70b model
- Prompt templates stored in text files under `prompts/` 

## Project Structure

```text
ai-service/
├── routes/
│   ├── describe.py
│   ├── recommend.py
│   └── generate_report.py
├── services/
│   └── groq_client.py
├── prompts/
│   ├── describe_prompt.txt
│   ├── recommend_prompt.txt
│   └── generate_report_prompt.txt
├── app.py
├── requirements.txt
├── Dockerfile
└── README.md
```

This folder structure follows the capstone guide for the Python AI microservice. 

## Prerequisites

Before running the service, make sure the following are installed:
- Python 3.11
- pip
- Groq API key
- virtual environment support (`venv`) 

## Environment Variables

Create a `.env` file inside `ai-service/` and define the required environment variables.

Example:

```env
GROQ_API_KEY=your_groq_api_key_here
```

The project guide requires environment variables to be used for secrets instead of hardcoding them in code. [file:16]

## Installation

Open a terminal inside the `ai-service` folder and run:

```bash
python -m venv .venv
```

Activate the virtual environment:

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### Windows CMD

```cmd
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Service

Start the Flask AI service with:

```bash
python app.py
```

The service will run on:

```text
http://127.0.0.1:5000
```

Health check endpoint:

```text
http://127.0.0.1:5000/health
``` 

The capstone project specifies the AI microservice on port 5000 and uses `/health` for service verification. 

## API Endpoints

### 1. POST /describe

Generates a human-readable description of the submitted audit issue.

#### Request Body

```json
{
  "input_text": "Missing supporting invoices for vendor payments."
}
```

#### Example Response

```json
{
  "description": "The audit issue indicates that vendor payments were processed without complete supporting invoices, creating a risk of unauthorized or unverifiable transactions.",
  "generated_at": "2026-05-21T09:25:10.000000+00:00",
  "response_time_ms": 1180.45,
  "is_fallback": false
}
```

#### Validation Rules

- `input_text` is required
- `input_text` must be a string
- `input_text` cannot be empty
- `input_text` cannot exceed 5000 characters

---

### 2. POST /recommend

Returns exactly 3 structured recommendations for the audit issue.

#### Request Body

```json
{
  "input_text": "Missing supporting invoices for vendor payments."
}
```

#### Example Response

```json
{
  "recommendations": [
    {
      "actiontype": "Control Improvement",
      "description": "Require complete supporting documents before vendor payment processing.",
      "priority": "High"
    },
    {
      "actiontype": "Compliance",
      "description": "Introduce mandatory approval checks for vendor payments above threshold limits.",
      "priority": "High"
    },
    