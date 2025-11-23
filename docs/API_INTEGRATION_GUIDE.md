# API Integration Guide - MWD Assistant

**Last Updated:** November 2025

This guide provides the latest best practices for integrating all AI APIs used in the MWD Assistant system.

---

## Overview

The MWD Assistant uses a multi-AI architecture with specialized roles:

| AI Provider | Role | Model | SDK Package |
|-------------|------|-------|-------------|
| **Gemini** | Primary workspace AI | Gemini 2.0 Flash | `google-genai` |
| **Claude** | Strategic deliverables | Sonnet 4.5 | `anthropic` |
| **OpenAI** | Internal communication | GPT-4o / GPT-4.1 | `openai` |
| **Perplexity** | Client comms & research | Sonar Pro | `perplexityai` |

---

## 1. Gemini API (Google) - PRIMARY AI

### Installation

```bash
pip install google-genai
```

⚠️ **IMPORTANT**: The old `google-generativeai` package is **DEPRECATED**. Support ends **November 30, 2025**. Use `google-genai` instead.

### Environment Variables

```bash
# For Gemini Developer API
GEMINI_API_KEY=your_gemini_api_key_here

# OR for Vertex AI (Google Cloud)
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
```

### Basic Usage

```python
from google import genai

# Initialize client (Developer API)
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

# OR for Vertex AI
client = genai.Client(
    vertexai=True,
    project=os.getenv('GOOGLE_CLOUD_PROJECT'),
    location=os.getenv('GOOGLE_CLOUD_LOCATION')
)

# Generate content
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Summarize this meeting: ...'
)

print(response.text)
```

### Streaming Responses

```python
response = client.models.generate_content_stream(
    model='gemini-2.0-flash',
    contents='Generate a detailed analysis...'
)

for chunk in response:
    print(chunk.text, end='')
```

### Function Calling (for Tool Use)

```python
def get_meeting_notes(meeting_id: str) -> dict:
    """Fetch meeting notes from Notion."""
    # Implementation
    return {"notes": "..."}

# Pass function directly - it will be auto-called
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Get notes from meeting 12345',
    tools=[get_meeting_notes]  # Auto function calling
)
```

### Context Caching (Cost Optimization)

```python
# Cache large context for reuse (up to 90% cost savings)
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Query about the cached content',
    cached_content='large_context_content_id'
)
```

### Best Practices

1. **Use Async for Performance**: The SDK supports async for concurrent requests
2. **Enable Context Caching**: For repeated large prompts (brand guidelines, project context)
3. **Configure Safety Settings**: Set safety thresholds for production
4. **Use Streaming**: For real-time user experience in meeting notes

### Configuration Parameters

```python
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Your prompt',
    config={
        'temperature': 0.7,           # Creativity (0-1)
        'max_output_tokens': 8192,    # Response length
        'top_p': 0.95,                # Nucleus sampling
        'top_k': 40                   # Top-k sampling
    }
)
```

---

## 2. Claude API (Anthropic) - STRATEGIC DELIVERABLES

### Installation

```bash
pip install anthropic>=0.45.0
```

### Environment Variables

```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Basic Usage

```python
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",  # Latest Sonnet 4.5
    max_tokens=4096,
    messages=[
        {"role": "user", "content": "Create a brand strategy for..."}
    ]
)

print(message.content[0].text)
```

### Prompt Caching (90% Cost Savings)

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    system=[
        {
            "type": "text",
            "text": "You are a brand strategist. Here are the brand guidelines: ...",
            "cache_control": {"type": "ephemeral"}  # Cache this content
        }
    ],
    messages=[
        {"role": "user", "content": "Create a tagline"}
    ]
)

# Check cache usage
print(f"Cache creation tokens: {message.usage.cache_creation_input_tokens}")
print(f"Cache read tokens: {message.usage.cache_read_input_tokens}")
```

### Structured Outputs (Beta - November 2025)

```python
from anthropic.types import ResponseFormat

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    messages=[{"role": "user", "content": "Generate brand strategy"}],
    response_format=ResponseFormat(
        type="json_schema",
        json_schema={
            "type": "object",
            "properties": {
                "brand_positioning": {"type": "string"},
                "target_audience": {"type": "string"},
                "color_palette": {"type": "array"}
            }
        }
    )
)
```

### Best Practices

1. **Use Prompt Caching**: For repeated system prompts (brand guidelines, templates)
2. **Monitor Token Usage**: Track cache hits for cost optimization
3. **Structured Outputs**: Use JSON schema for consistent API responses
4. **Model Selection**: Use Sonnet 4.5 for balance, Opus 4.1 for complex reasoning

---

## 3. OpenAI API - INTERNAL COMMUNICATION

### Installation

```bash
pip install openai>=1.0.0
```

### Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Basic Usage

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

completion = client.chat.completions.create(
    model="gpt-4o",  # or "gpt-4.1" for latest
    messages=[
        {"role": "system", "content": "You handle internal team communication."},
        {"role": "user", "content": "Draft a team update about project X"}
    ]
)

print(completion.choices[0].message.content)
```

### Streaming Responses

```python
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Write a team announcement"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
```

### Function Calling (Tool Use)

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "send_google_chat",
            "description": "Send a message to Google Chat",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string"},
                    "message": {"type": "string"}
                },
                "required": ["channel", "message"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Notify the team about the deployment"}],
    tools=tools,
    tool_choice="auto"
)

# Check if function was called
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        # Execute the function
```

### Best Practices

1. **Error Handling**: Catch `RateLimitError`, `APIConnectionError`, `APIStatusError`
2. **Model Selection**: Use `gpt-4o` for cost-effectiveness, `gpt-4.1` for complex tasks
3. **Temperature Control**: Lower (0.3-0.5) for consistent formatting, higher (0.7-0.9) for creativity
4. **Token Management**: Monitor usage with `completion.usage.total_tokens`

---

## 4. Perplexity API - CLIENT COMMUNICATION & RESEARCH

### Installation

```bash
pip install perplexityai
```

### Environment Variables

```bash
PERPLEXITY_API_KEY=your_perplexity_api_key_here
```

### Basic Usage

```python
from perplexity import Perplexity

client = Perplexity(api_key=os.getenv('PERPLEXITY_API_KEY'))

response = client.chat.completions.create(
    model="sonar-pro",
    messages=[
        {"role": "user", "content": "Research latest web design trends for 2025"}
    ]
)

print(response.choices[0].message.content)
```

### OpenAI SDK Compatibility

Since Perplexity is OpenAI-compatible, you can use the OpenAI SDK:

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv('PERPLEXITY_API_KEY'),
    base_url="https://api.perplexity.ai"
)

response = client.chat.completions.create(
    model="sonar-pro",
    messages=[{"role": "user", "content": "Latest AI news"}]
)
```

### Streaming with Citations

```python
stream = client.chat.completions.create(
    model="sonar-pro",
    messages=[{"role": "user", "content": "Research competitor analysis"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
```

### Best Practices

1. **Use for Real-time Data**: Perplexity excels at current information retrieval
2. **Citations**: Leverage built-in citation support for fact-checking
3. **Research Mode**: Use for competitive analysis, trend research, industry updates
4. **OpenAI Migration**: Easy to switch if already using OpenAI SDK

---

## Multi-AI Orchestration Pattern

### Example: Client Onboarding Workflow

```python
import os
from google import genai
from anthropic import Anthropic
from openai import OpenAI
from perplexity import Perplexity

class MWDAssistant:
    def __init__(self):
        self.gemini = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.claude = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.chatgpt = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.perplexity = Perplexity(api_key=os.getenv('PERPLEXITY_API_KEY'))

    def onboard_client(self, intake_data):
        # 1. Gemini orchestrates the workflow
        analysis = self.gemini.models.generate_content(
            model='gemini-2.0-flash',
            contents=f"Analyze this client intake: {intake_data}"
        )

        # 2. Claude generates strategic deliverables
        branding = self.claude.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[{"role": "user", "content": f"Create brand strategy: {intake_data}"}]
        )

        # 3. Perplexity researches industry trends
        research = self.perplexity.chat.completions.create(
            model="sonar-pro",
            messages=[{"role": "user", "content": f"Research trends in {intake_data['industry']}"}]
        )

        # 4. ChatGPT notifies the team
        team_update = self.chatgpt.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": f"Draft team notification for new client"}]
        )

        return {
            'analysis': analysis.text,
            'branding': branding.content[0].text,
            'research': research.choices[0].message.content,
            'team_notification': team_update.choices[0].message.content
        }
```

---

## Error Handling Best Practices

```python
import time
from anthropic import RateLimitError, APIError
from openai import RateLimitError as OpenAIRateLimitError

def call_with_retry(api_call, max_retries=3):
    """Retry API calls with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return api_call()
        except (RateLimitError, OpenAIRateLimitError) as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            print(f"Rate limited. Retrying in {wait_time}s...")
            time.sleep(wait_time)
        except APIError as e:
            print(f"API Error: {e}")
            raise

# Usage
result = call_with_retry(lambda: claude.messages.create(...))
```

---

## Cost Optimization Tips

### 1. Prompt Caching
- **Claude**: Up to 90% savings on repeated prompts
- **Gemini**: Context caching for large documents

### 2. Model Selection
- Use cheaper models (Haiku, GPT-4o-mini) for simple tasks
- Reserve premium models (Opus, GPT-4.1) for complex reasoning

### 3. Token Management
```python
# Track and log token usage
def log_usage(response, model_name):
    if hasattr(response, 'usage'):
        print(f"{model_name} - Input: {response.usage.input_tokens}, Output: {response.usage.output_tokens}")
```

### 4. Batch Processing
- Use async for parallel requests
- Batch similar requests together

---

## Testing Your Integration

```python
# tests/test_ai_apis.py
import pytest
import os

def test_gemini_connection():
    from google import genai
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents='Hello'
    )
    assert response.text is not None

def test_claude_connection():
    from anthropic import Anthropic
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=100,
        messages=[{"role": "user", "content": "Hello"}]
    )
    assert message.content[0].text is not None

def test_openai_connection():
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}]
    )
    assert completion.choices[0].message.content is not None

def test_perplexity_connection():
    from perplexity import Perplexity
    client = Perplexity(api_key=os.getenv('PERPLEXITY_API_KEY'))
    response = client.chat.completions.create(
        model="sonar-pro",
        messages=[{"role": "user", "content": "Hello"}]
    )
    assert response.choices[0].message.content is not None
```

---

## Summary Table

| Feature | Gemini | Claude | OpenAI | Perplexity |
|---------|--------|--------|--------|------------|
| **Package** | `google-genai` | `anthropic` | `openai` | `perplexityai` |
| **Best Model** | Gemini 2.0 Flash | Sonnet 4.5 | GPT-4o/4.1 | Sonar Pro |
| **Context Window** | 1M tokens | 200K tokens | 128K tokens | - |
| **Caching** | ✅ Context caching | ✅ Prompt caching | ❌ | ❌ |
| **Streaming** | ✅ | ✅ | ✅ | ✅ |
| **Function Calling** | ✅ Auto | ✅ Tool use | ✅ | Limited |
| **Real-time Data** | ❌ | ❌ | ❌ | ✅ |
| **Best For** | Workspace mgmt | Strategy docs | Team comms | Research |

---

## Additional Resources

- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Claude API Documentation](https://docs.claude.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Perplexity API Documentation](https://docs.perplexity.ai/)

---

**Last Updated:** November 15, 2025
