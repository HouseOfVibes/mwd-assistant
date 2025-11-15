# MCP (Model Context Protocol) Setup Guide

## Overview

The MWD Agent uses MCP servers to enable multi-AI coordination and workspace integration. MCP provides a standardized way for AI models to access tools, data, and functionality.

## Architecture

```
┌─────────────────────────────────────────┐
│  AI Models (Gemini, Claude, GPT, etc)   │
└──────────────┬──────────────────────────┘
               │
        ┌──────▼──────┐
        │ MCP Protocol │
        └──────┬──────┘
               │
    ┌──────────┼───────────┐
    │          │           │
┌───▼───┐  ┌──▼──┐  ┌────▼─────┐
│Memory │  │ Git  │  │Supabase │
│Server │  │Server│  │ Server  │
└───────┘  └──────┘  └──────────┘
```

## Installed MCP Servers

### Python-based Servers (via pip/uvx)

1. **Memory MCP** (`memory-mcp`)
   - **Purpose**: Long-term memory storage for multi-AI coordination
   - **Use Cases**:
     - Store client context across AI sessions
     - Project history and status tracking
     - Brand guidelines and templates
     - Shared knowledge base for all AIs
   - **Command**: `uvx memory-mcp`

2. **Supabase MCP** (`supabase-mcp-server`)
   - **Purpose**: Direct Supabase database integration
   - **Use Cases**:
     - Client intake data storage
     - Project milestones tracking
     - Meeting notes and action items
     - Integration with MWD Invoice System
   - **Command**: `uvx supabase-mcp-server`
   - **Env Vars**: `SUPABASE_URL`, `SUPABASE_KEY`

3. **Git MCP** (`mcp-server-git`)
   - **Purpose**: Git repository management
   - **Use Cases**:
     - Repository inspection and search
     - Commit history analysis
     - Branch management
     - Code review assistance
   - **Command**: `uvx mcp-server-git --repository /path/to/repo`

### TypeScript-based Servers (via npx)

4. **Filesystem MCP** (`@modelcontextprotocol/server-filesystem`)
   - **Purpose**: Secure file operations
   - **Use Cases**:
     - Template management
     - Brand asset organization
     - Deliverable file generation
   - **Command**: `npx -y @modelcontextprotocol/server-filesystem /allowed/path`

5. **GitHub MCP** (`@modelcontextprotocol/server-github`)
   - **Purpose**: GitHub API integration
   - **Use Cases**:
     - Issue tracking
     - Pull request management
     - Repository insights
     - Workflow automation
   - **Command**: `npx -y @modelcontextprotocol/server-github`
   - **Env Vars**: `GITHUB_PERSONAL_ACCESS_TOKEN`

6. **PostgreSQL MCP** (`@modelcontextprotocol/server-postgres`)
   - **Purpose**: PostgreSQL database queries
   - **Use Cases**:
     - Natural language database queries
     - Schema inspection
     - Data analysis
   - **Command**: `npx -y @modelcontextprotocol/server-postgres postgresql://connection-string`

7. **Sequential Thinking MCP** (`@modelcontextprotocol/server-sequential-thinking`)
   - **Purpose**: Enhanced reasoning for complex tasks
   - **Use Cases**:
     - Multi-step workflow planning
     - Task routing decisions
     - Complex logic decomposition
   - **Command**: `npx -y @modelcontextprotocol/server-sequential-thinking`

## Installation

### Python Packages

Already added to `requirements.txt`:

```bash
pip install "mcp[cli]>=1.21.0"
pip install mcp-server-git
pip install supabase-mcp-server
pip install memory-mcp
```

Or install all at once:

```bash
pip install -r requirements.txt
```

### TypeScript Packages

No installation needed! TypeScript MCP servers run directly via `npx`:

```bash
# Filesystem server
npx -y @modelcontextprotocol/server-filesystem /path/to/files

# GitHub server
npx -y @modelcontextprotocol/server-github

# PostgreSQL server
npx -y @modelcontextprotocol/server-postgres postgresql://url

# Sequential thinking server
npx -y @modelcontextprotocol/server-sequential-thinking
```

## Configuration

### Claude Desktop

Copy `.claude/mcp.json` to your Claude Desktop configuration directory:

**macOS:**
```bash
cp .claude/mcp.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Linux:**
```bash
cp .claude/mcp.json ~/.config/Claude/claude_desktop_config.json
```

**Windows:**
```powershell
copy .claude\mcp.json %APPDATA%\Claude\claude_desktop_config.json
```

### Claude Code (VS Code Extension)

The `.claude/mcp.json` file is automatically detected when opening this repository in VS Code with the Claude Code extension.

### Environment Variables

Update your `.env` file with required credentials:

```bash
# Supabase
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# GitHub (optional)
GITHUB_TOKEN=your_github_token_here
```

## Usage Examples

### Memory Server - Multi-AI Context Sharing

```python
from mcp import Client

# AI 1 (Gemini) stores meeting notes
client.call_tool("save_memory", {
    "key": "project_techflow_meeting_notes",
    "value": "Client wants modern, tech-forward brand..."
})

# AI 2 (Claude) retrieves context for branding
memories = client.call_tool("search_memories", {
    "query": "TechFlow brand requirements"
})
```

### Supabase Server - Project Data

```python
# Store client intake data
client.call_tool("execute_query", {
    "query": "INSERT INTO clients (name, industry, project_type) VALUES ($1, $2, $3)",
    "params": ["TechFlow Solutions", "B2B SaaS", "Full Branding + Website"]
})

# Query project status
results = client.call_tool("execute_query", {
    "query": "SELECT * FROM projects WHERE status = 'in_progress'"
})
```

### Git Server - Repository Analysis

```python
# Search for branding code
results = client.call_tool("search_repository", {
    "pattern": "BRANDING_PROMPT",
    "path": "main.py"
})

# Get recent commits
commits = client.call_tool("get_commit_history", {
    "limit": 10
})
```

## Integration with MWD Agent

### Multi-AI Workflow Example

```python
# main.py enhancement

from mcp import Client

class MWDAgentOrchestrator:
    def __init__(self):
        self.memory = Client("memory")
        self.supabase = Client("supabase")
        self.git = Client("git")

    async def onboard_client(self, intake_data):
        # 1. Store client data in Supabase
        await self.supabase.call_tool("execute_query", {
            "query": "INSERT INTO clients (...) VALUES (...)",
            "params": [intake_data]
        })

        # 2. Save context to memory for all AIs
        await self.memory.call_tool("save_memory", {
            "key": f"client_{intake_data['name']}_context",
            "value": intake_data
        })

        # 3. Gemini analyzes and creates Notion page
        gemini_analysis = await gemini_client.generate(...)

        # 4. Claude generates brand strategy using shared memory
        brand_strategy = await claude_client.generate(...)

        # 5. Store deliverables in Supabase
        await self.supabase.call_tool("execute_query", {
            "query": "INSERT INTO deliverables (...)",
            "params": [brand_strategy]
        })

        return {
            "analysis": gemini_analysis,
            "branding": brand_strategy
        }
```

## Testing MCP Servers

### Test Memory Server

```bash
# Start memory server
uvx memory-mcp

# In another terminal, test with MCP inspector
npx @modelcontextprotocol/inspector memory-mcp
```

### Test Supabase Server

```bash
# Set environment variables
export SUPABASE_URL="your_url"
export SUPABASE_KEY="your_key"

# Start server
uvx supabase-mcp-server

# Test connection
curl http://localhost:3000/health
```

### Test Git Server

```bash
# Start git server for this repository
uvx mcp-server-git --repository /home/user/mwd-agent

# Verify repository access
# Server should respond to MCP protocol messages
```

## Troubleshooting

### Python Package Issues

```bash
# Clear pip cache
pip cache purge

# Reinstall MCP packages
pip uninstall mcp mcp-server-git supabase-mcp-server memory-mcp
pip install -r requirements.txt
```

### TypeScript Server Issues

```bash
# Clear npm cache
npm cache clean --force

# Test npx directly
npx -y @modelcontextprotocol/server-filesystem --help
```

### Environment Variables Not Loading

```bash
# Verify .env file exists
cat .env

# Load manually for testing
export $(cat .env | xargs)
```

## Security Best Practices

1. **Never commit `.env` files** - Already in `.gitignore`
2. **Use read-only mode** for production Supabase connections
3. **Limit filesystem access** to specific directories
4. **Rotate API keys regularly**
5. **Use environment-specific configurations** (dev/staging/prod)

## Performance Optimization

### Memory Server Caching

Configure memory TTL for frequently accessed data:

```python
client.call_tool("save_memory", {
    "key": "brand_guidelines_techflow",
    "value": guidelines,
    "ttl": 3600  # 1 hour cache
})
```

### Supabase Connection Pooling

Use connection pooling for high-volume queries:

```python
# Configure in Supabase dashboard
# Connection pooling: Mode = Transaction
# Pool size: 15-20 for production
```

## Next Steps

1. **Configure Environment Variables** - Update `.env` with actual credentials
2. **Test Individual Servers** - Verify each MCP server works independently
3. **Integrate with Flask App** - Add MCP client to `main.py`
4. **Build Multi-AI Orchestrator** - Implement workflow coordination
5. **Deploy with Railway** - Add MCP servers to production deployment

## Resources

- [Official MCP Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers)
- [Supabase MCP Guide](https://supabase.com/docs/guides/getting-started/mcp)
- [Claude MCP Integration](https://docs.anthropic.com/en/docs/claude-code/mcp)

## Support

For issues or questions:
- GitHub Issues: https://github.com/HouseOfVibes/mwd-agent/issues
- MCP Discord: https://discord.gg/modelcontextprotocol
- Anthropic Support: https://support.anthropic.com

---

**Last Updated:** November 15, 2025
**MCP SDK Version:** 1.21.0
**Compatibility:** Python 3.10+, Node.js 18+
