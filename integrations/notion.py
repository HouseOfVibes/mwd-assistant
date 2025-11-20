"""
Notion API Integration
Project management and documentation
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    logger.warning("notion-client not installed. Install with: pip install notion-client")


class NotionClient:
    """Client for Notion API"""

    def __init__(self):
        self.api_key = os.getenv('NOTION_API_KEY', '')
        self.client = None

        if NOTION_AVAILABLE and self.api_key:
            self.client = Client(auth=self.api_key)

    def is_configured(self) -> bool:
        """Check if client is properly configured"""
        return NOTION_AVAILABLE and bool(self.api_key) and self.client is not None

    def create_project_page(self, database_id: str, project_data: Dict) -> Dict[str, Any]:
        """
        Create a new project page in Notion database

        Args:
            database_id: Notion database ID
            project_data: Project information

        Returns:
            Created page info
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Notion client not configured'}

        try:
            properties = {
                'Name': {
                    'title': [{'text': {'content': project_data.get('name', 'New Project')}}]
                }
            }

            # Add optional properties if provided
            if 'client_name' in project_data:
                properties['Client'] = {
                    'rich_text': [{'text': {'content': project_data['client_name']}}]
                }

            if 'status' in project_data:
                properties['Status'] = {
                    'select': {'name': project_data['status']}
                }

            if 'start_date' in project_data:
                properties['Start Date'] = {
                    'date': {'start': project_data['start_date']}
                }

            if 'due_date' in project_data:
                properties['Due Date'] = {
                    'date': {'start': project_data['due_date']}
                }

            if 'budget' in project_data:
                properties['Budget'] = {
                    'number': project_data['budget']
                }

            if 'services' in project_data:
                properties['Services'] = {
                    'multi_select': [{'name': s} for s in project_data['services']]
                }

            response = self.client.pages.create(
                parent={'database_id': database_id},
                properties=properties
            )

            return {
                'success': True,
                'page_id': response['id'],
                'page_url': response['url'],
                'created_time': response['created_time']
            }
        except Exception as e:
            logger.error(f"Notion create project error: {e}")
            return {'success': False, 'error': str(e)}

    def add_page_content(self, page_id: str, content: List[Dict]) -> Dict[str, Any]:
        """
        Add content blocks to a Notion page

        Args:
            page_id: Page ID to add content to
            content: List of content blocks

        Returns:
            Success status
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Notion client not configured'}

        try:
            blocks = []
            for item in content:
                block_type = item.get('type', 'paragraph')

                if block_type == 'heading_1':
                    blocks.append({
                        'object': 'block',
                        'type': 'heading_1',
                        'heading_1': {
                            'rich_text': [{'type': 'text', 'text': {'content': item['text']}}]
                        }
                    })
                elif block_type == 'heading_2':
                    blocks.append({
                        'object': 'block',
                        'type': 'heading_2',
                        'heading_2': {
                            'rich_text': [{'type': 'text', 'text': {'content': item['text']}}]
                        }
                    })
                elif block_type == 'bulleted_list':
                    for bullet in item.get('items', []):
                        blocks.append({
                            'object': 'block',
                            'type': 'bulleted_list_item',
                            'bulleted_list_item': {
                                'rich_text': [{'type': 'text', 'text': {'content': bullet}}]
                            }
                        })
                elif block_type == 'numbered_list':
                    for num_item in item.get('items', []):
                        blocks.append({
                            'object': 'block',
                            'type': 'numbered_list_item',
                            'numbered_list_item': {
                                'rich_text': [{'type': 'text', 'text': {'content': num_item}}]
                            }
                        })
                elif block_type == 'code':
                    blocks.append({
                        'object': 'block',
                        'type': 'code',
                        'code': {
                            'rich_text': [{'type': 'text', 'text': {'content': item['text']}}],
                            'language': item.get('language', 'plain text')
                        }
                    })
                elif block_type == 'divider':
                    blocks.append({
                        'object': 'block',
                        'type': 'divider',
                        'divider': {}
                    })
                else:  # paragraph
                    blocks.append({
                        'object': 'block',
                        'type': 'paragraph',
                        'paragraph': {
                            'rich_text': [{'type': 'text', 'text': {'content': item.get('text', '')}}]
                        }
                    })

            self.client.blocks.children.append(
                block_id=page_id,
                children=blocks
            )

            return {
                'success': True,
                'blocks_added': len(blocks)
            }
        except Exception as e:
            logger.error(f"Notion add content error: {e}")
            return {'success': False, 'error': str(e)}

    def update_project_status(self, page_id: str, status: str,
                             notes: str = None) -> Dict[str, Any]:
        """
        Update project status in Notion

        Args:
            page_id: Project page ID
            status: New status
            notes: Optional status notes

        Returns:
            Update result
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Notion client not configured'}

        try:
            properties = {
                'Status': {'select': {'name': status}}
            }

            if notes:
                properties['Status Notes'] = {
                    'rich_text': [{'text': {'content': notes}}]
                }

            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )

            return {
                'success': True,
                'page_id': page_id,
                'new_status': status
            }
        except Exception as e:
            logger.error(f"Notion update status error: {e}")
            return {'success': False, 'error': str(e)}

    def query_database(self, database_id: str, filters: Dict = None,
                      sorts: List[Dict] = None) -> Dict[str, Any]:
        """
        Query a Notion database

        Args:
            database_id: Database to query
            filters: Filter conditions
            sorts: Sort conditions

        Returns:
            Query results
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Notion client not configured'}

        try:
            query_params = {'database_id': database_id}

            if filters:
                query_params['filter'] = filters
            if sorts:
                query_params['sorts'] = sorts

            response = self.client.databases.query(**query_params)

            results = []
            for page in response['results']:
                results.append({
                    'id': page['id'],
                    'url': page['url'],
                    'properties': page['properties'],
                    'created_time': page['created_time'],
                    'last_edited_time': page['last_edited_time']
                })

            return {
                'success': True,
                'results': results,
                'count': len(results),
                'has_more': response.get('has_more', False)
            }
        except Exception as e:
            logger.error(f"Notion query database error: {e}")
            return {'success': False, 'error': str(e)}

    def create_meeting_notes(self, database_id: str, meeting_data: Dict) -> Dict[str, Any]:
        """
        Create meeting notes page in Notion

        Args:
            database_id: Meeting notes database ID
            meeting_data: Meeting information including notes

        Returns:
            Created page info
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Notion client not configured'}

        try:
            # Create the page with properties
            properties = {
                'Name': {
                    'title': [{'text': {'content': meeting_data.get('title', 'Meeting Notes')}}]
                }
            }

            if 'date' in meeting_data:
                properties['Date'] = {
                    'date': {'start': meeting_data['date']}
                }

            if 'attendees' in meeting_data:
                properties['Attendees'] = {
                    'rich_text': [{'text': {'content': ', '.join(meeting_data['attendees'])}}]
                }

            if 'project' in meeting_data:
                properties['Project'] = {
                    'rich_text': [{'text': {'content': meeting_data['project']}}]
                }

            page = self.client.pages.create(
                parent={'database_id': database_id},
                properties=properties
            )

            # Add meeting content
            content_blocks = []

            if 'summary' in meeting_data:
                content_blocks.append({
                    'object': 'block',
                    'type': 'heading_2',
                    'heading_2': {
                        'rich_text': [{'text': {'content': 'Summary'}}]
                    }
                })
                content_blocks.append({
                    'object': 'block',
                    'type': 'paragraph',
                    'paragraph': {
                        'rich_text': [{'text': {'content': meeting_data['summary']}}]
                    }
                })

            if 'action_items' in meeting_data:
                content_blocks.append({
                    'object': 'block',
                    'type': 'heading_2',
                    'heading_2': {
                        'rich_text': [{'text': {'content': 'Action Items'}}]
                    }
                })
                for item in meeting_data['action_items']:
                    content_blocks.append({
                        'object': 'block',
                        'type': 'to_do',
                        'to_do': {
                            'rich_text': [{'text': {'content': item}}],
                            'checked': False
                        }
                    })

            if 'decisions' in meeting_data:
                content_blocks.append({
                    'object': 'block',
                    'type': 'heading_2',
                    'heading_2': {
                        'rich_text': [{'text': {'content': 'Decisions'}}]
                    }
                })
                for decision in meeting_data['decisions']:
                    content_blocks.append({
                        'object': 'block',
                        'type': 'bulleted_list_item',
                        'bulleted_list_item': {
                            'rich_text': [{'text': {'content': decision}}]
                        }
                    })

            if content_blocks:
                self.client.blocks.children.append(
                    block_id=page['id'],
                    children=content_blocks
                )

            return {
                'success': True,
                'page_id': page['id'],
                'page_url': page['url']
            }
        except Exception as e:
            logger.error(f"Notion create meeting notes error: {e}")
            return {'success': False, 'error': str(e)}

    def search(self, query: str, filter_type: str = None) -> Dict[str, Any]:
        """
        Search across Notion workspace

        Args:
            query: Search query
            filter_type: Filter by 'page' or 'database'

        Returns:
            Search results
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Notion client not configured'}

        try:
            search_params = {'query': query}

            if filter_type:
                search_params['filter'] = {'property': 'object', 'value': filter_type}

            response = self.client.search(**search_params)

            results = []
            for item in response['results']:
                results.append({
                    'id': item['id'],
                    'type': item['object'],
                    'url': item.get('url', ''),
                    'created_time': item['created_time']
                })

            return {
                'success': True,
                'results': results,
                'count': len(results)
            }
        except Exception as e:
            logger.error(f"Notion search error: {e}")
            return {'success': False, 'error': str(e)}
