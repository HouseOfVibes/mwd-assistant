"""
MWD Invoice System API Client
Handles communication between MWD Agent and MWD Invoice System
"""

import os
import hmac
import hashlib
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class InvoiceSystemClient:
    """Client for MWD Invoice System API"""

    def __init__(self):
        self.base_url = os.getenv('MWD_INVOICE_SYSTEM_URL', '').rstrip('/')
        self.api_key = os.getenv('MWD_INVOICE_SYSTEM_API_KEY', '')
        self.webhook_secret = os.getenv('MWD_WEBHOOK_SECRET', '')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        self.timeout = 30

    def is_configured(self) -> bool:
        """Check if the client is properly configured"""
        return bool(self.base_url and self.api_key)

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify HMAC-SHA256 signature from webhook

        Args:
            payload: Raw request body bytes
            signature: Signature from X-MWD-Signature header

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping verification")
            return True  # Skip verification if not configured

        if not signature:
            logger.error("No signature provided in webhook request")
            return False

        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)

    def create_lead(self, intake_data: Dict, ai_assessment: Optional[Dict] = None) -> Dict:
        """
        Create lead in invoice system

        Args:
            intake_data: Client intake form data
            ai_assessment: AI-generated assessment of the lead

        Returns:
            Response with lead_id and lead_url
        """
        if not self.is_configured():
            logger.error("Invoice system client not configured")
            return {'success': False, 'error': 'Client not configured'}

        payload = {
            'source': 'mwd_agent_intake',
            'company_name': intake_data.get('company_name'),
            'contact_name': intake_data.get('contact_name'),
            'contact_email': intake_data.get('contact_email'),
            'phone': intake_data.get('phone'),
            'industry': intake_data.get('industry'),
            'budget': intake_data.get('budget'),
            'services_requested': intake_data.get('key_services', []),
            'agent_assessment': ai_assessment or {},
            'intake_form_data': intake_data
        }

        try:
            response = requests.post(
                f'{self.base_url}/api/v1/leads',
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create lead: {e}")
            return {'success': False, 'error': str(e)}

    def attach_deliverable(self, lead_id: str, deliverable: Dict) -> Dict:
        """
        Attach AI-generated deliverable to lead

        Args:
            lead_id: ID of the lead in invoice system
            deliverable: Deliverable data including type, content, and formatted output

        Returns:
            Response with deliverable_id and proposal status
        """
        if not self.is_configured():
            logger.error("Invoice system client not configured")
            return {'success': False, 'error': 'Client not configured'}

        try:
            response = requests.put(
                f'{self.base_url}/api/v1/leads/{lead_id}/deliverables',
                json=deliverable,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to attach deliverable to lead {lead_id}: {e}")
            return {'success': False, 'error': str(e)}

    def create_project(self, project_data: Dict) -> Dict:
        """
        Create project from approved proposal

        Args:
            project_data: Project details including lead_id, services, milestones

        Returns:
            Response with project_id
        """
        if not self.is_configured():
            logger.error("Invoice system client not configured")
            return {'success': False, 'error': 'Client not configured'}

        try:
            response = requests.post(
                f'{self.base_url}/api/v1/projects',
                json=project_data,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create project: {e}")
            return {'success': False, 'error': str(e)}

    def update_project_status(self, project_id: str, status_update: Dict) -> Dict:
        """
        Update project status

        Args:
            project_id: ID of the project in invoice system
            status_update: Status data including completion percentage, milestones

        Returns:
            Response confirming update
        """
        if not self.is_configured():
            logger.error("Invoice system client not configured")
            return {'success': False, 'error': 'Client not configured'}

        try:
            response = requests.patch(
                f'{self.base_url}/api/v1/projects/{project_id}/status',
                json=status_update,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update project {project_id} status: {e}")
            return {'success': False, 'error': str(e)}

    def get_lead(self, lead_id: str) -> Dict:
        """
        Get lead details from invoice system

        Args:
            lead_id: ID of the lead

        Returns:
            Lead data including intake info, contract status, etc.
        """
        if not self.is_configured():
            logger.error("Invoice system client not configured")
            return {'success': False, 'error': 'Client not configured'}

        try:
            response = requests.get(
                f'{self.base_url}/api/v1/leads/{lead_id}',
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get lead {lead_id}: {e}")
            return {'success': False, 'error': str(e)}

    def get_project(self, project_id: str) -> Dict:
        """
        Get project details from invoice system

        Args:
            project_id: ID of the project

        Returns:
            Project data including milestones, deliverables, etc.
        """
        if not self.is_configured():
            logger.error("Invoice system client not configured")
            return {'success': False, 'error': 'Client not configured'}

        try:
            response = requests.get(
                f'{self.base_url}/api/v1/projects/{project_id}',
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            return {'success': False, 'error': str(e)}
