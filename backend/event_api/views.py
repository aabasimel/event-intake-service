from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import uuid
import json
from datetime import datetime
from django.utils import timezone

from .serializers import EventSerializer
from .models import Event
from .storage import memory_store

class EventCreateView(APIView):
    
    def get(self, request):
        """View memory_store contents"""
        return Response({"memory_store": memory_store})

    def post(self,request):
        request_id = str(uuid.uuid4())[:8]
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
            print(f"DEBUG: Appending to memory_store. Current length: {len(memory_store)}")
            memory_store.append({
                "id": event.id,
                "event": event.event,
                "user_id": event.user_id,
                "received_at": event.received_at.isoformat(),
                "client_ts": event.client_ts.isoformat(),
                "metadata": event.metadata,
                "request_id": event.request_id
            })
            print(f"DEBUG: After append. memory_store length: {len(memory_store)}")
            response_data = {
                "event_id": event.id,
                "received_at": event.received_at.isoformat(),
                "request_id": event.request_id
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "error":"VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
