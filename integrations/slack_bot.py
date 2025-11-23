"""
Slack Bot Integration with Gemini Orchestrator
Conversational interface to MWD Agent
"""

import os
import json
import logging
import hashlib
import hmac
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_SDK_AVAILABLE = True
except ImportError:
    SLACK_SDK_AVAILABLE = False
    logger.warning("slack-sdk not installed. Install with: pip install slack-sdk")

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class SlackBot:
    """Conversational Slack bot with Gemini orchestration"""

    def __init__(self, supabase_client=None):
        self.bot_token = os.getenv('SLACK_BOT_TOKEN', '')
        self.signing_secret = os.getenv('SLACK_SIGNING_SECRET', '')
        self.app_token = os.getenv('SLACK_APP_TOKEN', '')

        self.client = None
        self.gemini_client = None
        self.supabase = supabase_client
        self.bot_user_id = None

        # Initialize Slack client
        if SLACK_SDK_AVAILABLE and self.bot_token:
            self.client = WebClient(token=self.bot_token)
            try:
                auth_response = self.client.auth_test()
                self.bot_user_id = auth_response['user_id']
                logger.info(f"Slack bot initialized: {auth_response['user']}")
            except SlackApiError as e:
                logger.error(f"Slack auth failed: {e}")

        # Initialize Gemini for orchestration
        if GENAI_AVAILABLE:
            api_key = os.getenv('GEMINI_API_KEY', '')
            if api_key:
                self.gemini_client = genai.Client(api_key=api_key)

    def is_configured(self) -> bool:
        """Check if bot is properly configured"""
        return (SLACK_SDK_AVAILABLE and
                bool(self.bot_token) and
                self.client is not None and
                self.bot_user_id is not None and  # Ensures auth succeeded
                self.gemini_client is not None)

    def verify_request(self, timestamp: str, signature: str, body: bytes) -> bool:
        """Verify Slack request signature"""
        if not self.signing_secret:
            return True  # Skip verification if not configured

        # Check timestamp to prevent replay attacks
        if abs(time.time() - int(timestamp)) > 60 * 5:
            return False

        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        my_signature = 'v0=' + hmac.new(
            self.signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(my_signature, signature)

    async def handle_message(self, event: Dict, channel_id: str,
                            thread_ts: str = None) -> Dict[str, Any]:
        """
        Handle incoming Slack message

        Args:
            event: Slack event data
            channel_id: Channel where message was sent
            thread_ts: Thread timestamp for conversation context

        Returns:
            Response data
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Slack bot not configured'}

        user_message = event.get('text', '')
        user_id = event.get('user', '')
        message_ts = event.get('ts', '')

        # Remove bot mention from message
        if self.bot_user_id:
            user_message = user_message.replace(f'<@{self.bot_user_id}>', '').strip()

        # Get conversation history for context
        conversation_history = await self._get_conversation_history(
            channel_id,
            thread_ts or message_ts
        )

        # Send thinking indicator
        self._send_reaction(channel_id, message_ts, 'thinking_face')

        try:
            # Orchestrate with Gemini
            response = await self._orchestrate_request(
                user_message,
                conversation_history,
                user_id
            )

            # Send response to Slack
            result = self._send_message(
                channel_id,
                response['message'],
                thread_ts=thread_ts or message_ts
            )

            # Store conversation in Supabase
            if self.supabase:
                await self._store_conversation(
                    channel_id,
                    thread_ts or message_ts,
                    user_id,
                    user_message,
                    response
                )

            # Remove thinking reaction
            self._remove_reaction(channel_id, message_ts, 'thinking_face')
            self._send_reaction(channel_id, message_ts, 'white_check_mark')

            return {'success': True, 'response': response}

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            self._remove_reaction(channel_id, message_ts, 'thinking_face')
            self._send_reaction(channel_id, message_ts, 'x')

            self._send_message(
                channel_id,
                f"Sorry, I encountered an error: {str(e)}",
                thread_ts=thread_ts or message_ts
            )

            return {'success': False, 'error': str(e)}

    async def _orchestrate_request(self, message: str,
                                   history: List[Dict],
                                   user_id: str) -> Dict[str, Any]:
        """
        Use Gemini to orchestrate the request

        Gemini analyzes the request and decides which tools/AIs to use
        """

        # Build conversation context
        context_messages = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in history[-10:]  # Last 10 messages for context
        ])

        # System prompt for MWD Assistant
        system_prompt = """You are the MWD Assistant - the internal AI assistant for MW Design Studio.

## About MW Design Studio
MW Design Studio is a creative agency specializing in:
- Brand Strategy & Identity Design
- Website Design & Development
- Social Media Strategy & Content
- Marketing Copywriting
- Client Project Management

## Your Role
You're the team's helpful assistant. You can chat naturally, answer questions, give advice, and execute tasks.
Be casual yet professional - you're talking to teammates, not clients.
Be proactive and helpful. If you can answer something directly, do it. Only use tools when actually needed.

## Your Capabilities

**AI-Powered Tools:**
1. RESEARCH - Deep industry research, competitor analysis, market trends (via Perplexity)
2. BRANDING - Brand strategy, positioning, identity concepts (via Claude)
3. WEBSITE - Website strategy, UX recommendations, site planning (via Claude)
4. SOCIAL - Social media strategy, content calendars, platform recommendations (via Claude)
5. COPYWRITING - Marketing copy, taglines, messaging (via Claude)
6. CLIENT_EMAIL - Draft professional client emails (via Perplexity)
7. MEETING_NOTES - Process and summarize meeting transcripts (via Gemini)

**Workspace Tools:**
8. NOTION - Search workspace, get overview, query databases, create/update projects, meeting notes
9. GOOGLE_DRIVE - Create folders, project structures, documents
10. CLIENT_PORTAL - Build comprehensive Notion portals for clients

**Communication:**
11. TEAM_MESSAGE - Draft internal team messages (via GPT)

## How to Respond

**For general questions, advice, or conversation:**
Respond directly! You know about design, marketing, project management, client relations. Share your knowledge.

**For tasks that need tools:**
Use the appropriate action(s) to get real data or create things.

**Response Format:**

If you can answer directly (questions, advice, chat, explanations):
{
    "understanding": "What they're asking/saying",
    "actions": [],
    "direct_response": "Your helpful, conversational response. Be natural and informative."
}

If you need to use tools:
{
    "understanding": "What they want to accomplish",
    "actions": [
        {
            "type": "ACTION_TYPE",
            "params": {"key": "value"},
            "reason": "Why this helps"
        }
    ],
    "response_plan": "How to present the results"
}

## Important Notes
- Be conversational and helpful, not robotic
- Answer questions directly when you can - don't always reach for tools
- For Notion operations, include the specific operation in params: "operation": "workspace_overview" / "search" / "query_database" etc.
- When unsure, ask clarifying questions
- Remember you're helping the MWD team manage their work and clients
"""

        prompt = f"""Previous conversation:
{context_messages}

Current request from user: {message}

Analyze this request and provide your orchestration plan."""

        try:
            response = self.gemini_client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                    system_instruction=system_prompt
                )
            )

            # Parse Gemini's orchestration plan
            plan = self._parse_orchestration_plan(response.text)

            # Execute the plan
            if plan.get('direct_response'):
                return {
                    'message': plan['direct_response'],
                    'actions_taken': [],
                    'plan': plan
                }

            # Execute actions and collect results
            results = await self._execute_actions(plan.get('actions', []))

            # Generate final response
            final_response = await self._generate_final_response(
                message, plan, results
            )

            return {
                'message': final_response,
                'actions_taken': [a['type'] for a in plan.get('actions', [])],
                'results': results,
                'plan': plan
            }

        except Exception as e:
            logger.error(f"Orchestration error: {e}")
            raise

    def _parse_orchestration_plan(self, response_text: str) -> Dict:
        """Parse Gemini's JSON response"""
        try:
            # Find JSON in response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response_text[start:end])
        except json.JSONDecodeError:
            pass

        # Fallback - treat as direct response
        return {
            'understanding': 'Could not parse plan',
            'direct_response': response_text
        }

    async def _execute_actions(self, actions: List[Dict]) -> List[Dict]:
        """Execute the planned actions by calling appropriate endpoints"""
        results = []

        for action in actions:
            action_type = action.get('type', '')
            params = action.get('params', {})

            try:
                # Import here to avoid circular imports
                if action_type == 'RESEARCH':
                    from integrations.perplexity import PerplexityClient
                    client = PerplexityClient()
                    result = client.research_topic(
                        params.get('topic', ''),
                        params.get('depth', 'comprehensive')
                    )

                elif action_type == 'BRANDING':
                    from integrations.invoice_system import InvoiceSystemClient
                    # Call internal branding endpoint
                    import requests
                    result = requests.post(
                        'http://localhost:8080/branding',
                        json=params
                    ).json()

                elif action_type == 'COMPETITORS':
                    from integrations.perplexity import PerplexityClient
                    client = PerplexityClient()
                    result = client.research_competitors(
                        params.get('company', ''),
                        params.get('competitors', []),
                        params.get('industry', '')
                    )

                elif action_type == 'TEAM_MESSAGE':
                    from integrations.openai_client import OpenAIClient
                    client = OpenAIClient()
                    result = client.draft_team_message(
                        params.get('context', ''),
                        params.get('message_type', 'update'),
                        params.get('tone', 'professional')
                    )

                elif action_type == 'CLIENT_EMAIL':
                    from integrations.perplexity import PerplexityClient
                    client = PerplexityClient()
                    result = client.draft_client_email(
                        params.get('context', ''),
                        params.get('email_type', 'update'),
                        params.get('client_name', '')
                    )

                elif action_type == 'MEETING_NOTES':
                    from integrations.gemini import GeminiClient
                    client = GeminiClient()
                    result = client.generate_meeting_notes(
                        params.get('transcript', ''),
                        params.get('participants', [])
                    )

                elif action_type == 'NOTION':
                    from integrations.notion import NotionClient
                    client = NotionClient()
                    operation = params.get('operation', '')

                    if operation == 'create_project':
                        result = client.create_project_page(
                            params.get('database_id') or os.getenv('NOTION_PROJECTS_DATABASE', ''),
                            params.get('project_data', {})
                        )
                    elif operation == 'search':
                        result = client.search(
                            params.get('query', ''),
                            params.get('filter_type')
                        )
                    elif operation == 'query_database':
                        result = client.query_database(
                            params.get('database_id') or os.getenv('NOTION_PROJECTS_DATABASE', ''),
                            params.get('filters'),
                            params.get('sorts')
                        )
                    elif operation == 'update_status':
                        result = client.update_project_status(
                            params.get('page_id', ''),
                            params.get('status', ''),
                            params.get('notes')
                        )
                    elif operation == 'create_meeting_notes':
                        result = client.create_meeting_notes(
                            params.get('database_id') or os.getenv('NOTION_MEETINGS_DATABASE', ''),
                            params.get('meeting_data', {})
                        )
                    elif operation == 'workspace_overview':
                        result = client.workspace_overview()
                    else:
                        result = {'success': False, 'error': f'Unknown Notion operation: {operation}'}

                elif action_type == 'GOOGLE_DRIVE':
                    from integrations.google_workspace import GoogleWorkspaceClient
                    client = GoogleWorkspaceClient()
                    if params.get('operation') == 'create_folder':
                        result = client.create_folder(
                            params.get('name', ''),
                            params.get('parent_id')
                        )
                    elif params.get('operation') == 'create_project_structure':
                        result = client.create_project_structure(
                            params.get('project_name', ''),
                            params.get('parent_id')
                        )
                    else:
                        result = {'success': False, 'error': 'Unknown Drive operation'}

                elif action_type == 'CLIENT_PORTAL':
                    from integrations.notion import NotionClient
                    client = NotionClient()
                    parent_page_id = params.get('parent_page_id') or os.getenv('NOTION_PORTALS_PAGE', '')
                    client_data = {
                        'company_name': params.get('company_name', 'New Client'),
                        'contact_name': params.get('contact_name', ''),
                        'contact_email': params.get('contact_email', ''),
                        'services': params.get('services', []),
                        'industry': params.get('industry', ''),
                        'project_timeline': params.get('project_timeline', ''),
                        'budget': params.get('budget', ''),
                        'goals': params.get('goals', '')
                    }
                    result = client.create_client_portal(parent_page_id, client_data)

                else:
                    result = {'success': False, 'error': f'Unknown action: {action_type}'}

                results.append({
                    'action': action_type,
                    'success': result.get('success', True),
                    'result': result
                })

            except Exception as e:
                logger.error(f"Action {action_type} failed: {e}")
                results.append({
                    'action': action_type,
                    'success': False,
                    'error': str(e)
                })

        return results

    async def _generate_final_response(self, original_request: str,
                                       plan: Dict, results: List[Dict]) -> str:
        """Generate user-friendly response from action results"""

        # Build context for response generation
        results_summary = json.dumps(results, indent=2)

        prompt = f"""Original request: {original_request}

Plan: {json.dumps(plan, indent=2)}

Action results:
{results_summary}

Generate a helpful, conversational response for the user that:
1. Summarizes what was done
2. Presents key findings/outputs clearly
3. Suggests next steps if appropriate
4. Uses Slack formatting (bold with *, code blocks with ```)

Keep it concise but informative."""

        response = self.gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=2048,
            )
        )

        return response.text

    async def _get_conversation_history(self, channel_id: str,
                                        thread_ts: str) -> List[Dict]:
        """Get conversation history from thread or Supabase"""
        history = []

        # Try to get from Slack thread
        if self.client:
            try:
                result = self.client.conversations_replies(
                    channel=channel_id,
                    ts=thread_ts,
                    limit=20
                )

                for msg in result.get('messages', []):
                    role = 'assistant' if msg.get('user') == self.bot_user_id else 'user'
                    history.append({
                        'role': role,
                        'content': msg.get('text', ''),
                        'ts': msg.get('ts')
                    })

            except SlackApiError as e:
                logger.error(f"Error getting thread history: {e}")

        return history

    async def _store_conversation(self, channel_id: str, thread_ts: str,
                                  user_id: str, user_message: str,
                                  response: Dict):
        """Store conversation in Supabase for persistence"""
        if not self.supabase:
            return

        try:
            self.supabase.table('conversations').insert({
                'channel_id': channel_id,
                'thread_ts': thread_ts,
                'user_id': user_id,
                'user_message': user_message,
                'assistant_response': response.get('message', ''),
                'actions_taken': response.get('actions_taken', []),
                'metadata': {
                    'plan': response.get('plan', {}),
                    'results': response.get('results', [])
                }
            }).execute()
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")

    def _send_message(self, channel: str, text: str,
                     thread_ts: str = None) -> Dict:
        """Send message to Slack channel"""
        try:
            return self.client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts
            )
        except SlackApiError as e:
            logger.error(f"Error sending message: {e}")
            return {}

    def _send_reaction(self, channel: str, timestamp: str, emoji: str):
        """Add reaction to message"""
        try:
            self.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=emoji
            )
        except SlackApiError:
            pass  # Ignore reaction errors

    def _remove_reaction(self, channel: str, timestamp: str, emoji: str):
        """Remove reaction from message"""
        try:
            self.client.reactions_remove(
                channel=channel,
                timestamp=timestamp,
                name=emoji
            )
        except SlackApiError:
            pass  # Ignore reaction errors
