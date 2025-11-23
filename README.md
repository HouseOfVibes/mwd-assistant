# MWD Assistant

> AI-Powered Internal Assistant for MW Design Studio

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.1.2-green.svg)](https://flask.palletsprojects.com/)
[![MCP](https://img.shields.io/badge/MCP-1.21.1-purple.svg)](https://modelcontextprotocol.io/)

Your team's intelligent assistant for managing clients, projects, and creative workflows. Chat naturally about branding, website design, social media strategy, copywriting, and workspace management. Integrates with Notion, Google Workspace, Slack, and the MWD Invoice System.

## ✨ What's New (November 2025)

- **🔌 MCP Integration**: Model Context Protocol for standardized multi-AI coordination
- **📦 Latest Dependencies**: All packages updated to November 2025 versions
  - Claude Sonnet 4.5 (anthropic 0.73.0)
  - Gemini 2.0 Flash (google-genai 1.50.0)
  - GPT-5.1 (openai 2.8.0)
  - MCP SDK 1.21.0
- **🧠 Persistent Memory**: Long-term memory storage across AI sessions
- **🔧 7 MCP Servers**: Memory, Git, Supabase, Filesystem, GitHub, PostgreSQL, Sequential Thinking
- **📖 Enhanced Documentation**: 400+ lines of MCP setup guides

## 🎯 Features

- **AI-Powered Strategy Generation**: Branding, website design, social media, and copywriting deliverables
- **Workspace Intelligence**: Gemini-powered meeting notes, Notion sync, and Google Drive organization
- **Multi-AI Orchestration**: Specialized AI routing (Gemini, Claude, ChatGPT, Perplexity)
- **MCP Integration**: Model Context Protocol for standardized AI tool access and multi-agent coordination
- **Persistent Memory**: Long-term memory storage across AI sessions for consistent client context
- **Invoice System Integration**: Automated lead creation, proposal generation, and client portal sync
- **Communication Hub**: Google Chat (internal) and Slack (client) integration
- **Project Management**: Automated Notion workspace updates and timeline tracking

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│           GEMINI (PRIMARY AI - CORE SYSTEM)             │
│  • Notion Workspace Understanding & Sync                │
│  • Google Meet → Automatic Meeting Notes                │
│  • Google Drive → File Organization & Management        │
│  • Action Item Extraction & Tracking                    │
└─────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        ┌───────▼─────────┐    ┌───────▼─────────┐
        │     CLAUDE      │    │   CHATGPT +     │
        │   Strategic     │    │   PERPLEXITY    │
        │  Deliverables   │    │  Communication  │
        └─────────────────┘    └─────────────────┘
                │                       │
                └───────────┬───────────┘
                            │
              ┌─────────────▼──────────────┐
              │   MCP (Model Context       │
              │   Protocol) Servers        │
              │  ┌──────────────────────┐  │
              │  │ • Memory (shared)    │  │
              │  │ • Supabase (data)    │  │
              │  │ • Git (repository)   │  │
              │  │ • Filesystem (files) │  │
              │  └──────────────────────┘  │
              └────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+ (tested on 3.11.14)
- Node.js 18+ (for TypeScript MCP servers)
- Anthropic API key (Claude)
- Google Cloud project (for Gemini API)
- Optional: OpenAI API key, Perplexity API key
- Optional: Supabase account, Slack workspace, Notion workspace

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/HouseOfVibes/mwd-agent.git
   cd mwd-agent
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the assistant**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8080`

## 🔑 Environment Variables

Create a `.env` file with the following:

```bash
# AI APIs - Required
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Integration APIs - Optional
NOTION_API_KEY=your_notion_api_key_here
SLACK_TOKEN=your_slack_token_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# Google Cloud (Optional - for Vertex AI)
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1

# MCP (Model Context Protocol) Servers - Optional
GITHUB_TOKEN=your_github_personal_access_token_here
```

### AI SDK Versions (Latest November 2025)

| Package | Version | Model | Status |
|---------|---------|-------|--------|
| **anthropic** | >=0.73.0 | Claude Sonnet 4.5 | ✅ Active |
| **google-genai** | >=1.50.0 | Gemini 2.0 Flash | ✅ Active |
| **openai** | >=2.8.0 | GPT-5.1 | ✅ Active |
| **perplexityai** | >=0.20.0 | Sonar Pro | ✅ Active |
| **mcp** | >=1.21.0 | MCP Protocol | ✅ Active |

⚠️ **Important**: `google-generativeai` is **DEPRECATED** (support ends Nov 30, 2025). Use `google-genai` instead.

See [docs/API_INTEGRATION_GUIDE.md](docs/API_INTEGRATION_GUIDE.md) for detailed integration instructions and [.claude/MCP_SETUP.md](.claude/MCP_SETUP.md) for MCP configuration.

## 📡 API Endpoints

### Current Endpoints (MVP)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check and service status |
| POST | `/branding` | Generate comprehensive branding strategy |
| POST | `/website` | Create website design plan and sitemap |
| POST | `/social` | Generate social media strategy |
| POST | `/copywriting` | Create marketing copy and messaging |

### Planned Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/gemini/meeting-notes` | Process Google Meet transcripts |
| POST | `/notion/sync` | Sync project to Notion workspace |
| POST | `/google/drive/organize` | Organize client folders in Drive |
| POST | `/gmail/draft` | Draft email communications |
| POST | `/slack/notify` | Send Slack notifications |
| POST | `/invoice/create-lead` | Create lead in invoice system |

## 🧪 Testing

Run the test suite:

```bash
# Start the main server in one terminal
python main.py

# In another terminal, run tests
python test_agent.py
```

## 📦 Project Structure

```
mwd-agent/
├── .claude/
│   ├── mcp.json         # MCP server configuration
│   └── MCP_SETUP.md     # MCP setup and usage guide
├── docs/
│   ├── API_INTEGRATION_GUIDE.md  # AI API integration guide
│   └── conversation-history/      # Planning screenshots
├── main.py              # Flask application entry point
├── test_agent.py        # Test suite
├── requirements.txt     # Python dependencies (all latest versions)
├── .env.example         # Environment template (updated for MCP)
├── .gitignore          # Git ignore rules
├── railway.toml        # Railway deployment config
├── PROJECT_PLAN.md     # Comprehensive 7-sprint project plan
└── README.md           # This file
```

## 🔄 Example Workflow: New Client Onboarding

```
1. Client fills intake form → Webhook triggers
2. Gemini receives data → Creates lead in Invoice System
3. Gemini routes to specialized AIs:
   • Claude generates branding strategy
   • Claude creates website plan
   • Claude develops social media strategy
   • Claude writes initial copy
4. Gemini orchestrates outputs:
   • Creates Notion project page
   • Organizes Google Drive folder
   • Links to Invoice System proposal
5. ChatGPT notifies team via Google Chat
6. Perplexity sends welcome to client via Slack
7. Gemini triggers invoice creation
```

## 🔌 MCP (Model Context Protocol) Integration

The MWD Assistant uses MCP to enable standardized multi-AI coordination and tool access.

### Available MCP Servers

**Python-based (installed via pip):**
- **Memory MCP** - Long-term memory storage for shared AI context
- **Git MCP** - Repository management and code analysis
- **Memory MCP** - Persistent storage for client context and project history

**TypeScript-based (via npx - no installation needed):**
- **Filesystem MCP** - Secure file operations for templates and assets
- **GitHub MCP** - Repository and issue management
- **PostgreSQL MCP** - Natural language database queries
- **Supabase MCP** - Supabase database integration
- **Sequential Thinking MCP** - Enhanced reasoning for complex workflows

### Configuration

MCP servers are configured in `.claude/mcp.json`. To use with Claude Desktop or VS Code:

```bash
# Claude Desktop (macOS)
cp .claude/mcp.json ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Claude Desktop (Linux)
cp .claude/mcp.json ~/.config/Claude/claude_desktop_config.json

# Claude Code (VS Code) - automatically detected in .claude/
```

### Usage Example

```python
from mcp import Client

# Connect to memory server for multi-AI coordination
memory_client = Client("memory")

# AI 1 (Gemini) stores meeting notes
await memory_client.call_tool("save_memory", {
    "key": "project_techflow_context",
    "value": "Client wants modern, tech-forward brand..."
})

# AI 2 (Claude) retrieves context for branding strategy
context = await memory_client.call_tool("search_memories", {
    "query": "TechFlow brand requirements"
})
```

See [.claude/MCP_SETUP.md](.claude/MCP_SETUP.md) for comprehensive setup instructions and integration patterns.

## 🌐 Deployment

### Deploy to Railway (Recommended)

1. **Install Railway CLI**
   ```bash
   npm i -g @railway/cli
   ```

2. **Login and initialize**
   ```bash
   railway login
   railway init
   ```

3. **Set environment variables**
   ```bash
   railway variables set ANTHROPIC_API_KEY=your_key_here
   railway variables set GEMINI_API_KEY=your_key_here
   ```

4. **Deploy**
   ```bash
   railway up
   ```

See [PROJECT_PLAN.md](PROJECT_PLAN.md#deployment-strategy-railway) for detailed deployment instructions.

## 🔗 Integration with MWD Invoice System

This agent integrates with the [MWD Invoice System](https://github.com/HouseOfVibes/mwd-invoice-system) to provide:

- Automatic lead creation from intake forms
- Project lifecycle synchronization
- Automated invoicing on deliverable completion
- Client portal integration for proposals and files

## 🗺️ Roadmap

### ✅ Phase 1: MVP (Complete)
- [x] Basic Flask API with 4 strategy endpoints
- [x] Claude AI integration (Sonnet 4.5)
- [x] Test suite
- [x] Latest dependencies (Nov 2025 versions)
- [x] MCP (Model Context Protocol) integration
- [x] Memory, Git, and Filesystem MCP servers
- [x] Comprehensive documentation

### 🔄 Phase 2: Workspace Integration (In Progress)
- [x] MCP infrastructure for multi-AI coordination
- [x] Persistent memory storage
- [ ] Gemini API integration for meeting notes
- [ ] OpenAI API integration for team communication
- [ ] Perplexity API integration for client communication
- [ ] Notion API for project management
- [ ] Google Workspace APIs (Drive, Docs, Gmail)
- [ ] Invoice System webhooks

### 📅 Phase 3: Advanced Intelligence (Planned)
- [ ] Multi-AI orchestration implementation
- [ ] Slack and Google Chat integration
- [ ] Agent specialization and learning
- [ ] Analytics and reporting dashboard
- [ ] Advanced MCP server integrations (GitHub, PostgreSQL)

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the complete 7-sprint development roadmap.

## 💰 Cost Estimates

### AI API Costs (Monthly)
- Gemini API: $0-100 (primary workspace management)
- Claude API: $30-100 (strategic deliverables)
- ChatGPT API: $20-50 (internal communication)
- Perplexity API: $20-50 (client communication)

**Total: $70-300/month**

### Infrastructure
- Railway hosting: $5-20/month
- Supabase database: $0-25/month (free tier available)
- Node.js runtime: $0 (for TypeScript MCP servers via npx)

**Total Infrastructure + AI: $75-345/month**

## 📚 Documentation

- **[PROJECT_PLAN.md](PROJECT_PLAN.md)** - Comprehensive 7-sprint project plan with architecture and roadmap (~830 lines)
- **[docs/API_INTEGRATION_GUIDE.md](docs/API_INTEGRATION_GUIDE.md)** - Complete guide for all AI API integrations with latest 2025 best practices (~560 lines)
- **[.claude/MCP_SETUP.md](.claude/MCP_SETUP.md)** - MCP server setup, configuration, and usage guide (~400 lines)
- **[.claude/mcp.json](.claude/mcp.json)** - MCP server configuration for Claude Desktop/Code
- **[docs/conversation-history/](docs/conversation-history/)** - Design conversation screenshots
- **API Reference** (coming soon)
- **Notion Integration Guide** (coming soon)

## 🤝 Contributing

This is a private project for MW Design Studio. For questions or suggestions, please open an issue.

## 📄 License

MIT License - see LICENSE file for details

## 🔒 Security

- Never commit `.env` files or API keys
- All credentials stored in environment variables
- HTTPS required for production deployments
- Regular security audits planned

## 👥 Team

- **MW Design Studio** - Design and business operations
- **AI Integration** - Gemini (Google), Claude (Anthropic), ChatGPT (OpenAI), Perplexity

## 📞 Support

For issues related to:
- **Assistant functionality**: Open a GitHub issue
- **Invoice System**: See [mwd-invoice-system](https://github.com/HouseOfVibes/mwd-invoice-system)
- **Business inquiries**: Contact MW Design Studio

---

**Built with ❤️ for MW Design Studio**

*Automating workflows, amplifying creativity*
