# Send email using an external SMTP server

import logging
import smtplib
from email.message import EmailMessage

log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)  # Set our own level separately

def send_email(smtp_server, sender, password, from_address, to_address, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address

    # Send the message via SMTP over SSL connection
    log.info(f"Sending email to {to_address}")
    with smtplib.SMTP_SSL(smtp_server, 465) as smtp_server:
        try:
            smtp_server.login(sender, password)
            smtp_server.sendmail(from_address, to_address, msg.as_string())
        except Exception as e:
            log.error(f"Error sending email to {to_address}")
            log.error(e)
        else:
            log.info(f"Successfully sent email to {to_address}")
