import json
import logging
from io import StringIO
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .storage import memory_store

class EventAPITests(APITestCase):
    def setUp(self):
        memory_store.clear()
    def tearDown(self):
        memory_store.clear()

    def test_valid_event_accepted_and_stored(self):
        url = reverse ('create-event')
        data ={
            "client_ts": "2024-06-01T12:00:00Z",
            "event": "user_signed_up",
            "user_id": "u_123",
            "metadata": {"plan": "premium"},
            "request_id": "req_456"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('event_id', response.data)
        self.assertTrue(response.data['event_id'].startswith('evt_'))
        self.assertEqual(len(memory_store), 1)
        stored_event = memory_store[0]
        self.assertEqual(stored_event['event'], data['event'])
        self.assertEqual(stored_event['user_id'], data['user_id'])
    def test_metadata_too_large(self):
        url = reverse('create-event')
        large_metadata = {"key": "x" * 3000}
        data = {
            "event": "large_metadata_event",
            "user_id": "u_456",
            "metadata": large_metadata
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('exceeds 2KB limit', str(response.data['details']['metadata']))
        self.assertEqual(len(memory_store), 0)

class EventListTests(APITestCase):
    
    def setUp(self):
        """Set up test data"""
        memory_store.clear()
        
        self.test_user = "u_test_123"
        self.other_user = "u_other_456"
        
        for i in range(10):
            memory_store.insert(0, {
                'id': f'evt_{i:08d}',
                'received_at': f'2026-01-07T11:{i:02d}:00Z',
                'client_ts': f'2026-01-07T11:{i:02d}:00Z',
                'event': f'event_{i}',
                'user_id': self.test_user,
                'metadata': {'index': i},
                'request_id': f'req_{i}'
            })
        
        for i in range(5):
            memory_store.insert(0, {
                'id': f'evt_other_{i:03d}',
                'received_at': f'2026-01-07T12:{i:02d}:00Z',
                'client_ts': f'2026-01-07T12:{i:02d}:00Z',
                'event': f'other_event_{i}',
                'user_id': self.other_user,
                'metadata': {},
                'request_id': f'req_other_{i}'
            })
    
    def tearDown(self):
        """Clean up after each test"""
        memory_store.clear()
    
    def test_get_events_returns_correct_ordering(self):
        """Test that events are returned most recent first"""
        url = reverse('create-event')
        response = self.client.get(url, {'user_id': self.test_user})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertEqual(response.data['user_id'], self.test_user)
        
        events = response.data['events']
        self.assertEqual(len(events), 10)
        
        for i, event in enumerate(events):
            expected_index = 9 - i  # Most recent first
            self.assertEqual(event['event'], f'event_{expected_index}')
            self.assertEqual(event['metadata']['index'], expected_index)

# class TrackingTests(APITestCase):
#     def test_tracking_log_output(self):
#         """Test that tracking events are logged with TRACK: prefix"""
#         log_capture = StringIO()
#         handler = logging.StreamHandler(log_capture)
#         handler.setLevel(logging.INFO)
        
#         track_logger = logging.getLogger('event_api.tracking')
#         track_logger.addHandler(handler)
#         track_logger.setLevel(logging.INFO)
        
#         url = reverse('create-event')
#         data = {
#             "event": "button_clicked",
#             "user_id": "u_tracking_test"
#         }
        
#         response = self.client.post(url, data, format='json')
        
#         log_contents = log_capture.getvalue()
#         self.assertIn('TRACK:', log_contents)
        
#         track_logger.removeHandler(handler)
    
#     def test_tracking_payload_structure(self):
#         """Test that tracking payloads have correct structure"""
#         import json
#         log_capture = StringIO()
#         handler = logging.StreamHandler(log_capture)
        
#         track_logger = logging.getLogger('event_api.tracking')
#         track_logger.addHandler(handler)
#         track_logger.setLevel(logging.INFO)
        
#         url = reverse('create-event')
#         data = {
#             "event": "page_view",
#             "user_id": "u_123",
#             "metadata": {"page": "/home"}
#         }
        
#         response = self.client.post(url, data, format='json')
        
#         logs = log_capture.getvalue().strip().split('\n')
#         track_logs = [log for log in logs if 'TRACK:' in log]
        
#         self.assertGreaterEqual(len(track_logs), 3)
        
#         for track_log in track_logs:
#             parts = track_log.split('TRACK:', 1)[1].strip()
#             vendor, payload_str = parts.split(':', 1)
#             payload = json.loads(payload_str)
            
#             if vendor == 'segment':
#                 self.assertIn('event', payload)
#                 self.assertEqual(payload['event'], 'page_view')
#                 self.assertIn('properties', payload)
#             elif vendor == 'posthog':
#                 self.assertEqual(payload['event'], 'page_view')
#                 self.assertEqual(payload['distinct_id'], 'u_123')
#             elif vendor == 'mixpanel':
#                 self.assertEqual(payload['event'], 'page_view')
#                 self.assertIn('token', payload['properties'])
        
#         track_logger.removeHandler(handler)
    
#     def test_tracking_continues_on_failure(self):
#         """Test that request succeeds even if tracking fails"""
#         url = reverse('create-event')
#         data = {
#             "event": "test_event",
#             "user_id": "u_456"
#         }
        
#         response = self.client.post(url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)