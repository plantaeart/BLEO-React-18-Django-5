import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from utils.logger import Logger
from models.enums.LogType import LogType
import os

class EmailService:
    """Email service for sending verification emails"""
    
    @staticmethod
    def send_email(to_email, subject, html_content, text_content=None):
        """Send email using SMTP"""
        try:
            # Email configuration from environment variables
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            from_email = os.getenv('FROM_EMAIL', smtp_username)
            
            if not smtp_username or not smtp_password:
                Logger.debug_error(
                    "Email sending failed: SMTP credentials not configured",
                    500,
                    None,
                    "SERVER"
                )
                return False
            
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = from_email
            message['To'] = to_email
            
            # Add text and HTML content
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                message.attach(text_part)
            
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(message)
            
            Logger.debug_system_action(
                f"Email sent successfully to: {to_email[:3]}***@{to_email.split('@')[1]}",
                LogType.SUCCESS.value,
                200
            )
            
            return True
            
        except Exception as e:
            Logger.debug_error(
                f"Email sending failed: {str(e)}",
                500,
                None,
                "SERVER"
            )
            return False
    
    @staticmethod
    def send_verification_email(user_email, username, verification_token):
        """Send email verification email"""
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{base_url}/verify-email?token={verification_token}"
        
        subject = "Verify Your BLEO Account"
        
        html_content = f"""
        <h2>Welcome to BLEO, {username}!</h2>
        <p>Please verify your email address to activate your account.</p>
        <p><a href="{verification_url}" style="background: #4A90E2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
        <p>This link expires in 24 hours.</p>
        """
        
        text_content = f"""
        Welcome to BLEO, {username}!
        
        Please verify your email address: {verification_url}
        
        This link expires in 24 hours.
        """
        
        return EmailService.send_email(user_email, subject, html_content, text_content)