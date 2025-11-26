"""
Google Chat Feature Extensions
- Deadline reminders
- Daily/weekly digests
- Quick action cards
- Scheduled notifications
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class GoogleChatFeatures:
    """Extended Google Chat features for MWD Assistant"""

    def __init__(self, chat_client=None, notion_client=None,
                 gemini_client=None, supabase_client=None):
        self.chat = chat_client
        self.notion = notion_client
        self.gemini = gemini_client
        self.supabase = supabase_client
        self.notification_space = os.getenv('GOOGLE_CHAT_NOTIFICATION_SPACE', '')
        self.team_space = os.getenv('GOOGLE_CHAT_TEAM_SPACE', '')
        self.client_profiles_db = os.getenv('NOTION_CLIENT_PROFILES_DB', '')

    # =========================================================================
    # 1. DEADLINE REMINDERS
    # =========================================================================

    def check_upcoming_deadlines(self, days_ahead: int = 3) -> List[Dict]:
        """
        Check Notion for upcoming deadlines

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of projects with upcoming deadlines
        """
        if not self.notion or not self.notion.is_configured():
            return []

        try:
            projects_db = os.getenv('NOTION_PROJECTS_DATABASE', '')
            if not projects_db:
                return []

            # Calculate date range
            today = datetime.now().date()
            end_date = today + timedelta(days=days_ahead)

            # Query Notion for projects with upcoming deadlines
            result = self.notion.query_database(
                projects_db,
                filters={
                    "and": [
                        {
                            "property": "Due Date",
                            "date": {
                                "on_or_before": end_date.isoformat()
                            }
                        },
                        {
                            "property": "Due Date",
                            "date": {
                                "on_or_after": today.isoformat()
                            }
                        },
                        {
                            "property": "Status",
                            "status": {
                                "does_not_equal": "Complete"
                            }
                        }
                    ]
                },
                sorts=[{
                    "property": "Due Date",
                    "direction": "ascending"
                }]
            )

            if not result.get('success'):
                return []

            deadlines = []
            for page in result.get('results', []):
                props = page.get('properties', {})

                # Extract project info
                title_prop = props.get('Name', {}) or props.get('Title', {})
                title = ''
                if title_prop.get('title'):
                    title = title_prop['title'][0].get('plain_text', '') if title_prop['title'] else ''

                due_date_prop = props.get('Due Date', {})
                due_date = due_date_prop.get('date', {}).get('start', '') if due_date_prop else ''

                status_prop = props.get('Status', {})
                status = status_prop.get('status', {}).get('name', '') if status_prop else ''

                client_prop = props.get('Client', {})
                client = ''
                if client_prop.get('relation'):
                    client = 'Linked Client'

                if title and due_date:
                    # Calculate days until deadline
                    deadline_date = datetime.fromisoformat(due_date).date()
                    days_until = (deadline_date - today).days

                    deadlines.append({
                        'title': title,
                        'due_date': due_date,
                        'days_until': days_until,
                        'status': status,
                        'client': client,
                        'page_id': page.get('id'),
                        'url': page.get('url', '')
                    })

            return deadlines

        except Exception as e:
            logger.error(f"Error checking deadlines: {e}")
            return []

    def send_deadline_reminders(self, space_name: str = None) -> Dict[str, Any]:
        """
        Send deadline reminder notifications to Google Chat

        Args:
            space_name: Optional specific space to send to

        Returns:
            Result of sending reminders
        """
        if not self.chat:
            return {'success': False, 'error': 'Google Chat client not configured'}

        target_space = space_name or self.notification_space
        if not target_space:
            return {'success': False, 'error': 'No notification space configured'}

        deadlines = self.check_upcoming_deadlines()

        if not deadlines:
            return {'success': True, 'message': 'No upcoming deadlines'}

        # Group by urgency
        overdue = [d for d in deadlines if d['days_until'] < 0]
        today_due = [d for d in deadlines if d['days_until'] == 0]
        upcoming = [d for d in deadlines if d['days_until'] > 0]

        # Build card
        sections = []

        if overdue:
            widgets = []
            for d in overdue:
                widgets.append({
                    'decoratedText': {
                        'startIcon': {'knownIcon': 'ERROR', 'altText': 'Overdue'},
                        'text': f"<font color=\"#ff0000\"><b>{d['title']}</b></font> - {abs(d['days_until'])} days overdue",
                        'bottomLabel': f"Status: {d['status']}"
                    }
                })
            sections.append({
                'header': 'OVERDUE',
                'widgets': widgets
            })

        if today_due:
            widgets = []
            for d in today_due:
                widgets.append({
                    'decoratedText': {
                        'startIcon': {'knownIcon': 'CLOCK', 'altText': 'Due Today'},
                        'text': f"<font color=\"#ff9800\"><b>{d['title']}</b></font> - Due TODAY",
                        'bottomLabel': f"Status: {d['status']}"
                    }
                })
            sections.append({
                'header': 'DUE TODAY',
                'widgets': widgets
            })

        if upcoming:
            widgets = []
            for d in upcoming[:5]:  # Limit to 5
                widgets.append({
                    'decoratedText': {
                        'startIcon': {'knownIcon': 'BOOKMARK', 'altText': 'Upcoming'},
                        'text': f"<b>{d['title']}</b> - {d['days_until']} day{'s' if d['days_until'] > 1 else ''}",
                        'bottomLabel': f"Due: {d['due_date']} | Status: {d['status']}"
                    }
                })
            sections.append({
                'header': 'UPCOMING',
                'widgets': widgets
            })

        card = {
            'cardsV2': [{
                'cardId': f'deadline_reminder_{datetime.now().timestamp()}',
                'card': {
                    'header': {
                        'title': 'Deadline Reminders',
                        'subtitle': f'{len(deadlines)} items need attention',
                        'imageUrl': 'https://www.gstatic.com/images/branding/product/2x/calendar_48dp.png',
                        'imageType': 'CIRCLE'
                    },
                    'sections': sections
                }
            }]
        }

        return self.chat.send_message(target_space, card=card)

    # =========================================================================
    # 2. DAILY/WEEKLY DIGESTS
    # =========================================================================

    def generate_digest(self, period: str = 'daily') -> Dict[str, Any]:
        """
        Generate activity digest from Notion

        Args:
            period: 'daily' or 'weekly'

        Returns:
            Digest data
        """
        if not self.notion or not self.notion.is_configured():
            return {'success': False, 'error': 'Notion not configured'}

        try:
            # Calculate date range
            today = datetime.now().date()
            if period == 'weekly':
                start_date = today - timedelta(days=7)
            else:
                start_date = today - timedelta(days=1)

            projects_db = os.getenv('NOTION_PROJECTS_DATABASE', '')

            # Get recently updated items
            result = self.notion.query_database(
                projects_db,
                filters={
                    "timestamp": "last_edited_time",
                    "last_edited_time": {
                        "on_or_after": start_date.isoformat()
                    }
                },
                sorts=[{
                    "timestamp": "last_edited_time",
                    "direction": "descending"
                }],
                page_size=20
            ) if projects_db else {'success': False}

            updates = []
            if result.get('success'):
                for page in result.get('results', []):
                    props = page.get('properties', {})

                    title_prop = props.get('Name', {}) or props.get('Title', {})
                    title = ''
                    if title_prop.get('title'):
                        title = title_prop['title'][0].get('plain_text', '') if title_prop['title'] else ''

                    status_prop = props.get('Status', {})
                    status = status_prop.get('status', {}).get('name', '') if status_prop else 'Unknown'

                    if title:
                        updates.append({
                            'title': title,
                            'status': status,
                            'url': page.get('url', '')
                        })

            # Get completed items
            completed_result = self.notion.query_database(
                projects_db,
                filters={
                    "and": [
                        {
                            "property": "Status",
                            "status": {
                                "equals": "Complete"
                            }
                        },
                        {
                            "timestamp": "last_edited_time",
                            "last_edited_time": {
                                "on_or_after": start_date.isoformat()
                            }
                        }
                    ]
                }
            ) if projects_db else {'success': False}

            completed = []
            if completed_result.get('success'):
                for page in completed_result.get('results', []):
                    props = page.get('properties', {})
                    title_prop = props.get('Name', {}) or props.get('Title', {})
                    title = ''
                    if title_prop.get('title'):
                        title = title_prop['title'][0].get('plain_text', '') if title_prop['title'] else ''
                    if title:
                        completed.append(title)

            return {
                'success': True,
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': today.isoformat(),
                'updates': updates,
                'completed': completed,
                'total_updates': len(updates),
                'total_completed': len(completed)
            }

        except Exception as e:
            logger.error(f"Error generating digest: {e}")
            return {'success': False, 'error': str(e)}

    def send_digest(self, period: str = 'daily', space_name: str = None) -> Dict[str, Any]:
        """
        Send activity digest to Google Chat

        Args:
            period: 'daily' or 'weekly'
            space_name: Optional specific space

        Returns:
            Result of sending digest
        """
        if not self.chat:
            return {'success': False, 'error': 'Google Chat client not configured'}

        target_space = space_name or self.team_space or self.notification_space
        if not target_space:
            return {'success': False, 'error': 'No space configured'}

        digest = self.generate_digest(period)
        if not digest.get('success'):
            return digest

        period_label = 'Weekly' if period == 'weekly' else 'Daily'

        sections = []

        # Summary section
        sections.append({
            'widgets': [{
                'columns': {
                    'columnItems': [
                        {
                            'horizontalSizeStyle': 'FILL_AVAILABLE_SPACE',
                            'horizontalAlignment': 'CENTER',
                            'verticalAlignment': 'CENTER',
                            'widgets': [{
                                'decoratedText': {
                                    'topLabel': 'Updates',
                                    'text': f"<b>{digest['total_updates']}</b>",
                                    'startIcon': {'knownIcon': 'DESCRIPTION'}
                                }
                            }]
                        },
                        {
                            'horizontalSizeStyle': 'FILL_AVAILABLE_SPACE',
                            'horizontalAlignment': 'CENTER',
                            'verticalAlignment': 'CENTER',
                            'widgets': [{
                                'decoratedText': {
                                    'topLabel': 'Completed',
                                    'text': f"<b>{digest['total_completed']}</b>",
                                    'startIcon': {'knownIcon': 'CONFIRMATION_NUMBER_ICON'}
                                }
                            }]
                        }
                    ]
                }
            }]
        })

        # Recent updates
        if digest['updates']:
            widgets = []
            for update in digest['updates'][:8]:
                widgets.append({
                    'decoratedText': {
                        'text': f"<b>{update['title']}</b>",
                        'bottomLabel': f"Status: {update['status']}"
                    }
                })
            sections.append({
                'header': 'Recent Activity',
                'widgets': widgets
            })

        # Completed items
        if digest['completed']:
            widgets = []
            for item in digest['completed'][:5]:
                widgets.append({
                    'decoratedText': {
                        'startIcon': {'knownIcon': 'CONFIRMATION_NUMBER_ICON'},
                        'text': item
                    }
                })
            sections.append({
                'header': 'Completed',
                'widgets': widgets
            })

        card = {
            'cardsV2': [{
                'cardId': f'{period}_digest_{datetime.now().timestamp()}',
                'card': {
                    'header': {
                        'title': f'{period_label} Digest',
                        'subtitle': f"{digest['start_date']} to {digest['end_date']}",
                        'imageUrl': 'https://www.gstatic.com/images/branding/product/2x/tasks_48dp.png',
                        'imageType': 'CIRCLE'
                    },
                    'sections': sections
                }
            }]
        }

        return self.chat.send_message(target_space, card=card)

    # =========================================================================
    # 3. QUICK ACTIONS
    # =========================================================================

    def send_quick_actions_menu(self, space_name: str) -> Dict[str, Any]:
        """
        Send quick actions menu card to a space

        Args:
            space_name: Space to send to

        Returns:
            Result of sending
        """
        if not self.chat:
            return {'success': False, 'error': 'Google Chat client not configured'}

        card = {
            'cardsV2': [{
                'cardId': 'quick_actions_menu',
                'card': {
                    'header': {
                        'title': 'MWD Assistant',
                        'subtitle': 'Quick Actions Menu',
                        'imageUrl': 'https://www.gstatic.com/images/branding/product/2x/chat_48dp.png',
                        'imageType': 'CIRCLE'
                    },
                    'sections': [
                        {
                            'header': 'Strategy Generation',
                            'collapsible': False,
                            'widgets': [{
                                'buttonList': {
                                    'buttons': [
                                        {
                                            'text': 'Brand Strategy',
                                            'onClick': {'action': {'function': 'open_dialog_branding'}}
                                        },
                                        {
                                            'text': 'Website Plan',
                                            'onClick': {'action': {'function': 'open_dialog_website'}}
                                        },
                                        {
                                            'text': 'Social Strategy',
                                            'onClick': {'action': {'function': 'open_dialog_social'}}
                                        },
                                        {
                                            'text': 'Copywriting',
                                            'onClick': {'action': {'function': 'open_dialog_copywriting'}}
                                        }
                                    ]
                                }
                            }]
                        },
                        {
                            'header': 'Research & Analysis',
                            'collapsible': False,
                            'widgets': [{
                                'buttonList': {
                                    'buttons': [
                                        {
                                            'text': 'Industry Research',
                                            'onClick': {'action': {'function': 'open_dialog_research'}}
                                        },
                                        {
                                            'text': 'Competitor Analysis',
                                            'onClick': {'action': {'function': 'open_dialog_competitors'}}
                                        },
                                        {
                                            'text': 'Draft Client Email',
                                            'onClick': {'action': {'function': 'open_dialog_email'}}
                                        }
                                    ]
                                }
                            }]
                        },
                        {
                            'header': 'Workspace Management',
                            'collapsible': False,
                            'widgets': [{
                                'buttonList': {
                                    'buttons': [
                                        {
                                            'text': 'Create Client Portal',
                                            'onClick': {'action': {'function': 'open_dialog_portal'}}
                                        },
                                        {
                                            'text': 'Search Notion',
                                            'onClick': {'action': {'function': 'open_dialog_search'}}
                                        },
                                        {
                                            'text': 'Meeting Notes',
                                            'onClick': {'action': {'function': 'open_dialog_meeting_notes'}}
                                        }
                                    ]
                                }
                            }]
                        },
                        {
                            'header': 'Reports',
                            'collapsible': True,
                            'widgets': [{
                                'buttonList': {
                                    'buttons': [
                                        {
                                            'text': 'Daily Digest',
                                            'onClick': {'action': {'function': 'send_daily_digest'}}
                                        },
                                        {
                                            'text': 'Deadline Reminders',
                                            'onClick': {'action': {'function': 'send_reminders'}}
                                        },
                                        {
                                            'text': 'System Status',
                                            'onClick': {'action': {'function': 'show_status'}}
                                        }
                                    ]
                                }
                            }]
                        }
                    ]
                }
            }]
        }

        return self.chat.send_message(space_name, card=card)

    # =========================================================================
    # 4. DIALOG HANDLERS
    # =========================================================================

    def create_dialog(self, dialog_type: str) -> Dict[str, Any]:
        """
        Create input dialog for various actions

        Args:
            dialog_type: Type of dialog to create

        Returns:
            Dialog response structure
        """
        dialogs = {
            'branding': {
                'title': 'Generate Brand Strategy',
                'fields': [
                    {'name': 'company_name', 'label': 'Company Name', 'required': True},
                    {'name': 'industry', 'label': 'Industry', 'required': True},
                    {'name': 'target_audience', 'label': 'Target Audience', 'required': True},
                    {'name': 'brand_values', 'label': 'Core Brand Values'},
                    {'name': 'competitors', 'label': 'Main Competitors'},
                    {'name': 'unique_value', 'label': 'Unique Value Proposition'}
                ],
                'submit_function': 'submit_branding'
            },
            'website': {
                'title': 'Generate Website Plan',
                'fields': [
                    {'name': 'company_name', 'label': 'Company Name', 'required': True},
                    {'name': 'website_type', 'label': 'Website Type (e.g., portfolio, e-commerce)'},
                    {'name': 'target_audience', 'label': 'Target Audience'},
                    {'name': 'key_pages', 'label': 'Key Pages Needed'},
                    {'name': 'features', 'label': 'Special Features Required'}
                ],
                'submit_function': 'submit_website'
            },
            'social': {
                'title': 'Generate Social Media Strategy',
                'fields': [
                    {'name': 'company_name', 'label': 'Company Name', 'required': True},
                    {'name': 'platforms', 'label': 'Target Platforms'},
                    {'name': 'goals', 'label': 'Social Media Goals'},
                    {'name': 'target_audience', 'label': 'Target Audience'},
                    {'name': 'content_themes', 'label': 'Content Themes/Topics'}
                ],
                'submit_function': 'submit_social'
            },
            'research': {
                'title': 'Industry Research',
                'fields': [
                    {'name': 'topic', 'label': 'Research Topic', 'required': True},
                    {'name': 'focus_areas', 'label': 'Specific Focus Areas'},
                    {'name': 'depth', 'label': 'Depth', 'type': 'dropdown',
                     'options': ['Quick Overview', 'Comprehensive Analysis']}
                ],
                'submit_function': 'submit_research'
            },
            'competitors': {
                'title': 'Competitor Analysis',
                'fields': [
                    {'name': 'company_name', 'label': 'Your Company', 'required': True},
                    {'name': 'competitors', 'label': 'Competitors (comma-separated)', 'required': True},
                    {'name': 'industry', 'label': 'Industry'},
                    {'name': 'analysis_focus', 'label': 'Analysis Focus'}
                ],
                'submit_function': 'submit_competitors'
            },
            'email': {
                'title': 'Draft Client Email',
                'fields': [
                    {'name': 'client_name', 'label': 'Client Name', 'required': True},
                    {'name': 'email_type', 'label': 'Email Type', 'type': 'dropdown',
                     'options': ['Update', 'Proposal', 'Follow-up', 'Introduction']},
                    {'name': 'context', 'label': 'Email Context', 'multiline': True}
                ],
                'submit_function': 'submit_email'
            },
            'portal': {
                'title': 'Create Client Portal',
                'fields': [
                    {'name': 'company_name', 'label': 'Company Name', 'required': True},
                    {'name': 'contact_name', 'label': 'Contact Name'},
                    {'name': 'contact_email', 'label': 'Contact Email'},
                    {'name': 'services', 'label': 'Services (comma-separated)'},
                    {'name': 'industry', 'label': 'Industry'},
                    {'name': 'goals', 'label': 'Project Goals'}
                ],
                'submit_function': 'submit_portal'
            },
            'meeting_notes': {
                'title': 'Generate Meeting Notes',
                'fields': [
                    {'name': 'transcript', 'label': 'Meeting Transcript', 'multiline': True, 'required': True},
                    {'name': 'participants', 'label': 'Participants (comma-separated)'},
                    {'name': 'meeting_type', 'label': 'Meeting Type'}
                ],
                'submit_function': 'submit_meeting_notes'
            },
            'search': {
                'title': 'Search Notion',
                'fields': [
                    {'name': 'query', 'label': 'Search Query', 'required': True}
                ],
                'submit_function': 'submit_search'
            }
        }

        config = dialogs.get(dialog_type, dialogs['research'])

        # Build widgets for each field
        widgets = []
        for field in config['fields']:
            if field.get('type') == 'dropdown':
                widgets.append({
                    'selectionInput': {
                        'name': field['name'],
                        'label': field['label'],
                        'type': 'DROPDOWN',
                        'items': [{'text': opt, 'value': opt.lower().replace(' ', '_')}
                                  for opt in field.get('options', [])]
                    }
                })
            else:
                widget = {
                    'textInput': {
                        'name': field['name'],
                        'label': field['label']
                    }
                }
                if field.get('multiline'):
                    widget['textInput']['type'] = 'MULTIPLE_LINE'
                widgets.append(widget)

        return {
            'action_response': {
                'type': 'DIALOG',
                'dialog_action': {
                    'dialog': {
                        'body': {
                            'sections': [{
                                'header': config['title'],
                                'widgets': widgets
                            }],
                            'fixedFooter': {
                                'primaryButton': {
                                    'text': 'Generate',
                                    'onClick': {
                                        'action': {
                                            'function': config['submit_function']
                                        }
                                    }
                                },
                                'secondaryButton': {
                                    'text': 'Cancel',
                                    'onClick': {
                                        'action': {
                                            'function': 'cancel_dialog'
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

    async def handle_dialog_submission(self, action_name: str, form_inputs: Dict,
                                       space: Dict, user: Dict) -> Dict[str, Any]:
        """
        Handle dialog form submission

        Args:
            action_name: The submit action function name
            form_inputs: Form field values
            space: Space info
            user: User info

        Returns:
            Response to send back
        """
        logger.info(f"Dialog submission: {action_name} with inputs: {form_inputs}")

        # Extract form values
        values = {}
        for key, val in form_inputs.items():
            if isinstance(val, dict):
                values[key] = val.get('stringInputs', {}).get('value', [''])[0]
            else:
                values[key] = val

        # Route to appropriate handler
        if action_name == 'submit_branding':
            return await self._process_branding(values, space)

        elif action_name == 'submit_website':
            return await self._process_website(values, space)

        elif action_name == 'submit_social':
            return await self._process_social(values, space)

        elif action_name == 'submit_research':
            return await self._process_research(values, space)

        elif action_name == 'submit_competitors':
            return await self._process_competitors(values, space)

        elif action_name == 'submit_email':
            return await self._process_email(values, space)

        elif action_name == 'submit_portal':
            return await self._process_portal(values, space)

        elif action_name == 'submit_meeting_notes':
            return await self._process_meeting_notes(values, space)

        elif action_name == 'submit_search':
            return await self._process_search(values, space)

        else:
            return {'text': f"Unknown action: {action_name}"}

    async def _process_branding(self, values: Dict, space: Dict) -> Dict:
        """Process branding request"""
        import requests
        try:
            response = requests.post(
                'http://localhost:8080/branding',
                json=values,
                timeout=60
            )
            result = response.json()

            if result.get('success'):
                return {
                    'text': f"*Brand Strategy for {values.get('company_name', 'Client')}*\n\n{result.get('response', '')[:3500]}"
                }
            else:
                return {'text': f"Error generating brand strategy: {result.get('error', 'Unknown error')}"}
        except Exception as e:
            return {'text': f"Error: {str(e)}"}

    async def _process_website(self, values: Dict, space: Dict) -> Dict:
        """Process website planning request"""
        import requests
        try:
            response = requests.post(
                'http://localhost:8080/website',
                json=values,
                timeout=60
            )
            result = response.json()

            if result.get('success'):
                return {
                    'text': f"*Website Plan for {values.get('company_name', 'Client')}*\n\n{result.get('response', '')[:3500]}"
                }
            else:
                return {'text': f"Error generating website plan: {result.get('error', 'Unknown error')}"}
        except Exception as e:
            return {'text': f"Error: {str(e)}"}

    async def _process_social(self, values: Dict, space: Dict) -> Dict:
        """Process social media strategy request"""
        import requests
        try:
            response = requests.post(
                'http://localhost:8080/social',
                json=values,
                timeout=60
            )
            result = response.json()

            if result.get('success'):
                return {
                    'text': f"*Social Media Strategy for {values.get('company_name', 'Client')}*\n\n{result.get('response', '')[:3500]}"
                }
            else:
                return {'text': f"Error generating social strategy: {result.get('error', 'Unknown error')}"}
        except Exception as e:
            return {'text': f"Error: {str(e)}"}

    async def _process_research(self, values: Dict, space: Dict) -> Dict:
        """Process research request"""
        from integrations.perplexity import PerplexityClient
        try:
            client = PerplexityClient()
            depth = 'comprehensive' if 'comprehensive' in values.get('depth', '').lower() else 'quick'
            result = client.research_topic(values.get('topic', ''), depth)

            if result.get('success'):
                return {
                    'text': f"*Research: {values.get('topic', 'Topic')}*\n\n{result.get('response', '')[:3500]}"
                }
            else:
                return {'text': f"Error with research: {result.get('error', 'Unknown error')}"}
        except Exception as e:
            return {'text': f"Error: {str(e)}"}

    async def _process_competitors(self, values: Dict, space: Dict) -> Dict:
        """Process competitor analysis request"""
        from integrations.perplexity import PerplexityClient
        try:
            client = PerplexityClient()
            competitors_list = [c.strip() for c in values.get('competitors', '').split(',')]
            result = client.research_competitors(
                values.get('company_name', ''),
                competitors_list,
                values.get('industry', '')
            )

            if result.get('success'):
                return {
                    'text': f"*Competitor Analysis*\n\n{result.get('response', '')[:3500]}"
                }
            else:
                return {'text': f"Error with analysis: {result.get('error', 'Unknown error')}"}
        except Exception as e:
            return {'text': f"Error: {str(e)}"}

    async def _process_email(self, values: Dict, space: Dict) -> Dict:
        """Process client email draft request"""
        from integrations.perplexity import PerplexityClient
        try:
            client = PerplexityClient()
            result = client.draft_client_email(
                values.get('context', ''),
                values.get('email_type', 'update'),
                values.get('client_name', '')
            )

            if result.get('success'):
                return {
                    'text': f"*Draft Email for {values.get('client_name', 'Client')}*\n\n{result.get('response', '')[:3500]}"
                }
            else:
                return {'text': f"Error drafting email: {result.get('error', 'Unknown error')}"}
        except Exception as e:
            return {'text': f"Error: {str(e)}"}

    async def _process_portal(self, values: Dict, space: Dict) -> Dict:
        """Process client portal creation request"""
        from integrations.notion import NotionClient
        try:
            client = NotionClient()
            parent_page_id = os.getenv('NOTION_PORTALS_PAGE', '')

            if not parent_page_id:
                return {'text': "Error: NOTION_PORTALS_PAGE not configured"}

            services_list = [s.strip() for s in values.get('services', '').split(',') if s.strip()]

            client_data = {
                'company_name': values.get('company_name', 'New Client'),
                'contact_name': values.get('contact_name', ''),
                'contact_email': values.get('contact_email', ''),
                'services': services_list,
                'industry': values.get('industry', ''),
                'goals': values.get('goals', '')
            }

            result = client.create_client_portal(parent_page_id, client_data)

            if result.get('success'):
                return {
                    'text': f"*Client Portal Created*\n\nCompany: {client_data['company_name']}\nPages Created: {result.get('pages_created', 0)}\nPortal URL: {result.get('portal_url', 'N/A')}"
                }
            else:
                return {'text': f"Error creating portal: {result.get('error', 'Unknown error')}"}
        except Exception as e:
            return {'text': f"Error: {str(e)}"}

    async def _process_meeting_notes(self, values: Dict, space: Dict) -> Dict:
        """Process meeting notes request"""
        from integrations.gemini import GeminiClient
        try:
            client = GeminiClient()
            participants = [p.strip() for p in values.get('participants', '').split(',') if p.strip()]
            result = client.generate_meeting_notes(
                values.get('transcript', ''),
                participants
            )

            if result.get('success'):
                return {
                    'text': f"*Meeting Notes*\n\n{result.get('notes', '')[:3500]}"
                }
            else:
                return {'text': f"Error generating notes: {result.get('error', 'Unknown error')}"}
        except Exception as e:
            return {'text': f"Error: {str(e)}"}

    async def _process_search(self, values: Dict, space: Dict) -> Dict:
        """Process Notion search request"""
        from integrations.notion import NotionClient
        try:
            client = NotionClient()
            result = client.search(values.get('query', ''))

            if result.get('success'):
                results_text = []
                for item in result.get('results', [])[:10]:
                    title = item.get('title', 'Untitled')
                    url = item.get('url', '')
                    results_text.append(f"- {title}")

                if results_text:
                    return {
                        'text': f"*Search Results for \"{values.get('query', '')}\"*\n\n" + '\n'.join(results_text)
                    }
                else:
                    return {'text': f"No results found for \"{values.get('query', '')}\""}
            else:
                return {'text': f"Error searching: {result.get('error', 'Unknown error')}"}
        except Exception as e:
            return {'text': f"Error: {str(e)}"}


# =========================================================================
# Scheduler Setup
# =========================================================================

def setup_scheduler(chat_features: GoogleChatFeatures):
    """
    Set up scheduled tasks for reminders and digests

    Requires APScheduler: pip install apscheduler
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning("APScheduler not installed. Scheduled tasks disabled.")
        return None

    scheduler = BackgroundScheduler()

    # Daily deadline reminders at 9 AM
    scheduler.add_job(
        chat_features.send_deadline_reminders,
        CronTrigger(hour=9, minute=0),
        id='daily_reminders',
        name='Daily Deadline Reminders'
    )

    # Daily digest at 6 PM
    scheduler.add_job(
        lambda: chat_features.send_digest(period='daily'),
        CronTrigger(hour=18, minute=0),
        id='daily_digest',
        name='Daily Activity Digest'
    )

    # Weekly digest on Friday at 5 PM
    scheduler.add_job(
        lambda: chat_features.send_digest(period='weekly'),
        CronTrigger(day_of_week='fri', hour=17, minute=0),
        id='weekly_digest',
        name='Weekly Activity Digest'
    )

    scheduler.start()
    logger.info("Scheduler started with reminder and digest jobs")

    return scheduler
