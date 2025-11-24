"""
Slack Quick Win Features
- Deadline reminders
- Daily/weekly digests
- Quick action buttons
- File upload handling
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_SDK_AVAILABLE = True
except ImportError:
    SLACK_SDK_AVAILABLE = False


class SlackFeatures:
    """Extended Slack features for MWD Assistant"""

    def __init__(self, slack_client: WebClient = None, notion_client=None,
                 gemini_client=None, supabase_client=None, google_client=None):
        self.client = slack_client
        self.notion = notion_client
        self.gemini = gemini_client
        self.supabase = supabase_client
        self.google = google_client
        self.reminder_channel = os.getenv('SLACK_REMINDER_CHANNEL', '')
        self.digest_channel = os.getenv('SLACK_DIGEST_CHANNEL', '')
        self.client_profiles_db = os.getenv('NOTION_CLIENT_PROFILES_DB', '')
        self.client_folders_id = os.getenv('GOOGLE_CLIENT_FOLDERS_ID', '1NFZ6HxW8piSyV6g7gHG_C7xaKJgxyXTP')

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
        if not self.notion:
            logger.warning("Notion client not configured for deadline checks")
            return []

        upcoming = []
        today = datetime.utcnow().date()
        cutoff = today + timedelta(days=days_ahead)

        try:
            # Query Notion for projects with deadlines
            # This assumes a database with a "Deadline" date property
            database_id = os.getenv('NOTION_PROJECTS_DATABASE', '')
            if not database_id:
                return []

            result = self.notion.query_database(
                database_id,
                filters={
                    "and": [
                        {
                            "property": "Deadline",
                            "date": {
                                "on_or_before": cutoff.isoformat()
                            }
                        },
                        {
                            "property": "Deadline",
                            "date": {
                                "on_or_after": today.isoformat()
                            }
                        },
                        {
                            "property": "Status",
                            "status": {
                                "does_not_equal": "Completed"
                            }
                        }
                    ]
                },
                sorts=[{"property": "Deadline", "direction": "ascending"}]
            )

            if result.get('success'):
                for page in result.get('results', []):
                    props = page.get('properties', {})
                    deadline_prop = props.get('Deadline', {}).get('date', {})
                    name_prop = props.get('Name', {}).get('title', [])

                    upcoming.append({
                        'id': page.get('id'),
                        'name': name_prop[0].get('text', {}).get('content', 'Untitled') if name_prop else 'Untitled',
                        'deadline': deadline_prop.get('start', ''),
                        'url': page.get('url', '')
                    })

        except Exception as e:
            logger.error(f"Error checking deadlines: {e}")

        return upcoming

    def send_deadline_reminders(self, channel: str = None) -> Dict[str, Any]:
        """
        Send deadline reminders to Slack

        Args:
            channel: Channel to send reminders (uses default if not specified)

        Returns:
            Result of sending reminders
        """
        if not self.client:
            return {'success': False, 'error': 'Slack client not configured'}

        channel = channel or self.reminder_channel
        if not channel:
            return {'success': False, 'error': 'No reminder channel configured'}

        # Check for deadlines in next 3 days
        upcoming = self.check_upcoming_deadlines(days_ahead=3)

        if not upcoming:
            return {'success': True, 'message': 'No upcoming deadlines'}

        # Build reminder message
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📅 Upcoming Deadlines",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"You have *{len(upcoming)}* deadline(s) in the next 3 days:"
                }
            },
            {"type": "divider"}
        ]

        today = datetime.utcnow().date()

        for item in upcoming:
            deadline_date = datetime.fromisoformat(item['deadline']).date()
            days_until = (deadline_date - today).days

            if days_until == 0:
                urgency = "🔴 *TODAY*"
            elif days_until == 1:
                urgency = "🟠 Tomorrow"
            else:
                urgency = f"🟡 In {days_until} days"

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{item['name']}*\n{urgency} ({item['deadline']})"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View in Notion",
                        "emoji": True
                    },
                    "url": item.get('url', '#'),
                    "action_id": f"view_project_{item['id']}"
                }
            })

        try:
            result = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"📅 {len(upcoming)} upcoming deadline(s)"
            )
            return {'success': True, 'reminders_sent': len(upcoming), 'ts': result.get('ts')}
        except SlackApiError as e:
            logger.error(f"Error sending reminders: {e}")
            return {'success': False, 'error': str(e)}

    # =========================================================================
    # 2. DAILY/WEEKLY DIGEST
    # =========================================================================

    def generate_activity_digest(self, period: str = 'daily') -> Dict[str, Any]:
        """
        Generate activity digest from various sources

        Args:
            period: 'daily' or 'weekly'

        Returns:
            Digest data
        """
        digest = {
            'period': period,
            'generated_at': datetime.utcnow().isoformat(),
            'projects_updated': [],
            'deliverables_created': [],
            'messages_processed': 0,
            'ai_tasks_completed': 0
        }

        # Get time range
        if period == 'weekly':
            since = datetime.utcnow() - timedelta(days=7)
        else:
            since = datetime.utcnow() - timedelta(days=1)

        # Get activity from Supabase if available
        if self.supabase:
            try:
                # Get conversation count
                convos = self.supabase.table('conversations').select('id').gte(
                    'created_at', since.isoformat()
                ).execute()
                digest['messages_processed'] = len(convos.data) if convos.data else 0

                # Get deliverables created (if tracking table exists)
                # deliverables = self.supabase.table('deliverables')...

            except Exception as e:
                logger.error(f"Error getting digest data from Supabase: {e}")

        # Get project updates from Notion
        if self.notion:
            try:
                database_id = os.getenv('NOTION_PROJECTS_DATABASE', '')
                if database_id:
                    result = self.notion.query_database(
                        database_id,
                        filters={
                            "property": "Last edited time",
                            "date": {
                                "on_or_after": since.isoformat()
                            }
                        }
                    )
                    if result.get('success'):
                        for page in result.get('results', []):
                            props = page.get('properties', {})
                            name_prop = props.get('Name', {}).get('title', [])
                            name = name_prop[0].get('text', {}).get('content', 'Untitled') if name_prop else 'Untitled'
                            digest['projects_updated'].append(name)
            except Exception as e:
                logger.error(f"Error getting Notion updates: {e}")

        return digest

    def send_digest(self, channel: str = None, period: str = 'daily') -> Dict[str, Any]:
        """
        Send activity digest to Slack

        Args:
            channel: Channel to send digest
            period: 'daily' or 'weekly'

        Returns:
            Result of sending digest
        """
        if not self.client:
            return {'success': False, 'error': 'Slack client not configured'}

        channel = channel or self.digest_channel
        if not channel:
            return {'success': False, 'error': 'No digest channel configured'}

        digest = self.generate_activity_digest(period)

        # Build digest message
        period_emoji = "📊" if period == 'daily' else "📈"
        period_title = "Daily" if period == 'daily' else "Weekly"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{period_emoji} {period_title} Activity Digest",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Messages Processed:*\n{digest['messages_processed']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Projects Updated:*\n{len(digest['projects_updated'])}"
                    }
                ]
            }
        ]

        # Add project list if any were updated
        if digest['projects_updated']:
            project_list = "\n".join([f"• {p}" for p in digest['projects_updated'][:10]])
            if len(digest['projects_updated']) > 10:
                project_list += f"\n_...and {len(digest['projects_updated']) - 10} more_"

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Updated Projects:*\n{project_list}"
                }
            })

        # Add quick actions
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📋 View All Projects",
                        "emoji": True
                    },
                    "action_id": "view_all_projects"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📅 Check Deadlines",
                        "emoji": True
                    },
                    "action_id": "check_deadlines"
                }
            ]
        })

        try:
            result = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"{period_emoji} {period_title} Digest: {digest['messages_processed']} messages, {len(digest['projects_updated'])} projects"
            )
            return {'success': True, 'digest': digest, 'ts': result.get('ts')}
        except SlackApiError as e:
            logger.error(f"Error sending digest: {e}")
            return {'success': False, 'error': str(e)}

    # =========================================================================
    # 3. QUICK ACTION BUTTONS
    # =========================================================================

    def send_quick_actions_menu(self, channel: str, thread_ts: str = None) -> Dict[str, Any]:
        """
        Send a quick actions menu to Slack

        Args:
            channel: Channel to send menu
            thread_ts: Optional thread timestamp

        Returns:
            Result of sending menu
        """
        if not self.client:
            return {'success': False, 'error': 'Slack client not configured'}

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Quick Actions* - What would you like to do?"
                }
            },
            {
                "type": "actions",
                "block_id": "quick_actions_row_1",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🎨 New Branding",
                            "emoji": True
                        },
                        "style": "primary",
                        "action_id": "quick_branding",
                        "value": "branding"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🌐 Website Plan",
                            "emoji": True
                        },
                        "action_id": "quick_website",
                        "value": "website"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📱 Social Strategy",
                            "emoji": True
                        },
                        "action_id": "quick_social",
                        "value": "social"
                    }
                ]
            },
            {
                "type": "actions",
                "block_id": "quick_actions_row_2",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔍 Research Topic",
                            "emoji": True
                        },
                        "action_id": "quick_research",
                        "value": "research"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📝 Meeting Notes",
                            "emoji": True
                        },
                        "action_id": "quick_meeting_notes",
                        "value": "meeting_notes"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✉️ Draft Email",
                            "emoji": True
                        },
                        "action_id": "quick_email",
                        "value": "email"
                    }
                ]
            },
            {
                "type": "actions",
                "block_id": "quick_actions_row_3",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📁 Create Project Folder",
                            "emoji": True
                        },
                        "action_id": "quick_project_folder",
                        "value": "project_folder"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📊 Competitor Analysis",
                            "emoji": True
                        },
                        "action_id": "quick_competitors",
                        "value": "competitors"
                    }
                ]
            },
            {
                "type": "actions",
                "block_id": "quick_actions_row_4",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🏢 Build Client Portal",
                            "emoji": True
                        },
                        "style": "primary",
                        "action_id": "quick_client_portal",
                        "value": "client_portal"
                    }
                ]
            }
        ]

        try:
            result = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text="Quick Actions Menu",
                thread_ts=thread_ts
            )
            return {'success': True, 'ts': result.get('ts')}
        except SlackApiError as e:
            logger.error(f"Error sending quick actions: {e}")
            return {'success': False, 'error': str(e)}

    def handle_quick_action(self, action_id: str, user_id: str,
                           channel: str, trigger_id: str) -> Dict[str, Any]:
        """
        Handle quick action button press

        Opens a modal for user input based on the action

        Args:
            action_id: The action that was triggered
            user_id: User who clicked
            channel: Channel where action occurred
            trigger_id: Slack trigger ID for opening modals

        Returns:
            Result of handling the action
        """
        if not self.client:
            return {'success': False, 'error': 'Slack client not configured'}

        # Map action IDs to modal configurations
        modal_configs = {
            'quick_branding': {
                'title': 'New Branding Strategy',
                'callback_id': 'modal_branding',
                'fields': [
                    {'id': 'company_name', 'label': 'Company Name', 'type': 'text'},
                    {'id': 'industry', 'label': 'Industry', 'type': 'text'},
                    {'id': 'target_audience', 'label': 'Target Audience', 'type': 'text'},
                    {'id': 'key_values', 'label': 'Key Brand Values', 'type': 'textarea'}
                ]
            },
            'quick_website': {
                'title': 'Website Plan',
                'callback_id': 'modal_website',
                'fields': [
                    {'id': 'company_name', 'label': 'Company Name', 'type': 'text'},
                    {'id': 'website_goal', 'label': 'Primary Website Goal', 'type': 'text'},
                    {'id': 'key_pages', 'label': 'Key Pages Needed', 'type': 'textarea'}
                ]
            },
            'quick_social': {
                'title': 'Social Media Strategy',
                'callback_id': 'modal_social',
                'fields': [
                    {'id': 'company_name', 'label': 'Company Name', 'type': 'text'},
                    {'id': 'platforms', 'label': 'Preferred Platforms', 'type': 'text'},
                    {'id': 'goals', 'label': 'Social Media Goals', 'type': 'textarea'}
                ]
            },
            'quick_research': {
                'title': 'Research Topic',
                'callback_id': 'modal_research',
                'fields': [
                    {'id': 'topic', 'label': 'Research Topic', 'type': 'text'},
                    {'id': 'depth', 'label': 'Depth', 'type': 'select',
                     'options': ['quick', 'moderate', 'comprehensive']}
                ]
            },
            'quick_meeting_notes': {
                'title': 'Generate Meeting Notes',
                'callback_id': 'modal_meeting_notes',
                'fields': [
                    {'id': 'transcript', 'label': 'Meeting Transcript', 'type': 'textarea'},
                    {'id': 'participants', 'label': 'Participants (comma-separated)', 'type': 'text'}
                ]
            },
            'quick_email': {
                'title': 'Draft Client Email',
                'callback_id': 'modal_email',
                'fields': [
                    {'id': 'client_name', 'label': 'Client Name', 'type': 'text'},
                    {'id': 'email_type', 'label': 'Email Type', 'type': 'select',
                     'options': ['update', 'proposal', 'follow-up', 'introduction']},
                    {'id': 'context', 'label': 'Email Context', 'type': 'textarea'}
                ]
            },
            'quick_project_folder': {
                'title': 'Create Project Folder',
                'callback_id': 'modal_project_folder',
                'fields': [
                    {'id': 'project_name', 'label': 'Project Name', 'type': 'text'}
                ]
            },
            'quick_competitors': {
                'title': 'Competitor Analysis',
                'callback_id': 'modal_competitors',
                'fields': [
                    {'id': 'company', 'label': 'Your Company', 'type': 'text'},
                    {'id': 'competitors', 'label': 'Competitors (comma-separated)', 'type': 'text'},
                    {'id': 'industry', 'label': 'Industry', 'type': 'text'}
                ]
            },
            'quick_client_portal': {
                'title': 'Build Client Portal',
                'callback_id': 'modal_client_portal',
                'fields': [
                    {'id': 'company_name', 'label': 'Company Name', 'type': 'text'},
                    {'id': 'contact_name', 'label': 'Contact Name', 'type': 'text'},
                    {'id': 'contact_email', 'label': 'Contact Email', 'type': 'text'},
                    {'id': 'industry', 'label': 'Industry', 'type': 'text'},
                    {'id': 'services', 'label': 'Services (comma-separated: branding, website, social, copywriting)', 'type': 'text'},
                    {'id': 'project_timeline', 'label': 'Project Timeline', 'type': 'text'},
                    {'id': 'goals', 'label': 'Goals & Objectives', 'type': 'textarea'}
                ]
            }
        }

        config = modal_configs.get(action_id)
        if not config:
            return {'success': False, 'error': f'Unknown action: {action_id}'}

        # Build modal blocks
        modal_blocks = []
        for field in config['fields']:
            if field['type'] == 'text':
                modal_blocks.append({
                    "type": "input",
                    "block_id": field['id'],
                    "element": {
                        "type": "plain_text_input",
                        "action_id": f"input_{field['id']}"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": field['label']
                    }
                })
            elif field['type'] == 'textarea':
                modal_blocks.append({
                    "type": "input",
                    "block_id": field['id'],
                    "element": {
                        "type": "plain_text_input",
                        "multiline": True,
                        "action_id": f"input_{field['id']}"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": field['label']
                    }
                })
            elif field['type'] == 'select':
                modal_blocks.append({
                    "type": "input",
                    "block_id": field['id'],
                    "element": {
                        "type": "static_select",
                        "action_id": f"input_{field['id']}",
                        "options": [
                            {
                                "text": {"type": "plain_text", "text": opt},
                                "value": opt
                            }
                            for opt in field.get('options', [])
                        ]
                    },
                    "label": {
                        "type": "plain_text",
                        "text": field['label']
                    }
                })

        # Open modal
        try:
            result = self.client.views_open(
                trigger_id=trigger_id,
                view={
                    "type": "modal",
                    "callback_id": config['callback_id'],
                    "title": {
                        "type": "plain_text",
                        "text": config['title'][:24]  # Slack limit
                    },
                    "submit": {
                        "type": "plain_text",
                        "text": "Generate"
                    },
                    "close": {
                        "type": "plain_text",
                        "text": "Cancel"
                    },
                    "private_metadata": channel,  # Store channel for response
                    "blocks": modal_blocks
                }
            )
            return {'success': True, 'view_id': result.get('view', {}).get('id')}
        except SlackApiError as e:
            logger.error(f"Error opening modal: {e}")
            return {'success': False, 'error': str(e)}

    # =========================================================================
    # 4. FILE UPLOAD HANDLING & GOOGLE DRIVE INTEGRATION
    # =========================================================================

    def get_channel_name(self, channel_id: str) -> str:
        """Get channel name from channel ID"""
        if not self.client:
            return ''
        try:
            result = self.client.conversations_info(channel=channel_id)
            return result.get('channel', {}).get('name', '')
        except SlackApiError as e:
            logger.error(f"Error getting channel info: {e}")
            return ''

    def download_slack_file(self, file_url: str) -> Optional[bytes]:
        """
        Download a file from Slack

        Args:
            file_url: The url_private from file info

        Returns:
            File content as bytes or None if failed
        """
        if not self.client:
            return None

        try:
            token = os.getenv('SLACK_BOT_TOKEN', '')
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(file_url, headers=headers)

            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Failed to download file: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error downloading Slack file: {e}")
            return None

    async def handle_file_upload(self, event: Dict, channel_id: str) -> Dict[str, Any]:
        """
        Handle file uploads in Slack with Google Drive integration

        For images/videos in client channels, prompts for content type
        and uploads to Google Drive.

        Args:
            event: Slack event containing file info
            channel_id: Channel where file was uploaded

        Returns:
            Result of processing the file
        """
        if not self.client:
            return {'success': False, 'error': 'Slack client not configured'}

        files = event.get('files', [])
        if not files:
            return {'success': False, 'error': 'No files in event'}

        # Get channel name to check if it's a client channel
        channel_name = self.get_channel_name(channel_id)
        logger.info(f"File upload in channel: {channel_name}")

        # Check if this is a client channel with Drive integration
        client_profile = None
        if self.notion and self.client_profiles_db and channel_name:
            client_profile = self.notion.get_client_profile_by_channel(
                self.client_profiles_db,
                channel_name
            )
            if client_profile.get('success'):
                logger.info(f"Found client profile: {client_profile.get('client_name')}")

        # Filter for media files (images/videos)
        media_files = [
            f for f in files
            if f.get('filetype', '') in ['png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'webm', 'm4v']
        ]

        # If we have a client profile and media files, use Drive upload flow
        if client_profile and client_profile.get('success') and media_files:
            return await self._handle_drive_upload_flow(
                event, channel_id, media_files, client_profile
            )

        # Otherwise, use the standard file handling flow
        return await self._handle_standard_file_upload(event, channel_id, files)

    async def _handle_drive_upload_flow(self, event: Dict, channel_id: str,
                                        files: List[Dict], client_profile: Dict) -> Dict[str, Any]:
        """
        Handle file upload flow with Google Drive integration

        Args:
            event: Slack event
            channel_id: Channel ID
            files: List of media files
            client_profile: Client profile from Notion

        Returns:
            Result of processing
        """
        client_name = client_profile.get('client_name', 'Unknown')
        content_types = client_profile.get('content_types', [])
        file_count = len(files)
        file_type = 'image' if files[0].get('filetype') in ['png', 'jpg', 'jpeg', 'gif', 'webp'] else 'video'
        file_word = f"{file_count} {file_type}{'s' if file_count > 1 else ''}"

        # Build file IDs list for the action value
        file_ids = [f.get('id') for f in files]
        file_data = json.dumps({
            'file_ids': file_ids,
            'client_name': client_name,
            'drive_folder_id': client_profile.get('drive_folder_id', ''),
            'channel_id': channel_id
        })

        # Build content type buttons
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📸 Got {file_word} for *{client_name}*. What type of content?"
                }
            }
        ]

        # Create buttons for content types (max 5 per row)
        if content_types:
            button_elements = []
            for i, content_type in enumerate(content_types[:10]):  # Max 10 options
                button_elements.append({
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": content_type[:24],  # Slack limit
                        "emoji": True
                    },
                    "action_id": f"drive_upload_type_{i}",
                    "value": json.dumps({
                        'content_type': content_type,
                        'file_data': file_data
                    })
                })

                # Add row every 5 buttons
                if len(button_elements) == 5:
                    blocks.append({
                        "type": "actions",
                        "elements": button_elements
                    })
                    button_elements = []

            # Add remaining buttons
            if button_elements:
                blocks.append({
                    "type": "actions",
                    "elements": button_elements
                })

        # Add "Other" option
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Other...",
                        "emoji": True
                    },
                    "action_id": "drive_upload_other",
                    "value": file_data
                }
            ]
        })

        try:
            message_ts = event.get('ts', '')
            thread_ts = event.get('thread_ts', message_ts)

            self.client.chat_postMessage(
                channel=channel_id,
                blocks=blocks,
                text=f"Got {file_word} for {client_name}. What type of content?",
                thread_ts=thread_ts
            )

            return {
                'success': True,
                'action': 'drive_upload_prompt',
                'files_count': len(files),
                'client': client_name
            }

        except SlackApiError as e:
            logger.error(f"Error sending Drive upload prompt: {e}")
            return {'success': False, 'error': str(e)}

    async def _handle_standard_file_upload(self, event: Dict, channel_id: str,
                                           files: List[Dict]) -> Dict[str, Any]:
        """
        Handle standard file upload flow (non-Drive)

        Args:
            event: Slack event
            channel_id: Channel ID
            files: List of files

        Returns:
            Result of processing
        """
        results = []

        for file_info in files:
            file_id = file_info.get('id')
            file_name = file_info.get('name', 'unknown')
            file_type = file_info.get('filetype', '')

            logger.info(f"Processing uploaded file: {file_name} ({file_type})")

            # Determine response based on file type
            if file_type in ['pdf', 'doc', 'docx', 'txt', 'md']:
                response_text = (
                    f"📄 I received *{file_name}*\n\n"
                    "I can help you with this document. Would you like me to:\n"
                    "• Summarize the content\n"
                    "• Extract key points\n"
                    "• Generate meeting notes (if it's a transcript)\n\n"
                    "_Reply with what you'd like me to do._"
                )
            elif file_type in ['csv', 'xlsx', 'xls']:
                response_text = (
                    f"📊 I received *{file_name}*\n\n"
                    "I can help analyze this data. Tell me what insights you're looking for."
                )
            elif file_type in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                response_text = (
                    f"🖼️ I received *{file_name}*\n\n"
                    "Let me know what you'd like me to do with it."
                )
            elif file_type in ['mp3', 'mp4', 'wav', 'm4a', 'webm']:
                response_text = (
                    f"🎥 I received *{file_name}*\n\n"
                    "If this is a recording, I can help generate notes from a transcript."
                )
            else:
                response_text = (
                    f"📎 I received *{file_name}*\n\n"
                    "Let me know if you'd like me to do anything with it."
                )

            message_ts = event.get('ts', '')
            thread_ts = event.get('thread_ts', message_ts)

            try:
                blocks = [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": response_text
                    }
                }]

                # Add action buttons for documents
                if file_type in ['pdf', 'doc', 'docx', 'txt', 'md']:
                    blocks.append({
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "📝 Summarize",
                                    "emoji": True
                                },
                                "action_id": f"file_summarize_{file_id}",
                                "value": file_id
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "🎯 Key Points",
                                    "emoji": True
                                },
                                "action_id": f"file_keypoints_{file_id}",
                                "value": file_id
                            }
                        ]
                    })

                self.client.chat_postMessage(
                    channel=channel_id,
                    blocks=blocks,
                    text=f"Received file: {file_name}",
                    thread_ts=thread_ts
                )

                results.append({
                    'file_id': file_id,
                    'file_name': file_name,
                    'success': True
                })

            except SlackApiError as e:
                logger.error(f"Error responding to file upload: {e}")
                results.append({
                    'file_id': file_id,
                    'file_name': file_name,
                    'success': False,
                    'error': str(e)
                })

        return {
            'success': True,
            'files_processed': len(results),
            'results': results
        }

    def handle_drive_upload_action(self, action_id: str, action_value: str,
                                   channel_id: str, user_id: str,
                                   message_ts: str, trigger_id: str = None) -> Dict[str, Any]:
        """
        Handle content type selection for Drive upload

        Args:
            action_id: The action ID (drive_upload_type_X or drive_upload_other)
            action_value: JSON string with file data and content type
            channel_id: Channel ID
            user_id: User who clicked
            message_ts: Message timestamp
            trigger_id: Trigger ID for modals

        Returns:
            Result of the upload
        """
        if not self.client or not self.google:
            return {'success': False, 'error': 'Required clients not configured'}

        try:
            # Handle "Other" option - open modal for custom description
            if action_id == 'drive_upload_other':
                if not trigger_id:
                    return {'success': False, 'error': 'Trigger ID required for modal'}

                file_data = action_value
                return self._open_custom_content_type_modal(trigger_id, file_data, channel_id)

            # Parse the action value
            data = json.loads(action_value)
            content_type = data.get('content_type', 'Uploads')
            file_data = json.loads(data.get('file_data', '{}'))

            return self._execute_drive_upload(
                file_data=file_data,
                content_type=content_type,
                channel_id=channel_id,
                message_ts=message_ts
            )

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing action value: {e}")
            return {'success': False, 'error': 'Invalid action data'}
        except Exception as e:
            logger.error(f"Error handling Drive upload action: {e}")
            return {'success': False, 'error': str(e)}

    def _open_custom_content_type_modal(self, trigger_id: str, file_data: str,
                                        channel_id: str) -> Dict[str, Any]:
        """Open modal for custom content type description"""
        try:
            self.client.views_open(
                trigger_id=trigger_id,
                view={
                    "type": "modal",
                    "callback_id": "modal_drive_upload_custom",
                    "title": {
                        "type": "plain_text",
                        "text": "Describe Content"
                    },
                    "submit": {
                        "type": "plain_text",
                        "text": "Upload"
                    },
                    "close": {
                        "type": "plain_text",
                        "text": "Cancel"
                    },
                    "private_metadata": json.dumps({
                        'file_data': file_data,
                        'channel_id': channel_id
                    }),
                    "blocks": [
                        {
                            "type": "input",
                            "block_id": "content_description",
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "input_description",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "e.g., Youth Group Event Photos"
                                }
                            },
                            "label": {
                                "type": "plain_text",
                                "text": "What are these of?"
                            }
                        }
                    ]
                }
            )
            return {'success': True, 'action': 'modal_opened'}
        except SlackApiError as e:
            logger.error(f"Error opening modal: {e}")
            return {'success': False, 'error': str(e)}

    def handle_custom_content_type_submission(self, view: Dict) -> Dict[str, Any]:
        """
        Handle submission of custom content type modal

        Args:
            view: The modal view data

        Returns:
            Result of the upload
        """
        try:
            # Get the description from the modal
            values = view.get('state', {}).get('values', {})
            description = values.get('content_description', {}).get('input_description', {}).get('value', 'Uploads')

            # Get the file data from private_metadata
            metadata = json.loads(view.get('private_metadata', '{}'))
            file_data = json.loads(metadata.get('file_data', '{}'))
            channel_id = metadata.get('channel_id', '')

            return self._execute_drive_upload(
                file_data=file_data,
                content_type=description,
                channel_id=channel_id,
                message_ts=None
            )

        except Exception as e:
            logger.error(f"Error handling custom content type: {e}")
            return {'success': False, 'error': str(e)}

    def _execute_drive_upload(self, file_data: Dict, content_type: str,
                              channel_id: str, message_ts: str = None) -> Dict[str, Any]:
        """
        Execute the actual upload to Google Drive

        Args:
            file_data: Dict with file_ids, client_name, drive_folder_id
            content_type: The content type/description
            channel_id: Channel to post confirmation
            message_ts: Optional message to update

        Returns:
            Upload result
        """
        if not self.google:
            return {'success': False, 'error': 'Google client not configured'}

        file_ids = file_data.get('file_ids', [])
        client_name = file_data.get('client_name', 'Unknown')
        drive_folder_id = file_data.get('drive_folder_id', '')

        if not file_ids:
            return {'success': False, 'error': 'No files to upload'}

        # Create date folder name
        today = datetime.now().strftime('%Y-%m-%d')
        folder_name = f"{today} - {content_type}"

        try:
            # Create the folder in the client's Drive folder
            folder_result = self.google.create_folder(folder_name, drive_folder_id)
            if not folder_result.get('success'):
                raise Exception(f"Failed to create folder: {folder_result.get('error')}")

            new_folder_id = folder_result.get('folder_id')
            folder_url = folder_result.get('url', '')

            # Download and upload each file
            uploaded_files = []
            failed_files = []

            for file_id in file_ids:
                try:
                    # Get file info from Slack
                    file_info = self.client.files_info(file=file_id)
                    file_data_slack = file_info.get('file', {})
                    file_name = file_data_slack.get('name', f'file_{file_id}')
                    file_url = file_data_slack.get('url_private', '')
                    mime_type = file_data_slack.get('mimetype', 'application/octet-stream')

                    # Download the file
                    file_content = self.download_slack_file(file_url)
                    if not file_content:
                        failed_files.append(file_name)
                        continue

                    # Upload to Google Drive
                    upload_result = self.google.upload_file(
                        file_content=file_content,
                        file_name=file_name,
                        mime_type=mime_type,
                        folder_id=new_folder_id
                    )

                    if upload_result.get('success'):
                        uploaded_files.append(file_name)
                    else:
                        failed_files.append(file_name)

                except Exception as e:
                    logger.error(f"Error processing file {file_id}: {e}")
                    failed_files.append(file_id)

            # Send confirmation message
            if uploaded_files:
                success_text = (
                    f"✅ Uploaded {len(uploaded_files)} file{'s' if len(uploaded_files) > 1 else ''} "
                    f"to *{client_name}/{folder_name}*"
                )

                if failed_files:
                    success_text += f"\n⚠️ {len(failed_files)} file(s) failed to upload"

                blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": success_text
                        },
                        "accessory": {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📁 View in Drive",
                                "emoji": True
                            },
                            "url": folder_url,
                            "action_id": "view_drive_folder"
                        }
                    }
                ]

                self.client.chat_postMessage(
                    channel=channel_id,
                    blocks=blocks,
                    text=success_text
                )

                return {
                    'success': True,
                    'uploaded': len(uploaded_files),
                    'failed': len(failed_files),
                    'folder_url': folder_url,
                    'folder_name': folder_name
                }
            else:
                # All files failed
                self.client.chat_postMessage(
                    channel=channel_id,
                    text=f"❌ Failed to upload files to Google Drive. Please try again."
                )
                return {
                    'success': False,
                    'error': 'All files failed to upload',
                    'failed': len(failed_files)
                }

        except Exception as e:
            logger.error(f"Error executing Drive upload: {e}")
            self.client.chat_postMessage(
                channel=channel_id,
                text=f"❌ Error uploading to Google Drive: {str(e)}"
            )
            return {'success': False, 'error': str(e)}


# Scheduler functions for automated tasks
def setup_scheduler(slack_features: SlackFeatures):
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
        slack_features.send_deadline_reminders,
        CronTrigger(hour=9, minute=0),
        id='daily_reminders',
        name='Daily Deadline Reminders'
    )

    # Daily digest at 6 PM
    scheduler.add_job(
        lambda: slack_features.send_digest(period='daily'),
        CronTrigger(hour=18, minute=0),
        id='daily_digest',
        name='Daily Activity Digest'
    )

    # Weekly digest on Friday at 5 PM
    scheduler.add_job(
        lambda: slack_features.send_digest(period='weekly'),
        CronTrigger(day_of_week='fri', hour=17, minute=0),
        id='weekly_digest',
        name='Weekly Activity Digest'
    )

    scheduler.start()
    logger.info("Scheduler started with reminder and digest jobs")

    return scheduler
