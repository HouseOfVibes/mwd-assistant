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
                # Extract title based on object type
                title = ''
                if item['object'] == 'page':
                    props = item.get('properties', {})
                    # Try common title property names
                    for key in ['Name', 'Title', 'name', 'title']:
                        if key in props:
                            title_prop = props[key]
                            if title_prop.get('title'):
                                title = ''.join([t.get('plain_text', '') for t in title_prop['title']])
                                break
                elif item['object'] == 'database':
                    title_list = item.get('title', [])
                    title = ''.join([t.get('plain_text', '') for t in title_list])

                results.append({
                    'id': item['id'],
                    'type': item['object'],
                    'title': title,
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

    def workspace_overview(self) -> Dict[str, Any]:
        """
        Get a comprehensive overview of the entire Notion workspace

        Returns:
            Overview with all databases and pages
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Notion client not configured'}

        try:
            # Get all databases
            db_response = self.client.search(filter={'property': 'object', 'value': 'database'})
            databases = []
            for db in db_response['results']:
                title_list = db.get('title', [])
                title = ''.join([t.get('plain_text', '') for t in title_list])
                databases.append({
                    'id': db['id'],
                    'title': title or 'Untitled Database',
                    'url': db.get('url', ''),
                    'created_time': db['created_time'],
                    'last_edited_time': db.get('last_edited_time', '')
                })

            # Get top-level pages (search with empty query, filter by page)
            page_response = self.client.search(filter={'property': 'object', 'value': 'page'})
            pages = []
            for page in page_response['results']:
                # Extract title
                props = page.get('properties', {})
                title = ''
                for key in ['Name', 'Title', 'name', 'title']:
                    if key in props:
                        title_prop = props[key]
                        if title_prop.get('title'):
                            title = ''.join([t.get('plain_text', '') for t in title_prop['title']])
                            break

                pages.append({
                    'id': page['id'],
                    'title': title or 'Untitled',
                    'url': page.get('url', ''),
                    'created_time': page['created_time'],
                    'last_edited_time': page.get('last_edited_time', ''),
                    'parent_type': page.get('parent', {}).get('type', 'unknown')
                })

            return {
                'success': True,
                'databases': databases,
                'database_count': len(databases),
                'pages': pages,
                'page_count': len(pages),
                'total_items': len(databases) + len(pages)
            }
        except Exception as e:
            logger.error(f"Notion workspace overview error: {e}")
            return {'success': False, 'error': str(e)}

    def create_client_portal(self, parent_page_id: str, client_data: Dict) -> Dict[str, Any]:
        """
        Create a comprehensive client portal in Notion

        Args:
            parent_page_id: Parent page ID where portal will be created
            client_data: Client information including:
                - company_name: Client company name
                - contact_name: Primary contact
                - contact_email: Contact email
                - services: List of services (branding, website, social, copywriting, etc.)
                - industry: Client industry
                - project_timeline: Expected timeline
                - budget: Project budget
                - goals: Client goals/objectives

        Returns:
            Created portal info with page IDs
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Notion client not configured'}

        try:
            company_name = client_data.get('company_name', 'New Client')
            services = client_data.get('services', [])
            created_pages = []

            # Create main portal page
            main_page = self.client.pages.create(
                parent={'page_id': parent_page_id},
                properties={
                    'title': [{'text': {'content': f"{company_name} - Client Portal"}}]
                },
                icon={'type': 'emoji', 'emoji': '🏢'},
                cover={
                    'type': 'external',
                    'external': {'url': 'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=1200'}
                }
            )
            main_page_id = main_page['id']
            created_pages.append({'name': 'Main Portal', 'id': main_page_id, 'url': main_page['url']})

            # Add overview content to main page
            overview_blocks = [
                {
                    'object': 'block',
                    'type': 'callout',
                    'callout': {
                        'rich_text': [{'text': {'content': f"Welcome to your project portal, {company_name}! This is your central hub for all project information, deliverables, and communication."}}],
                        'icon': {'type': 'emoji', 'emoji': '👋'}
                    }
                },
                {
                    'object': 'block',
                    'type': 'heading_1',
                    'heading_1': {
                        'rich_text': [{'text': {'content': 'Project Overview'}}]
                    }
                },
                {
                    'object': 'block',
                    'type': 'column_list',
                    'column_list': {'children': []}
                }
            ]

            # Add client details
            details_blocks = [
                {'type': 'heading_2', 'text': 'Client Details'},
                {'type': 'paragraph', 'text': f"**Company:** {company_name}"},
                {'type': 'paragraph', 'text': f"**Contact:** {client_data.get('contact_name', 'TBD')}"},
                {'type': 'paragraph', 'text': f"**Email:** {client_data.get('contact_email', 'TBD')}"},
                {'type': 'paragraph', 'text': f"**Industry:** {client_data.get('industry', 'TBD')}"},
                {'type': 'divider'},
                {'type': 'heading_2', 'text': 'Services'},
            ]

            # Add services list
            if services:
                details_blocks.append({
                    'type': 'bulleted_list',
                    'items': [self._format_service_name(s) for s in services]
                })
            else:
                details_blocks.append({'type': 'paragraph', 'text': 'Services to be determined'})

            # Add project info
            details_blocks.extend([
                {'type': 'divider'},
                {'type': 'heading_2', 'text': 'Project Info'},
                {'type': 'paragraph', 'text': f"**Timeline:** {client_data.get('project_timeline', 'TBD')}"},
                {'type': 'paragraph', 'text': f"**Budget:** {client_data.get('budget', 'TBD')}"},
            ])

            if client_data.get('goals'):
                details_blocks.extend([
                    {'type': 'heading_2', 'text': 'Goals & Objectives'},
                    {'type': 'paragraph', 'text': client_data.get('goals', '')}
                ])

            self.add_page_content(main_page_id, details_blocks)

            # Create sub-pages based on services
            subpages_to_create = [
                {
                    'name': 'Timeline & Milestones',
                    'emoji': '📅',
                    'content': self._get_timeline_content(services, client_data.get('project_timeline', ''))
                },
                {
                    'name': 'Deliverables',
                    'emoji': '📦',
                    'content': self._get_deliverables_content(services)
                },
                {
                    'name': 'Communication Log',
                    'emoji': '💬',
                    'content': self._get_communication_content()
                },
                {
                    'name': 'Resources & Assets',
                    'emoji': '📁',
                    'content': self._get_resources_content()
                }
            ]

            # Add service-specific pages
            service_pages = self._get_service_pages(services)
            subpages_to_create.extend(service_pages)

            # Create all sub-pages
            for subpage in subpages_to_create:
                page = self.client.pages.create(
                    parent={'page_id': main_page_id},
                    properties={
                        'title': [{'text': {'content': subpage['name']}}]
                    },
                    icon={'type': 'emoji', 'emoji': subpage.get('emoji', '📄')}
                )

                # Add content to the page
                if subpage.get('content'):
                    self.add_page_content(page['id'], subpage['content'])

                created_pages.append({
                    'name': subpage['name'],
                    'id': page['id'],
                    'url': page['url']
                })

            return {
                'success': True,
                'portal_id': main_page_id,
                'portal_url': main_page['url'],
                'pages_created': len(created_pages),
                'pages': created_pages
            }

        except Exception as e:
            logger.error(f"Notion create client portal error: {e}")
            return {'success': False, 'error': str(e)}

    def _format_service_name(self, service: str) -> str:
        """Format service name for display"""
        service_names = {
            'branding': 'Branding & Identity',
            'website': 'Website Design & Development',
            'social': 'Social Media Strategy',
            'copywriting': 'Copywriting & Content',
            'seo': 'SEO & Analytics',
            'email': 'Email Marketing',
            'advertising': 'Advertising & PPC',
            'video': 'Video Production',
            'photography': 'Photography',
            'print': 'Print Design'
        }
        return service_names.get(service.lower(), service.title())

    def _get_timeline_content(self, services: List[str], timeline: str) -> List[Dict]:
        """Generate timeline page content"""
        content = [
            {'type': 'heading_1', 'text': 'Project Timeline'},
            {'type': 'paragraph', 'text': f"Expected completion: {timeline}" if timeline else "Timeline to be determined"},
            {'type': 'divider'},
            {'type': 'heading_2', 'text': 'Milestones'},
        ]

        # Generate milestones based on services
        milestones = ['Project Kickoff', 'Discovery & Research']

        if 'branding' in [s.lower() for s in services]:
            milestones.extend(['Brand Strategy Review', 'Brand Identity Delivery'])
        if 'website' in [s.lower() for s in services]:
            milestones.extend(['Wireframes & Sitemap', 'Design Mockups', 'Development', 'Website Launch'])
        if 'social' in [s.lower() for s in services]:
            milestones.extend(['Social Strategy Review', 'Content Calendar Delivery'])
        if 'copywriting' in [s.lower() for s in services]:
            milestones.extend(['Copy Draft Review', 'Final Copy Delivery'])

        milestones.append('Project Completion')

        # Add as to-do items
        for milestone in milestones:
            content.append({
                'type': 'to_do',
                'text': milestone,
                'checked': False
            })

        return content

    def _get_deliverables_content(self, services: List[str]) -> List[Dict]:
        """Generate deliverables page content"""
        content = [
            {'type': 'heading_1', 'text': 'Project Deliverables'},
            {'type': 'paragraph', 'text': 'All project deliverables will be uploaded here for your review and approval.'},
            {'type': 'divider'},
        ]

        # Add service-specific deliverable sections
        service_deliverables = {
            'branding': {
                'title': 'Branding Deliverables',
                'items': ['Brand Strategy Document', 'Logo Files (all formats)', 'Color Palette', 'Typography Guide', 'Brand Guidelines PDF']
            },
            'website': {
                'title': 'Website Deliverables',
                'items': ['Sitemap', 'Wireframes', 'Design Mockups', 'Development Files', 'Launch Checklist']
            },
            'social': {
                'title': 'Social Media Deliverables',
                'items': ['Platform Strategy', 'Content Pillars', 'Content Calendar', 'Post Templates', 'Hashtag Strategy']
            },
            'copywriting': {
                'title': 'Copywriting Deliverables',
                'items': ['Website Copy', 'Taglines', 'Email Sequences', 'Social Captions', 'Marketing Materials']
            }
        }

        for service in services:
            service_key = service.lower()
            if service_key in service_deliverables:
                deliverable = service_deliverables[service_key]
                content.append({'type': 'heading_2', 'text': deliverable['title']})
                content.append({'type': 'bulleted_list', 'items': deliverable['items']})

        if not services:
            content.append({'type': 'paragraph', 'text': 'Deliverables will be added based on selected services.'})

        return content

    def _get_communication_content(self) -> List[Dict]:
        """Generate communication log page content"""
        return [
            {'type': 'heading_1', 'text': 'Communication Log'},
            {'type': 'paragraph', 'text': 'Record of all project communications, decisions, and updates.'},
            {'type': 'divider'},
            {'type': 'heading_2', 'text': 'Latest Updates'},
            {'type': 'paragraph', 'text': f"**{datetime.now().strftime('%Y-%m-%d')}** - Client portal created. Welcome to your project!"},
            {'type': 'divider'},
            {'type': 'heading_2', 'text': 'Key Decisions'},
            {'type': 'paragraph', 'text': 'Important decisions will be documented here.'},
            {'type': 'divider'},
            {'type': 'heading_2', 'text': 'Questions & Answers'},
            {'type': 'paragraph', 'text': 'Questions and their resolutions will be tracked here.'}
        ]

    def _get_resources_content(self) -> List[Dict]:
        """Generate resources page content"""
        return [
            {'type': 'heading_1', 'text': 'Resources & Assets'},
            {'type': 'paragraph', 'text': 'Upload brand assets, reference materials, and other resources here.'},
            {'type': 'divider'},
            {'type': 'heading_2', 'text': 'Brand Assets'},
            {'type': 'paragraph', 'text': 'Logos, images, and brand materials'},
            {'type': 'divider'},
            {'type': 'heading_2', 'text': 'Reference Materials'},
            {'type': 'paragraph', 'text': 'Competitor examples, inspiration, and reference documents'},
            {'type': 'divider'},
            {'type': 'heading_2', 'text': 'Project Documents'},
            {'type': 'paragraph', 'text': 'Contracts, briefs, and other project documentation'}
        ]

    def _get_service_pages(self, services: List[str]) -> List[Dict]:
        """Generate service-specific sub-pages"""
        pages = []

        service_configs = {
            'branding': {
                'name': 'Brand Strategy',
                'emoji': '🎨',
                'content': [
                    {'type': 'heading_1', 'text': 'Brand Strategy'},
                    {'type': 'paragraph', 'text': 'Your comprehensive brand strategy and identity guidelines.'},
                    {'type': 'divider'},
                    {'type': 'heading_2', 'text': 'Brand Positioning'},
                    {'type': 'paragraph', 'text': 'To be completed...'},
                    {'type': 'heading_2', 'text': 'Target Audience'},
                    {'type': 'paragraph', 'text': 'To be completed...'},
                    {'type': 'heading_2', 'text': 'Brand Personality'},
                    {'type': 'paragraph', 'text': 'To be completed...'},
                    {'type': 'heading_2', 'text': 'Visual Identity'},
                    {'type': 'paragraph', 'text': 'To be completed...'}
                ]
            },
            'website': {
                'name': 'Website Plan',
                'emoji': '🌐',
                'content': [
                    {'type': 'heading_1', 'text': 'Website Design Plan'},
                    {'type': 'paragraph', 'text': 'Your website strategy, sitemap, and design specifications.'},
                    {'type': 'divider'},
                    {'type': 'heading_2', 'text': 'Sitemap'},
                    {'type': 'paragraph', 'text': 'To be completed...'},
                    {'type': 'heading_2', 'text': 'Page Layouts'},
                    {'type': 'paragraph', 'text': 'To be completed...'},
                    {'type': 'heading_2', 'text': 'User Journey'},
                    {'type': 'paragraph', 'text': 'To be completed...'},
                    {'type': 'heading_2', 'text': 'Technical Requirements'},
                    {'type': 'paragraph', 'text': 'To be completed...'}
                ]
            },
            'social': {
                'name': 'Social Strategy',
                'emoji': '📱',
                'content': [
                    {'type': 'heading_1', 'text': 'Social Media Strategy'},
                    {'type': 'paragraph', 'text': 'Your social media presence strategy and content plan.'},
                    {'type': 'divider'},
                    {'type': 'heading_2', 'text': 'Platform Strategy'},
                    {'type': 'paragraph', 'text': 'To be completed...'},
                    {'type': 'heading_2', 'text': 'Content Pillars'},
                    {'type': 'paragraph', 'text': 'To be completed...'},
                    {'type': 'heading_2', 'text': 'Posting Schedule'},
                    {'type': 'paragraph', 'text': 'To be completed...'},
                    {'type': 'heading_2', 'text': 'Content Calendar'},
                    {'type': 'paragraph', 'text': 'To be completed...'}
                ]
            },
            'copywriting': {
                'name': 'Copy & Content',
                'emoji': '✍️',
                'content': [
                    {'type': 'heading_1', 'text': 'Copywriting & Content'},
                    {'type': 'paragraph', 'text': 'All written content and messaging for your brand.'},
                    {'type': 'divider'},
                    {'type': 'heading_2', 'text': 'Messaging Framework'},
                    {'type': 'paragraph', 'text': 'To be completed...'},
                    {'type': 'heading_2', 'text': 'Website Copy'},
                    {'type': 'paragraph', 'text': 'To be completed...'},
                    {'type': 'heading_2', 'text': 'Marketing Copy'},
                    {'type': 'paragraph', 'text': 'To be completed...'},
                    {'type': 'heading_2', 'text': 'Email Sequences'},
                    {'type': 'paragraph', 'text': 'To be completed...'}
                ]
            }
        }

        for service in services:
            service_key = service.lower()
            if service_key in service_configs:
                pages.append(service_configs[service_key])

        return pages
