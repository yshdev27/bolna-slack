from fastapi import FastAPI, Request
from dotenv import load_dotenv
import os
import sys
import requests
import threading

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

load_dotenv()


app = FastAPI()


SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
BOLNA_API_KEY = os.getenv("BOLNA_API_KEY")


processed_calls = set()


''' send only the 4 fields we care about: id, agent_id, duration, transcript '''

# slack caps section text at 3000 chars, keep transcript within that
TRANSCRIPT_MAX = 2500


def send_to_slack(call):
    execution_id = call.get("id") or "unknown"
    agent_id = call.get("agent_id") or "unknown"
    duration = call.get("conversation_duration") or 0
    transcript = call.get("transcript") or "(no transcript)"
    if len(transcript) > TRANSCRIPT_MAX:
        transcript = transcript[:TRANSCRIPT_MAX] + "\n... [truncated]"

    text = (
        f"*id:* `{execution_id}`\n"
        f"*agent_id:* `{agent_id}`\n"
        f"*duration:* {duration}s\n"
        f"*transcript:*\n```{transcript}```"
    )

    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]

    r = requests.post(SLACK_WEBHOOK, json={"blocks": blocks}, timeout=10)
    print(f"[slack] {r.status_code}: {r.text[:200]}")  # debugging


def process_call(call):
    execution_id = call.get("id")
    try:
        send_to_slack(call)
    except Exception as e:
        print(f"[process_call] failed for {execution_id}: {e}")
        # let it retry next time
        processed_calls.discard(execution_id)




@app.post("/webhook/bolna")
async def webhook(request: Request):

    payload = await request.json()

    print("Incoming:", payload)  # debugging

    # fire on any terminal status so every call gets exactly one slack msg.
    # dedup below makes sure we send only once even if multiple arrive.
    TERMINAL = {
        "completed",
        "call-disconnected",
        "failed",
        "no-answer",
        "busy",
        "canceled",
        "balance-low",
    }
    if payload.get("status") not in TERMINAL:
        return {"ignored": True}

    execution_id = payload.get("id")

    # deduplication
    if execution_id in processed_calls:
        return {"duplicate": True}

    processed_calls.add(execution_id)

    # async in background, pass the whole payload so we don't re-fetch
    threading.Thread(
        target=process_call,
        args=(payload,),
        daemon=True,
    ).start()

    return {"accepted": True}
