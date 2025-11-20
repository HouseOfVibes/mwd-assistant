#!/usr/bin/env python3
"""
MWD Agent - Marketing Website Design Agent
Handles branding, website design, social media, and copywriting workflows
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from anthropic import Anthropic
from integrations.invoice_system import InvoiceSystemClient
from integrations.gemini import GeminiClient
from integrations.openai_client import OpenAIClient
from integrations.perplexity import PerplexityClient
from integrations.notion import NotionClient
from integrations.google_workspace import GoogleWorkspaceClient
from integrations.slack_bot import SlackBot
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize AI clients
anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
gemini_client = GeminiClient()
openai_client = OpenAIClient()
perplexity_client = PerplexityClient()

# Initialize Integration clients
invoice_client = InvoiceSystemClient()
notion_client = NotionClient()
google_client = GoogleWorkspaceClient()
slack_bot = SlackBot()

# Configuration check
def check_config():
    """Check which services are configured"""
    config_status = {
        # AI Services
        'anthropic': 'configured' if os.getenv('ANTHROPIC_API_KEY') else 'missing',
        'gemini': 'configured' if gemini_client.is_configured() else 'optional',
        'openai': 'configured' if openai_client.is_configured() else 'optional',
        'perplexity': 'configured' if perplexity_client.is_configured() else 'optional',
        # Integrations
        'invoice_system': 'configured' if invoice_client.is_configured() else 'optional',
        'notion': 'configured' if notion_client.is_configured() else 'optional',
        'google_workspace': 'configured' if google_client.is_configured() else 'optional',
        'slack_bot': 'configured' if slack_bot.is_configured() else 'optional',
        'supabase': 'configured' if os.getenv('SUPABASE_URL') else 'optional'
    }
    return config_status

# Agent prompts
BRANDING_PROMPT = """You are a branding expert helping create a comprehensive brand identity.

Based on the client information provided, create:
1. Brand positioning statement
2. Target audience definition
3. Brand personality (3-5 traits)
4. Color palette suggestions (primary, secondary, accent colors)
5. Typography recommendations
6. Key messaging points

Client Info:
{client_info}

Return your response as a structured JSON object."""

WEBSITE_PROMPT = """You are a website design strategist creating a website plan.

Based on the client information and branding, create:
1. Sitemap (main pages and structure)
2. Homepage layout description
3. Key page descriptions
4. Call-to-action strategy
5. User journey map

Client Info:
{client_info}

Return your response as a structured JSON object."""

SOCIAL_PROMPT = """You are a social media strategist creating a content plan.

Based on the client information and branding, create:
1. Platform recommendations (which social media platforms and why)
2. Content pillars (3-5 main themes)
3. Posting frequency recommendations
4. Sample post ideas (5 examples)
5. Hashtag strategy

Client Info:
{client_info}

Return your response as a structured JSON object."""

COPYWRITING_PROMPT = """You are a professional copywriter creating marketing copy.

Based on the client information and branding, create:
1. Tagline options (3-5 variations)
2. About section copy
3. Value proposition statement
4. Service/Product descriptions
5. Email welcome sequence outline

Client Info:
{client_info}

Return your response as a structured JSON object."""


def call_claude(prompt, client_data):
    """Call Claude API with the given prompt and client data using latest features"""
    try:
        formatted_prompt = prompt.format(client_info=str(client_data))

        message = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",  # Latest Sonnet 4.5 model
            max_tokens=4096,
            messages=[
                {"role": "user", "content": formatted_prompt}
            ],
            # Enable prompt caching for repeated system prompts (future enhancement)
            # system=[
            #     {
            #         "type": "text",
            #         "text": "System instructions here",
            #         "cache_control": {"type": "ephemeral"}
            #     }
            # ]
        )

        return {
            'success': True,
            'response': message.content[0].text,
            'usage': {
                'input_tokens': message.usage.input_tokens,
                'output_tokens': message.usage.output_tokens,
                'cache_creation_tokens': getattr(message.usage, 'cache_creation_input_tokens', 0),
                'cache_read_tokens': getattr(message.usage, 'cache_read_input_tokens', 0)
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@app.route('/')
def home():
    """Health check and service status"""
    config = check_config()
    return jsonify({
        'status': 'running',
        'service': 'MWD Agent',
        'version': '2.1.0',
        'config': config,
        'endpoints': {
            'strategy': [
                'POST /branding',
                'POST /website',
                'POST /social',
                'POST /copywriting'
            ],
            'ai': [
                'POST /ai/gemini/meeting-notes',
                'POST /ai/gemini/summarize',
                'POST /ai/gemini/orchestrate',
                'POST /ai/openai/team-message',
                'POST /ai/openai/slack-message',
                'POST /ai/openai/summarize-thread',
                'POST /ai/perplexity/research',
                'POST /ai/perplexity/competitors',
                'POST /ai/perplexity/client-email'
            ],
            'notion': [
                'POST /notion/project',
                'POST /notion/meeting-notes',
                'GET /notion/search'
            ],
            'google': [
                'POST /google/drive/folder',
                'POST /google/drive/project-structure',
                'POST /google/docs/document',
                'POST /google/docs/deliverable'
            ],
            'slack': [
                'POST /slack/events',
                'POST /slack/interact'
            ],
            'webhooks': [
                'POST /api/intake',
                'POST /api/project/status'
            ]
        }
    })


@app.route('/branding', methods=['POST'])
def branding():
    """Generate branding strategy"""
    client_data = request.json
    result = call_claude(BRANDING_PROMPT, client_data)
    return jsonify(result)


@app.route('/website', methods=['POST'])
def website():
    """Generate website design plan"""
    client_data = request.json
    result = call_claude(WEBSITE_PROMPT, client_data)
    return jsonify(result)


@app.route('/social', methods=['POST'])
def social():
    """Generate social media strategy"""
    client_data = request.json
    result = call_claude(SOCIAL_PROMPT, client_data)
    return jsonify(result)


@app.route('/copywriting', methods=['POST'])
def copywriting():
    """Generate marketing copy"""
    client_data = request.json
    result = call_claude(COPYWRITING_PROMPT, client_data)
    return jsonify(result)


# =============================================================================
# GEMINI AI ENDPOINTS
# =============================================================================

@app.route('/ai/gemini/meeting-notes', methods=['POST'])
def gemini_meeting_notes():
    """Generate meeting notes from transcript"""
    data = request.json
    transcript = data.get('transcript', '')
    participants = data.get('participants', [])
    result = gemini_client.generate_meeting_notes(transcript, participants)
    return jsonify(result)


@app.route('/ai/gemini/summarize', methods=['POST'])
def gemini_summarize():
    """Summarize a document"""
    data = request.json
    content = data.get('content', '')
    doc_type = data.get('doc_type', 'general')
    result = gemini_client.summarize_document(content, doc_type)
    return jsonify(result)


@app.route('/ai/gemini/orchestrate', methods=['POST'])
def gemini_orchestrate():
    """Orchestrate multi-AI workflow"""
    data = request.json
    task = data.get('task', '')
    context = data.get('context', {})
    result = gemini_client.orchestrate_workflow(task, context)
    return jsonify(result)


# =============================================================================
# OPENAI ENDPOINTS
# =============================================================================

@app.route('/ai/openai/team-message', methods=['POST'])
def openai_team_message():
    """Draft internal team communication"""
    data = request.json
    context = data.get('context', '')
    message_type = data.get('message_type', 'update')
    tone = data.get('tone', 'professional')
    result = openai_client.draft_team_message(context, message_type, tone)
    return jsonify(result)


@app.route('/ai/openai/slack-message', methods=['POST'])
def openai_slack_message():
    """Draft a Slack message"""
    data = request.json
    context = data.get('context', '')
    channel_type = data.get('channel_type', 'project')
    result = openai_client.draft_slack_message(context, channel_type)
    return jsonify(result)


@app.route('/ai/openai/summarize-thread', methods=['POST'])
def openai_summarize_thread():
    """Summarize a conversation thread"""
    data = request.json
    messages = data.get('messages', [])
    result = openai_client.summarize_thread(messages)
    return jsonify(result)


@app.route('/ai/openai/analyze-feedback', methods=['POST'])
def openai_analyze_feedback():
    """Analyze feedback and extract insights"""
    data = request.json
    feedback = data.get('feedback', '')
    source = data.get('source', 'client')
    result = openai_client.analyze_feedback(feedback, source)
    return jsonify(result)


# =============================================================================
# PERPLEXITY ENDPOINTS
# =============================================================================

@app.route('/ai/perplexity/research', methods=['POST'])
def perplexity_research():
    """Research a topic with citations"""
    data = request.json
    topic = data.get('topic', '')
    depth = data.get('depth', 'comprehensive')
    result = perplexity_client.research_topic(topic, depth)
    return jsonify(result)


@app.route('/ai/perplexity/industry', methods=['POST'])
def perplexity_industry():
    """Research an industry"""
    data = request.json
    industry = data.get('industry', '')
    focus_areas = data.get('focus_areas', [])
    result = perplexity_client.research_industry(industry, focus_areas)
    return jsonify(result)


@app.route('/ai/perplexity/competitors', methods=['POST'])
def perplexity_competitors():
    """Research competitors"""
    data = request.json
    company = data.get('company', '')
    competitors = data.get('competitors', [])
    industry = data.get('industry', '')
    result = perplexity_client.research_competitors(company, competitors, industry)
    return jsonify(result)


@app.route('/ai/perplexity/client-email', methods=['POST'])
def perplexity_client_email():
    """Draft client-facing email"""
    data = request.json
    context = data.get('context', '')
    email_type = data.get('email_type', 'update')
    client_name = data.get('client_name', '')
    result = perplexity_client.draft_client_email(context, email_type, client_name)
    return jsonify(result)


@app.route('/ai/perplexity/market-data', methods=['POST'])
def perplexity_market_data():
    """Get market data and statistics"""
    data = request.json
    query = data.get('query', '')
    result = perplexity_client.get_market_data(query)
    return jsonify(result)


# =============================================================================
# NOTION ENDPOINTS
# =============================================================================

@app.route('/notion/project', methods=['POST'])
def notion_create_project():
    """Create a project page in Notion"""
    data = request.json
    database_id = data.get('database_id', '')
    project_data = data.get('project_data', {})
    result = notion_client.create_project_page(database_id, project_data)
    return jsonify(result)


@app.route('/notion/meeting-notes', methods=['POST'])
def notion_meeting_notes():
    """Create meeting notes in Notion"""
    data = request.json
    database_id = data.get('database_id', '')
    meeting_data = data.get('meeting_data', {})
    result = notion_client.create_meeting_notes(database_id, meeting_data)
    return jsonify(result)


@app.route('/notion/search', methods=['GET'])
def notion_search():
    """Search Notion workspace"""
    query = request.args.get('query', '')
    filter_type = request.args.get('filter_type', None)
    result = notion_client.search(query, filter_type)
    return jsonify(result)


@app.route('/notion/database/query', methods=['POST'])
def notion_query_database():
    """Query a Notion database"""
    data = request.json
    database_id = data.get('database_id', '')
    filters = data.get('filters', None)
    sorts = data.get('sorts', None)
    result = notion_client.query_database(database_id, filters, sorts)
    return jsonify(result)


@app.route('/notion/page/status', methods=['PATCH'])
def notion_update_status():
    """Update project status in Notion"""
    data = request.json
    page_id = data.get('page_id', '')
    status = data.get('status', '')
    notes = data.get('notes', '')
    result = notion_client.update_project_status(page_id, status, notes)
    return jsonify(result)


# =============================================================================
# GOOGLE WORKSPACE ENDPOINTS
# =============================================================================

@app.route('/google/drive/folder', methods=['POST'])
def google_create_folder():
    """Create a folder in Google Drive"""
    data = request.json
    name = data.get('name', '')
    parent_id = data.get('parent_id', None)
    result = google_client.create_folder(name, parent_id)
    return jsonify(result)


@app.route('/google/drive/project-structure', methods=['POST'])
def google_create_project_structure():
    """Create project folder structure in Google Drive"""
    data = request.json
    project_name = data.get('project_name', '')
    parent_id = data.get('parent_id', None)
    result = google_client.create_project_structure(project_name, parent_id)
    return jsonify(result)


@app.route('/google/drive/files', methods=['GET'])
def google_list_files():
    """List files in Google Drive folder"""
    folder_id = request.args.get('folder_id', None)
    file_type = request.args.get('file_type', None)
    result = google_client.list_files(folder_id, file_type)
    return jsonify(result)


@app.route('/google/drive/share', methods=['POST'])
def google_share_file():
    """Share a file or folder"""
    data = request.json
    file_id = data.get('file_id', '')
    email = data.get('email', '')
    role = data.get('role', 'reader')
    result = google_client.share_file(file_id, email, role)
    return jsonify(result)


@app.route('/google/docs/document', methods=['POST'])
def google_create_document():
    """Create a Google Doc"""
    data = request.json
    title = data.get('title', '')
    folder_id = data.get('folder_id', None)
    result = google_client.create_document(title, folder_id)
    return jsonify(result)


@app.route('/google/docs/deliverable', methods=['POST'])
def google_create_deliverable():
    """Create a formatted deliverable document"""
    data = request.json
    title = data.get('title', '')
    content = data.get('content', {})
    folder_id = data.get('folder_id', None)
    result = google_client.create_deliverable_doc(title, content, folder_id)
    return jsonify(result)


# =============================================================================
# SLACK BOT ENDPOINTS
# =============================================================================

@app.route('/slack/events', methods=['POST'])
def slack_events():
    """
    Handle Slack Events API

    This endpoint receives all Slack events (messages, mentions, etc.)
    and routes them to the appropriate handler.
    """
    # Verify request signature
    timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
    signature = request.headers.get('X-Slack-Signature', '')

    if not slack_bot.verify_request(timestamp, signature, request.data):
        return jsonify({'error': 'Invalid signature'}), 403

    data = request.json

    # Handle URL verification challenge
    if data.get('type') == 'url_verification':
        return jsonify({'challenge': data.get('challenge')})

    # Handle events
    event = data.get('event', {})
    event_type = event.get('type')

    # Ignore bot messages to prevent loops
    if event.get('bot_id') or event.get('subtype') == 'bot_message':
        return jsonify({'ok': True})

    if event_type == 'app_mention' or event_type == 'message':
        # Only process direct messages or mentions
        channel_type = event.get('channel_type', '')
        if event_type == 'message' and channel_type != 'im':
            # In channels, only respond to mentions
            if f'<@{slack_bot.bot_user_id}>' not in event.get('text', ''):
                return jsonify({'ok': True})

        channel_id = event.get('channel')
        thread_ts = event.get('thread_ts')

        # Process message asynchronously
        async def process():
            await slack_bot.handle_message(event, channel_id, thread_ts)

        # Run async handler
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process())
        except Exception as e:
            logger.error(f"Error processing Slack event: {e}")

    return jsonify({'ok': True})


@app.route('/slack/interact', methods=['POST'])
def slack_interact():
    """
    Handle Slack interactive components

    Buttons, menus, modals, etc.
    """
    # Verify request signature
    timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
    signature = request.headers.get('X-Slack-Signature', '')

    if not slack_bot.verify_request(timestamp, signature, request.data):
        return jsonify({'error': 'Invalid signature'}), 403

    # Parse payload (comes as form data)
    import json
    payload = json.loads(request.form.get('payload', '{}'))

    action_type = payload.get('type')

    if action_type == 'block_actions':
        # Handle button clicks, menu selections
        actions = payload.get('actions', [])
        for action in actions:
            action_id = action.get('action_id')
            # Route to appropriate handler based on action_id
            logger.info(f"Slack action: {action_id}")

    elif action_type == 'view_submission':
        # Handle modal submissions
        view = payload.get('view', {})
        callback_id = view.get('callback_id')
        logger.info(f"Modal submission: {callback_id}")

    return jsonify({'ok': True})


# =============================================================================
# WEBHOOK ENDPOINTS (Invoice System Integration)
# =============================================================================

@app.route('/api/intake', methods=['POST'])
def receive_intake():
    """
    Receive client intake from MWD Invoice System webhook

    Expected headers:
        X-MWD-Signature: HMAC-SHA256 signature
        X-MWD-Event-Type: client.intake.submitted
        Authorization: Bearer <token>

    Expected payload:
        {
            "event_type": "client.intake.submitted",
            "event_id": "uuid",
            "timestamp": "ISO8601",
            "intake_data": { ... },
            "invoice_system_metadata": { ... }
        }
    """
    # Verify webhook signature
    signature = request.headers.get('X-MWD-Signature', '')
    if not invoice_client.verify_webhook_signature(request.data, signature):
        logger.warning("Invalid webhook signature received")
        return jsonify({'error': 'Invalid signature'}), 403

    try:
        data = request.json
        event_type = data.get('event_type')
        intake_data = data.get('intake_data', {})
        metadata = data.get('invoice_system_metadata', {})

        logger.info(f"Received intake webhook: {event_type} for {intake_data.get('company_name')}")

        # Generate AI deliverables
        workflows_triggered = []
        deliverables = {}

        # Generate branding strategy
        branding_result = call_claude(BRANDING_PROMPT, intake_data)
        if branding_result.get('success'):
            deliverables['branding'] = branding_result
            workflows_triggered.append('branding')

        # Generate website plan
        website_result = call_claude(WEBSITE_PROMPT, intake_data)
        if website_result.get('success'):
            deliverables['website'] = website_result
            workflows_triggered.append('website')

        # Generate social media strategy
        social_result = call_claude(SOCIAL_PROMPT, intake_data)
        if social_result.get('success'):
            deliverables['social'] = social_result
            workflows_triggered.append('social')

        # Generate copywriting
        copy_result = call_claude(COPYWRITING_PROMPT, intake_data)
        if copy_result.get('success'):
            deliverables['copywriting'] = copy_result
            workflows_triggered.append('copywriting')

        # Create AI assessment
        ai_assessment = {
            'complexity_score': 7,  # Could be calculated based on services
            'estimated_hours': len(workflows_triggered) * 20,
            'recommended_package': 'premium' if len(intake_data.get('key_services', [])) > 2 else 'standard',
            'ai_generated_summary': f"Client {intake_data.get('company_name')} in {intake_data.get('industry')} seeking {', '.join(intake_data.get('key_services', []))}",
            'deliverables_generated': workflows_triggered
        }

        # Create lead in invoice system (if configured)
        lead_response = {'success': False, 'lead_id': None}
        if invoice_client.is_configured():
            lead_response = invoice_client.create_lead(intake_data, ai_assessment)

            # Attach deliverables to lead
            if lead_response.get('success') and lead_response.get('lead_id'):
                lead_id = lead_response['lead_id']
                for deliverable_type, deliverable_data in deliverables.items():
                    invoice_client.attach_deliverable(lead_id, {
                        'deliverable_type': f'{deliverable_type}_strategy',
                        'generated_at': datetime.utcnow().isoformat(),
                        'ai_model': 'claude-sonnet-4.5',
                        'content': deliverable_data.get('response'),
                        'tokens_used': deliverable_data.get('usage', {})
                    })

        return jsonify({
            'success': True,
            'event_id': data.get('event_id'),
            'lead_id': lead_response.get('lead_id'),
            'workflows_triggered': workflows_triggered,
            'deliverables_count': len(deliverables),
            'ai_assessment': ai_assessment
        })

    except Exception as e:
        logger.error(f"Error processing intake webhook: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/project/status', methods=['POST'])
def receive_project_status():
    """
    Receive project status updates from MWD Invoice System webhook

    Expected payload:
        {
            "event_type": "project.status.changed",
            "event_id": "uuid",
            "timestamp": "ISO8601",
            "project_data": {
                "project_id": "...",
                "lead_id": "...",
                "company_name": "...",
                "old_status": "...",
                "new_status": "...",
                "payment_status": "...",
                ...
            }
        }
    """
    # Verify webhook signature
    signature = request.headers.get('X-MWD-Signature', '')
    if not invoice_client.verify_webhook_signature(request.data, signature):
        logger.warning("Invalid webhook signature received for project status")
        return jsonify({'error': 'Invalid signature'}), 403

    try:
        data = request.json
        event_type = data.get('event_type')
        project_data = data.get('project_data', {})

        logger.info(
            f"Received project status webhook: {project_data.get('company_name')} "
            f"{project_data.get('old_status')} -> {project_data.get('new_status')}"
        )

        # Handle different status transitions
        new_status = project_data.get('new_status')
        actions_taken = []

        if new_status == 'contract_signed':
            # Project officially started - could trigger additional workflows
            actions_taken.append('project_kickoff_initialized')
            logger.info(f"Contract signed for {project_data.get('company_name')}")

        elif new_status == 'payment_received':
            # Payment received - could unlock deliverables
            actions_taken.append('payment_confirmed')
            logger.info(f"Payment received for {project_data.get('company_name')}")

        elif new_status == 'milestone_completed':
            # Milestone completed - could trigger next phase
            actions_taken.append('milestone_acknowledged')
            logger.info(f"Milestone completed for {project_data.get('company_name')}")

        elif new_status == 'project_completed':
            # Project completed - archive and cleanup
            actions_taken.append('project_archived')
            logger.info(f"Project completed for {project_data.get('company_name')}")

        return jsonify({
            'success': True,
            'event_id': data.get('event_id'),
            'project_id': project_data.get('project_id'),
            'new_status': new_status,
            'actions_taken': actions_taken
        })

    except Exception as e:
        logger.error(f"Error processing project status webhook: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("MWD Agent v2.1.0 starting on port 8080")
    print("="*50)

    config = check_config()
    print("\nConfiguration Status:")
    for service, status in config.items():
        icon = '[OK]' if status == 'configured' else '[--]'
        print(f"  {icon} {service}: {status}")

    print("\nStrategy Endpoints:")
    print("  POST /branding, /website, /social, /copywriting")

    print("\nAI Endpoints:")
    print("  Gemini: /ai/gemini/meeting-notes, /summarize, /orchestrate")
    print("  OpenAI: /ai/openai/team-message, /slack-message, /summarize-thread")
    print("  Perplexity: /ai/perplexity/research, /competitors, /client-email")

    print("\nIntegration Endpoints:")
    print("  Notion: /notion/project, /meeting-notes, /search")
    print("  Google: /google/drive/*, /google/docs/*")
    print("  Slack Bot: /slack/events, /slack/interact")

    print("\nWebhook Endpoints:")
    print("  POST /api/intake, /api/project/status")

    print("\n" + "="*50 + "\n")

    app.run(host='0.0.0.0', port=8080, debug=True)
