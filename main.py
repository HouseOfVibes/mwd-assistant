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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Initialize Invoice System client
invoice_client = InvoiceSystemClient()

# Configuration check
def check_config():
    """Check which services are configured"""
    config_status = {
        'anthropic': 'configured' if os.getenv('ANTHROPIC_API_KEY') else 'missing',
        'invoice_system': 'configured' if invoice_client.is_configured() else 'optional',
        'supabase': 'configured' if os.getenv('SUPABASE_URL') else 'optional',
        'slack': 'configured' if os.getenv('SLACK_TOKEN') else 'optional'
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
        'version': '1.1.0',
        'config': config,
        'endpoints': {
            'strategy': [
                'POST /branding',
                'POST /website',
                'POST /social',
                'POST /copywriting'
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
    print("MWD Agent v1.1.0 starting on port 8080")
    print("="*50)

    config = check_config()
    print("\nConfiguration Status:")
    for service, status in config.items():
        icon = '[OK]' if status == 'configured' else '[--]'
        print(f"  {icon} {service}: {status}")

    print("\nStrategy Endpoints:")
    print("  POST /branding")
    print("  POST /website")
    print("  POST /social")
    print("  POST /copywriting")

    print("\nWebhook Endpoints (Invoice System):")
    print("  POST /api/intake")
    print("  POST /api/project/status")

    print("\n" + "="*50 + "\n")

    app.run(host='0.0.0.0', port=8080, debug=True)
