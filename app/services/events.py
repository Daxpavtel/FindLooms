"""
Events & Notifications Module
Acts as an event dispatcher and clear hook point for future notifications
(e.g., in-app notification center, email/SMS/push alerts).
Currently records structured events into the audit log and prepares notification payloads.
"""
from typing import Dict, Any, Optional
from app.repositories.audit import log_event


def emit_event(
    event_type: str,
    entity_type: str,
    entity_id: Optional[Any] = None,
    actor_id: Optional[Any] = None,
    payload: Optional[Dict[str, Any]] = None
) -> None:
    """
    Central event dispatch hook.
    1. Immediately records the event to immutable audit log.
    2. Dispatches to future notification channels (hook point).
    """
    details = payload or {}
    
    # 1. Audit log integration
    log_event(
        action=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        details=details
    )
    
    # 2. Future Notification Hook Point
    _dispatch_future_notification(event_type, entity_type, entity_id, actor_id, details)


def _dispatch_future_notification(
    event_type: str,
    entity_type: str,
    entity_id: Optional[Any],
    actor_id: Optional[Any],
    details: Dict[str, Any]
) -> None:
    """
    Hook point for future notifications:
    - strong_match_found: notify reporter and finder
    - claim_filed: notify staff reviewers
    - claim_decided: notify claimant with Approved/Rejected status and pickup details
    - item_archived: notify custodian/staff
    
    In this release, this hook simply formats the payload so an external
    notifier (email, push, WebSocket) can be attached seamlessly.
    """
    pass
