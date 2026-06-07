#!/usr/bin/env python3
"""
SELA IMAP Listener
Polls an email inbox for booth form submissions and queues them for verification.

Usage:
    python sela_imap_listener.py

Environment Variables:
    IMAP_HOST: IMAP server hostname (default: imap.gmail.com)
    IMAP_PORT: IMAP server port (default: 993)
    IMAP_EMAIL: Email address to authenticate
    IMAP_PASSWORD: Email password or app-specific password
    IMAP_MAILBOX: Mailbox name to poll (default: SELA_Reports)
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from imapclient import IMAPClient
from loguru import logger
import dotenv

# Load environment variables
dotenv.load_dotenv()

logger.add("logs/imap_listener.log", rotation="500 MB")


class SELAIMAPListener:
    """Polls IMAP inbox for SELA booth form submissions."""

    def __init__(
        self,
        imap_host: str = os.getenv("IMAP_HOST", "imap.gmail.com"),
        imap_port: int = int(os.getenv("IMAP_PORT", "993")),
        email: str = os.getenv("IMAP_EMAIL"),
        password: str = os.getenv("IMAP_PASSWORD"),
        mailbox: str = os.getenv("IMAP_MAILBOX", "SELA_Reports"),
    ):
        """
        Initialize IMAP listener.
        
        Args:
            imap_host: IMAP server hostname
            imap_port: IMAP server port (usually 993 for SSL)
            email: Email address to authenticate
            password: Email password or app-specific password
            mailbox: Mailbox name to poll
        """
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.email = email
        self.password = password
        self.mailbox = mailbox
        self.client = None
        self.processed_ids = set()

    def connect(self) -> bool:
        """Connect to IMAP server."""
        try:
            self.client = IMAPClient(self.imap_host, self.imap_port, use_uid=True)
            self.client.login(self.email, self.password)
            logger.info(f"Connected to {self.imap_host} as {self.email}")
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect from IMAP server."""
        if self.client:
            self.client.logout()
            logger.info("Disconnected from IMAP server")

    def parse_form_submission(self, email_body: str) -> Optional[Dict]:
        """
        Parse structured email form submission.
        Expected format:
        
        WHAT: Odor
        WHERE: South Gate High School
        WHEN: 2024-06-07T14:30:00
        WHO: Big diesel truck idling
        
        Returns:
            Dict with parsed fields and metadata, or None if parsing fails
        """
        try:
            lines = email_body.strip().split("\n")
            report = {}
            
            for line in lines:
                if line.startswith("WHAT:"):
                    report["what"] = line.replace("WHAT:", "").strip()
                elif line.startswith("WHERE:"):
                    report["where"] = line.replace("WHERE:", "").strip()
                elif line.startswith("WHEN:"):
                    report["when"] = line.replace("WHEN:", "").strip()
                elif line.startswith("WHO:"):
                    report["who"] = line.replace("WHO:", "").strip()
            
            # Validate required fields
            if all(key in report for key in ["what", "where", "when", "who"]):
                # Generate unique hash ID
                hash_input = f"{report['where']}_{report['when']}_{report['who']}"
                report["_id"] = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
                report["timestamp"] = datetime.utcnow().isoformat()
                report["status"] = "PENDING_VERIFICATION"
                logger.info(f"Parsed report {report['_id']}: {report['what']} @ {report['where']}")
                return report
        except Exception as e:
            logger.error(f"Failed to parse form submission: {e}")
        
        return None

    def fetch_new_reports(self) -> List[Dict]:
        """
        Fetch unread emails from SELA_Reports mailbox.
        Returns list of parsed report dictionaries.
        """
        reports = []
        
        try:
            # Select mailbox
            self.client.select_folder(self.mailbox)
            
            # Search for unseen messages
            uids = self.client.search("UNSEEN")
            logger.info(f"Found {len(uids)} new emails in {self.mailbox}")
            
            for uid in uids:
                try:
                    # Fetch email
                    message_data = self.client.fetch([uid], [b"RFC822", b"BODY[]"])
                    email_body = message_data[uid][b"RFC822"].decode("utf-8", errors="ignore")
                    
                    # Extract text body (simplified)
                    body_start = email_body.find("\n\n")
                    if body_start != -1:
                        body_text = email_body[body_start:]
                    else:
                        body_text = email_body
                    
                    # Parse form
                    report = self.parse_form_submission(body_text)
                    if report:
                        reports.append(report)
                        logger.info(f"Queued report {report['_id']} for verification")
                        
                        # Mark as read
                        self.client.set_flags([uid], [b"\\\\Seen"])
                    else:
                        logger.warning(f"Failed to parse email UID {uid}")
                
                except Exception as e:
                    logger.error(f"Error processing email UID {uid}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to fetch new reports: {e}")
        
        return reports

    def queue_reports(self, reports: List[Dict]) -> bool:
        """
        Write reports to queue file (JSON Lines format).
        Each report is written as a single JSON line.
        """
        try:
            os.makedirs("data", exist_ok=True)
            
            with open("data/verification_queue.jsonl", "a") as f:
                for report in reports:
                    f.write(json.dumps(report) + "\n")
            
            logger.info(f"Queued {len(reports)} reports for verification")
            return True
        except Exception as e:
            logger.error(f"Failed to queue reports: {e}")
            return False

    def run(self, interval_seconds: int = 30):
        """
        Run continuous listener loop.
        
        Args:
            interval_seconds: Poll interval (default 30 seconds)
        """
        import time
        
        if not self.connect():
            logger.error("Failed to connect. Exiting.")
            return
        
        try:
            logger.info(f"Starting listener loop (polling every {interval_seconds}s)")
            while True:
                reports = self.fetch_new_reports()
                if reports:
                    self.queue_reports(reports)
                
                logger.debug(f"Sleeping for {interval_seconds} seconds...")
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            logger.info("Listener interrupted by user.")
        
        finally:
            self.disconnect()


if __name__ == "__main__":
    listener = SELAIMAPListener()
    listener.run(interval_seconds=30)
