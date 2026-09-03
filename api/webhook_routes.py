"""
FastAPI router simulating Terra Webhook Data Ingestion.
Demonstrates processing of incoming streaming telemetry from Apple, Oura, Whoop, Dexcom.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from data.terra_schemas import TerraWebhookEvent

router = APIRouter(prefix="/api/webhooks", tags=["Terra Webhook Ingestion"])

# In-memory buffer for recent webhooks (observability demo)
RECENT_WEBHOOKS: List[Dict[str, Any]] = []


@router.post("/terra")
async def receive_terra_webhook(event: TerraWebhookEvent):
    """
    Ingests real-time Terra webhook payload events (daily, sleep, activity, body).
    Validates payload integrity and acknowledges delivery with a 200 OK.
    """
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
