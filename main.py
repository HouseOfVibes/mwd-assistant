#!/usr/bin/env python3
"""
MWD Assistant - Internal AI Assistant for MW Design Studio
Handles branding, website design, social media, copywriting, and workspace management
"""

import os
import hmac
import hashlib
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from anthropic import Anthropic
from integrations.gemini import GeminiClient
from integrations.openai_client import OpenAIClient
from integrations.perplexity import PerplexityClient
from integrations.notion import NotionClient
from integrations.google_chat import GoogleChatBot
from integrations.google_chat_features import GoogleChatFeatures, setup_scheduler
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
notion_client = NotionClient()
chat_bot = GoogleChatBot()

# Initialize Google Chat features with required clients
chat_features = GoogleChatFeatures(
    chat_client=chat_bot.chat_service,
    notion_client=notion_client,
    gemini_client=gemini_client,
    supabase_client=None  # Will be set if Supabase is configured
)

# Set up scheduler for automated tasks (reminders, digests)
scheduler = setup_scheduler(chat_features)

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
        'notion': 'configured' if notion_client.is_configured() else 'optional',
        'google_chat': 'configured' if chat_bot.is_configured() else 'optional',
        'supabase': 'configured' if os.getenv('SUPABASE_URL') else 'optional',
        'email': 'configured' if os.getenv('SMTP_HOST') else 'optional',
        'contact_webhook': 'configured' if os.getenv('CONTACT_WEBHOOK_SECRET') else 'optional',
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
        'service': 'MWD Assistant',
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
                'GET /notion/search',
                'POST /notion/client-portal'
            ],
            'google_chat': [
                'POST /chat/events',
                'POST /chat/reminders',
                'POST /chat/digest',
                'POST /chat/quick-actions'
            ],
            'contact': [
                'POST /api/contact'
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


@app.route('/notion/client-portal', methods=['POST'])
def notion_client_portal():
    """Create a comprehensive client portal in Notion"""
    data = request.json
    parent_page_id = data.get('parent_page_id', os.getenv('NOTION_PORTALS_PAGE', ''))

    if not parent_page_id:
        return jsonify({'success': False, 'error': 'parent_page_id is required or set NOTION_PORTALS_PAGE env var'}), 400

    client_data = {
        'company_name': data.get('company_name', 'New Client'),
        'contact_name': data.get('contact_name', ''),
        'contact_email': data.get('contact_email', ''),
        'services': data.get('services', []),
        'industry': data.get('industry', ''),
        'project_timeline': data.get('project_timeline', ''),
        'budget': data.get('budget', ''),
        'goals': data.get('goals', '')
    }

    result = notion_client.create_client_portal(parent_page_id, client_data)
    return jsonify(result)


# =============================================================================
# GOOGLE CHAT BOT ENDPOINTS
# =============================================================================

@app.route('/chat/events', methods=['POST'])
def chat_events():
    """
    Handle Google Chat Events API

    This endpoint receives all Google Chat events (messages, space events, card clicks)
    and routes them to the appropriate handler.

    Event types:
    - MESSAGE: User sent a message
    - ADDED_TO_SPACE: Bot added to a space or DM
    - REMOVED_FROM_SPACE: Bot removed from a space
    - CARD_CLICKED: User clicked a card button/action
    """
    # Verify request (Google Chat uses bearer token or service account)
    # For production, implement proper Google Cloud IAP or service account verification
    auth_header = request.headers.get('Authorization', '')

    # Get event data
    event = request.json

    if not event:
        return jsonify({'error': 'No event data'}), 400

    event_type = event.get('type', '')
    logger.info(f"Google Chat event received: {event_type}")

    try:
        # Process the event asynchronously
        result = asyncio.run(chat_bot.handle_event(event))
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error processing Google Chat event: {e}")
        return jsonify({
            'text': 'Sorry, I encountered an error processing your request. Please try again.'
        })


# =============================================================================
# GOOGLE CHAT FEATURE ENDPOINTS (Reminders, Digests, Quick Actions)
# =============================================================================

@app.route('/chat/reminders', methods=['POST'])
def chat_send_reminders():
    """Manually trigger deadline reminders"""
    data = request.json or {}
    space = data.get('space', '')
    result = chat_features.send_deadline_reminders(space)
    return jsonify(result)


@app.route('/chat/digest', methods=['POST'])
def chat_send_digest():
    """Manually trigger activity digest"""
    data = request.json or {}
    space = data.get('space', '')
    period = data.get('period', 'daily')
    result = chat_features.send_digest(period, space)
    return jsonify(result)


@app.route('/chat/quick-actions', methods=['POST'])
def chat_quick_actions():
    """Send quick actions menu to a space"""
    data = request.json or {}
    space = data.get('space', '')

    if not space:
        return jsonify({'success': False, 'error': 'Space is required'}), 400

    result = chat_features.send_quick_actions_card(space)
    return jsonify(result)


# =============================================================================
# CONTACT FORM WEBHOOK ENDPOINT
# =============================================================================

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify HMAC-SHA256 signature from webhook

    Args:
        payload: Raw request body bytes
        signature: Signature from X-Webhook-Signature header

    Returns:
        True if signature is valid, False otherwise
    """
    webhook_secret = os.getenv('CONTACT_WEBHOOK_SECRET', '')

    if not webhook_secret:
        logger.warning("Webhook secret not configured, skipping verification")
        return True  # Skip verification if not configured

    if not signature:
        logger.error("No signature provided in webhook request")
        return False

    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature, expected_signature)


def send_email(to_email: str, subject: str, html_body: str, text_body: str = None) -> dict:
    """
    Send email via SMTP

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML content of the email
        text_body: Plain text fallback (optional)

    Returns:
        Success/failure dict
    """
    smtp_host = os.getenv('SMTP_HOST', '')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    from_email = os.getenv('SMTP_FROM_EMAIL', smtp_user)
    from_name = os.getenv('SMTP_FROM_NAME', 'MW Design Studio')

    if not all([smtp_host, smtp_user, smtp_password]):
        logger.warning("SMTP not configured, skipping email")
        return {'success': False, 'error': 'SMTP not configured'}

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = to_email

        # Add plain text part
        if text_body:
            msg.attach(MIMEText(text_body, 'plain'))

        # Add HTML part
        msg.attach(MIMEText(html_body, 'html'))

        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {to_email}")
        return {'success': True, 'to': to_email}

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {'success': False, 'error': str(e)}


def format_deliverables_email(contact_data: dict, deliverables: dict) -> str:
    """Format deliverables as HTML email - FOR INTERNAL TEAM USE"""
    company_name = contact_data.get('company_name', 'Your Company')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #2c3e50; color: white; padding: 30px; text-align: center; }}
            .section {{ margin: 30px 0; padding: 20px; background: #f9f9f9; border-radius: 8px; }}
            .section h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Strategy Deliverables</h1>
                <p>Prepared for {company_name}</p>
            </div>
    """

    section_titles = {
        'branding': 'Brand Strategy',
        'website': 'Website Design Plan',
        'social': 'Social Media Strategy',
        'copywriting': 'Marketing Copy'
    }

    for key, title in section_titles.items():
        if key in deliverables:
            content = deliverables[key].get('response', '')
            content_html = content.replace('\n', '<br>')
            html += f"""
            <div class="section">
                <h2>{title}</h2>
                <div>{content_html}</div>
            </div>
            """

    html += """
            <div class="footer">
                <p>Generated by MWD Assistant</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def format_thank_you_email(contact_data: dict) -> str:
    """Format thank you email for leads - NO deliverables included"""
    contact_name = contact_data.get('contact_name', 'there')
    company_name = contact_data.get('company_name', 'your company')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.8; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header h1 {{ color: #2c3e50; margin-bottom: 10px; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 8px; }}
            .footer {{ text-align: center; padding: 30px 0; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Thank You!</h1>
            </div>
            <div class="content">
                <p>Hi {contact_name},</p>

                <p>Thank you for reaching out to MW Design Studio about {company_name}! We're excited to learn more about your project.</p>

                <p>We've received your information and our team is already reviewing it. <strong>You can expect to hear from us within 24-48 hours.</strong></p>

                <p>In the meantime, feel free to check out some of our recent work at <a href="https://mwdesignstudio.com">mwdesignstudio.com</a>.</p>

                <p>We look forward to connecting with you soon!</p>

                <p>Best,<br>
                <strong>The MW Design Studio Team</strong><br>
                Sheri & Tierra</p>
            </div>
            <div class="footer">
                <p>MW Design Studio | Empowering small businesses with big ideas</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


@app.route('/api/contact', methods=['POST'])
def receive_contact():
    """
    Receive contact form submission from website

    Flow:
    1. Verify webhook signature
    2. Generate AI deliverables (branding, website, social, copywriting)
    3. Send "thank you" email to lead (NO deliverables - just confirmation)
    4. Send notification email to team (contact@mwdesign.agency)
    5. Send FULL deliverables to Slack channel for team review
    6. Return deliverables in response

    Expected headers:
        X-Webhook-Signature: HMAC-SHA256 signature
        Content-Type: application/json

    Expected payload:
        {
            "company_name": "...",
            "contact_name": "...",
            "contact_email": "...",
            "phone": "...",
            "industry": "...",
            "target_audience": "...",
            "key_services": [...],
            "brand_values": [...],
            "project_goals": [...],
            "budget": "...",
            "timeline": "...",
            "message": "..."
        }
    """
    # Verify webhook signature
    signature = request.headers.get('X-Webhook-Signature', '')
    if not verify_webhook_signature(request.data, signature):
        logger.warning("Invalid webhook signature received")
        return jsonify({'error': 'Invalid signature'}), 403

    try:
        contact_data = request.json
        contact_email = contact_data.get('contact_email', '')
        company_name = contact_data.get('company_name', 'Unknown')

        logger.info(f"Received contact form: {company_name} - {contact_email}")

        # Generate AI deliverables
        workflows_triggered = []
        deliverables = {}

        # Generate branding strategy
        branding_result = call_claude(BRANDING_PROMPT, contact_data)
        if branding_result.get('success'):
            deliverables['branding'] = branding_result
            workflows_triggered.append('branding')

        # Generate website plan
        website_result = call_claude(WEBSITE_PROMPT, contact_data)
        if website_result.get('success'):
            deliverables['website'] = website_result
            workflows_triggered.append('website')

        # Generate social media strategy
        social_result = call_claude(SOCIAL_PROMPT, contact_data)
        if social_result.get('success'):
            deliverables['social'] = social_result
            workflows_triggered.append('social')

        # Generate copywriting
        copy_result = call_claude(COPYWRITING_PROMPT, contact_data)
        if copy_result.get('success'):
            deliverables['copywriting'] = copy_result
            workflows_triggered.append('copywriting')

        # Create assessment
        assessment = {
            'complexity_score': 7,
            'estimated_hours': len(workflows_triggered) * 20,
            'recommended_package': 'premium' if len(contact_data.get('key_services', [])) > 2 else 'standard',
            'summary': f"Client {company_name} in {contact_data.get('industry', 'N/A')} seeking {', '.join(contact_data.get('key_services', []))}",
            'deliverables_generated': workflows_triggered
        }

        # Send thank you email to lead (NO deliverables - just confirmation)
        lead_email_sent = False
        if contact_email:
            thank_you_html = format_thank_you_email(contact_data)
            email_result = send_email(
                to_email=contact_email,
                subject=f"Thank You for Contacting MW Design Studio!",
                html_body=thank_you_html,
                text_body=f"Thank you for reaching out! We've received your information and will be in touch within 24-48 hours."
            )
            lead_email_sent = email_result.get('success', False)

        # Send notification email to team (contact@mwdesign.agency)
        team_email_sent = False
        team_email = os.getenv('TEAM_NOTIFICATION_EMAIL', 'contact@mwdesign.agency')
        if team_email:
            team_html = f"""
            <h2>New Contact Form Submission</h2>
            <p><strong>Company:</strong> {company_name}</p>
            <p><strong>Contact:</strong> {contact_data.get('contact_name', 'N/A')} ({contact_email})</p>
            <p><strong>Phone:</strong> {contact_data.get('phone', 'N/A')}</p>
            <p><strong>Industry:</strong> {contact_data.get('industry', 'N/A')}</p>
            <p><strong>Services:</strong> {', '.join(contact_data.get('key_services', []))}</p>
            <p><strong>Budget:</strong> {contact_data.get('budget', 'N/A')}</p>
            <p><strong>Timeline:</strong> {contact_data.get('timeline', 'N/A')}</p>
            <p><strong>Message:</strong> {contact_data.get('message', 'N/A')}</p>
            <hr>
            <p><strong>Deliverables Generated:</strong> {len(deliverables)}</p>
            <p><em>Full deliverables sent to Google Chat space for review.</em></p>
            """
            team_result = send_email(
                to_email=team_email,
                subject=f"New Lead: {company_name} - {contact_data.get('contact_name', 'Unknown')}",
                html_body=team_html,
                text_body=f"New contact form submission from {company_name}"
            )
            team_email_sent = team_result.get('success', False)

        # Send FULL DELIVERABLES to Google Chat for team review
        chat_notified = False
        if chat_bot.is_configured():
            notification_space = os.getenv('GOOGLE_CHAT_NOTIFICATION_SPACE', '')
            if notification_space:
                try:
                    # First message: Lead info summary card
                    lead_card = {
                        "cardsV2": [{
                            "cardId": f"lead_{company_name.replace(' ', '_')}",
                            "card": {
                                "header": {
                                    "title": f"New Lead: {company_name}",
                                    "subtitle": "Contact Form Submission",
                                    "imageUrl": "https://www.gstatic.com/images/icons/material/system/2x/person_add_black_48dp.png",
                                    "imageType": "CIRCLE"
                                },
                                "sections": [
                                    {
                                        "header": "Contact Information",
                                        "widgets": [
                                            {"decoratedText": {"topLabel": "Name", "text": contact_data.get('contact_name', 'N/A')}},
                                            {"decoratedText": {"topLabel": "Email", "text": contact_email}},
                                            {"decoratedText": {"topLabel": "Phone", "text": contact_data.get('phone', 'N/A')}},
                                            {"decoratedText": {"topLabel": "Industry", "text": contact_data.get('industry', 'N/A')}}
                                        ]
                                    },
                                    {
                                        "header": "Project Details",
                                        "widgets": [
                                            {"decoratedText": {"topLabel": "Services", "text": ', '.join(contact_data.get('key_services', []))}},
                                            {"decoratedText": {"topLabel": "Budget", "text": contact_data.get('budget', 'N/A')}},
                                            {"decoratedText": {"topLabel": "Timeline", "text": contact_data.get('timeline', 'N/A')}},
                                            {"decoratedText": {"topLabel": "Message", "text": contact_data.get('message', 'N/A')[:200]}}
                                        ]
                                    },
                                    {
                                        "header": "Status",
                                        "widgets": [
                                            {"decoratedText": {"text": f"Thank you email sent: {'Yes' if lead_email_sent else 'No'}"}},
                                            {"decoratedText": {"text": f"Team email sent: {'Yes' if team_email_sent else 'No'}"}},
                                            {"decoratedText": {"text": f"Deliverables generated: {len(deliverables)}"}}
                                        ]
                                    }
                                ]
                            }
                        }]
                    }
                    chat_bot.send_message(notification_space, lead_card)

                    # Send each deliverable as a separate message for readability
                    deliverable_titles = {
                        'branding': 'Brand Strategy',
                        'website': 'Website Design Plan',
                        'social': 'Social Media Strategy',
                        'copywriting': 'Marketing Copy'
                    }

                    for key, title in deliverable_titles.items():
                        if key in deliverables:
                            content = deliverables[key].get('response', '')
                            # Truncate if too long (max ~4000 chars per message)
                            if len(content) > 3500:
                                content = content[:3500] + "\n\n_[Content truncated - see full version in API response]_"

                            chat_bot.send_message(
                                notification_space,
                                {"text": f"*{title}* for {company_name}\n\n{content}"}
                            )

                    chat_notified = True
                except Exception as e:
                    logger.error(f"Failed to send Google Chat notification: {e}")

        # Return response with generated deliverables
        return jsonify({
            'success': True,
            'message': 'Contact form processed successfully',
            'workflows_triggered': workflows_triggered,
            'deliverables_count': len(deliverables),
            'notifications': {
                'lead_thank_you_email': lead_email_sent,
                'team_email_sent': team_email_sent,
                'chat_deliverables_sent': chat_notified
            },
            'assessment': assessment,
            'deliverables': {
                key: {
                    'content': value.get('response'),
                    'usage': value.get('usage', {})
                }
                for key, value in deliverables.items()
            }
        })

    except Exception as e:
        logger.error(f"Error processing contact form: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("MWD Assistant v2.1.0 starting on port 8080")
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
    print("  Google Chat: /chat/events, /chat/reminders, /chat/digest")

    print("\nContact Form Endpoint:")
    print("  POST /api/contact (generates deliverables + sends email)")

    print("\n" + "="*50 + "\n")

    app.run(host='0.0.0.0', port=8080, debug=True)
