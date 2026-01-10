# Event Intake Service

A Django REST API for ingesting, validating, storing, and tracking events from client applications. The service provides a reliable endpoint for event collection with multi-vendor analytics integration (Segment, PostHog, Mixpanel) and comprehensive error handling.

## Features

- **Event Ingestion**: POST endpoint to accept events from clients
-  **Request Validation**: Strict schema validation with detailed error messages
- **Persistent Storage**: SQLite/PostgreSQL backed event persistence
- **In-Memory Cache**: Fast retrieval of recent events by user
- **Multi-Vendor Tracking**: Automatic event forwarding to Segment, PostHog, and Mixpanel
- **Request Tracking**: Request ID propagation across the call stack
-  **Error Handling**: Graceful failure modes with per-vendor retry logic

## Quick Start

### Prerequisites

- Python 3.14+
- pip / virtual environment
- SQLite3 (default) or PostgreSQL

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/aabasimel/event-intake-service.git
   cd event-intake-service
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Apply database migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Start the development server**:
   ```bash
   python manage.py runserver 8000 --noreload
   ```
   The API is now available at `http://localhost:8000/api/v1/events`.

## API Endpoints

### POST /api/v1/events

Create a new event.

**Request Body**:
```json
{
  "event": "user_signed_up",
  "user_id": "user_123",
  "client_ts": "2024-06-01T12:00:00Z",
  "metadata": {
    "plan": "premium",
    "source": "mobile_app"
  }
}
```

**Response (201 Created)**:
```json
{
  "event_id": "evt_abc12345",
  "accepted": true,
  
}
```

**Field Requirements**:
- `event` (string, required): Event name (3–64 chars)
- `user_id` (string, required): User identifier (3–64 chars)
- `client_ts` (ISO 8601 datetime, optional): Client timestamp (defaults to server time)
- `metadata` (object, optional): Additional properties (max 2KB when serialized)
- `request_id` (string, optional): Request ID (auto-generated if not provided)

**Error Responses**:

- **400 Bad Request**: Validation failed
  ```json
  {
    "error": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "event": ["Ensure this field has at least 3 characters."],
      "metadata": ["Metadata exceeds 2KB limit when serialized"]
    }
  }
  ```

- **500 Internal Server Error**: Server-side failure (event still stored in DB)

### GET /api/v1/events

Retrieve recent events for a specific user.

**Query Parameters**:
- `user_id` (string, required): User identifier to filter by
- `limit` (integer, optional, default=20, max=100): Max events to return

**Request**:
```bash
GET /api/v1/events?user_id=user_123&limit=10
```

**Response (200 OK)**:
```json
{
  "events": [
    {
      "id": "evt_abc12345",
      "event": "user_signed_up",
      "user_id": "user_123",
      "received_at": "2024-06-01T12:00:10.123456Z",
      "client_ts": "2024-06-01T12:00:00Z",
      "metadata": { "plan": "premium" },
      "request_id": "req_12345678"
    }
  ],
  "count": 1,
  "user_id": "user_123"
}
```

**Error Responses**:

- **400 Bad Request**: Missing required `user_id` query parameter
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Missing required parameter",
      "details": {
        "user_id": "This query parameter is required."
      }
    }
  }
  ```

## Testing

Run the full test suite:

```bash
cd backend
python manage.py test event_api
```

Run specific tests:

```bash
python manage.py test event_api.tests.EventAPITests
python manage.py test event_api.tests.TrackingTests
```

Run with coverage:

```bash
coverage run --source='event_api' manage.py test
coverage report
```

For detailed testing documentation, see [TESTING.md](TESTING.md).

## Architecture

The service follows a layered architecture:

- **Views** (`views.py`): HTTP request handling and response formatting
- **Serializers** (`serializers.py`): Request/response validation and deserialization
- **Models** (`models.py`): Event data persistence
- **Tracking** (`tracking.py`): Multi-vendor analytics integration
- **Storage** (`storage.py`): In-memory event cache
- **Middleware** (`error_capture.py`): Global error handling and logging

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Configuration

Database settings are in `event_intake/settings.py`. Default uses SQLite:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

To use PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'event_intake_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Tracking Integration

Events are automatically forwarded to three analytics vendors after successful storage:

- **Segment**: `segment_write_key` (configured in `tracking.py`)
- **PostHog**: `posthog_api_key`
- **Mixpanel**: `mixpanel_token`

Tracking failures do **not** block the API response. Failed shipments are logged with error details for manual retry or investigation.

## Development

### Project Structure

```
event-intake-service/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── db.sqlite3
│   ├── api.http                    # HTTP test file for VS Code REST Client
│   ├── event_api/
│   │   ├── models.py               # Event model
│   │   ├── views.py                # EventView (GET/POST)
│   │   ├── serializers.py          # EventSerializer, EventResponseSerializer
│   │   ├── urls.py                 # API routes
│   │   ├── tracking.py             # TrackingClient (Segment, PostHog, Mixpanel)
│   │   ├── storage.py              # In-memory event cache
│   │   ├── error_capture.py        # Global error middleware
│   │   ├── tests.py                # Full test suite
│   │   ├── apps.py
│   │   ├── admin.py
│   │   └── migrations/
│   ├── event_intake/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
├── ARCHITECTURE.md
├── TESTING.md
├── README.md
└── LICENSE
```

### Running with the REST Client

Use the included `api.http` file in VS Code with the [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) extension:

```http
POST http://localhost:8000/api/v1/events
Content-Type: application/json

{
  "event": "user_signup",
  "user_id": "user_123",
  "metadata": {"plan": "premium"}
}

###

GET http://localhost:8000/api/v1/events?user_id=user_123&limit=20
Accept: application/json
```

## Deployment

For production deployment, use a WSGI/ASGI server:

### Gunicorn (WSGI)

```bash
pip install gunicorn
gunicorn event_intake.wsgi --workers 4 --bind 0.0.0.0:8000
```

### Uvicorn (ASGI)

```bash
pip install uvicorn
uvicorn event_intake.asgi --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
CMD ["gunicorn", "event_intake.wsgi", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

Build and run:

```bash
docker build -t event-intake-service .
docker run -p 8000:8000 event-intake-service
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for your changes
4. Commit your changes (`git commit -m "feat: add my feature"`)
5. Push to the branch (`git push origin feature/my-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License—see [LICENSE](LICENSE) for details.

## Support

For issues, questions, or contributions, please open an issue on [GitHub](https://github.com/aabasimel/event-intake-service/issues).

---

**Last Updated**: January 7, 2026
