from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import uuid
import json
from datetime import datetime
from django.utils import timezone

from .serializers import EventSerializer, EventResponseSerializer
from .models import Event
from .storage import memory_store
from .tracking import tracking_client
from .error_capture import trigger_explode_error, DeliberateError


def get_request_id(request):
    request_id = request.headers.get('X-Request-ID')
    if request_id:
        return request_id
    return str(uuid.uuid4())[:8]
class EventView(APIView):

    def get(self, request):
        request_id = get_request_id(request)
        user_id = request.query_params.get('user_id')
        limit = request.query_params.get('limit', 20)

        if not user_id:
            response = Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Missing required parameter",
                        "details": {"user_id": "This query parameter is required."}
                    }

                }, status=status.HTTP_400_BAD_REQUEST
            )
            response['X-Request-ID'] = request_id
            return response 
        try:
            limit = int(limit)
            if limit <=0:
                raise ValueError("Limit must be positive")
            if limit > 100:
                limit = 100
        except ValueError:
            response = Response({
                "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid parameter",
                        "details": {"limit": ["Must be a positive integer ≤ 100"]}
                    }
            }, status=status.HTTP_400_BAD_REQUEST)
            response['X-Request-ID'] = request_id
            return response
        user_events = [event for event in memory_store if event['user_id'] == user_id]

        user_events = user_events[:limit]
        serializer = EventResponseSerializer(user_events, many=True)
        response = Response({
                "events": serializer.data,
                "count": len(user_events),
                "user_id": user_id
            },
            status=status.HTTP_200_OK)
        response['X-Request-ID'] = request_id
        return response

    def post(self,request):
        request_id = get_request_id(request)
        try:
            trigger_explode_error(request)
        except DeliberateError:
            raise
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        data = request.data.copy()
        data['request_id'] = request_id
        serializer = EventSerializer(data=data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            event = Event(
                id=event_id,
                received_at=timezone.now(),
                client_ts=validated_data.get('client_ts', timezone.now()),
                event=validated_data['event'],
                user_id=validated_data['user_id'],
                metadata=validated_data.get('metadata', {}),
                request_id=validated_data['request_id']
            )
            event.save()
            print(f"DEBUG memory_store before append: {len(memory_store)}")
            memory_store.insert(0, {
                "id": event.id,
                "event": event.event,
                "user_id": event.user_id,
                "received_at": event.received_at.isoformat(),
                "client_ts": event.client_ts.isoformat(),
                "metadata": event.metadata,
                "request_id": event.request_id
            })
            print(f"DEBUG memory_store after append: {len(memory_store)}")
            try:
                tracking_client.track_event(
                    user_id=event.user_id,
                    event_name=event.event,
                    properties={
                    'event_id': event_id,
                    'client_ts': event.client_ts.isoformat(),
                    'metadata': event.metadata,
                    'source': 'api_v1'
                },request_id=event.request_id)

            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Tracking error for event {event.id}: {str(e)}", exc_info=True)
                    
            response_data = {
                "id": event.id,
                "accepted": True,
                
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "error":"VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request):
        request_id = get_request_id(request)
        user_id = request.query_params.get('user_id')

        if user_id:
            deleted_db, _ = Event.objects.filter(user_id=user_id).delete()
            before_cache = len(memory_store)
            memory_store[:] = [event for event in memory_store if event.get('user_id') != user_id]
            deleted_cache = before_cache - len(memory_store)
        else:
            deleted_db, _ = Event.objects.all().delete()
            deleted_cache = len(memory_store)
            memory_store.clear()

        response = Response({
            "deleted_db": deleted_db,
            "deleted_cache": deleted_cache
        }, status=status.HTTP_200_OK)
        response['X-Request-ID'] = request_id
        return response