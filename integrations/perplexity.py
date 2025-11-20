"""
Perplexity AI Integration
Perplexity Sonar Pro - Client communication and research
"""

import os
import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class PerplexityClient:
    """Client for Perplexity AI API"""

    def __init__(self):
        self.api_key = os.getenv('PERPLEXITY_API_KEY', '')
        self.base_url = 'https://api.perplexity.ai'
        self.model = 'sonar-pro'  # Sonar Pro for research
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def is_configured(self) -> bool:
        """Check if client is properly configured"""
        return bool(self.api_key)

    def research_industry(self, industry: str, focus_areas: List[str] = None) -> Dict[str, Any]:
        """
        Research an industry for client work

        Args:
            industry: Industry to research
            focus_areas: Specific areas to focus on

        Returns:
            Research findings with citations
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Perplexity client not configured'}

        focus = ', '.join(focus_areas) if focus_areas else 'market trends, key players, challenges, opportunities'

        prompt = f"""Research the {industry} industry with focus on: {focus}

Provide:
1. Industry overview and current state
2. Key market trends (2024-2025)
3. Major players and competitors
4. Common challenges and pain points
5. Emerging opportunities
6. Technology trends affecting the industry
7. Consumer/buyer behavior insights

Include specific data, statistics, and cite sources."""

        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=self.headers,
                json={
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are a market research expert. Provide detailed, data-driven insights with citations.'
                        },
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 4096
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()

            return {
                'success': True,
                'response': data['choices'][0]['message']['content'],
                'model': self.model,
                'industry': industry,
                'citations': data.get('citations', [])
            }
        except Exception as e:
            logger.error(f"Perplexity industry research error: {e}")
            return {'success': False, 'error': str(e)}

    def research_competitors(self, company: str, competitors: List[str] = None,
                            industry: str = None) -> Dict[str, Any]:
        """
        Research competitors for a client

        Args:
            company: Client company name
            competitors: Known competitors to research
            industry: Industry context

        Returns:
            Competitive analysis with citations
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Perplexity client not configured'}

        competitor_list = ', '.join(competitors) if competitors else 'main competitors'

        prompt = f"""Conduct competitive analysis for {company} in the {industry or 'their'} industry.

Analyze: {competitor_list}

Provide for each competitor:
1. Company overview and positioning
2. Key products/services
3. Target audience
4. Pricing strategy (if available)
5. Marketing approach and channels
6. Strengths and weaknesses
7. Recent news or developments

Then provide:
- Competitive positioning map
- Gap analysis
- Opportunities for differentiation
- Threats to be aware of

Include specific data and cite sources."""

        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=self.headers,
                json={
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are a competitive intelligence analyst. Provide thorough, factual analysis with citations.'
                        },
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 4096
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()

            return {
                'success': True,
                'response': data['choices'][0]['message']['content'],
                'model': self.model,
                'company': company,
                'citations': data.get('citations', [])
            }
        except Exception as e:
            logger.error(f"Perplexity competitor research error: {e}")
            return {'success': False, 'error': str(e)}

    def draft_client_email(self, context: str, email_type: str = 'update',
                          client_name: str = None) -> Dict[str, Any]:
        """
        Draft client-facing email with current best practices

        Args:
            context: Email context and content needed
            email_type: Type (update, proposal, follow_up, introduction)
            client_name: Client name for personalization

        Returns:
            Professional client email
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Perplexity client not configured'}

        type_context = {
            'update': 'project status update',
            'proposal': 'proposal or pitch',
            'follow_up': 'follow-up after meeting',
            'introduction': 'initial introduction or outreach'
        }

        prompt = f"""Draft a professional {type_context.get(email_type, 'client')} email.

Client: {client_name or 'Client'}
Context: {context}

Use current email best practices:
1. Clear, compelling subject line
2. Professional but warm greeting
3. Clear purpose in first paragraph
4. Specific details and value
5. Clear call to action
6. Professional sign-off

Format:
Subject: [subject line]

[email body]"""

        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=self.headers,
                json={
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are an expert at client communication. Write professional, effective emails that build relationships.'
                        },
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.7,
                    'max_tokens': 1024
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            return {
                'success': True,
                'response': data['choices'][0]['message']['content'],
                'model': self.model,
                'email_type': email_type
            }
        except Exception as e:
            logger.error(f"Perplexity client email error: {e}")
            return {'success': False, 'error': str(e)}

    def research_topic(self, topic: str, depth: str = 'comprehensive') -> Dict[str, Any]:
        """
        General research on any topic

        Args:
            topic: Topic to research
            depth: Research depth (quick, moderate, comprehensive)

        Returns:
            Research findings with citations
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Perplexity client not configured'}

        depth_tokens = {
            'quick': 1024,
            'moderate': 2048,
            'comprehensive': 4096
        }

        prompt = f"""Research: {topic}

Provide a {'brief overview' if depth == 'quick' else 'comprehensive analysis'} including:
1. Key facts and background
2. Current state and recent developments
3. Different perspectives or approaches
4. Practical applications or implications
5. Expert opinions and sources

Cite all sources."""

        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=self.headers,
                json={
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are a research assistant. Provide accurate, well-sourced information.'
                        },
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': depth_tokens.get(depth, 2048)
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()

            return {
                'success': True,
                'response': data['choices'][0]['message']['content'],
                'model': self.model,
                'topic': topic,
                'citations': data.get('citations', [])
            }
        except Exception as e:
            logger.error(f"Perplexity research error: {e}")
            return {'success': False, 'error': str(e)}

    def get_market_data(self, query: str) -> Dict[str, Any]:
        """
        Get current market data and statistics

        Args:
            query: Specific data or statistics needed

        Returns:
            Market data with sources
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Perplexity client not configured'}

        prompt = f"""Find current market data and statistics for: {query}

Provide:
1. Specific numbers and statistics
2. Data sources and dates
3. Trends over time if available
4. Regional breakdowns if relevant
5. Projections or forecasts

Only include data from reliable sources. Cite all sources with dates."""

        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=self.headers,
                json={
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are a market data analyst. Provide accurate statistics with proper citations.'
                        },
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.1,
                    'max_tokens': 2048
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            return {
                'success': True,
                'response': data['choices'][0]['message']['content'],
                'model': self.model,
                'query': query,
                'citations': data.get('citations', [])
            }
        except Exception as e:
            logger.error(f"Perplexity market data error: {e}")
            return {'success': False, 'error': str(e)}
