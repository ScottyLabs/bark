# Bark 🐕

A modular chatbot for [ScottyLabs](https://scottylabs.org) powered by OpenRouter with Slack integration.

## Features

- **OpenRouter Integration**: Uses Claude 3.5 Sonnet by default, but any OpenRouter model is supported
- **Tool System**: Extensible tool system for adding custom capabilities
- **Slack Integration**: Responds to DMs and @mentions with thread-aware conversations
- **Railway Ready**: Configured for easy deployment to Railway

## Project Structure

```
bark/
├── src/bark/
│   ├── core/           # Core chatbot functionality
│   │   ├── chatbot.py  # Main ChatBot class
│   │   ├── config.py   # Configuration management
│   │   ├── openrouter.py  # OpenRouter API client
│   │   └── tools.py    # Tool system
│   ├── integrations/   # Platform integrations
│   │   └── slack/      # Slack integration
│   ├── cli.py          # CLI interface
│   └── server.py       # FastAPI server
├── Dockerfile
├── railway.toml
└── pyproject.toml
```

## Local Development

### Prerequisites

- Python 3.11+
- [UV](https://docs.astral.sh/uv/) package manager
- OpenRouter API key

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/ScottyLabs/bark.git
   cd bark
   ```

2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` with your credentials:
   ```
   OPENROUTER_API_KEY=your_key_here
   SLACK_BOT_TOKEN=xoxb-your-token
   SLACK_SIGNING_SECRET=your_secret
   ```

4. Install dependencies:
   ```bash
   uv sync
   ```

5. Run the CLI for testing:
   ```bash
   uv run bark
   ```

6. Or start the server:
   ```bash
   uv run bark --serve
   ```

## Slack App Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app

2. Under **OAuth & Permissions**, add these Bot Token Scopes:
   - `app_mentions:read`
   - `chat:write`
   - `im:history`
   - `im:read`
   - `im:write`

3. Install the app to your workspace and copy the **Bot User OAuth Token**

4. Under **Basic Information**, copy the **Signing Secret**

5. Deploy to Railway (see below) to get your public URL

6. Under **Event Subscriptions**:
   - Enable events
   - Set Request URL to `https://your-railway-url.up.railway.app/slack/events`
   - Subscribe to bot events:
     - `app_mention`
     - `message.im`

7. Save changes and reinstall the app if prompted

## Deployment to Railway

1. Install the Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login and link your project:
   ```bash
   railway login
   railway init
   ```

3. Set environment variables:
   ```bash
   railway variables set OPENROUTER_API_KEY=your_key
   railway variables set SLACK_BOT_TOKEN=xoxb-your-token
   railway variables set SLACK_SIGNING_SECRET=your_secret
   ```

4. Deploy:
   ```bash
   railway up
   ```

5. Get your public URL:
   ```bash
   railway domain
   ```

## Adding Custom Tools

Tools extend Bark's capabilities. Here's how to add one:

```python
# src/bark/tools/my_tools.py
from bark.core.tools import tool

@tool(
    name="get_weather",
    description="Get the current weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name, e.g., 'Pittsburgh'"
            }
        },
        "required": ["location"]
    }
)
async def get_weather(location: str) -> str:
    # Your implementation here
    return f"Weather in {location}: Sunny, 72°F"
```

Then import it in your server or CLI to register it:

```python
import bark.tools.my_tools  # This registers the tools
```

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | Required |
| `OPENROUTER_MODEL` | Model to use | `anthropic/claude-3.5-sonnet` |
| `SLACK_BOT_TOKEN` | Slack bot OAuth token | Required for Slack |
| `SLACK_SIGNING_SECRET` | Slack signing secret | Required for Slack |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

## License

MIT
