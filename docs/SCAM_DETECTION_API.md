# Scam Detection API Documentation

## Overview
The Nova AI Scam Detection Service provides an intelligent API endpoint that detects scam/spam messages with fuzzy matching and context analysis.

## Features
- **Multilingual Support**: English, Spanish, Vietnamese
- **Smart Detection**: Detects variations of contact app names (Telegram, WhatsApp, Viber, Zalo, Messenger)
- **Fuzzy Matching**: Handles common obfuscations:
  - Dots: `te.legram`
  - Underscores: `tele_gram`
  - Mixed characters: `telegrаm` (with Cyrillic 'а')
  - Typos: `telagram`
- **Context-Aware**: Uses ML model to understand context
  - "I don't use telegram" → Safe (not scam)
  - "Call me on telegram" → Scam
- **Scope**: Detects contact app promotion, NOT email addresses

## API Endpoint

### POST `/api/v1/detect-scam`

Analyzes a message for scam indicators.

#### Request Body
```json
{
  "message": "Contact me on te.legram",
  "language": "en"
}
```

**Parameters:**
- `message` (string, required): The message text to analyze
- `language` (string, optional): Language code - 'en' (default), 'es', 'vi'

#### Response

```json
{
  "is_scam": true,
  "scam_score": 78.5,
  "reason": "Contact app(s) detected: telegram | Scam context detected (confidence: 0.23)",
  "keywords_found": {
    "telegram": 0.98
  },
  "context": {
    "is_scam_context": true,
    "confidence": 0.23,
    "top_label": "user is promoting a contact method for scam/money",
    "all_scores": {
      "user is promoting a contact method for scam/money": 0.23,
      "user is discussing a contact method for legitimate purposes": 0.35,
      "user is warning about scammers": 0.28,
      "user is sharing personal experience or opinion": 0.14
    }
  },
  "language": "en"
}
```

**Response Fields:**
- `is_scam` (boolean): Whether the message is classified as scam (threshold: score >= 50)
- `scam_score` (float): Confidence score 0-100
  - 0-40: Likely safe
  - 40-60: Uncertain/warning zone
  - 60-100: Likely scam
- `reason` (string): Human-readable explanation
- `keywords_found` (object): Contact apps detected with confidence scores
- `context` (object): ML model's context analysis
- `language` (string): Language used for analysis

## Scam Score Calculation

The scam_score is calculated with two components:

### 1. Keyword Detection (0-70 points)
- Based on fuzzy matching of contact app names
- Higher confidence = higher score

### 2. Context Analysis (-50 to +30 points)
- Uses zero-shot classification (facebook/bart-large-mnli model)
- Positive contexts (promoting contact method) → adds 0-30 points
- Negative contexts (warning, legitimate discussion) → subtracts 0-50 points

**Example:**
- Message: "Contact me on telegram"
  - Keywords: telegram (1.0 confidence) → 70 points base
  - Context: "promoting contact method" → +15 points
  - Total: 85 points → is_scam = true

- Message: "I don't use telegram"
  - Keywords: telegram (1.0 confidence) → 70 points base
  - Context: "legitimate discussion" → -40 points
  - Total: 30 points → is_scam = false

## Usage Examples

### Python Client
```python
import httpx

async def check_message(message: str, language: str = "en"):
    client = httpx.AsyncClient()
    response = await client.post(
        "http://localhost:8000/api/v1/detect-scam",
        json={
            "message": message,
            "language": language
        }
    )
    return response.json()

# Usage
result = await check_message("Call me on telegram")
if result['is_scam']:
    print(f"Scam detected! Score: {result['scam_score']}")
else:
    print("Message appears safe")
```

### Rails Integration
```ruby
require 'net/http'
require 'json'

def check_message_for_scam(message, language = 'en')
  uri = URI('http://localhost:8000/api/v1/detect-scam')
  
  request = Net::HTTP::Post.new(uri)
  request.content_type = 'application/json'
  request.body = JSON.generate({
    message: message,
    language: language
  })
  
  response = Net::HTTP.start(uri.hostname, uri.port) do |http|
    http.request(request)
  end
  
  JSON.parse(response.body)
end

# Usage
result = check_message_for_scam("Contact me on te.legram")
if result['is_scam']
  # Take action: flag message, increment scam_score, etc.
  puts "Scam detected: #{result['reason']}"
else
  puts "Message is safe to deliver"
end
```

### cURL Example
```bash
curl -X POST http://localhost:8000/api/v1/detect-scam \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Call me on telegram",
    "language": "en"
  }'
```

## Supported Contact Apps
- Telegram / Tele / TG
- WhatsApp / WA / Whatapp
- Viber
- Zalo (Vietnamese messenger)
- Messenger / Facebook Messenger
- **NOT**: Email addresses (by design)

## Error Handling

### 400 Bad Request
```json
{
  "detail": "Message cannot be empty"
}
```

```json
{
  "detail": "Language must be 'en', 'es', or 'vi'"
}
```

### 500 Internal Server Error
If the ML model fails to load or analyze context, the service will:
1. Return `is_scam_context: false` in context
2. Still provide keyword-based detection
3. Log warning message

## Performance Notes
- **First request**: ~3-5 seconds (model loading)
- **Subsequent requests**: ~200-500ms
- **Memory**: ~2.5 GB for the classification model
- **GPU**: Optimized for MPS (Mac), CUDA (Nvidia), CPU fallback

## Language Support
- **English (en)** - Full support
- **Spanish (es)** - Full support  
- **Vietnamese (vi)** - Full support
- **Other languages** - English fallback detection may work

## Best Practices
1. Cache the result if checking same message multiple times
2. Use appropriate language parameter for accurate multi-language detection
3. Score >= 60 should trigger manual review or account action
4. Score >= 80 can trigger automatic message censoring
5. Consider the `reason` and `context` in logs for monitoring patterns

## Deployment Configuration
Add to `.env`:
```
SCAM_DETECTION_ENABLED=true
SCAM_DETECTION_THRESHOLD=50  # is_scam = True if score >= threshold
SCAM_ACTION_THRESHOLD=70     # Auto-action (censor/suspend) if >= this
```
