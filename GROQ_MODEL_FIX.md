# Fix: Groq Model Not Found Error

## Error Message
```
Model llama-3.3-70b-versatile not found: Error code: 404
```

## Solution

The model `llama-3.3-70b-versatile` **does NOT exist**. Update your `.env` file to use a valid model name.

### Quick Fix

1. Open your `.env` file in the project root
2. Find the line with `GROQ_MODEL=`
3. Change it to one of these valid models:

```env
GROQ_MODEL=llama-3.1-70b-versatile
```

### Valid Groq Models

- `llama-3.1-70b-versatile` (recommended - best quality)
- `llama-3.1-8b-instant` (fast, good quality)
- `mixtral-8x7b-32768` (high quality, large context window)
- `gemma-7b-it` (fast, efficient)
- `llama-3.2-3b-preview` (very fast, smaller model)

### Complete .env Example

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
```

### After Updating

1. Save the `.env` file
2. Restart your Flask backend
3. Try generating a study plan again

### Check Available Models

For the latest list of available Groq models, visit:
https://console.groq.com/docs/models

