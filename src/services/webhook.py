"""
Webhook notification service for dispatching task completion alerts.
"""
import logging
import httpx

logger = logging.getLogger("hmd_matrix")


async def send_webhook_notification(webhook_url: str, task_id: str, status: str, payload: dict):
    """Sends an asynchronous POST request to an external webhook URL upon task completion."""
    if not webhook_url:
        return

    data = {
        "task_id": task_id,
        "status": status,
        "result": payload
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=data)
            if response.status_code >= 400:
                logger.warning(f"Webhook delivery failed for task {task_id} with status code {response.status_code}")
            else:
                logger.info(f"Webhook successfully delivered for task {task_id} to {webhook_url}")
    except Exception as e:
        logger.error(f"Error sending webhook for task {task_id}: {str(e)}")