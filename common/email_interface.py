# Send email using an external SMTP server
# TODO: Move SMTP .env data here and simplify send_email parameters

import smtplib
from email.message import EmailMessage

def send_email(smtp_server, sender, password, from_address, to_address, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address

    # Send the message via SMTP over SSL connection
    with smtplib.SMTP_SSL(smtp_server, 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(from_address, to_address, msg.as_string())
