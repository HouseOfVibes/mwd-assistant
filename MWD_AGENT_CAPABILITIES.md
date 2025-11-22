# MWD Agent Capabilities

A comprehensive list of everything the MWD Agent can do.

## AI Models Integrated

| Model | Purpose |
|-------|---------|
| **Claude Sonnet 4.5** | Strategic deliverables (branding, website, social, copywriting) |
| **Gemini 2.0 Flash** | Primary orchestrator, meeting notes, summarization |
| **GPT-4o/GPT-4.1** | Internal team communication, Slack drafts, feedback analysis |
| **Perplexity Sonar Pro** | Research, competitor analysis, client emails, market data |

---

## Strategy Generation (Claude)

- **Brand Strategy** - positioning, audience, personality, colors, typography, messaging
- **Website Design Strategy** - sitemap, page layouts, CTAs, user journeys
- **Social Media Strategy** - platform recommendations, content pillars, posting frequency, hashtags
- **Copywriting** - taglines, about sections, value propositions, email sequences

---

## Gemini AI Capabilities

- **Meeting Notes** - summaries, action items, decisions, follow-ups
- **Document Summarization** - general, contracts, proposals, reports
- **Multi-AI Orchestration** - routes tasks to appropriate AI models

---

## OpenAI Capabilities

- **Team Messages** - updates, requests, announcements, feedback
- **Slack Messages** - channel-specific drafts with proper formatting
- **Thread Summarization** - key decisions, action items, unresolved questions
- **Feedback Analysis** - sentiment, themes, concerns, priority assessment

---

## Perplexity Capabilities

- **General Research** - with sources and citations
- **Industry Research** - market trends, players, opportunities
- **Competitive Analysis** - positioning, pricing, gaps, differentiation
- **Client Emails** - updates, proposals, follow-ups, introductions
- **Market Data** - statistics, forecasts, regional breakdowns

---

## Platform Integrations

### Slack Bot
- Conversational interface with Gemini orchestration
- Direct messages and @mentions
- Thread-aware context
- Emoji status reactions
- Conversation persistence
- **Deadline Reminders** - Automated daily reminders for upcoming deadlines (9 AM)
- **Activity Digests** - Daily (6 PM) and weekly (Friday 5 PM) summaries
- **Quick Action Buttons** - Interactive menus for common tasks
- **File Upload Handling** - Process documents, images, spreadsheets with suggested actions

### Notion
- Create/manage project pages
- Create meeting notes with action items
- Search workspace
- Query databases with filters
- Update project status

### Google Workspace
- **Drive** - create folders, organize projects, share files
- **Docs** - create documents, formatted deliverables
- Standard project folder structure (Strategy, Design, Content, Assets, Deliverables, Client_Feedback)

### Supabase
- Conversation storage
- Project data management
- Usage tracking

### Invoice System
- Receive client intake forms
- Create leads with AI assessment scores
- Attach AI-generated deliverables
- Receive status updates (contract_signed, payment_received, milestone_completed, project_completed)

---

## MCP Servers (7 available)

1. **Memory MCP** - Long-term memory across AI sessions
2. **Git MCP** - Repository management
3. **Supabase MCP** - Database integration
4. **Filesystem MCP** - Secure file operations
5. **GitHub MCP** - Repository and issue management
6. **PostgreSQL MCP** - Natural language database queries
7. **Sequential Thinking MCP** - Enhanced reasoning

---

## Automated Workflows

### Client Intake Webhook
1. Receives intake form
2. Auto-generates 4 deliverables (branding, website, social, copy)
3. Calculates complexity score and recommended package
4. Creates lead in Invoice System
5. Attaches all deliverables

### Project Status Webhook
- `contract_signed` → project kickoff initialized
- `payment_received` → payment confirmed
- `milestone_completed` → milestone acknowledged
- `project_completed` → project archived

---

## API Endpoints (35+)

| Category | Count | Endpoints |
|----------|-------|-----------|
| Strategy | 4 | `/branding`, `/website`, `/social`, `/copywriting` |
| Gemini | 3 | `/ai/gemini/meeting-notes`, `/summarize`, `/orchestrate` |
| OpenAI | 4 | `/ai/openai/team-message`, `/slack-message`, `/summarize-thread`, `/analyze-feedback` |
| Perplexity | 5 | `/ai/perplexity/research`, `/industry`, `/competitors`, `/client-email`, `/market-data` |
| Notion | 5 | `/notion/project`, `/meeting-notes`, `/search`, `/database/query`, `/page/status` |
| Google | 6 | `/google/drive/folder`, `/project-structure`, `/files`, `/share`, `/docs/document`, `/deliverable` |
| Slack | 5 | `/slack/events`, `/slack/interact`, `/slack/reminders`, `/slack/digest`, `/slack/quick-actions` |
| Webhooks | 2 | `/api/intake`, `/api/project/status` |

---

## Security Features

- HMAC-SHA256 webhook verification
- Slack request signature verification
- Bearer token authentication
- Environment variable credential storage
- Bot loop prevention

---

## Summary

The MWD Agent is a **multi-AI orchestration platform** that can:
- Generate strategic deliverables for client projects
- Research topics, industries, and competitors
- Draft communications for teams and clients
- Create meeting notes and document summaries
- Manage projects in Notion and Google Workspace
- Provide conversational AI assistance via Slack
- Automate client onboarding workflows
- Coordinate multiple AI models for complex tasks
- **Send automated deadline reminders** (daily at 9 AM)
- **Generate activity digests** (daily and weekly)
- **Provide quick action buttons** for common tasks
- **Process file uploads** with intelligent suggestions
