"""
Email Service for ResumeAI

This module provides email notification functionality for ResumeAI, supporting
different email providers (SMTP, Gmail, MailerSend) and allowing for digest emails
to be sent after processing.
"""

import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional, Any, Union
from datetime import datetime

from app.config import email_config, EMAIL_ENABLED

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""

    def __init__(self):
        """Initialize the email service."""
        self.enabled = EMAIL_ENABLED
        self.config = email_config
        logger.info(f"Email service initialized. Enabled: {self.enabled}")

    def _create_smtp_connection(self):
        """Create an SMTP connection based on the current configuration."""
        if self.config.provider == "gmail":
            smtp_host = "smtp.gmail.com"
            smtp_port = 587
        else:  # default to configured SMTP settings
            smtp_host = self.config.smtp_host
            smtp_port = self.config.smtp_port

        # Create connection
        try:
            connection = smtplib.SMTP(smtp_host, smtp_port)
            
            # Use TLS if configured
            if self.config.smtp_use_tls:
                context = ssl.create_default_context()
                connection.starttls(context=context)
            
            # Login if credentials are provided
            if self.config.username and self.config.password:
                connection.login(self.config.username, self.config.password)
            
            return connection
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {str(e)}")
            raise

    def send_email(self, subject: str, recipients: Optional[List[str]] = None, 
                  html_content: str = "", text_content: str = "") -> bool:
        """
        Send an email with the given subject and content.
        
        Args:
            subject: Email subject
            recipients: List of recipient email addresses (overrides config if provided)
            html_content: HTML content of the email
            text_content: Plain text content of the email
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info("Email service is disabled. Not sending email.")
            return False
            
        if not recipients and not self.config.recipients:
            logger.warning("No recipients specified. Not sending email.")
            return False
            
        if not html_content and not text_content:
            logger.warning("No email content provided. Not sending email.")
            return False
            
        # Use configuration recipients if none provided
        if not recipients:
            recipients = [email.strip() for email in self.config.recipients.split(',') if email.strip()]
            
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = ", ".join(recipients)
            
            # Add text and HTML parts
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            if html_content:
                msg.attach(MIMEText(html_content, 'html'))
                
            # Send email based on provider
            if self.config.provider == "mailersend":
                self._send_mailersend(msg, recipients)
            else:  # smtp or gmail
                self._send_smtp(msg, recipients)
                
            logger.info(f"Email sent successfully to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
            
    def _send_smtp(self, msg: MIMEMultipart, recipients: List[str]) -> None:
        """Send email using SMTP."""
        with self._create_smtp_connection() as connection:
            connection.send_message(msg)
            
    def _send_mailersend(self, msg: MIMEMultipart, recipients: List[str]) -> None:
        """Send email using MailerSend API."""
        try:
            # Import inside the method to avoid dependency requirements for those not using MailerSend
            import requests
            
            # Check if we have an API key (stored in username for MailerSend)
            if not self.config.username:
                raise Exception("MailerSend API key is required (set in the Username field)")
            
            # Convert MIME message to MailerSend API format
            data = {
                "from": {"email": self.config.from_email, "name": self.config.from_name},
                "to": [{"email": recipient} for recipient in recipients],
                "subject": msg["Subject"],
            }
            
            # Add text and HTML content
            for part in msg.get_payload():
                if part.get_content_type() == "text/plain":
                    data["text"] = part.get_payload(decode=True).decode()
                elif part.get_content_type() == "text/html":
                    data["html"] = part.get_payload(decode=True).decode()
            
            # Send request to MailerSend API
            response = requests.post(
                "https://api.mailersend.com/v1/email",
                json=data,
                headers={
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest", 
                    "Authorization": f"Bearer {self.config.username}"  # Use username field for API key
                }
            )
            
            # Log detailed information for debugging
            logger.info(f"MailerSend API response: {response.status_code}")
            
            if response.status_code >= 400:
                raise Exception(f"MailerSend API error: {response.status_code} - {response.text}")
                
        except ImportError:
            logger.error("Requests library not installed. Cannot use MailerSend provider.")
            raise
        except Exception as e:
            logger.error(f"Failed to send email via MailerSend: {str(e)}")
            raise
            
    def send_digest(self, processed_vacancies: List[Dict[str, Any]], 
                    processing_stats: Dict[str, Any]) -> bool:
        """
        Send a digest email with processing results.
        
        Args:
            processed_vacancies: List of processed vacancy data
            processing_stats: Dictionary of processing statistics
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.enabled or not processed_vacancies:
            return False
        
        # Filter to only include Open vacancies
        open_vacancies = []
        for vacancy in processed_vacancies:
            # Check for status in both lowercase and uppercase format
            status = vacancy.get("status") or vacancy.get("Status", "")
            if status == "Open":
                open_vacancies.append(vacancy)
        
        # Only proceed if there are open vacancies to report
        if not open_vacancies:
            logger.info("No open vacancies to include in digest email. Not sending.")
            return False
            
        # Create subject with count of open vacancies
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        subject = f"{self.config.digest_subject} - {len(open_vacancies)} Open Vacancies - {now}"
        
        # Create content with filtered vacancies
        html_content = self._create_digest_html(open_vacancies, processing_stats)
        text_content = self._create_digest_text(open_vacancies, processing_stats)
        
        # Send email
        return self.send_email(subject, html_content=html_content, text_content=text_content)
        
    def _create_digest_html(self, processed_vacancies: List[Dict[str, Any]], 
                          processing_stats: Dict[str, Any]) -> str:
        """Create HTML content for digest email."""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .stats {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .highlight {{ color: #2980b9; font-weight: bold; }}
                .reject {{ color: #e74c3c; }}
                .match {{ color: #27ae60; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>ResumeAI Processing Results</h1>
                <p>The ResumeAI system has found {len(processed_vacancies)} open vacancies with potential matches.</p>
                
                <div class="stats">
                    <h2>Processing Statistics</h2>
                    <p>Total time: <span class="highlight">{processing_stats.get('total_time', 'N/A')}</span></p>
                    <p>Token usage: <span class="highlight">{processing_stats.get('token_usage', 'N/A')}</span></p>
                </div>
                
                <h2>Processed Vacancies</h2>
                <table>
                    <tr>
                        <th>Vacancy</th>
                        <th>Client</th>
                        <th>Status</th>
                        <th>Top Match</th>
                        <th>Checked Resumes</th>
                        <th>Spinweb Link</th>
                        <th>Details</th>
                    </tr>
        """
        
        # Add rows for each vacancy
        for vacancy in processed_vacancies:
            # Get status in a case-insensitive way since database columns might vary
            status = vacancy.get("status") or vacancy.get("Status", "N/A")
            status_class = "match" if status == "Open" else "reject"
            
            # Get values with fallbacks for different field name variations
            functie = vacancy.get('functie') or vacancy.get('Functie', 'N/A')
            klant = vacancy.get('klant') or vacancy.get('Klant', 'N/A')
            top_match = vacancy.get('top_match') or vacancy.get('Top_Match', 'N/A')
            resumes = vacancy.get('checked_resumes') or vacancy.get('Checked_resumes', 'N/A')
            
            # Get URL and ID for links
            url = vacancy.get('url') or vacancy.get('Url', '')
            vacancy_id = vacancy.get('id', '') # Database ID for the details page
            
            # Create links with styling
            spinweb_link = f"https://{url}" if url else "#"
            detail_link = f"http://localhost:3000/vacancies/{vacancy_id}" if vacancy_id else "#"
            
            # Create styled link buttons
            spinweb_button = f'<a href="{spinweb_link}" target="_blank" style="display:inline-block; padding:4px 8px; background-color:#3498db; color:white; border-radius:4px; text-decoration:none; font-size:12px;">Spinweb</a>'
            detail_button = f'<a href="{detail_link}" target="_blank" style="display:inline-block; padding:4px 8px; background-color:#2ecc71; color:white; border-radius:4px; text-decoration:none; font-size:12px;">Details</a>'
            
            html += f"""
                <tr>
                    <td>{functie}</td>
                    <td>{klant}</td>
                    <td class="{status_class}">{status}</td>
                    <td>{top_match}</td>
                    <td>{resumes}</td>
                    <td>{spinweb_button}</td>
                    <td>{detail_button}</td>
                </tr>
            """
        
        html += """
                </table>
                
                <p>This is an automated email from the ResumeAI system.</p>
            </div>
        </body>
        </html>
        """
        
        return html
        
    def _create_digest_text(self, processed_vacancies: List[Dict[str, Any]], 
                           processing_stats: Dict[str, Any]) -> str:
        """Create plain text content for digest email."""
        text = f"""
ResumeAI Processing Results
==========================

The ResumeAI system has found {len(processed_vacancies)} open vacancies with potential matches.

Processing Statistics:
- Total time: {processing_stats.get('total_time', 'N/A')}
- Token usage: {processing_stats.get('token_usage', 'N/A')}

Processed Vacancies:
        """
        
        # Add info for each vacancy
        for vacancy in processed_vacancies:
            # Get values with fallbacks for different field name variations
            functie = vacancy.get('functie') or vacancy.get('Functie', 'N/A')
            klant = vacancy.get('klant') or vacancy.get('Klant', 'N/A')
            status = vacancy.get("status") or vacancy.get("Status", "N/A")
            top_match = vacancy.get('top_match') or vacancy.get('Top_Match', 'N/A')
            resumes = vacancy.get('checked_resumes') or vacancy.get('Checked_resumes', 'N/A')
            
            # Get URL and ID for links
            url = vacancy.get('url') or vacancy.get('Url', '')
            vacancy_id = vacancy.get('id', '') # Database ID for the details page
            
            # Create links for text version
            spinweb_link = f"https://{url}" if url else "N/A"
            detail_link = f"http://localhost:3000/vacancies/{vacancy_id}" if vacancy_id else "N/A"
            
            text += f"""
- {functie} at {klant}
  Status: {status}
  Top Match: {top_match}
  Checked Resumes: {resumes}
  Spinweb: {spinweb_link}
  Details: {detail_link}
            """
        
        text += """
This is an automated email from the ResumeAI system.
        """
        
        return text


# Create a global instance of the service
email_service = EmailService()