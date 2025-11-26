# MWD Assistant - Project Plan
**MW Design Studio AI Agent**

**Version:** 1.0
**Date:** November 15, 2025
**Repository:** https://github.com/HouseOfVibes/mwd-assistant

---

## Executive Summary

The MWD Assistant is an intelligent AI-powered assistant designed to streamline MW Design Studio's business operations across multiple domains: branding, website design, social media strategy, copywriting, client communication, and workspace management.

### Vision
Create a centralized AI agent that integrates with the existing workspace tools (Notion, Slack, Gemini, ChatGPT, Perplexity) to automate workflows, enhance productivity, and deliver consistent, high-quality output for client projects.

### Current Status
- **Phase:** Early Development (MVP)
- **Local Implementation:** Basic Flask API with 4 endpoints (branding, website, social media, copywriting) using Claude
- **Primary AI:** Gemini (for workspace management) - Integration planned
- **Current AI:** Claude 3.5 Haiku (temporary for MVP strategy endpoints)
- **Documentation:** Conversation history and planning screenshots in GitHub repo

---

## Project Objectives

### Primary Goals
1. **Workflow Automation** - Reduce manual repetitive tasks across client projects
2. **Consistency** - Standardize deliverables with branded templates and tone
3. **Integration** - Connect all workspace tools into a unified system
4. **Intelligence** - Leverage multiple AI models (Claude, ChatGPT, Perplexity) for optimal results
5. **Scalability** - Build a system that grows with the business

### Success Metrics
- 50% reduction in time spent on initial client deliverables
- 100% of projects documented in Notion workspace
- Automated meeting notes and follow-ups
- Consistent brand voice across all client communications
- Real-time project status tracking via Slack

---

## System Architecture

### AI Hierarchy & Specialization

```
MWD WORKSPACE MANAGEMENT SYSTEM

┌─────────────────────────────────────────────────────────┐
│           GEMINI (PRIMARY AI - CORE SYSTEM)             │
│  ┌───────────────────────────────────────────────────┐  │
│  │ • Notion Workspace Understanding & Sync           │  │
│  │ • Google Meet → Automatic Meeting Notes           │  │
│  │ • In-Person Notes Management (via Notion)         │  │
│  │ • Action Item Extraction & Tracking               │  │
│  │ • Project Timeline Updates                        │  │
│  │ • Workspace Intelligence & Context Awareness      │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        ┌───────▼─────────┐    ┌───────▼─────────┐
        │  SPECIALIZED    │    │   SPECIALIZED   │
        │  AI WORKERS     │    │   AI WORKERS    │
        └─────────────────┘    └─────────────────┘
                │                       │
    ┌───────────┼──────────┐   ┌───────┼────────┐
    │           │          │   │       │        │
┌───▼───┐  ┌───▼───┐  ┌───▼───▼┐  ┌───▼────┐   │
│CLAUDE │  │CHATGPT│  │PERPLEXI│  │ FUTURE │   │
│       │  │       │  │   TY   │  │  AIs   │   │
└───┬───┘  └───┬───┘  └───┬────┘  └────────┘   │
    │          │          │                     │
    │          │          │                     │
Strategic  Internal   Client Slack        Additional
Deliverables: Team     Communication      Specialized
• Branding   Google                       Agents
• Website    Chat
• Social
• Copy
```

### Communication Channel Mapping
- **Google Chat (ChatGPT)**: Internal team communication and announcements
- **Slack (Perplexity)**: Client-facing communications
- **Notion (Gemini)**: Workspace management and in-person notes
- **Google Meet (Gemini)**: Automatic meeting transcription

### Core Components

#### 1. AI Agent Layer
- **Primary AI:** Gemini (Google) - Main workspace management, meeting notes, Notion integration
- **Architecture AI:** Claude (Anthropic) - Current MVP implementation for branding/website/social/copywriting strategy
- **Internal Comms AI:** ChatGPT (planned) - Google Chat integration for team communication
- **Client Comms AI:** Perplexity (planned) - Slack integration for client communication
- **Framework:** Flask REST API (Python)

#### 2. Integration Layer (Planned)
- **MWD Invoice System** - Client lifecycle management, invoicing, contracts, CRM, lead tracking (https://github.com/HouseOfVibes/mwd-invoice-system)
- **Notion API** - Workspace management, project tracking, knowledge base
- **Google Workspace APIs:**
  - Google Docs - Document creation and collaboration
  - Gmail - Email communication
  - Google Meet + Gemini - Automated meeting transcription, note-taking, and action item extraction
- **Slack API** - Team communication and notifications
- **Supabase** - Data persistence and project history

#### 3. Workflow Orchestration
- Multi-agent coordination
- Task routing based on request type
- Context management across conversations
- Template and brand asset storage

---

## Feature Breakdown

### Phase 1: Core AI Capabilities (Current - MVP with Claude)

**Note:** These endpoints currently use Claude as a temporary solution. The final architecture will integrate Gemini as the primary AI with specialized routing.

#### Implemented Features (Using Claude - MVP)
✅ **Branding Strategy Endpoint** (`POST /branding`)
- Brand positioning statements
- Target audience definition
- Brand personality traits
- Color palette suggestions
- Typography recommendations
- Key messaging points

✅ **Website Design Endpoint** (`POST /website`)
- Sitemap generation
- Homepage layout descriptions
- Key page descriptions
- Call-to-action strategy
- User journey mapping

✅ **Social Media Strategy Endpoint** (`POST /social`)
- Platform recommendations
- Content pillars (3-5 themes)
- Posting frequency recommendations
- Sample post ideas
- Hashtag strategy

✅ **Copywriting Endpoint** (`POST /copywriting`)
- Tagline variations
- About section copy
- Value proposition statements
- Service/product descriptions
- Email welcome sequences

#### Planned: Gemini Core Integration (Priority)
🔲 **Gemini Workspace Management** - PRIMARY SYSTEM
- Notion workspace understanding and sync
- Google Meet automatic meeting notes
- In-person notes management via Notion
- Action item extraction and tracking
- Project timeline updates
- Workspace intelligence and context awareness

### Phase 2: Workspace Integration (Next Priority)

#### MWD Invoice System Integration
- **Automatic Lead Creation**
  - Agent receives client intake form data
  - Creates lead in invoice system CRM via webhook
  - Populates client database automatically

- **Project Lifecycle Sync**
  - Agent-generated deliverables (branding, website plans) → Invoice system proposals
  - Project status updates between systems
  - Contract generation triggers from project milestones

- **Invoice Automation**
  - Agent triggers invoice creation upon deliverable completion
  - Payment tracking and status updates
  - Revenue analytics integration

- **Client Portal Integration**
  - Agent-generated content visible in client portal
  - Proposal PDFs auto-populated

#### Notion Integration
- **Project Database Sync**
  - Auto-create project entries from client intake
  - Update project status and deliverables
  - Link all project assets and documents

- **Meeting Notes Integration**
  - Capture Google Meet notes via Gemini
  - Auto-save to Notion project pages
  - Extract action items and deadlines

- **Knowledge Base**
  - Store brand guidelines per client
  - Template library for recurring deliverables
  - Case study repository

#### Google Workspace Integration
- **Gmail**
  - Draft client communications
  - Auto-respond to common inquiries
  - Schedule follow-ups

- **Google Docs**
  - Generate proposal documents
  - Create client presentation decks
  - Collaborative editing workflows

#### Slack Integration
- **Client Communication Channel**
  - Route client messages to appropriate team members
  - Send project updates and milestones
  - Share deliverables for review

- **Internal Workflows**
  - Trigger agent workflows via Slack commands
  - Receive notifications on project progress
  - Team collaboration on agent outputs

### Phase 3: Advanced Intelligence (Future)

#### Multi-AI Orchestration (Specialized Roles)
- **Gemini (PRIMARY)** - Workspace intelligence, meeting transcription, note-taking, action item extraction, Notion workspace understanding
- **Claude** - Strategic deliverables (branding, website design, UX/UI reasoning) - technical architecture planning
- **ChatGPT** - Internal team communication via Google Chat, announcements, conversational content
- **Perplexity** - Client communication via Slack, external messaging, industry research

#### Agent Specialization
- **Brand Strategist Agent** - Deep brand development
- **Content Writer Agent** - Blog posts, long-form content
- **Social Media Manager Agent** - Post scheduling, engagement tracking
- **Research Analyst Agent** - Market research, competitive intelligence
- **Project Manager Agent** - Timeline tracking, resource allocation

#### Learning & Personalization
- Client preference learning
- Brand voice adaptation per client
- Success pattern recognition
- Template improvement based on feedback

---

## Technical Implementation

### Current Stack
```
Backend:        Python 3.13 + Flask
AI Provider:    Anthropic Claude (claude-3-5-haiku-20241022)
Environment:    dotenv for configuration
Dependencies:   anthropic, flask, python-dotenv, requests
```

### Planned Stack Additions
```
Database:       Supabase (PostgreSQL) - shared with Invoice System
Integrations:   Notion API, Google APIs, Slack SDK, MWD Invoice System API
Message Queue:  Celery (for async workflows)
Caching:        Redis (for API rate limiting)
Monitoring:     Sentry (error tracking)
Deployment:     Railway (recommended for easy integration with existing Invoice System)
AI APIs:        Gemini API, Claude API, ChatGPT API, Perplexity API
```

### API Structure

#### Current Endpoints
```
GET  /              - Health check and config status
POST /branding      - Generate branding strategy
POST /website       - Generate website design plan
POST /social        - Generate social media strategy
POST /copywriting   - Generate marketing copy
```

#### Planned Endpoints
```
POST /notion/sync           - Sync project to Notion
POST /notion/meeting-notes  - Save meeting notes
POST /google/drive/organize - Organize client folders
POST /google/docs/create    - Create documents
POST /gmail/draft           - Draft emails
POST /gemini/meeting-notes  - Process Google Meet transcripts
POST /slack/notify          - Send Slack notifications
POST /research              - Run Perplexity research
POST /multi-agent           - Orchestrate multiple AI models
```

---

## Workflow Examples

### Workflow 1: New Client Onboarding (Full Integration)
```
1. Client fills intake form → Webhook to Agent + Invoice System
2. Gemini (PRIMARY) receives intake data
3. Gemini creates lead in Invoice System CRM via API
4. Gemini analyzes intake → Routes to specialized AIs:
   - Claude → /branding (brand strategy)
   - Claude → /website (website plan)
   - Claude → /social (social media plan)
   - Claude → /copywriting (initial copy)
5. Gemini orchestrates deliverables:
   - Creates Notion project page with all outputs
   - Links deliverables to Invoice System proposal
6. ChatGPT sends Google Chat notification to team
7. Perplexity drafts Slack welcome message to client
8. Gemini triggers invoice creation in Invoice System
9. All deliverables linked across: Notion, Invoice Portal
```

### Workflow 2: Meeting Notes Processing (Gemini Integration)
```
1. Google Meet records meeting → Gemini auto-transcribes in real-time
2. Gemini extracts:
   - Meeting summary
   - Key discussion points
   - Action items with owners
   - Decisions made
   - Follow-up questions
3. MWD Assistant receives Gemini output via webhook/API
4. Agent structures notes and saves to Notion project page
5. Agent extracts deliverables and deadlines → updates project timeline
6. Agent creates Slack tasks for action items with @mentions
7. Agent drafts recap email for client with summary and next steps
8. Agent links meeting notes to relevant project documents in Drive
```

### Workflow 3: Social Media Content Creation
```
1. Trigger: Weekly content generation request
2. Agent fetches client brand guidelines from Notion
3. Agent calls Perplexity for trending topics
4. Agent calls ChatGPT for post variations
5. Agent calls Claude for strategy review
6. Agent formats posts for each platform
7. Agent saves to Notion content calendar
8. Agent sends preview to Slack for approval
```

---

## Data Models

### Project Schema
```json
{
  "project_id": "uuid",
  "client_name": "string",
  "company_name": "string",
  "industry": "string",
  "status": "intake|branding|design|development|launched",
  "brand_strategy": {
    "positioning": "string",
    "target_audience": "string",
    "personality_traits": ["string"],
    "color_palette": {
      "primary": "string",
      "secondary": "string",
      "accent": "string"
    },
    "typography": ["string"],
    "messaging": ["string"]
  },
  "website_plan": {
    "sitemap": ["string"],
    "homepage_layout": "string",
    "pages": [{"name": "string", "description": "string"}],
    "cta_strategy": "string"
  },
  "social_strategy": {
    "platforms": ["string"],
    "content_pillars": ["string"],
    "posting_frequency": "string",
    "hashtag_strategy": "string"
  },
  "deliverables": [
    {
      "type": "string",
      "url": "string",
      "status": "pending|in-progress|completed",
      "due_date": "datetime"
    }
  ],
  "notion_page_id": "string",
  "drive_folder_id": "string",
  "slack_channel_id": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Client Intake Schema
```json
{
  "company_name": "string",
  "industry": "string",
  "target_audience": "string",
  "key_services": ["string"],
  "brand_values": ["string"],
  "competitors": ["string"],
  "unique_selling_point": "string",
  "project_goals": ["string"],
  "budget": "string",
  "timeline": "string",
  "contact_email": "string"
}
```

---

## Integration Specifications

### Notion Workspace Structure
```
MW Design Studio Workspace
├── 📊 Projects Database
│   ├── Active Projects
│   ├── Completed Projects
│   └── Archived Projects
├── 📝 Meeting Notes
│   └── Linked to Projects
├── 🎨 Brand Guidelines Database
│   └── Per-client brand assets
├── 📅 Content Calendar
│   └── Social media scheduling
├── 📚 Knowledge Base
│   ├── Templates
│   ├── Case Studies
│   └── Best Practices
└── ✅ Tasks & Deliverables
    └── Linked to Projects
```

### Slack Channel Architecture
```
#client-[name]       - Client-specific channels
#agent-notifications - Agent status updates
#approvals           - Review agent outputs
#project-updates     - Automated project status
```

---

## Security & Privacy

### API Key Management
- Environment variables for all credentials
- Separate dev/staging/production keys
- Key rotation policy (90 days)
- Encrypted storage in Supabase

### Data Protection
- Client data encrypted at rest
- HTTPS for all API communications
- Role-based access control
- Regular security audits

### Compliance
- GDPR compliance for EU clients
- Data retention policies
- Client data export/deletion capabilities
- Terms of service and privacy policy

---

## Development Roadmap

### Sprint 1 (Weeks 1-2): Foundation
- ✅ Basic Flask API setup
- ✅ Claude integration for 4 core endpoints
- ✅ Environment configuration
- ✅ Test suite implementation
- 🔲 README and documentation
- 🔲 Git repository cleanup and organization
- 🔲 CI/CD pipeline setup

### Sprint 2 (Weeks 3-4): Notion Integration
- 🔲 Notion API authentication
- 🔲 Project database sync
- 🔲 Meeting notes integration
- 🔲 Template library setup
- 🔲 Automated project creation workflow

### Sprint 3 (Weeks 5-6): Google Workspace Integration
- 🔲 Google OAuth setup
- 🔲 Drive folder organization
- 🔲 Gmail draft generation
- 🔲 Google Docs creation
- 🔲 Meeting notes from Gemini

### Sprint 4 (Weeks 7-8): Slack Integration
- 🔲 Slack bot setup
- 🔲 Command interface (/mwd-assistant commands)
- 🔲 Notification system
- 🔲 Client channel automation
- 🔲 Approval workflows

### Sprint 5 (Weeks 9-10): Multi-AI Orchestration
- 🔲 ChatGPT integration
- 🔲 Perplexity integration
- 🔲 Agent routing logic
- 🔲 Context management across AIs
- 🔲 Cost optimization strategies

### Sprint 6 (Weeks 11-12): Advanced Features
- 🔲 Supabase database implementation
- 🔲 Project history and analytics
- 🔲 Client preference learning
- 🔲 Template improvement system
- 🔲 Performance monitoring

### Sprint 7 (Weeks 13-14): Polish & Deploy
- 🔲 End-to-end testing
- 🔲 User acceptance testing
- 🔲 Documentation completion
- 🔲 Production deployment to Railway
- 🔲 Team training

---

## Deployment Strategy (Railway)

### Why Railway?
Railway is recommended for the MWD Assistant deployment because:
1. **Easy Integration** - Your invoice system can also be hosted on Railway
2. **Simple Setup** - Connect GitHub repo → Auto-deploy on push
3. **Environment Variables** - Secure API key management
4. **Database Support** - Built-in PostgreSQL or Supabase connection
5. **Cost Effective** - ~$5-20/month for small services
6. **Zero Config** - Detects Flask/Python automatically

### Railway Deployment Steps
```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login to Railway
railway login

# 3. Initialize project in your repo
cd /path/to/mwd-assistant
railway init

# 4. Add environment variables
railway variables set ANTHROPIC_API_KEY=your_key_here
railway variables set GEMINI_API_KEY=your_key_here
railway variables set SUPABASE_URL=your_url_here
railway variables set SUPABASE_KEY=your_key_here

# 5. Deploy
railway up

# 6. Get deployment URL
railway open
```

### Railway Configuration File (`railway.toml`)
```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "python main.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[[services]]
name = "mwd-assistant"
```

### Environment Variables on Railway
```
ANTHROPIC_API_KEY
GEMINI_API_KEY
CHATGPT_API_KEY
PERPLEXITY_API_KEY
SUPABASE_URL
SUPABASE_KEY
SLACK_TOKEN
NOTION_TOKEN
MWD_INVOICE_SYSTEM_URL (for webhook integration)
MWD_INVOICE_SYSTEM_API_KEY
```

### CI/CD with Railway
- **Auto Deploy on Git Push** - Railway automatically deploys when you push to main branch
- **Preview Environments** - Each PR gets a preview deployment
- **Rollback** - Easy one-click rollback to previous deployments
- **Logs & Monitoring** - Built-in logging and metrics dashboard

### Connecting to Invoice System
If the invoice system is also on Railway:
```python
# Internal Railway networking
INVOICE_SYSTEM_URL = os.getenv('MWD_INVOICE_SYSTEM_URL', 'https://mwd-invoice.railway.app')

# Agent can call invoice system APIs directly
import requests
response = requests.post(
    f"{INVOICE_SYSTEM_URL}/api/leads/create",
    json=lead_data,
    headers={"Authorization": f"Bearer {os.getenv('MWD_INVOICE_SYSTEM_API_KEY')}"}
)
```

---

## Budget & Resources

### AI API Costs (Monthly Estimates)
```
Gemini API:      $0-100   (PRIMARY - workspace mgmt, meeting notes, Notion integration)
Claude API:      $30-100  (strategic deliverables - branding, website, design)
ChatGPT API:     $20-50   (internal team Google Chat communication)
Perplexity API:  $20-50   (client Slack communication)
Total:           $70-300/month
```

### Infrastructure Costs
```
Railway Agent:   $5-20/month    (MWD Assistant service)
Railway Invoice: $10-25/month   (Invoice System - if not already hosted)
Supabase:        $0-25/month    (Shared database - Free tier initially)
Domain:          $15/year
Monitoring:      $0             (Free tier Sentry)
Total:           $15-70/month
```

### Development Time
```
Total Estimated Hours: 200-280 hours
Sprint 1-2:  60 hours (foundation + Notion)
Sprint 3-4:  60 hours (Google + Slack)
Sprint 5-6:  60 hours (multi-AI + advanced)
Sprint 7:    20-40 hours (testing + deployment)
```

---

## Risk Assessment

### Technical Risks
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| API rate limits | High | Medium | Implement caching, queue system |
| AI costs exceed budget | Medium | Medium | Set spending alerts, optimize prompts |
| Integration API changes | Medium | Low | Version locking, regular testing |
| Data loss | High | Low | Regular backups, redundancy |

### Business Risks
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Low user adoption | High | Medium | Training, gradual rollout |
| Client data privacy concerns | High | Low | Clear privacy policy, compliance |
| Over-reliance on AI | Medium | Medium | Human review workflows |
| Vendor lock-in | Medium | Low | Design for modularity |

---

## Success Criteria

### MVP Launch (Sprint 1)
- [ ] All 4 core endpoints functional
- [ ] API deployed and accessible
- [ ] Basic error handling and logging
- [ ] Test coverage >80%

### Phase 2 Complete (Sprint 4)
- [ ] Notion, Google, Slack integrations working
- [ ] Automated client onboarding workflow
- [ ] Meeting notes processing pipeline
- [ ] 5 successful client projects processed

### Full System (Sprint 7)
- [ ] Multi-AI orchestration operational
- [ ] All integrations stable
- [ ] Team trained and using daily
- [ ] 50% time savings demonstrated
- [ ] Positive client feedback

---

## Repository Structure Plan

### Proposed Folder Structure
```
mwd-assistant/
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   ├── agents/
│   │   ├── branding.py
│   │   ├── website.py
│   │   ├── social.py
│   │   ├── copywriting.py
│   │   └── orchestrator.py
│   ├── integrations/
│   │   ├── notion.py
│   │   ├── google_workspace.py
│   │   ├── slack.py
│   │   └── supabase.py
│   ├── ai_clients/
│   │   ├── claude.py
│   │   ├── gemini.py
│   │   ├── chatgpt.py
│   │   └── perplexity.py
│   ├── models/
│   │   ├── project.py
│   │   └── client.py
│   └── utils/
│       ├── config.py
│       └── logging.py
├── tests/
│   ├── test_agents.py
│   ├── test_integrations.py
│   └── test_workflows.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── INTEGRATION_GUIDE.md
│   └── conversation-history/ (screenshots)
├── templates/
│   ├── brand_strategy.json
│   ├── website_plan.json
│   └── social_strategy.json
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
├── PROJECT_PLAN.md (this file)
└── main.py
```

---

## Next Steps

### Immediate Actions
1. **Repository Organization**
   - Merge local code with GitHub repo
   - Move screenshots to docs/conversation-history/
   - Create proper folder structure
   - Add comprehensive README.md

2. **Documentation**
   - Create API reference
   - Write integration guides
   - Document environment setup
   - Add code comments

3. **Testing & Quality**
   - Expand test coverage
   - Add integration tests
   - Set up CI/CD pipeline
   - Error handling improvements

4. **Planning**
   - Prioritize Sprint 2 features
   - Design Notion integration schema
   - Create API authentication flow
   - Schedule development sprints

### Questions to Resolve
1. Which cloud hosting platform? (Render, Railway, Fly.io, or other?)
2. Supabase vs. PostgreSQL self-hosted?
3. Celery + Redis for background tasks, or alternatives?
4. Should we add a frontend dashboard? (React/Next.js?)
5. Multi-tenant support for other design studios?

---

## Appendix

### References
- [Anthropic Claude API Docs](https://docs.anthropic.com/)
- [Notion API Docs](https://developers.notion.com/)
- [Google Workspace APIs](https://developers.google.com/workspace)
- [Slack API Docs](https://api.slack.com/)
- [Supabase Docs](https://supabase.com/docs)

### Conversation History
All planning conversations and design decisions are documented in screenshots at:
`docs/conversation-history/` in the GitHub repository.

---

**Document Status:** Living Document
**Last Updated:** November 15, 2025
**Next Review:** Sprint 1 Completion
