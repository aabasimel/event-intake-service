# Testing Strategy

### 1. API Endpoint Tests (`EventAPITests`)
- **Valid events are accepted and stored** 
  - Complete payload with all fields
- **Invalid events are rejected with proper errors**
  - Missing required fields (`event`, `user_id`)
  - Field length violations (too short/long)
  - Invalid timestamp format
  - **Metadata exceeding 2KB limit** (specific requirement)
  - Non-dict metadata

  ### 2. GET Endpoint Tests (`EventListTests`)
- **Correct ordering** (most recent first by insertion time)
- **Limit parameter respected**
  - Custom limit values
  - Default limit (20)
  - Maximum limit enforcement (100)
  - Invalid limit values rejected
  

# what I skipped due to time
### test for X-Request-Id propagation works
### 2. **Load/Performance Tests**
- Request rate limiting
- Response time under load (p95, p99)
- Memory usage with large event volumes

### 3. **Network Failure Tests**
- Simulated network partitions
- Third-party service timeouts
- Database connection failures

### 4. **Security Tests**
- Injection attack vectors
- Authentication/authorization (beyond scope)
- Rate limiting evasion attempts
## Extending to CI/CD

### 1. **Continuous Integration Pipeline**

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:alpine
        ports: [6379:6379]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements.txt
        pip install coverage pytest-django
    
    - name: Run tests with coverage
      run: |
        cd backend
        coverage run manage.py test event_api
        coverage xml
        coverage report
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
```
    
# 2. Real Coverage Metrics

```bash
cd backend
coverage run --source='.' manage.py test event_api
coverage report -m  
coverage html      
  