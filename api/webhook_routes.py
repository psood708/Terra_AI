"""
FastAPI router simulating Terra Webhook Data Ingestion.
Demonstrates processing of incoming streaming telemetry from Apple, Oura, Whoop, Dexcom.
"""

import json
import os
from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError
from typing import List, Dict, Any
from datetime import datetime
from data.terra_schemas import TerraWebhookEvent
from security.terra_signature import verify_terra_signature

router = APIRouter(prefix="/api/webhooks", tags=["Terra Webhook Ingestion"])

# In-memory buffer for recent webhooks (observability demo)
RECENT_WEBHOOKS: List[Dict[str, Any]] = []


@router.post("/terra")
async def receive_terra_webhook(request: Request):
    """
    Ingests real-time Terra webhook payload events (daily, sleep, activity, body).

    When `TERRA_SIGNING_SECRET` is configured, requests must carry a valid
    `terra-signature: t=<ts>,v1=<hex_hmac>` header (Terra's documented HMAC-SHA256
    scheme, verified against the raw body) or the request is rejected with 401.
    Without a configured secret, signature verification is skipped (local/dev use).
    """
    raw_body = await request.body()

    signing_secret = os.getenv("TERRA_SIGNING_SECRET")
    if signing_secret:
        signature_header = request.headers.get("terra-signature", "")
        if not verify_terra_signature(raw_body, signature_header, signing_secret):
            raise HTTPException(status_code=401, detail="Invalid Terra webhook signature")

    try:
        event = TerraWebhookEvent(**json.loads(raw_body))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid Terra webhook payload: {exc}")

    record = {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "user_id": event.user_id,
        "received_at": datetime.now().isoformat(),
        "payload_summary": {
            "keys_count": len(event.data),
            "sample_keys": list(event.data.keys())[:5]
        }
    }
    RECENT_WEBHOOKS.insert(0, record)
    if len(RECENT_WEBHOOKS) > 50:
        RECENT_WEBHOOKS.pop()

    return {
        "status": "success",
        "message": f"Terra event {event.event_type} ingested successfully",
        "event_id": event.event_id,
        "processed_at": record["received_at"]
    }


@router.get("/recent")
async def get_recent_webhooks():
    """
    Get recent simulated webhook deliveries for observability and debugging.
    """
    return {
        "buffer_size": len(RECENT_WEBHOOKS),
        "recent_events": RECENT_WEBHOOKS
    }
