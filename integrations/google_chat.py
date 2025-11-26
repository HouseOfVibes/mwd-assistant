"""
Google Chat Bot Integration with Gemini Orchestrator
Conversational interface to MWD Assistant via Google Chat
"""

import os
import json
import logging
import hashlib
import hmac
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_CHAT_AVAILABLE = True
except ImportError:
    GOOGLE_CHAT_AVAILABLE = False
    logger.warning("Google API client not installed. Install with: pip install google-api-python-client google-auth")

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GoogleChatBot:
    """Conversational Google Chat bot with Gemini orchestration"""

    def __init__(self, supabase_client=None):
        self.credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON', '')
        self.credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', '')
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', '')

        self.client = None
        self.gemini_client = None
        self.supabase = supabase_client
        self.bot_name = os.getenv('GOOGLE_CHAT_BOT_NAME', 'MWD Assistant')

        # Initialize Google Chat client
        if GOOGLE_CHAT_AVAILABLE:
            self._initialize_chat_client()

        # Initialize Gemini for orchestration
        if GENAI_AVAILABLE:
            api_key = os.getenv('GEMINI_API_KEY', '')
            if api_key:
                self.gemini_client = genai.Client(api_key=api_key)

    def _initialize_chat_client(self):
        """Initialize Google Chat API client"""
        try:
            credentials = None

            # Try JSON credentials first (for cloud deployment)
            if self.credentials_json:
                import json
                creds_dict = json.loads(self.credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=['https://www.googleapis.com/auth/chat.bot']
                )
            # Fall back to file path (for local development)
            elif self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/chat.bot']
                )

            if credentials:
                self.client = build('chat', 'v1', credentials=credentials)
                logger.info("Google Chat client initialized successfully")
            else:
                logger.warning("No Google credentials found for Chat API")

        except Exception as e:
            logger.error(f"Failed to initialize Google Chat client: {e}")

    def is_configured(self) -> bool:
        """Check if bot is properly configured for basic Chat operations"""
        return GOOGLE_CHAT_AVAILABLE and self.client is not None

    def is_fully_configured(self) -> bool:
        """Check if bot is configured with AI orchestration (Gemini)"""
        return self.is_configured() and self.gemini_client is not None

    def verify_request(self, token: str) -> bool:
        """
        Verify Google Chat request using bearer token

        For Google Chat, verification is typically done via:
        1. Bearer token validation
        2. Project number verification in the request
        """
        # Google Chat sends requests with authentication headers
        # The token should match your project's service account
        expected_token = os.getenv('GOOGLE_CHAT_VERIFICATION_TOKEN', '')
        if expected_token and token:
            return hmac.compare_digest(token, expected_token)
        return True  # Skip verification if not configured

    async def handle_event(self, event: Dict) -> Dict[str, Any]:
        """
        Handle incoming Google Chat event

        Event types:
        - ADDED_TO_SPACE: Bot added to a space
        - REMOVED_FROM_SPACE: Bot removed from a space
        - MESSAGE: User sent a message
        - CARD_CLICKED: User clicked a card button

        Args:
            event: Google Chat event data

        Returns:
            Response to send back to Google Chat
        """
        event_type = event.get('type', '')

        if event_type == 'ADDED_TO_SPACE':
            return self._handle_added_to_space(event)

        elif event_type == 'REMOVED_FROM_SPACE':
            return self._handle_removed_from_space(event)

        elif event_type == 'MESSAGE':
            return await self._handle_message(event)

        elif event_type == 'CARD_CLICKED':
            return await self._handle_card_click(event)

        else:
            logger.warning(f"Unknown event type: {event_type}")
            return {}

    def _handle_added_to_space(self, event: Dict) -> Dict[str, Any]:
        """Handle bot being added to a space"""
        space = event.get('space', {})
        space_type = space.get('type', '')
        space_name = space.get('displayName', 'this space')

        if space_type == 'DM':
            welcome_text = (
                f"Hi! I'm the *MWD Assistant* - your AI-powered helper for MW Design Studio.\n\n"
                "I can help you with:\n"
                "- Branding strategy and brand identity\n"
                "- Website design and planning\n"
                "- Social media strategy\n"
                "- Copywriting and messaging\n"
                "- Research and competitor analysis\n"
                "- Meeting notes and action items\n"
                "- Notion workspace management\n\n"
                "Just send me a message to get started!"
            )
        else:
            welcome_text = (
                f"Hi everyone! I'm the *MWD Assistant* and I'm here to help the team.\n\n"
                f"Mention me in {space_name} to ask questions or get help with projects!"
            )

        return self._create_text_response(welcome_text)

    def _handle_removed_from_space(self, event: Dict) -> Dict[str, Any]:
        """Handle bot being removed from a space"""
        # Clean up any space-specific data if needed
        space = event.get('space', {})
        logger.info(f"Bot removed from space: {space.get('name')}")
        return {}

    async def _handle_message(self, event: Dict) -> Dict[str, Any]:
        """Handle incoming message"""
        if not self.is_configured():
            return self._create_text_response(
                "I'm not fully configured yet. Please contact the admin."
            )

        message = event.get('message', {})
        user_message = message.get('text', '').strip()
        sender = message.get('sender', {})
        user_name = sender.get('displayName', 'there')
        user_email = sender.get('email', '')
        space = event.get('space', {})
        thread = message.get('thread', {})

        # Remove bot mention from message if present
        if user_message.startswith(f'@{self.bot_name}'):
            user_message = user_message[len(f'@{self.bot_name}'):].strip()

        # Handle empty messages
        if not user_message:
            return self._create_text_response(
                "I didn't catch that. How can I help you today?"
            )

        # Check for quick commands
        lower_message = user_message.lower()

        if lower_message in ['help', '/help']:
            return self._create_help_card()

        if lower_message in ['menu', '/menu', 'actions', '/actions']:
            return self._create_quick_actions_card()

        if lower_message in ['status', '/status']:
            return self._create_status_card()

        # Check if AI orchestration is available
        if not self.is_fully_configured():
            return self._create_text_response(
                "I'm currently running in limited mode (AI orchestration not configured). "
                "Please contact the admin to set up `GEMINI_API_KEY` for full functionality."
            )

        # Get conversation context from thread if available
        conversation_history = []
        if thread:
            conversation_history = await self._get_thread_history(
                space.get('name', ''),
                thread.get('name', '')
            )

        try:
            # Orchestrate with Gemini
            response = await self._orchestrate_request(
                user_message,
                conversation_history,
                user_email,
                user_name
            )

            # Store conversation in Supabase
            if self.supabase:
                await self._store_conversation(
                    space.get('name', ''),
                    thread.get('name', ''),
                    user_email,
                    user_message,
                    response
                )

            # Format response based on content
            if response.get('actions_taken'):
                return self._create_result_card(response)
            else:
                return self._create_text_response(response.get('message', ''))

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return self._create_text_response(
                f"Sorry, I encountered an error processing your request. Please try again."
            )

    async def _handle_card_click(self, event: Dict) -> Dict[str, Any]:
        """Handle card button clicks"""
        action = event.get('action', {})
        action_name = action.get('actionMethodName', '')
        parameters = {p['key']: p['value'] for p in action.get('parameters', [])}

        user = event.get('user', {})
        space = event.get('space', {})

        logger.info(f"Card action: {action_name} with params: {parameters}")

        # Handle different action types
        if action_name == 'generate_branding':
            return await self._handle_branding_action(parameters, space)

        elif action_name == 'generate_website':
            return await self._handle_website_action(parameters, space)

        elif action_name == 'generate_social':
            return await self._handle_social_action(parameters, space)

        elif action_name == 'research_topic':
            return await self._handle_research_action(parameters, space)

        elif action_name == 'create_client_portal':
            return await self._handle_portal_action(parameters, space)

        elif action_name == 'show_help':
            return self._create_help_card()

        elif action_name == 'show_menu':
            return self._create_quick_actions_card()

        elif action_name.startswith('open_dialog_'):
            dialog_type = action_name.replace('open_dialog_', '')
            return self._create_input_dialog(dialog_type)

        else:
            return self._create_text_response(
                f"Action '{action_name}' received. Processing..."
            )

    async def _orchestrate_request(self, message: str, history: List[Dict],
                                   user_email: str, user_name: str) -> Dict[str, Any]:
        """Use Gemini to orchestrate the request"""

        # Build conversation context
        context_messages = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in history[-10:]
        ])

        # System prompt for MWD Assistant
        system_prompt = """You are the MWD Assistant - the internal AI assistant for MW Design Studio.

## About MW Design Studio
MW Design Studio was founded by Sheri McDowell and Tierra White to empower small businesses with big ideas.
Mission: Help businesses look professional, feel authentic, and grow sustainably.

## The Team

**Sheri McDowell** - Co-Founder
- Expertise: Brand strategy, visual design, identity systems
- Handles: Branding projects, logo design, brand guidelines, website design
- Style: Strategic, detail-oriented, design-focused

**Tierra White** - Co-Founder
- Expertise: Marketing, photography, social media, content creation
- Handles: Social media strategy, content creation, photography, marketing campaigns
- Style: Creative, community-focused, storytelling

## Services & Pricing

**Branding** (from $750)
- Logo design & brand identity
- Color palette & typography
- Brand guidelines
- Social media assets
- Voice & messaging framework

**Website Design** (custom quote)
- Responsive, hand-coded sites
- User journey optimization
- SEO-friendly structure
- Reliable hosting included
- Conversion-focused design

**Social Media** (from $350)
- Platform strategy
- Content creation
- Community management
- Scheduling & analytics
- Engagement strategies

**Content Creation**
- Copywriting (from $250): Brand storytelling, website copy, email sequences
- Photography (from $200): Brand photos, product shots, lifestyle imagery

**Automation Systems** (from $500)
- Lead nurturing workflows
- Appointment scheduling
- Email automation
- CRM setup
- Operations streamlining

## Your Role
You're the team's helpful assistant. You can chat naturally, answer questions, give advice, and execute tasks.
Be casual yet professional - you're talking to teammates (Sheri and Tierra), not clients.
Be proactive and helpful. If you can answer something directly, do it. Only use tools when actually needed.
Know who handles what - route questions to the right person when needed.

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
9. CLIENT_PORTAL - Build comprehensive Notion portals for clients

**Communication:**
10. TEAM_MESSAGE - Draft internal team messages

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
- For Notion operations, include the specific operation in params
- When unsure, ask clarifying questions
- Remember you're helping the MWD team manage their work and clients
"""

        prompt = f"""Previous conversation:
{context_messages}

User ({user_name}): {message}

Analyze this request and provide your orchestration plan."""

        try:
            response = self.gemini_client.models.generate_content(
                model='gemini-2.0-flash',
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
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response_text[start:end])
        except json.JSONDecodeError:
            pass

        return {
            'understanding': 'Could not parse plan',
            'direct_response': response_text
        }

    async def _execute_actions(self, actions: List[Dict]) -> List[Dict]:
        """Execute the planned actions"""
        results = []

        for action in actions:
            action_type = action.get('type', '')
            params = action.get('params', {})

            try:
                if action_type == 'RESEARCH':
                    from integrations.perplexity import PerplexityClient
                    client = PerplexityClient()
                    result = client.research_topic(
                        params.get('topic', ''),
                        params.get('depth', 'comprehensive')
                    )

                elif action_type == 'BRANDING':
                    import requests
                    response = requests.post(
                        'http://localhost:8080/branding',
                        json=params,
                        timeout=60
                    )
                    result = response.json() if response.ok else {'success': False, 'error': response.text}

                elif action_type == 'NOTION':
                    from integrations.notion import NotionClient
                    client = NotionClient()
                    operation = params.get('operation', '')

                    if operation == 'workspace_overview':
                        result = client.workspace_overview()
                    elif operation == 'search':
                        result = client.search(params.get('query', ''))
                    elif operation == 'create_project':
                        result = client.create_project_page(
                            params.get('database_id') or os.getenv('NOTION_PROJECTS_DATABASE', ''),
                            params.get('project_data', {})
                        )
                    else:
                        result = {'success': False, 'error': f'Unknown Notion operation: {operation}'}

                elif action_type == 'CLIENT_PORTAL':
                    from integrations.notion import NotionClient
                    client = NotionClient()
                    parent_page_id = params.get('parent_page_id') or os.getenv('NOTION_PORTALS_PAGE', '')
                    result = client.create_client_portal(parent_page_id, params.get('client_data', {}))

                elif action_type == 'TEAM_MESSAGE':
                    from integrations.openai_client import OpenAIClient
                    client = OpenAIClient()
                    result = client.draft_team_message(
                        params.get('context', ''),
                        params.get('message_type', 'update'),
                        params.get('tone', 'professional')
                    )

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
        results_summary = json.dumps(results, indent=2)

        prompt = f"""Original request: {original_request}

Plan: {json.dumps(plan, indent=2)}

Action results:
{results_summary}

Generate a helpful, conversational response for the user that:
1. Summarizes what was done
2. Presents key findings/outputs clearly
3. Suggests next steps if appropriate
4. Uses simple formatting (bold with *, lists with -)

Keep it concise but informative."""

        response = self.gemini_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=2048,
            )
        )

        return response.text

    async def _get_thread_history(self, space_name: str, thread_name: str) -> List[Dict]:
        """Get conversation history from thread"""
        # For now, return empty - can be expanded to fetch from Supabase
        return []

    async def _store_conversation(self, space_name: str, thread_name: str,
                                  user_email: str, user_message: str,
                                  response: Dict):
        """Store conversation in Supabase"""
        if not self.supabase:
            return

        try:
            self.supabase.table('conversations').insert({
                'space_name': space_name,
                'thread_name': thread_name,
                'user_email': user_email,
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

    # =========================================================================
    # Response Builders - Google Chat Card Format
    # =========================================================================

    def _create_text_response(self, text: str) -> Dict[str, Any]:
        """Create a simple text response"""
        return {'text': text}

    def _create_help_card(self) -> Dict[str, Any]:
        """Create help card with available commands"""
        return {
            'cardsV2': [{
                'cardId': 'help_card',
                'card': {
                    'header': {
                        'title': 'MWD Assistant Help',
                        'subtitle': 'Your AI-powered design studio assistant',
                        'imageUrl': 'https://www.gstatic.com/images/branding/product/2x/chat_48dp.png',
                        'imageType': 'CIRCLE'
                    },
                    'sections': [
                        {
                            'header': 'What I Can Do',
                            'widgets': [
                                {
                                    'decoratedText': {
                                        'startIcon': {'knownIcon': 'STAR'},
                                        'text': '<b>Branding</b> - Generate brand strategies and identity concepts'
                                    }
                                },
                                {
                                    'decoratedText': {
                                        'startIcon': {'knownIcon': 'BOOKMARK'},
                                        'text': '<b>Website</b> - Create website plans and UX recommendations'
                                    }
                                },
                                {
                                    'decoratedText': {
                                        'startIcon': {'knownIcon': 'PERSON'},
                                        'text': '<b>Social Media</b> - Develop social strategies and content calendars'
                                    }
                                },
                                {
                                    'decoratedText': {
                                        'startIcon': {'knownIcon': 'DESCRIPTION'},
                                        'text': '<b>Research</b> - Industry analysis and competitor insights'
                                    }
                                },
                                {
                                    'decoratedText': {
                                        'startIcon': {'knownIcon': 'INVITE'},
                                        'text': '<b>Notion</b> - Manage projects and create client portals'
                                    }
                                }
                            ]
                        },
                        {
                            'header': 'Quick Commands',
                            'widgets': [
                                {
                                    'decoratedText': {
                                        'text': '<b>/menu</b> - Show quick actions menu'
                                    }
                                },
                                {
                                    'decoratedText': {
                                        'text': '<b>/status</b> - Check system status'
                                    }
                                },
                                {
                                    'decoratedText': {
                                        'text': '<b>/help</b> - Show this help message'
                                    }
                                }
                            ]
                        }
                    ]
                }
            }]
        }

    def _create_quick_actions_card(self) -> Dict[str, Any]:
        """Create quick actions menu card"""
        return {
            'cardsV2': [{
                'cardId': 'quick_actions',
                'card': {
                    'header': {
                        'title': 'Quick Actions',
                        'subtitle': 'What would you like to do?'
                    },
                    'sections': [
                        {
                            'header': 'Strategy Generation',
                            'widgets': [
                                {
                                    'buttonList': {
                                        'buttons': [
                                            {
                                                'text': 'Brand Strategy',
                                                'onClick': {
                                                    'action': {
                                                        'function': 'open_dialog_branding'
                                                    }
                                                }
                                            },
                                            {
                                                'text': 'Website Plan',
                                                'onClick': {
                                                    'action': {
                                                        'function': 'open_dialog_website'
                                                    }
                                                }
                                            },
                                            {
                                                'text': 'Social Strategy',
                                                'onClick': {
                                                    'action': {
                                                        'function': 'open_dialog_social'
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        },
                        {
                            'header': 'Research & Analysis',
                            'widgets': [
                                {
                                    'buttonList': {
                                        'buttons': [
                                            {
                                                'text': 'Industry Research',
                                                'onClick': {
                                                    'action': {
                                                        'function': 'open_dialog_research'
                                                    }
                                                }
                                            },
                                            {
                                                'text': 'Competitor Analysis',
                                                'onClick': {
                                                    'action': {
                                                        'function': 'open_dialog_competitors'
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        },
                        {
                            'header': 'Workspace',
                            'widgets': [
                                {
                                    'buttonList': {
                                        'buttons': [
                                            {
                                                'text': 'Create Client Portal',
                                                'onClick': {
                                                    'action': {
                                                        'function': 'open_dialog_portal'
                                                    }
                                                }
                                            },
                                            {
                                                'text': 'Search Notion',
                                                'onClick': {
                                                    'action': {
                                                        'function': 'open_dialog_notion_search'
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            }]
        }

    def _create_status_card(self) -> Dict[str, Any]:
        """Create system status card"""
        from integrations.notion import NotionClient
        from integrations.perplexity import PerplexityClient
        from integrations.openai_client import OpenAIClient

        notion = NotionClient()
        perplexity = PerplexityClient()
        openai = OpenAIClient()

        def status_icon(configured: bool) -> str:
            return "CHECK_CIRCLE" if configured else "ERROR"

        def status_text(configured: bool) -> str:
            return "Connected" if configured else "Not configured"

        return {
            'cardsV2': [{
                'cardId': 'status_card',
                'card': {
                    'header': {
                        'title': 'System Status',
                        'subtitle': f'Last checked: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
                    },
                    'sections': [
                        {
                            'header': 'AI Services',
                            'widgets': [
                                {
                                    'decoratedText': {
                                        'startIcon': {'knownIcon': status_icon(self.is_fully_configured())},
                                        'text': f'<b>Gemini</b> - {status_text(self.is_fully_configured())}'
                                    }
                                },
                                {
                                    'decoratedText': {
                                        'startIcon': {'knownIcon': status_icon(perplexity.is_configured())},
                                        'text': f'<b>Perplexity</b> - {status_text(perplexity.is_configured())}'
                                    }
                                },
                                {
                                    'decoratedText': {
                                        'startIcon': {'knownIcon': status_icon(openai.is_configured())},
                                        'text': f'<b>OpenAI</b> - {status_text(openai.is_configured())}'
                                    }
                                }
                            ]
                        },
                        {
                            'header': 'Integrations',
                            'widgets': [
                                {
                                    'decoratedText': {
                                        'startIcon': {'knownIcon': status_icon(self.is_configured())},
                                        'text': f'<b>Google Chat</b> - {status_text(self.is_configured())}'
                                    }
                                },
                                {
                                    'decoratedText': {
                                        'startIcon': {'knownIcon': status_icon(notion.is_configured())},
                                        'text': f'<b>Notion</b> - {status_text(notion.is_configured())}'
                                    }
                                }
                            ]
                        }
                    ]
                }
            }]
        }

    def _create_result_card(self, response: Dict) -> Dict[str, Any]:
        """Create a card displaying action results"""
        actions = response.get('actions_taken', [])
        message = response.get('message', '')

        widgets = []

        # Add actions summary
        if actions:
            actions_text = ', '.join(actions)
            widgets.append({
                'decoratedText': {
                    'startIcon': {'knownIcon': 'CONFIRMATION_NUMBER_ICON'},
                    'text': f'<b>Actions:</b> {actions_text}'
                }
            })

        # Add main message
        widgets.append({
            'textParagraph': {
                'text': message[:4096]  # Google Chat limit
            }
        })

        return {
            'cardsV2': [{
                'cardId': 'result_card',
                'card': {
                    'header': {
                        'title': 'Task Complete',
                        'subtitle': 'Here are the results'
                    },
                    'sections': [{
                        'widgets': widgets
                    }]
                }
            }]
        }

    def _create_input_dialog(self, dialog_type: str) -> Dict[str, Any]:
        """Create input dialog for various actions"""
        dialogs = {
            'branding': {
                'title': 'Generate Brand Strategy',
                'fields': [
                    {'name': 'company_name', 'label': 'Company Name'},
                    {'name': 'industry', 'label': 'Industry'},
                    {'name': 'target_audience', 'label': 'Target Audience'},
                    {'name': 'brand_values', 'label': 'Brand Values'}
                ]
            },
            'research': {
                'title': 'Industry Research',
                'fields': [
                    {'name': 'topic', 'label': 'Research Topic'},
                    {'name': 'depth', 'label': 'Depth (quick/comprehensive)'}
                ]
            },
            'portal': {
                'title': 'Create Client Portal',
                'fields': [
                    {'name': 'company_name', 'label': 'Company Name'},
                    {'name': 'contact_name', 'label': 'Contact Name'},
                    {'name': 'contact_email', 'label': 'Contact Email'},
                    {'name': 'services', 'label': 'Services (comma-separated)'}
                ]
            }
        }

        config = dialogs.get(dialog_type, dialogs['research'])

        widgets = []
        for field in config['fields']:
            widgets.append({
                'textInput': {
                    'name': field['name'],
                    'label': field['label']
                }
            })

        return {
            'actionResponse': {
                'type': 'DIALOG',
                'dialogAction': {
                    'dialog': {
                        'body': {
                            'header': {
                                'title': config['title']
                            },
                            'sections': [{
                                'widgets': widgets
                            }],
                            'fixedFooter': {
                                'primaryButton': {
                                    'text': 'Submit',
                                    'onClick': {
                                        'action': {
                                            'function': f'submit_{dialog_type}'
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

    # =========================================================================
    # Action Handlers
    # =========================================================================

    async def _handle_branding_action(self, params: Dict, space: Dict) -> Dict:
        """Handle branding generation action"""
        # This would be called from card button clicks
        return self._create_text_response(
            "Starting brand strategy generation... I'll analyze the information and create a comprehensive brand strategy."
        )

    async def _handle_website_action(self, params: Dict, space: Dict) -> Dict:
        """Handle website planning action"""
        return self._create_text_response(
            "Starting website strategy... I'll create a detailed website plan and sitemap."
        )

    async def _handle_social_action(self, params: Dict, space: Dict) -> Dict:
        """Handle social media strategy action"""
        return self._create_text_response(
            "Starting social media strategy... I'll develop a comprehensive social media plan."
        )

    async def _handle_research_action(self, params: Dict, space: Dict) -> Dict:
        """Handle research action"""
        topic = params.get('topic', '')
        if topic:
            from integrations.perplexity import PerplexityClient
            client = PerplexityClient()
            result = client.research_topic(topic, 'comprehensive')

            if result.get('success'):
                return self._create_text_response(
                    f"*Research Results: {topic}*\n\n{result.get('response', '')[:3000]}"
                )

        return self._create_text_response("Please provide a research topic.")

    async def _handle_portal_action(self, params: Dict, space: Dict) -> Dict:
        """Handle client portal creation action"""
        return self._create_text_response(
            "Creating client portal... I'll set up the Notion workspace for the new client."
        )

    # =========================================================================
    # Proactive Messaging
    # =========================================================================

    def send_message(self, space_name: str, text: str = None,
                    card: Dict = None, thread_key: str = None) -> Dict[str, Any]:
        """
        Send a proactive message to a Google Chat space

        Args:
            space_name: The space resource name (e.g., 'spaces/AAAA')
            text: Plain text message
            card: Card message structure
            thread_key: Optional thread key for threading

        Returns:
            API response
        """
        if not self.client:
            return {'success': False, 'error': 'Google Chat client not configured'}

        try:
            message_body = {}

            if text:
                message_body['text'] = text

            if card:
                message_body.update(card)

            request_body = message_body

            if thread_key:
                request_body['thread'] = {'threadKey': thread_key}

            result = self.client.spaces().messages().create(
                parent=space_name,
                body=request_body,
                messageReplyOption='REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD' if thread_key else None
            ).execute()

            return {'success': True, 'message': result}

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {'success': False, 'error': str(e)}

    def send_notification(self, space_name: str, title: str,
                         message: str, icon: str = 'BELL') -> Dict[str, Any]:
        """Send a notification card to a space"""
        card = {
            'cardsV2': [{
                'cardId': f'notification_{datetime.now().timestamp()}',
                'card': {
                    'header': {
                        'title': title,
                        'subtitle': datetime.now().strftime('%Y-%m-%d %H:%M')
                    },
                    'sections': [{
                        'widgets': [{
                            'decoratedText': {
                                'startIcon': {'knownIcon': icon},
                                'text': message
                            }
                        }]
                    }]
                }
            }]
        }

        return self.send_message(space_name, card=card)
