import json
import logging
from io import StringIO
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class TrackingTests(APITestCase):
    """Tests for tracking integration"""
    
    def test_tracking_log_output(self):
        """Test that tracking events are logged with TRACK: prefix"""
        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.INFO)
        
        # Get tracking logger
        track_logger = logging.getLogger('event_api.tracking')
        track_logger.addHandler(handler)
        track_logger.setLevel(logging.INFO)
        
        # Create an event
        url = reverse('create-event')
        data = {
            "event": "button_clicked",
            "user_id": "u_tracking_test"
        }
        
        response = self.client.post(url, data, format='json')
        
        # Check logs contain TRACK: entries
        log_contents = log_capture.getvalue()
        self.assertIn('TRACK:', log_contents)
        
        # Clean up handler
        track_logger.removeHandler(handler)
    
    def test_tracking_payload_structure(self):
        """Test that tracking payloads have correct structure"""
        import json
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        
        track_logger = logging.getLogger('event_api.tracking')
        track_logger.addHandler(handler)
        track_logger.setLevel(logging.INFO)
        
        # Create event
        url = reverse('create-event')
        data = {
            "event": "page_view",
            "user_id": "u_123",
            "metadata": {"page": "/home"}
        }
        
        response = self.client.post(url, data, format='json')
        
        # Parse log lines
        logs = log_capture.getvalue().strip().split('\n')
        track_logs = [log for log in logs if 'TRACK:' in log]
        
        # Should have 3 track logs (segment, posthog, mixpanel)
        self.assertGreaterEqual(len(track_logs), 3)
        
        for track_log in track_logs:
            # Parse the log line
            parts = track_log.split('TRACK:', 1)[1].strip()
            vendor, payload_str = parts.split(':', 1)
            payload = json.loads(payload_str)
            
            # Verify common fields
            if vendor == 'segment':
                self.assertIn('event', payload)
                self.assertEqual(payload['event'], 'page_view')
                self.assertIn('properties', payload)
            elif vendor == 'posthog':
                self.assertEqual(payload['event'], 'page_view')
                self.assertEqual(payload['distinct_id'], 'u_123')
            elif vendor == 'mixpanel':
                self.assertEqual(payload['event'], 'page_view')
                self.assertIn('token', payload['properties'])
        
        track_logger.removeHandler(handler)
    
    def test_tracking_continues_on_failure(self):
        """Test that request succeeds even if tracking fails"""
        url = reverse('create-event')
        data = {
            "event": "test_event",
            "user_id": "u_456"
        }
        
        # This should succeed even if tracking fails
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)