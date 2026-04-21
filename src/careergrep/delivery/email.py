"""Email digest delivery via Gmail SMTP."""

import os
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from careergrep.config import Settings
from careergrep.models import Job

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def render_digest(jobs: list[Job], settings: Settings) -> str:
    """Render the HTML email digest from the Jinja2 template."""
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("digest.html")
    us_jobs = [j for j in jobs if j.is_us_job()]
    intl_jobs = [j for j in jobs if not j.is_us_job()]
    return template.render(
        us_jobs=us_jobs,
        intl_jobs=intl_jobs,
        total=len(jobs),
        date=date.today().strftime("%A, %B %d, %Y"),
        max_age_hours=settings.filters.max_age_hours,
    )


def send_digest(jobs: list[Job], settings: Settings) -> None:
    """Send the job digest email via SMTP.

    Credentials come from environment variables (SMTP_USER, SMTP_PASSWORD),
    not from config.yaml — secrets should never be in version control.
    """
    email_cfg = settings.delivery.email
    if not email_cfg.enabled:
        print("Email delivery is disabled in config.")
        return

    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    if not smtp_user or not smtp_password:
        print("Warning: SMTP_USER and SMTP_PASSWORD must be set in .env")
        print("Skipping email delivery. Printing digest to stdout instead.\n")
        print(render_digest(jobs, settings))
        return

    html_body = render_digest(jobs, settings)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"careergrep: {len(jobs)} job{'s' if len(jobs) != 1 else ''} — {date.today().strftime('%b %d')}"
    msg["From"] = email_cfg.from_
    msg["To"] = email_cfg.to
    msg.attach(MIMEText(html_body, "html"))

    # Python's smtplib is the stdlib SMTP client — similar to PHPMailer/SwiftMailer
    # but built in. STARTTLS upgrades the connection to encrypted after connecting.
    with smtplib.SMTP(email_cfg.smtp_host, email_cfg.smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    print(f"Digest sent to {email_cfg.to}")
