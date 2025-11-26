# MWD Assistant ↔ Invoice System Integration Specification

**Version:** 1.0
**Date:** November 15, 2025
**Purpose:** Define bi-directional communication between MWD Assistant and MWD Invoice System

---

## Overview

The MWD Assistant and MWD Invoice System need to communicate in both directions:

- **Invoice System → Agent**: Send client intake data to trigger AI workflows
- **Agent → Invoice System**: Send AI-generated deliverables, create leads, update project status

---

## 1. Changes Needed in MWD Invoice System

### A. Outbound Webhooks (Invoice System → Agent)

#### Webhook: New Client Intake Submitted

**When:** Client submits intake form
**Trigger:** Form submission in invoice system
**Destination:** `POST https://mwd-assistant.railway.app/api/intake`

**Payload Schema:**
```json
{
  "event_type": "client.intake.submitted",
  "event_id": "uuid",
  "timestamp": "2025-11-15T10:30:00Z",
  "intake_data": {
    "company_name": "TechFlow Solutions",
    "industry": "B2B SaaS",
    "target_audience": "Enterprise software teams",
    "key_services": ["Website Design", "Branding", "Social Media"],
    "brand_values": ["Innovation", "Trust", "Efficiency"],
    "competitors": ["Competitor A", "Competitor B"],
    "unique_selling_point": "AI-powered workflow automation",
    "project_goals": ["Launch new brand", "Increase conversions", "Build authority"],
    "budget": "$50,000 - $75,000",
    "timeline": "3-4 months",
    "contact_email": "[email protected]",
    "contact_name": "John Smith",
    "phone": "+1-555-0123"
  },
  "invoice_system_metadata": {
    "lead_id": "lead_abc123",
    "form_id": "intake_form_v2",
    "source": "website_form",
    "assigned_to": "sales_team"
  }
}
```

**Required Headers:**
```
Content-Type: application/json
X-MWD-Signature: <HMAC signature for verification>
X-MWD-Event-Type: client.intake.submitted
Authorization: Bearer <shared_secret_token>
```

#### Webhook: Project Status Changed

**When:** Project status updates in invoice system
**Trigger:** Status field changed (contract signed, payment received, etc.)
**Destination:** `POST https://mwd-assistant.railway.app/api/project/status`

**Payload Schema:**
```json
{
  "event_type": "project.status.changed",
  "event_id": "uuid",
  "timestamp": "2025-11-15T14:00:00Z",
  "project_data": {
    "project_id": "proj_xyz789",
    "lead_id": "lead_abc123",
    "company_name": "TechFlow Solutions",
    "old_status": "proposal_sent",
    "new_status": "contract_signed",
    "payment_status": "deposit_received",
    "amount_paid": 15000.00,
    "next_milestone": "branding_kickoff"
  }
}
```

### B. Inbound API Endpoints (Invoice System Must Accept)

#### Endpoint 1: Create Lead

**Purpose:** Agent creates new lead from intake data
**Method:** `POST /api/v1/leads`
**URL:** `https://invoice-system.your-domain.com/api/v1/leads`

**Request Payload (from Agent):**
```json
{
  "source": "mwd_assistant_intake",
  "company_name": "TechFlow Solutions",
  "contact_name": "John Smith",
  "contact_email": "[email protected]",
  "phone": "+1-555-0123",
  "industry": "B2B SaaS",
  "budget": "$50,000 - $75,000",
  "services_requested": ["Branding", "Website Design", "Social Media"],
  "agent_assessment": {
    "complexity_score": 8,
    "estimated_hours": 120,
    "recommended_package": "premium",
    "ai_generated_summary": "Enterprise B2B SaaS client seeking..."
  },
  "intake_form_data": { /* full intake data */ }
}
```

**Response:**
```json
{
  "success": true,
  "lead_id": "lead_abc123",
  "lead_url": "https://invoice-system.com/leads/lead_abc123",
  "created_at": "2025-11-15T10:30:00Z"
}
```

#### Endpoint 2: Update Lead with Deliverables

**Purpose:** Agent uploads AI-generated deliverables
**Method:** `PUT /api/v1/leads/{lead_id}/deliverables`
**URL:** `https://invoice-system.com/api/v1/leads/lead_abc123/deliverables`

**Request Payload:**
```json
{
  "deliverable_type": "branding_strategy",
  "generated_at": "2025-11-15T11:00:00Z",
  "ai_model": "claude-sonnet-4.5",
  "content": {
    "brand_positioning": "TechFlow positions itself as...",
    "target_audience": "Enterprise software teams (50-500 employees)...",
    "brand_personality": ["Innovative", "Trustworthy", "Efficient"],
    "color_palette": {
      "primary": "#1E40AF",
      "secondary": "#3B82F6",
      "accent": "#F59E0B"
    },
    "typography": {
      "heading": "Inter Bold",
      "body": "Inter Regular"
    },
    "key_messaging": ["AI-powered efficiency", "Enterprise-grade security", "Seamless integration"]
  },
  "formatted_output": {
    "pdf_url": "https://storage.agent.com/deliverables/branding_techflow.pdf",
    "markdown": "# Brand Strategy\n\n## Positioning...",
    "notion_page_url": "https://notion.so/techflow-brand-strategy"
  },
  "tokens_used": {
    "input": 1250,
    "output": 3840,
    "cost": 0.12
  }
}
```

**Response:**
```json
{
  "success": true,
  "deliverable_id": "deliv_456",
  "lead_updated": true,
  "proposal_ready": true,
  "proposal_url": "https://invoice-system.com/proposals/prop_789"
}
```

#### Endpoint 3: Create Project from Approved Proposal

**Purpose:** Notify invoice system when agent starts project work
**Method:** `POST /api/v1/projects`
**URL:** `https://invoice-system.com/api/v1/projects`

**Request Payload:**
```json
{
  "lead_id": "lead_abc123",
  "project_name": "TechFlow Solutions - Full Branding Package",
  "services": ["branding", "website", "social_media", "copywriting"],
  "estimated_completion": "2025-03-15",
  "agent_workspace": {
    "notion_project_url": "https://notion.so/techflow-project",
    "slack_channel": "#client-techflow"
  },
  "milestones": [
    {
      "name": "Brand Strategy Completed",
      "target_date": "2025-12-01",
      "deliverables": ["Brand Guidelines PDF", "Logo Concepts"]
    }
  ]
}
```

#### Endpoint 4: Project Status Update

**Purpose:** Agent updates project progress
**Method:** `PATCH /api/v1/projects/{project_id}/status`

**Request Payload:**
```json
{
  "status": "branding_complete",
  "completion_percentage": 35,
  "milestone_completed": "Brand Strategy Completed",
  "deliverables_ready": [
    {
      "name": "Brand Guidelines",
      "url": "https://storage.agent.com/deliverables/brand_guidelines.pdf",
      "type": "pdf"
    }
  ],
  "next_steps": "Website design wireframes - starting Monday",
  "trigger_invoice": true,
  "invoice_amount": 15000.00,
  "invoice_description": "Milestone 1: Brand Strategy & Guidelines"
}
```

#### Endpoint 5: Request Client Information

**Purpose:** Agent requests additional client details mid-project
**Method:** `GET /api/v1/leads/{lead_id}`
**URL:** `https://invoice-system.com/api/v1/leads/lead_abc123`

**Response:**
```json
{
  "lead_id": "lead_abc123",
  "company_name": "TechFlow Solutions",
  "contact_info": { /* ... */ },
  "intake_data": { /* original intake */ },
  "contract_status": "signed",
  "payment_status": "deposit_received",
  "assigned_team": ["designer_jane", "developer_mike"],
  "custom_fields": {
    "brand_preferences": "Modern, minimal, tech-forward",
    "competitors_analyzed": ["CompA", "CompB"]
  }
}
```

### C. Authentication & Security

**Required from Invoice System:**

1. **API Authentication Token**
   - Generate long-lived API token for Agent
   - Include in all responses: `X-API-Key: mwd_assistant_secret_token_abc123`
   - Store in Agent's `.env`: `MWD_INVOICE_SYSTEM_API_KEY`

2. **Webhook Signature Verification**
   - Use HMAC-SHA256 for webhook payload signing
   - Shared secret: `MWD_WEBHOOK_SECRET` (exchange securely)
   - Agent verifies signature before processing

3. **HTTPS Only**
   - All communication over HTTPS
   - TLS 1.2 or higher

4. **Rate Limiting**
   - Allow 100 requests/minute from Agent
   - Return `429 Too Many Requests` if exceeded

### D. Configuration in Invoice System

**Add to Invoice System Settings:**

```json
{
  "mwd_assistant_integration": {
    "enabled": true,
    "agent_api_url": "https://mwd-assistant.railway.app",
    "agent_api_key": "<generate_secure_token>",
    "webhook_endpoints": {
      "intake_submitted": "https://mwd-assistant.railway.app/api/intake",
      "project_status_changed": "https://mwd-assistant.railway.app/api/project/status"
    },
    "webhook_secret": "<generate_secure_secret>",
    "auto_create_leads": true,
    "auto_attach_deliverables": true
  }
}
```

---

## 2. Changes Needed in MWD Assistant

### A. New API Endpoints (Agent Must Accept)

#### Endpoint 1: Receive Client Intake

**Purpose:** Accept intake data from invoice system webhook
**Method:** `POST /api/intake`
**URL:** `https://mwd-assistant.railway.app/api/intake`

**Implementation Needed:**
```python
@app.route('/api/intake', methods=['POST'])
def receive_intake():
    """
    Receive client intake from MWD Invoice System
    1. Verify webhook signature
    2. Store intake data
    3. Trigger AI workflow (Gemini orchestration)
    4. Create lead in invoice system
    5. Return acknowledgment
    """
    # Verify HMAC signature
    signature = request.headers.get('X-MWD-Signature')
    if not verify_webhook_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 403

    intake_data = request.json['intake_data']

    # Store in MCP Memory for all AIs
    await memory_client.call_tool('save_memory', {
        'key': f'intake_{intake_data["company_name"]}',
        'value': intake_data
    })

    # Trigger AI workflow
    result = await orchestrate_client_onboarding(intake_data)

    # Create lead in invoice system
    lead_response = create_lead_in_invoice_system(intake_data, result)

    return jsonify({
        'success': True,
        'lead_id': lead_response['lead_id'],
        'workflows_triggered': ['branding', 'website', 'social', 'copywriting']
    })
```

#### Endpoint 2: Receive Project Status Update

**Purpose:** Accept status updates from invoice system
**Method:** `POST /api/project/status`

**Implementation Needed:**
```python
@app.route('/api/project/status', methods=['POST'])
def receive_project_status():
    """
    Receive project status updates from invoice system
    Update internal project state
    Notify team via Slack
    Adjust AI workflows based on status
    """
    status_data = request.json['project_data']

    # Update project in Supabase
    supabase_client.table('projects').update({
        'status': status_data['new_status'],
        'payment_status': status_data['payment_status']
    }).eq('invoice_lead_id', status_data['lead_id']).execute()

    # Notify team
    await slack_notify(f"Project {status_data['company_name']} status: {status_data['new_status']}")

    return jsonify({'success': True})
```

### B. Outbound API Client (Agent → Invoice System)

**Implementation Needed:**

```python
# integrations/invoice_system.py

import os
import requests
from typing import Dict, Any

class InvoiceSystemClient:
    """Client for MWD Invoice System API"""

    def __init__(self):
        self.base_url = os.getenv('MWD_INVOICE_SYSTEM_URL')
        self.api_key = os.getenv('MWD_INVOICE_SYSTEM_API_KEY')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

    def create_lead(self, intake_data: Dict, ai_assessment: Dict) -> Dict:
        """Create lead in invoice system"""
        payload = {
            'source': 'mwd_assistant_intake',
            'company_name': intake_data['company_name'],
            'contact_name': intake_data.get('contact_name'),
            'contact_email': intake_data['contact_email'],
            'industry': intake_data['industry'],
            'budget': intake_data['budget'],
            'services_requested': intake_data['key_services'],
            'agent_assessment': ai_assessment,
            'intake_form_data': intake_data
        }

        response = requests.post(
            f'{self.base_url}/api/v1/leads',
            json=payload,
            headers=self.headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def attach_deliverable(self, lead_id: str, deliverable: Dict) -> Dict:
        """Attach AI-generated deliverable to lead"""
        response = requests.put(
            f'{self.base_url}/api/v1/leads/{lead_id}/deliverables',
            json=deliverable,
            headers=self.headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def update_project_status(self, project_id: str, status_update: Dict) -> Dict:
        """Update project status"""
        response = requests.patch(
            f'{self.base_url}/api/v1/projects/{project_id}/status',
            json=status_update,
            headers=self.headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_lead(self, lead_id: str) -> Dict:
        """Get lead details"""
        response = requests.get(
            f'{self.base_url}/api/v1/leads/{lead_id}',
            headers=self.headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
```

### C. Environment Variables (Add to .env)

```bash
# MWD Invoice System Integration
MWD_INVOICE_SYSTEM_URL=https://invoice-system.your-domain.com
MWD_INVOICE_SYSTEM_API_KEY=your_invoice_system_api_key_here
MWD_WEBHOOK_SECRET=shared_webhook_secret_for_hmac_verification
```

---

## 3. Integration Workflow Example

### Complete Flow: New Client Intake → Deliverables → Invoice

```
1. CLIENT SUBMITS INTAKE FORM
   ↓
   [Invoice System] Receives form submission
   ↓

2. INVOICE SYSTEM SENDS WEBHOOK
   POST https://mwd-assistant.railway.app/api/intake
   Payload: { intake_data, invoice_metadata }
   ↓

3. AGENT RECEIVES & PROCESSES
   - Verifies webhook signature ✓
   - Stores in MCP Memory
   - Triggers Gemini orchestration
   ↓

4. GEMINI ORCHESTRATES AI WORKFLOW
   - Claude generates branding strategy
   - Claude creates website plan
   - Claude develops social strategy
   - Claude writes marketing copy
   ↓

5. AGENT CREATES LEAD IN INVOICE SYSTEM
   POST https://invoice-system.com/api/v1/leads
   Payload: { intake_data, ai_assessment }
   ← Response: { lead_id: "lead_abc123" }
   ↓

6. AGENT ATTACHES DELIVERABLES
   PUT https://invoice-system.com/api/v1/leads/lead_abc123/deliverables
   Payload: { branding_strategy, website_plan, social_strategy, copywriting }
   ← Response: { proposal_ready: true, proposal_url }
   ↓

7. SALES TEAM REVIEWS IN INVOICE SYSTEM
   - Views AI-generated deliverables
   - Customizes proposal
   - Sends to client
   ↓

8. CLIENT SIGNS CONTRACT
   [Invoice System] Updates status to "contract_signed"
   ↓

9. INVOICE SYSTEM SENDS STATUS WEBHOOK
   POST https://mwd-assistant.railway.app/api/project/status
   Payload: { new_status: "contract_signed", payment_received }
   ↓

10. AGENT CREATES PROJECT
    POST https://invoice-system.com/api/v1/projects
    Payload: { lead_id, project_details, milestones }
    ↓

11. ONGOING STATUS UPDATES
    Agent → Invoice System: Milestone completions, deliverables
    Invoice System → Agent: Payment updates, scope changes
```

---

## 4. Database Schema Changes

### Invoice System - New Tables/Fields

**`leads` table - Add fields:**
```sql
ALTER TABLE leads ADD COLUMN agent_generated BOOLEAN DEFAULT FALSE;
ALTER TABLE leads ADD COLUMN intake_source VARCHAR(50);
ALTER TABLE leads ADD COLUMN ai_assessment_score INTEGER;
ALTER TABLE leads ADD COLUMN agent_summary TEXT;
```

**`deliverables` table - New table:**
```sql
CREATE TABLE agent_deliverables (
  id UUID PRIMARY KEY,
  lead_id UUID REFERENCES leads(id),
  project_id UUID REFERENCES projects(id),
  deliverable_type VARCHAR(50), -- 'branding', 'website', 'social', 'copywriting'
  ai_model VARCHAR(50),
  content JSONB,
  formatted_output JSONB,
  generated_at TIMESTAMP,
  tokens_used JSONB,
  cost DECIMAL(10,2),
  status VARCHAR(20) DEFAULT 'pending_review'
);
```

**`webhook_logs` table - New table:**
```sql
CREATE TABLE webhook_logs (
  id UUID PRIMARY KEY,
  event_type VARCHAR(100),
  payload JSONB,
  sent_at TIMESTAMP,
  response_status INTEGER,
  response_body JSONB,
  retries INTEGER DEFAULT 0
);
```

### MWD Assistant - New Tables

**Supabase `projects` table:**
```sql
CREATE TABLE projects (
  id UUID PRIMARY KEY,
  invoice_lead_id VARCHAR(50),
  invoice_project_id VARCHAR(50),
  company_name VARCHAR(255),
  intake_data JSONB,
  status VARCHAR(50),
  payment_status VARCHAR(50),
  deliverables JSONB,
  notion_url TEXT,
  slack_channel VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. Testing Checklist

### Invoice System Side

- [ ] Webhook endpoint configured for intake submissions
- [ ] Webhook signature generation (HMAC-SHA256) working
- [ ] API endpoint `/api/v1/leads` accepts POST requests
- [ ] API endpoint `/api/v1/leads/{id}/deliverables` accepts PUT
- [ ] API authentication token generated
- [ ] HTTPS enabled
- [ ] Rate limiting configured
- [ ] Webhook retry logic (in case Agent is down)

### Agent Side

- [ ] `/api/intake` endpoint verifies webhook signatures
- [ ] `/api/intake` stores data in MCP Memory
- [ ] Invoice system client created (`integrations/invoice_system.py`)
- [ ] `create_lead()` function working
- [ ] `attach_deliverable()` function working
- [ ] Environment variables configured
- [ ] Error handling for API failures
- [ ] Logging webhook events

### Integration Testing

- [ ] End-to-end test: Submit intake → Receive webhook → Create lead
- [ ] Test webhook signature verification
- [ ] Test API authentication
- [ ] Test deliverable attachment
- [ ] Test status update flow
- [ ] Test error scenarios (network failure, invalid data)

---

## 6. Deployment Steps

### Phase 1: Setup (Week 1)

1. **Invoice System:**
   - Add webhook configuration UI
   - Implement API endpoints
   - Generate authentication tokens
   - Set up webhook signing

2. **Agent:**
   - Add `/api/intake` endpoint
   - Create invoice system client
   - Configure environment variables

### Phase 2: Testing (Week 2)

1. Use staging environments for both systems
2. Test with sample intake data
3. Verify webhooks, API calls, data flow
4. Fix any integration issues

### Phase 3: Production (Week 3)

1. Deploy to production
2. Monitor webhook logs
3. Monitor API usage
4. Track deliverable attachment success rate

---

## 7. Monitoring & Alerts

### Metrics to Track

**Invoice System:**
- Webhook delivery success rate
- API response times
- Failed webhook retries
- Deliverables attached per lead

**Agent:**
- Intake webhooks received
- Intake processing time
- Lead creation success rate
- Deliverable generation time
- API call failures

### Alert Triggers

- Webhook delivery failure > 5% in 1 hour → Alert team
- API response time > 5 seconds → Investigate
- Signature verification failures → Security alert
- Failed lead creation → Immediate notification

---

## Summary

### Invoice System Must Provide:

1. ✅ Webhook for new intake submissions → `POST /api/intake`
2. ✅ Webhook for project status changes → `POST /api/project/status`
3. ✅ API endpoint to create leads → `POST /api/v1/leads`
4. ✅ API endpoint to attach deliverables → `PUT /api/v1/leads/{id}/deliverables`
5. ✅ API endpoint for project creation → `POST /api/v1/projects`
6. ✅ API endpoint for status updates → `PATCH /api/v1/projects/{id}/status`
7. ✅ API authentication tokens
8. ✅ Webhook HMAC signature generation

### MWD Assistant Must Provide:

1. ✅ Endpoint to receive intake webhooks → `POST /api/intake`
2. ✅ Endpoint to receive status webhooks → `POST /api/project/status`
3. ✅ Invoice system API client (`integrations/invoice_system.py`)
4. ✅ Webhook signature verification
5. ✅ Error handling and retry logic
6. ✅ MCP Memory integration for shared context

---

**Next Steps:** Start with Phase 1 implementation on both sides, then proceed to integration testing.

