from rest_framework import serializers 
from django.utils import timezone 
import json 

class EventSerializer(serializers.Serializer):
    event = serializers.CharField(
        required = True,
        min_length = 3,
        max_length = 64,
        trim_whitespace = True
    )
    user_id = serializers.CharField(
        required = True,
        min_length = 3,
        max_length = 64,
        trim_whitespace = True)
    client_ts = serializers.DateTimeField(required = False, default_timezone=timezone.UTC)
    metadata = serializers.JSONField(required = False, default=dict)
    request_id = serializers.CharField(
        required = False,
        min_length = 3,
        max_length = 64,
        trim_whitespace = True)
    def validate_metadata(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Metadata must be a JSON object.")
        try:
            json_str = json.dumps(value)
            if len(json_str) > 2048:
                raise serializers.ValidationError("Metadata exceeds 2KB limit when serialized")
            

        except (TypeError, ValueError):
            raise serializers.ValidationError("Metadata must be JSON serializable")
        
        return value
    
    def validate(self, attrs):
        if 'client_ts' not in attrs or attrs['client_ts'] is None:
            attrs['client_ts'] = timezone.now()
        return attrs