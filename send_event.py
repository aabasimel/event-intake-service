#!/usr/bin/env python3
"""
CLI script to demonstrate frontend-backend wiring
Sends sample events and retrieves them back
"""
import requests
import json
import time
import sys
import uuid
from typing import Dict, Any

API_BASE_URL = "http://localhost:8081/api/v1/events"

class EventSimulator:
    
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def submit_event(self, event_data: Dict[str, Any], custom_request_id: str = None) -> Dict[str, Any]:
        headers = {}
        if custom_request_id:
            headers['X-Request-Id'] = custom_request_id
        
        event_name = event_data.get('event', '<missing>')
        user_id = event_data.get('user_id', '<missing>')
        print(f"Submitting event: {event_name} for user {user_id}")
        
        try:
            response = self.session.post(
                self.base_url,
                json=event_data,
                headers=headers
            )
            
            request_id = response.headers.get('X-Request-Id')
            print(f"   Request ID: {request_id}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 201:
                result = response.json()
                print(f" Event ID: {result['id']}")
                return {'success': True, 'data': result, 'request_id': request_id}
            else:
                error = response.json()
                print(f"   Error: {error.get('error', {}).get('message', 'Unknown error')}")
                return {'success': False, 'error': error, 'request_id': request_id}
                
        except requests.exceptions.ConnectionError:
            print(f"   Cannot connect to {self.base_url}")
            print("   Make sure the Django server is running: python manage.py runserver")
            return {'success': False, 'error': 'Connection failed'}
        except Exception as e:
            print(f"    Unexpected error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def retrieve_events(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        
        try:
            response = self.session.get(
                self.base_url,
                params={'user_id': user_id, 'limit': limit}
            )
            
            request_id = response.headers.get('X-Request-Id')
            print(f"   Request ID: {request_id}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                count = result.get('count', 0)
                print(f"  Found {count} events")
                
                events = result.get('events', [])
                for event in events:
                    print(f"       {event['event']} (ID: {event['id']}) at {event['received_at']}")
                
                return {'success': True, 'data': result, 'request_id': request_id}
            else:
                error = response.json()
                print(f"   Error: {error.get('error', {}).get('message', 'Unknown error')}")
                return {'success': False, 'error': error, 'request_id': request_id}
                
        except requests.exceptions.ConnectionError:
            print(f"    Cannot connect to {self.base_url}")
            return {'success': False, 'error': 'Connection failed'}
        except Exception as e:
            print(f"   Unexpected error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def test_api_connection(self) -> bool:
        """Test if API is accessible"""
        print("🔍 Testing API connection...")
        try:
            response = self.session.get(self.base_url)
            if response.status_code in [400, 200]:
                print(f" API is responding (status: {response.status_code})")
                return True
            else:
                print(f"   Unexpected status: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"   Cannot connect to {self.base_url}")
            print("   Start the backend with: cd backend && python manage.py runserver")
            return False
    
    def run_demo(self):
        print("=" * 60)
        
        
        if not self.test_api_connection():
            print("\n Cannot proceed. Please start the backend server.")
            return
        
        user_id = f"u_demo_{uuid.uuid4().hex[:8]}"
        print(f"\n Using demo user: {user_id}")
        
        sample_events = [
            {
                "event": "page_view",
                "user_id": user_id,
                "client_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "metadata": {"page": "/home", "source": "direct"}
            },
            {
                "event": "button_clicked",
                "user_id": user_id,
                "client_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "metadata": {"button": "signup", "color": "blue"}
            },
            {
                "event": "signup_completed",
                "user_id": user_id,
                "client_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "metadata": {"plan": "premium", "referral": "friend"}
            }
        ]
        
        print("\n" + "=" * 60)
        
        submitted_ids = []
        for i, event in enumerate(sample_events, 1):
            print(f"\nEvent {i}/3:")
            
            custom_request_id = None
            if i == 3:
                custom_request_id = f"demo-custom-req-{uuid.uuid4().hex[:8]}"
                print(f"   Using custom request ID: {custom_request_id}")
            
            result = self.submit_event(event, custom_request_id)
            if result['success']:
                submitted_ids.append(result['data']['id'])
            
            if i < len(sample_events):
                time.sleep(0.5)
        
     
        
        time.sleep(1)  
        retrieve_result = self.retrieve_events(user_id, limit=5)
        
    
        
        print("\nTesting 'explode' event (should trigger error):")
        explode_event = {
            "event": "explode",
            "user_id": user_id,
            "metadata": {"test": "error_handling"}
        }
        self.submit_event(explode_event)
        
        print("\nTesting validation error (missing required field):")
        invalid_event = {
            "user_id": user_id
        }
        self.submit_event(invalid_event)
        
        print("\n" + "=" * 60)
        print("Demo Complete! 🎉")
        print("=" * 60)
        print(f"User ID for testing: {user_id}")
        print(f"Backend URL: {self.base_url}")
    
    def quick_test(self):
       
        
        user_id = f"u_test_{uuid.uuid4().hex[:6]}"
        
        event = {
            "event": "test_event",
            "user_id": user_id,
            "metadata": {"test": True, "timestamp": time.time()}
        }
        
        submit_result = self.submit_event(event)
        if not submit_result['success']:
            return False
        
        time.sleep(0.5)
        retrieve_result = self.retrieve_events(user_id)
        
        return retrieve_result['success'] and retrieve_result['data']['count'] > 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Event Intake Frontend Simulator')
    parser.add_argument('--mode', choices=['demo', 'test', 'submit', 'retrieve'], 
                       default='demo', help='Operation mode')
    parser.add_argument('--url', default=API_BASE_URL, help='API base URL')
    parser.add_argument('--user-id', help='User ID for submit/retrieve operations')
    parser.add_argument('--event', help='Event type for submission')
    parser.add_argument('--metadata', help='JSON metadata for submission')
    parser.add_argument('--request-id', help='Custom X-Request-Id header value')
    parser.add_argument('--limit', type=int, default=10, help='Limit for retrieval')
    
    args = parser.parse_args()
    
    simulator = EventSimulator(args.url)
    
    if args.mode == 'demo':
        simulator.run_demo()
    elif args.mode == 'test':
        success = simulator.quick_test()
        sys.exit(0 if success else 1)
    elif args.mode == 'submit':
        if not args.user_id or not args.event:
            print("Error: --user-id and --event are required for submit mode")
            sys.exit(1)
        
        metadata = {}
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                print("Error: Invalid JSON in --metadata")
                sys.exit(1)
        
        event_data = {
            "event": args.event,
            "user_id": args.user_id,
            "client_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metadata": metadata
        }
        
        result = simulator.submit_event(event_data, args.request_id)
        sys.exit(0 if result['success'] else 1)
    elif args.mode == 'retrieve':
        if not args.user_id:
            print("Error: --user-id is required for retrieve mode")
            sys.exit(1)
        
        result = simulator.retrieve_events(args.user_id, args.limit)
        sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()