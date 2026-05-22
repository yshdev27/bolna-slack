# Bolna → Slack Integration

Small FastAPI service that listens to Bolna webhook events and sends a Slack alert when a call is completed.

---

## Flow

Bolna webhook → FastAPI endpoint → fetch execution → Slack notification

---

## Data sent to Slack

- execution id  
- agent id  
- call duration  
- transcript  

---

## Setup

### 1. Install dependencies

pip install -r requirements.txt

---

### 2. Add environment variables

Create a `.env` file:

SLACK_WEBHOOK=<your_slack_webhook>  
BOLNA_API_KEY=<your_bolna_api_key>

---

## Run locally

uvicorn main:app --reload

Server runs on:  
http://localhost:8000

---

## Expose webhook (for testing)

Using ngrok:

ngrok http 8000

Webhook endpoint:

POST /webhook/bolna

Example:

https://<ngrok-url>/webhook/bolna

---