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
