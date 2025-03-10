# ResumeAI Email Notifications

This document describes the email notification system for ResumeAI, which provides digest emails after processing resumes and vacancies.

> **IMPORTANT:** When running in Docker mode, make sure PG_HOST is set to "db" in your environment configuration. The Docker containers communicate within their own network where the database is accessible at hostname "db", not "localhost".

## Features

- **Digest Emails**: Automatically send digest emails with processing results when the scheduled process completes
- **Multiple Email Providers**: Support for SMTP, Gmail, and MailerSend
- **Configurable Settings**: Easy configuration via the Settings page in the UI
- **Test Email Functionality**: Send test emails to verify configuration
- **Customizable Recipients**: Add multiple email recipients for notifications
- **HTML and Text Formats**: All emails are sent in both HTML and plain text formats

## Configuration

All email settings can be configured in the Settings page of the ResumeAI web interface:

1. **Email Provider**: Choose between SMTP, Gmail, or MailerSend
2. **Connection Settings**: Configure SMTP host, port, TLS, etc.
3. **Authentication**: Set username, password, or API key
4. **Sender Information**: Configure the From name and email address
5. **Recipients**: Comma-separated list of email recipients
6. **Digest Subject**: Customize the subject line for digest emails (date will be appended)

## Environment Variables

Email functionality can also be configured through environment variables in the `.env` file:

```
EMAIL_ENABLED=true
EMAIL_PROVIDER=smtp
EMAIL_SMTP_HOST=smtp.example.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USE_TLS=true
EMAIL_USERNAME=your_username
EMAIL_PASSWORD=your_password
EMAIL_FROM_EMAIL=resumeai@example.com
EMAIL_FROM_NAME=ResumeAI
EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com
EMAIL_DIGEST_SUBJECT=ResumeAI - New Processing Results
```

## Digest Email Content

The digest emails include:
- List of processed vacancies and their status
- Top match details for each vacancy
- Processing statistics (tokens used, time taken)
- Processing date and time

## Implementation Details

1. **Email Service**: `app/services/email_service.py` - Handles all email functionality
2. **Configuration**: Email settings added to `app/config.py`
3. **API Routes**: Email settings and test endpoints in `app/routers/settings.py`
4. **UI Component**: Email settings section in the Settings page (`frontend/src/pages/Settings.js`)
5. **Integration**: Automatic email sending at the end of processing in `app/combined_process.py`

## Security Considerations

- Email passwords are masked in the UI and stored securely
- TLS encryption is enabled by default for SMTP connections
- Configuration is validated to prevent common issues

## Testing

You can test the email functionality using the "Send Test Email" button in the Settings page, which allows sending a test message to verify your configuration is working correctly.

## Troubleshooting

### Database Connection Issues in Docker

If you see errors like:
```
Error connecting to PostgreSQL: connection to server at "db" (172.19.0.3), port 5432 failed: FATAL: password authentication failed for user "postgres"
```

This usually happens when:
1. The root `.env` file is overriding the Docker database configuration
2. The backend container is trying to connect to "db" but using credentials from your host's `.env` file

**Solution:**
1. For Docker operation, edit your `.env` file to set `PG_HOST=db` or
2. Create a separate `.env.docker` file with correct settings and mount only that file in docker-compose.yml:
   ```yaml
   volumes:
     - ./backend:/app
     - ./backend/.env.docker:/app/.env
   ```

### Email Authentication Errors

If you see errors related to email authentication:

1. **SMTP/Gmail**: Check your username and password. For Gmail, you may need to use an app password rather than your regular password.
2. **MailerSend**: Make sure your API key is entered in the Username field (not the Password field).

For MailerSend users: the API key must be placed in the Username field. The Password field is ignored for MailerSend connections.