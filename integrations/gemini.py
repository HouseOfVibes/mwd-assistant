"""
Google Gemini AI Integration
Gemini 2.0 Flash - Primary workspace AI for meeting notes and general tasks
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import google-genai (new SDK)
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai not installed. Install with: pip install google-genai")


class GeminiClient:
    """Client for Google Gemini AI API"""

    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY', '')
        self.client = None
        self.model = 'gemini-2.0-flash-exp'  # Latest Gemini 2.0 Flash

        if GENAI_AVAILABLE and self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def is_configured(self) -> bool:
        """Check if client is properly configured"""
        return GENAI_AVAILABLE and bool(self.api_key) and self.client is not None

    def generate_meeting_notes(self, transcript: str, participants: list = None) -> Dict[str, Any]:
        """
        Generate structured meeting notes from transcript

        Args:
            transcript: Raw meeting transcript
            participants: List of participant names

        Returns:
            Structured meeting notes with summary, action items, decisions
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Gemini client not configured'}

        prompt = f"""Analyze this meeting transcript and create structured notes.

Participants: {', '.join(participants) if participants else 'Not specified'}

Transcript:
{transcript}

Create a JSON response with:
1. "summary": Brief overview (2-3 sentences)
2. "key_points": List of main discussion points
3. "action_items": List of tasks with assignee and deadline if mentioned
4. "decisions": List of decisions made
5. "follow_ups": Items needing follow-up
6. "next_meeting": Any mentioned next steps or meeting dates

Return only valid JSON."""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=4096,
                )
            )

            return {
                'success': True,
                'response': response.text,
                'model': self.model,
                'usage': {
                    'prompt_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0),
                    'completion_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0),
                }
            }
        except Exception as e:
            logger.error(f"Gemini meeting notes error: {e}")
            return {'success': False, 'error': str(e)}

    def summarize_document(self, content: str, doc_type: str = 'general') -> Dict[str, Any]:
        """
        Summarize a document

        Args:
            content: Document content
            doc_type: Type of document (general, contract, proposal, report)

        Returns:
            Document summary
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Gemini client not configured'}

        prompts = {
            'general': "Summarize this document, highlighting key points:",
            'contract': "Summarize this contract, noting key terms, obligations, and dates:",
            'proposal': "Summarize this proposal, highlighting scope, deliverables, timeline, and budget:",
            'report': "Summarize this report, noting findings, recommendations, and next steps:"
        }

        prompt = f"""{prompts.get(doc_type, prompts['general'])}

{content}

Provide a structured summary with:
1. Overview (2-3 sentences)
2. Key Points (bullet list)
3. Important Dates/Deadlines
4. Action Required (if any)"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                )
            )

            return {
                'success': True,
                'response': response.text,
                'model': self.model,
                'doc_type': doc_type
            }
        except Exception as e:
            logger.error(f"Gemini summarize error: {e}")
            return {'success': False, 'error': str(e)}

    def generate_content(self, prompt: str, temperature: float = 0.7) -> Dict[str, Any]:
        """
        General content generation

        Args:
            prompt: The prompt to send
            temperature: Creativity level (0-1)

        Returns:
            Generated content
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Gemini client not configured'}

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=4096,
                )
            )

            return {
                'success': True,
                'response': response.text,
                'model': self.model
            }
        except Exception as e:
            logger.error(f"Gemini generate error: {e}")
            return {'success': False, 'error': str(e)}

    def orchestrate_workflow(self, task: str, context: Dict) -> Dict[str, Any]:
        """
        Orchestrate multi-AI workflow based on task

        Args:
            task: Task description
            context: Context including client info, previous outputs

        Returns:
            Workflow orchestration plan
        """
        if not self.is_configured():
            return {'success': False, 'error': 'Gemini client not configured'}

        prompt = f"""You are an AI orchestrator for a marketing agency workflow.

Task: {task}

Context:
{context}

Determine the best workflow:
1. Which AI models should handle which parts (Claude for strategy, GPT for communication, Perplexity for research)
2. What sequence of operations
3. What data needs to flow between steps
4. Expected outputs

Return a JSON workflow plan with:
- "steps": Array of workflow steps
- "ai_assignments": Which AI handles each step
- "data_flow": How data passes between steps
- "expected_outputs": What each step produces"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=4096,
                )
            )

            return {
                'success': True,
                'response': response.text,
                'model': self.model,
                'task': task
            }
        except Exception as e:
            logger.error(f"Gemini orchestrate error: {e}")
            return {'success': False, 'error': str(e)}
