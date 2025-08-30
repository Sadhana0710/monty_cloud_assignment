# Image Service (Pyramid + AWS S3/DynamoDB via LocalStack)

## Prerequisites
- Docker / Docker Desktop
- Python 3.8+

## Setup
1. Start LocalStack
```bash
docker compose up -d
```
2. Create virtualenv and install deps
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
```
3. Load LocalStack environment (or export manually)
```bash
# Bash:
set -a && source local.env && set +a
# PowerShell:
Get-Content local.env | ForEach-Object { $k,$v = $_ -split '='; [System.Environment]::SetEnvironmentVariable($k,$v) }
```
4. Run the app
```bash
python run_local.py
# or
# pserve development.ini --reload
```

## APIs
- POST `/images` Upload image with metadata
  - multipart/form-data fields:
    - file: binary file
    - user_id: string (required)
    - title, description: optional
    - tags: comma separated e.g. "cat,pet"
  - or application/json:
    - file_base64: base64 string (required)
    - content_type: MIME type (optional)
    - user_id: string (required)
    - title, description, tags: optional
- GET `/images` List images with filters
  - Query params: `user_id`, `tag`, `limit`, `next_token`
- GET `/images/{image_id}` Get image metadata
- GET `/images/{image_id}/download` Download image bytes
- DELETE `/images/{image_id}` Delete image and metadata

## Curl examples
```bash
# Upload (multipart)
curl -X POST http://localhost:6543/images \
  -F user_id=user-123 \
  -F file=@./sample.jpg \
  -F title="My photo" \
  -F tags="cat,pet"

# List by user and tag
curl "http://localhost:6543/images?user_id=user-123&tag=cat"

# Get metadata
curl http://localhost:6543/images/{image_id}

# Download
curl -OJ http://localhost:6543/images/{image_id}/download

# Delete
curl -X DELETE http://localhost:6543/images/{image_id}
```

## Lambda handler
- Entry: `lambda_handler.handler`

## Testing
```bash
pytest -q
```