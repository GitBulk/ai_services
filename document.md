# 📡 API Documentation
## 1. Process Image
Endpoint: POST /process

Payload (Form-data):
- file: Image file (binary).
- features: nsfw,vector (comma separated).

Response:
```json
{
  "image_id": "image_101.jpg",
  "moderation": {
    "label": "normal",
    "score": 0.982
  },
  "embedding": [0.12, -0.05, 0.88, "..."],
  "action": "allow"
}
```