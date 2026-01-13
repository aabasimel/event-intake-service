import json
import logging 
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import hashlib
import os

logger = logging.getLogger(__name__)

class TrackingClient:
    
    def __init__(self):
        self.config ={
            'segment_write_key': 'dummy_write_key_123',
            'posthog_api_key': 'dummy_posthog_key_456',
            'mixpanel_token': 'dummy_mixpanel_token_789',
            'enable_tracking': True
        }
        self.simulated_failure_rate = float(os.getenv("TRACKING_SIMULATED_FAILURE_RATE", "0.0"))

    def track_event(
            self,
            user_id:str,
            event_name:str,
            properties:Optional[Dict[str, Any]]=None,
            request_id:Optional[str]=None
    )->bool:
        if not self.config['enable_tracking']:
            logger.info("Tracking is disabled in configuration.")
            return False
        
        if not user_id or not event_name:
            logger.warning(f"Invalid: user_id ={user_id}, event_name = {event_name}")
            return False
        
        base_payload = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'userId': user_id,
            'event': event_name,
            'properties': properties or {},
            'context': {
                'library': {
                    'name': 'event-intake-service',
                    'version': '1.0.0'
                },
                'requestId': request_id or f'req_{uuid.uuid4().hex[:8]}'
            }
        }
        vendor_payloads ={
            'segment': self._build_segment_payload(base_payload),
            'posthog': self._build_posthog_payload(base_payload),
            'mixpanel': self._build_mixpanel_payload(base_payload)
        }

        for vendor, payload in vendor_payloads.items():
            logger.info(f"TRACK: {vendor}: {json.dumps(payload)}")
            try:
                self._send_to_vendor(vendor, payload)
            except Exception as e:
                logger.error(f"Failed to send to {vendor}: {str(e)}", exc_info=True)

        return True
    def _build_segment_payload(self, base_payload:Dict[str, Any])->Dict[str, Any]:
        segment_payload = {
            'writeKey': self.config['segment_write_key'],
            'type': 'track',
            'timestamp': base_payload['timestamp'],
            'event': base_payload['event'],
            'userId': base_payload['userId'],
            'properties': {**base_payload['properties']} ,
            'context': {**base_payload['context']}
        }
        return segment_payload
    def _build_posthog_payload(self, base_payload:Dict[str, Any])->Dict[str, Any]:
        return {
            'api_key': self.config['posthog_api_key'],
            'event': base_payload['event'],
            'distinct_id': base_payload['userId'],
            'properties': {**base_payload['properties'],'distinct_id': base_payload['userId'],},
            'timestamp': base_payload['timestamp']

        }
    def _build_mixpanel_payload(self, base_payload:Dict[str, Any])->Dict[str, Any]:
        return {
            'event': base_payload['event'],
            'properties': {
                'token': self.config['mixpanel_token'],
                'distinct_id': base_payload['userId'],
                'time': int(datetime.strptime(base_payload['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()),
                **base_payload['properties'],
                'mp_lib':'python'
            }
        }
    
    def _send_to_vendor(self, vendor:str, payload:Dict[str, Any])->None:
        logger.info(f"Sending event to {vendor}: {json.dumps(payload)}")
        import time
        time.sleep(0.01)

        import random
        if self.simulated_failure_rate > 0 and random.random() < self.simulated_failure_rate:
            raise Exception("Simulated network error")
        
tracking_client = TrackingClient()
