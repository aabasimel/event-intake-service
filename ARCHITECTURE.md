## 1. Request Flow (ASCII Diagram)
```text
[Frontend]
        |
        | POST /api/events
        v
[Django Middleware Stack]
        | (Security, Logging, Metrics)
        v
[Django API View]
        |
        | 1. Validate payload
        | 2. Sanitize input
        | 3. Log metrics
        v
[Event Model]
        |
        | save()
        v
[PostgreSQL Database]
```
## 2. Three Failure Modes

- invalid payload (400 Bad Request)
   Return 400 with validation errors
   e.g Missing event field or invalid timestamp format

- Database Connection Failure(503 Service unvailable)
   Return 503, retry mechanism for aync tasks
   e.g When PostgresSQL is down, connection timeout
- Rate Limiting/Throttling Protection
  Return 429 Too Many Requests when client exceeds limits
## 3. API contract

### Endpoint 
```text
post /api/events

```
### Request Body

```json
{
  "client_ts": "ISO 8601 datetime",
  "event": "string, required",
  "user_id": "string, required",
  "metadata": "object, optional"
}
```
### Success Response(201 Created)
```json
{
  "id": "event_uuid",
  "status": "created",
  "received_at": "server_timestamp"
}
```
### Error Response
- 400 Bad Request: Validation failed
```json
{
  "error": "validation_error",
  "detail": {
    "event": ["This field is required."]
  }
}
```
### Tracking Integration Point

**Location in flow**: Tracking is called **after successful event storage** but **before returning response**.

**Reasoning**:
Event storage is primary: Ensure data persistence even if tracking fails
Non-blocking: Tracking should not block the user's request


### Vendor Failure Strategy

**Strategy**: **Async retry with**
- Retrying in the background, without blocking the main request/response flow.

**Implementation**:
```python
try:
    tracking_client.track_event(user_id, event_name, properties, request_id)
except Exception as e:
    # 1. Log failure (already captured by logger)
    # 2. Queue for async retry (Celery task)
    # 3. Continue request flow - DO NOT FAIL