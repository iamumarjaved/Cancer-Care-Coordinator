"""Email Service - SendGrid integration for notifications."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications via SendGrid."""

    def __init__(self):
        self._client = None
        self._enabled = False

        if settings.EMAIL_ENABLED and settings.SENDGRID_API_KEY and settings.SENDGRID_FROM_EMAIL:
            try:
                self._client = SendGridAPIClient(settings.SENDGRID_API_KEY)
                self._enabled = True
                logger.info(f"EmailService initialized (from: {settings.SENDGRID_FROM_EMAIL})")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid client: {e}")
        else:
            logger.info("EmailService disabled (missing API key or from email)")

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def _get_base_template(self, content: str) -> str:
        """Get base HTML email template matching website style."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cancer Care Coordinator</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f8fafc;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8fafc; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); padding: 32px 40px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600;">
                                Cancer Care Coordinator
                            </h1>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            {content}
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f1f5f9; padding: 24px 40px; text-align: center; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0; color: #64748b; font-size: 13px;">
                                This is an automated notification from Cancer Care Coordinator.
                            </p>
                            <p style="margin: 8px 0 0 0; color: #94a3b8; font-size: 12px;">
                                &copy; {datetime.now().year} Cancer Care Coordinator. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    def _get_analysis_complete_template(
        self,
        patient_name: str,
        patient_id: str,
        analysis_summary: Dict[str, Any]
    ) -> str:
        """Generate HTML content for analysis completion email."""
        # Extract summary data
        recommendations_count = len(analysis_summary.get("treatment_recommendations", []))
        trials_count = analysis_summary.get("clinical_trials_count", 0)
        summary = analysis_summary.get("summary", "")
        key_findings = analysis_summary.get("key_findings", [])

        # Build recommendations preview
        recommendations_html = ""
        recommendations = analysis_summary.get("treatment_recommendations", [])[:3]
        for i, rec in enumerate(recommendations, 1):
            name = rec.get("name", "Unknown Treatment")
            confidence = rec.get("confidence_score", 0) * 100
            recommendations_html += f"""
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0;">
                    <div style="display: flex; align-items: center;">
                        <span style="background-color: #0ea5e9; color: white; border-radius: 50%; width: 24px; height: 24px; display: inline-block; text-align: center; line-height: 24px; font-size: 12px; font-weight: 600; margin-right: 12px;">{i}</span>
                        <span style="color: #334155; font-weight: 500;">{name}</span>
                    </div>
                    <div style="margin-top: 4px; margin-left: 36px;">
                        <span style="color: #64748b; font-size: 13px;">Confidence: {confidence:.0f}%</span>
                    </div>
                </td>
            </tr>
            """

        # Build key findings HTML
        key_findings_html = ""
        for finding in key_findings[:5]:
            key_findings_html += f"""
            <li style="margin-bottom: 8px; color: #334155;">{finding}</li>
            """

        content = f"""
        <div style="text-align: center; margin-bottom: 32px;">
            <div style="background-color: #dcfce7; border-radius: 50%; width: 64px; height: 64px; margin: 0 auto 16px; display: flex; align-items: center; justify-content: center;">
                <span style="color: #16a34a; font-size: 32px;">&#10003;</span>
            </div>
            <h2 style="margin: 0; color: #0f172a; font-size: 20px; font-weight: 600;">
                Analysis Complete
            </h2>
            <p style="margin: 8px 0 0 0; color: #64748b; font-size: 14px;">
                AI-powered analysis has been completed for this patient
            </p>
        </div>

        <!-- Patient Info -->
        <div style="background-color: #f8fafc; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td width="50%">
                        <p style="margin: 0; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Patient Name</p>
                        <p style="margin: 4px 0 0 0; color: #0f172a; font-size: 16px; font-weight: 600;">{patient_name}</p>
                    </td>
                    <td width="50%">
                        <p style="margin: 0; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Patient ID</p>
                        <p style="margin: 4px 0 0 0; color: #0f172a; font-size: 16px; font-weight: 600;">{patient_id}</p>
                    </td>
                </tr>
            </table>
        </div>

        <!-- Stats -->
        <div style="margin-bottom: 24px;">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td width="50%" style="padding-right: 8px;">
                        <div style="background-color: #eff6ff; border-radius: 8px; padding: 16px; text-align: center;">
                            <p style="margin: 0; color: #3b82f6; font-size: 28px; font-weight: 700;">{recommendations_count}</p>
                            <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">Treatment Options</p>
                        </div>
                    </td>
                    <td width="50%" style="padding-left: 8px;">
                        <div style="background-color: #f0fdf4; border-radius: 8px; padding: 16px; text-align: center;">
                            <p style="margin: 0; color: #16a34a; font-size: 28px; font-weight: 700;">{trials_count}</p>
                            <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">Clinical Trials</p>
                        </div>
                    </td>
                </tr>
            </table>
        </div>

        <!-- Summary -->
        {f'''
        <div style="margin-bottom: 24px;">
            <h3 style="margin: 0 0 12px 0; color: #0f172a; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                Analysis Summary
            </h3>
            <div style="background-color: #f8fafc; border-radius: 8px; padding: 16px;">
                <p style="margin: 0; color: #334155; line-height: 1.6;">{summary}</p>
            </div>
        </div>
        ''' if summary else ''}

        <!-- Key Findings -->
        {f'''
        <div style="margin-bottom: 24px;">
            <h3 style="margin: 0 0 12px 0; color: #0f172a; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                Key Findings
            </h3>
            <div style="background-color: #fefce8; border-radius: 8px; padding: 16px;">
                <ul style="margin: 0; padding-left: 20px;">
                    {key_findings_html}
                </ul>
            </div>
        </div>
        ''' if key_findings_html else ''}

        <!-- Top Recommendations -->
        <div style="margin-bottom: 24px;">
            <h3 style="margin: 0 0 12px 0; color: #0f172a; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                Top Treatment Recommendations
            </h3>
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8fafc; border-radius: 8px; overflow: hidden;">
                {recommendations_html if recommendations_html else '<tr><td style="padding: 16px; color: #64748b; text-align: center;">No recommendations available</td></tr>'}
            </table>
        </div>

        <!-- CTA Button -->
        <div style="text-align: center; margin-top: 32px;">
            <a href="http://localhost:3000/patients/{patient_id}" style="display: inline-block; background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 14px;">
                View Full Analysis
            </a>
        </div>
        """
        return self._get_base_template(content)

    def _get_patient_opened_template(self, patient_name: str, patient_id: str) -> str:
        """Generate HTML content for patient file opened email."""
        content = f"""
        <div style="text-align: center; margin-bottom: 32px;">
            <div style="background-color: #dbeafe; border-radius: 50%; width: 64px; height: 64px; margin: 0 auto 16px; display: flex; align-items: center; justify-content: center;">
                <span style="color: #2563eb; font-size: 28px;">&#128196;</span>
            </div>
            <h2 style="margin: 0; color: #0f172a; font-size: 20px; font-weight: 600;">
                Patient File Opened
            </h2>
            <p style="margin: 8px 0 0 0; color: #64748b; font-size: 14px;">
                A patient record has been accessed
            </p>
        </div>

        <!-- Patient Info -->
        <div style="background-color: #f8fafc; border-radius: 8px; padding: 24px; margin-bottom: 24px;">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td>
                        <p style="margin: 0; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Patient Name</p>
                        <p style="margin: 4px 0 0 0; color: #0f172a; font-size: 18px; font-weight: 600;">{patient_name}</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding-top: 16px;">
                        <p style="margin: 0; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Patient ID</p>
                        <p style="margin: 4px 0 0 0; color: #0f172a; font-size: 16px; font-weight: 500;">{patient_id}</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding-top: 16px;">
                        <p style="margin: 0; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Opened At</p>
                        <p style="margin: 4px 0 0 0; color: #0f172a; font-size: 16px; font-weight: 500;">{datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
                    </td>
                </tr>
            </table>
        </div>

        <!-- CTA Button -->
        <div style="text-align: center; margin-top: 32px;">
            <a href="http://localhost:3000/patients/{patient_id}" style="display: inline-block; background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 14px;">
                View Patient Record
            </a>
        </div>
        """
        return self._get_base_template(content)

    def _get_patient_closed_template(self, patient_name: str, patient_id: str) -> str:
        """Generate HTML content for patient file closed email."""
        content = f"""
        <div style="text-align: center; margin-bottom: 32px;">
            <div style="background-color: #fef3c7; border-radius: 50%; width: 64px; height: 64px; margin: 0 auto 16px; display: flex; align-items: center; justify-content: center;">
                <span style="color: #d97706; font-size: 28px;">&#128194;</span>
            </div>
            <h2 style="margin: 0; color: #0f172a; font-size: 20px; font-weight: 600;">
                Patient File Closed
            </h2>
            <p style="margin: 8px 0 0 0; color: #64748b; font-size: 14px;">
                Session ended for patient record
            </p>
        </div>

        <!-- Patient Info -->
        <div style="background-color: #f8fafc; border-radius: 8px; padding: 24px; margin-bottom: 24px;">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td>
                        <p style="margin: 0; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Patient Name</p>
                        <p style="margin: 4px 0 0 0; color: #0f172a; font-size: 18px; font-weight: 600;">{patient_name}</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding-top: 16px;">
                        <p style="margin: 0; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Patient ID</p>
                        <p style="margin: 4px 0 0 0; color: #0f172a; font-size: 16px; font-weight: 500;">{patient_id}</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding-top: 16px;">
                        <p style="margin: 0; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Closed At</p>
                        <p style="margin: 4px 0 0 0; color: #0f172a; font-size: 16px; font-weight: 500;">{datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
                    </td>
                </tr>
            </table>
        </div>

        <!-- CTA Button -->
        <div style="text-align: center; margin-top: 32px;">
            <a href="http://localhost:3000/patients" style="display: inline-block; background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 14px;">
                View All Patients
            </a>
        </div>
        """
        return self._get_base_template(content)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        """Send an email using SendGrid.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self._enabled:
            logger.warning("Email service is disabled, skipping send")
            return False

        try:
            message = Mail(
                from_email=settings.SENDGRID_FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )

            response = self._client.send(message)

            if response.status_code in (200, 201, 202):
                logger.info(f"Email sent successfully to {to_email} (status: {response.status_code})")
                return True
            else:
                logger.error(f"Failed to send email: status {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False

    async def send_analysis_complete_notification(
        self,
        to_email: str,
        patient_name: str,
        patient_id: str,
        analysis_summary: Dict[str, Any]
    ) -> bool:
        """Send notification when analysis is complete."""
        subject = f"Analysis Complete - {patient_name}"
        html_content = self._get_analysis_complete_template(
            patient_name=patient_name,
            patient_id=patient_id,
            analysis_summary=analysis_summary
        )
        return await self.send_email(to_email, subject, html_content)

    async def send_patient_opened_notification(
        self,
        to_email: str,
        patient_name: str,
        patient_id: str
    ) -> bool:
        """Send notification when patient file is opened."""
        subject = f"Patient File Opened - {patient_name}"
        html_content = self._get_patient_opened_template(
            patient_name=patient_name,
            patient_id=patient_id
        )
        return await self.send_email(to_email, subject, html_content)

    async def send_patient_closed_notification(
        self,
        to_email: str,
        patient_name: str,
        patient_id: str
    ) -> bool:
        """Send notification when patient file is closed."""
        subject = f"Patient File Closed - {patient_name}"
        html_content = self._get_patient_closed_template(
            patient_name=patient_name,
            patient_id=patient_id
        )
        return await self.send_email(to_email, subject, html_content)


# Global email service instance
email_service = EmailService()


def get_email_service() -> EmailService:
    """Get the global email service instance."""
    return email_service
