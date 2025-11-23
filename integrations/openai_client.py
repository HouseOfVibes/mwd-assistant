"""
OpenAI GPT Integration
GPT-5.1 - Internal team communication and collaboration

GPT-5.1 Features (November 2025):
- Adaptive Reasoning: Dynamically adjusts thinking based on task complexity
- No Reasoning Mode: Faster responses for simple tasks
- Extended Prompt Caching: Up to 24-hour cache retention
"""

import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai not installed. Install with: pip install openai")


class OpenAIClient:
    """Client for OpenAI GPT API"""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY', '')
        self.client = None
        self.model = 'gpt-5.1'  # GPT-5.1 for team communication (Nov 2025)
        self.model_instant = 'gpt-5.1-instant'  # Faster variant for simple tasks

        if OPENAI_AVAILABLE and self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def is_configured(self) -> bool:
        """Check if client is properly configured"""
        return OPENAI_AVAILABLE and bool(self.api_key) and self.client is not None

    def draft_team_message(self, context: str, message_type: str = 'update',
                          tone: str = 'professional') -> Dict[str, Any]:
        """
        Draft internal team communication

        Args:
            context: Context for the message
            message_type: Type (update, request, announcement, feedback)
            tone: Tone (professional, casual, urgent)

        Returns:
            Drafted message
        """
        if not self.is_configured():
            return {'success': False, 'error': 'OpenAI client not configured'}

        tone_guides = {
            'professional': 'formal but friendly, clear and concise',
            'casual': 'relaxed and conversational, using informal language',
            'urgent': 'direct and action-oriented, emphasizing priority'
        }

        type_guides = {
            'update': 'project status update or progress report',
            'request': 'asking for input, resources, or action',
            'announcement': 'sharing news or important information',
            'feedback': 'providing constructive feedback or suggestions'
        }

        prompt = f"""Draft an internal team message.

Type: {type_guides.get(message_type, 'general communication')}
Tone: {tone_guides.get(tone, 'professional')}

Context:
{context}

Create a well-structured message that:
1. Has a clear subject line
2. Gets to the point quickly
3. Includes any necessary action items
4. Ends with clear next steps

Format:
Subject: [subject line]

[message body]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional communication assistant helping draft clear, effective internal team messages."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1024
            )

            return {
                'success': True,
                'response': response.choices[0].message.content,
                'model': self.model,
                'message_type': message_type,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"OpenAI team message error: {e}")
            return {'success': False, 'error': str(e)}

    def draft_slack_message(self, context: str, channel_type: str = 'project') -> Dict[str, Any]:
        """
        Draft a Slack message

        Args:
            context: Message context
            channel_type: Type of channel (project, general, client)

        Returns:
            Drafted Slack message with formatting
        """
        if not self.is_configured():
            return {'success': False, 'error': 'OpenAI client not configured'}

        prompt = f"""Draft a Slack message for a {channel_type} channel.

Context:
{context}

Format the message using Slack markdown:
- *bold* for emphasis
- `code` for technical terms
- > for quotes
- Bullet points for lists
- Emojis where appropriate (but don't overdo it)

Keep it concise and scannable."""

        try:
            # Use instant model for simple drafting tasks
            response = self.client.chat.completions.create(
                model=self.model_instant,
                messages=[
                    {"role": "system", "content": "You are a Slack communication expert. Create clear, well-formatted messages."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=512
            )

            return {
                'success': True,
                'response': response.choices[0].message.content,
                'model': self.model_instant,
                'channel_type': channel_type
            }
        except Exception as e:
            logger.error(f"OpenAI Slack message error: {e}")
            return {'success': False, 'error': str(e)}

    def summarize_thread(self, messages: List[Dict]) -> Dict[str, Any]:
        """
        Summarize a conversation thread

        Args:
            messages: List of messages with 'author' and 'content'

        Returns:
            Thread summary with key points and action items
        """
        if not self.is_configured():
            return {'success': False, 'error': 'OpenAI client not configured'}

        thread_text = "\n".join([
            f"{msg.get('author', 'Unknown')}: {msg.get('content', '')}"
            for msg in messages
        ])

        prompt = f"""Summarize this conversation thread:

{thread_text}

Provide:
1. Brief summary (2-3 sentences)
2. Key decisions made
3. Action items (with owners if mentioned)
4. Unresolved questions
5. Recommended next steps"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at summarizing team conversations and extracting actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1024
            )

            return {
                'success': True,
                'response': response.choices[0].message.content,
                'model': self.model,
                'message_count': len(messages)
            }
        except Exception as e:
            logger.error(f"OpenAI summarize thread error: {e}")
            return {'success': False, 'error': str(e)}

    def generate_response(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """
        General GPT response generation

        Args:
            prompt: User prompt
            system_prompt: Optional system context

        Returns:
            Generated response
        """
        if not self.is_configured():
            return {'success': False, 'error': 'OpenAI client not configured'}

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )

            return {
                'success': True,
                'response': response.choices[0].message.content,
                'model': self.model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"OpenAI generate error: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_feedback(self, feedback: str, source: str = 'client') -> Dict[str, Any]:
        """
        Analyze feedback and extract insights

        Args:
            feedback: Feedback text
            source: Source of feedback (client, team, stakeholder)

        Returns:
            Analyzed feedback with sentiment and recommendations
        """
        if not self.is_configured():
            return {'success': False, 'error': 'OpenAI client not configured'}

        prompt = f"""Analyze this {source} feedback:

{feedback}

Provide:
1. Sentiment (positive/neutral/negative) with confidence
2. Key themes identified
3. Specific concerns or praises
4. Suggested response approach
5. Action items to address feedback
6. Priority level (high/medium/low)

Return as structured analysis."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing feedback and extracting actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1024
            )

            return {
                'success': True,
                'response': response.choices[0].message.content,
                'model': self.model,
                'source': source
            }
        except Exception as e:
            logger.error(f"OpenAI analyze feedback error: {e}")
            return {'success': False, 'error': str(e)}
