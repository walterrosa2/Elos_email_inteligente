import email
from typing import List, Optional, Tuple
from datetime import date
from imapclient import IMAPClient
from loguru import logger
from app.core.config import settings

class IMAPService:
    def __init__(self):
        self.host = settings.IMAP_SERVER
        self.port = settings.IMAP_PORT
        self.user = settings.IMAP_USER
        self.ssl = True # Defaulting to True for now as config doesn't have it explicitly but port 993 implies it
        self.folder = "INBOX" # Default or add to settings
        self.client: Optional[IMAPClient] = None

    def connect(self, password: str = None, retries: int = 2) -> None:
        """Connects to the IMAP server using either Basic Auth or OAuth2."""
        last_error = None
        for attempt in range(retries + 1):
            try:
                # Fallback to Outlook if not set (since we are debugging OAuth for Outlook)
                self.host = self.host or "outlook.office365.com"
                
                logger.info(f"Connecting to IMAP server: {self.host}:{self.port} (SSL={self.ssl}, Attempt={attempt+1}/{retries+1})")
                
                # Use a larger timeout for connection and commands
                self.client = IMAPClient(self.host, port=self.port, ssl=self.ssl, use_uid=True, timeout=60)

                # Check if we should use OAuth2 (Explicit flag OR if password is empty but client_id is present)
                use_oauth = settings.USE_OAUTH2 or (settings.AZURE_CLIENT_ID and not password)

                if use_oauth:
                    logger.info(f"Authenticating via OAuth2 (XOAUTH2) for {self.user}...")
                    token = self._get_oauth2_token()
                    if token:
                        logger.info("Token acquired. Sending AUTH command...")
                        self.client.oauth2_login(self.user, token)
                        logger.info("OAuth2 Login Successful.")
                    else:
                        raise ConnectionError("Failed to acquire OAuth2 token.")
                else:
                    logger.info(f"Logging in via Basic Auth as {self.user}...")
                    if not password:
                        raise ValueError("Password is required for Basic Auth.")
                    self.client.login(self.user, password)
                
                # Select folder (default INBOX)
                folder = self.folder or "INBOX"
                logger.info(f"Selecting folder: {folder}")
                self.client.select_folder(folder)
                
                # If we reach here, we succeeded
                return
                
            except Exception as e:
                last_error = e
                logger.error(f"IMAP Attempt {attempt+1} failed: {e}")
                if self.client:
                    try:
                        self.client.logout()
                    except:
                        pass
                
                if attempt < retries:
                    import time
                    wait_time = (attempt + 1) * 2
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        
        # All retries failed
        logger.error(f"IMAP Connection failed after all retries: {last_error}")
        raise last_error

    def _get_oauth2_token(self) -> Optional[str]:
        """Acquires OAuth2 token using MSAL with file-based persistence."""
        from msal import PublicClientApplication, SerializableTokenCache
        
        resource_scopes = ["https://outlook.office.com/IMAP.AccessAsUser.All"]
        # Use common if tenant not strict, but config usually has it
        tenant = settings.AZURE_TENANT_ID or "common" 
        authority = f"https://login.microsoftonline.com/{tenant}"
        
        # Ensure DATA_ROOT exists
        if not settings.DATA_ROOT.exists():
            settings.DATA_ROOT.mkdir(parents=True, exist_ok=True)

        cache_path = settings.DATA_ROOT / "token_cache.bin"
        cache = SerializableTokenCache()
        
        if cache_path.exists():
            try:
                cache.deserialize(cache_path.read_text())
                logger.debug(f"Loaded token cache from {cache_path}")
            except Exception as e:
                logger.warning(f"Failed to load token cache: {e}")

        # Helper to save cache
        def save_cache():
            if cache.has_state_changed:
                cache_path.write_text(cache.serialize())
                logger.info(f"Token cache saved to {cache_path}")

        app = PublicClientApplication(
            settings.AZURE_CLIENT_ID,
            authority=authority,
            token_cache=cache
        )

        # 1. Try silent first (from cache)
        accounts = app.get_accounts()
        if accounts:
            account = accounts[0]
            # Fallback for self.user if it was None
            if not self.user:
                self.user = account.get("username")
                logger.info(f"Detected user from cache: {self.user}")
            
            logger.info(f"Trying silent auth for {self.user}...")
            # CRITICAL: Do NOT include offline_access in silent auth - it's a reserved scope
            result = app.acquire_token_silent(resource_scopes, account=account)
            if result and "access_token" in result:
                logger.info("Silent auth successful.")
                save_cache()
                return result["access_token"]
            else:
                logger.warning("Silent auth failed. Refresh token might be expired.")

        # 2. Device Flow (Interactive)
        logger.info("Initiating Device Code Flow (Interactive)...")
        # Include offline_access here to ensure we get a refresh token
        request_scopes = resource_scopes + ["offline_access"]
        try:
            flow = app.initiate_device_flow(scopes=request_scopes)
            if "user_code" in flow:
                # IMPORTANT: Since we are running in Streamlit, we can't easily print to console if detatched.
                # Use logger and hopefully user checks logs, OR if running interactively we print.
                msg = f"""
                
                ================================================================
                OAUTH2 NECESSÁRIO
                {flow['message']}
                ================================================================
                """
                logger.warning(msg) 
                print(msg) # Print to terminal just in case
                
                result = app.acquire_token_by_device_flow(flow)
                if "access_token" in result:
                    save_cache()
                    return result["access_token"]
                else:
                    logger.error(f"Auth failed: {result.get('error_description')}")
        except Exception as e:
            logger.error(f"OAuth2 flow error: {e}")
            
        return None

    def disconnect(self) -> None:
        """Logs out and closes the connection."""
        if self.client:
            try:
                self.client.logout()
                logger.info("Disconnected from IMAP server.")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")

    def list_folders(self) -> List[Tuple]:
        """Lists available folders on the server."""
        if not self.client:
            raise ConnectionError("Not connected to IMAP server.")
        return self.client.list_folders()

    def search_candidates(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[int]:
        """
        Searches for email candidates based on settings and date range.
        If start_date and end_date are the same, searches that specific day.
        """
        if not self.client:
            raise ConnectionError("Not connected to IMAP server.")
        
        criteria_parts = []
        
        if start_date:
            criteria_parts.append(f'SINCE {start_date.strftime("%d-%b-%Y")}')
        
        if end_date:
            import datetime
            # IMAP BEFORE is exclusive, so we add 1 day to end_date to include it
            exclusive_end = end_date + datetime.timedelta(days=1)
            criteria_parts.append(f'BEFORE {exclusive_end.strftime("%d-%b-%Y")}')

        criteria = " ".join(criteria_parts) if criteria_parts else 'ALL'
            
        logger.info(f"Searching emails with criteria: {criteria}")
        try:
            messages = self.client.search(criteria)
            logger.info(f"Found {len(messages)} messages.")
            return messages
        except Exception as e:
            logger.error(f"Search failed with criteria {criteria}: {e}")
            if criteria_parts:
                logger.info("Retrying with ALL criteria...")
                return self.client.search('ALL')
            raise

    def fetch_message_data(self, msg_id: int) -> dict:
        """
        Fetches the raw email content (RFC822) and envelope data for a given ID.
        """
        if not self.client:
            raise ConnectionError("Not connected to IMAP server.")
            
        # Fetching structure and envelope can be lighter, but we need body for attachment checks.
        response = self.client.fetch([msg_id], ['RFC822'])
        
        if msg_id not in response:
            logger.warning(f"Message ID {msg_id} not found in fetch response.")
            return {}

        raw_content = response[msg_id][b'RFC822']
        email_message = email.message_from_bytes(raw_content)
        
        return {
            "msg_id": msg_id,
            "email_object": email_message,
            "subject": email_message.get("Subject", ""),
            "from": email_message.get("From", ""),
            "date": email_message.get("Date", "")
        }

    def get_email_body(self, email_message) -> str:
        """Extracts the plain text body from the email object with robust encoding detection."""
        body = ""
        
        def safe_decode(payload, declared_charset=None):
            if not payload:
                return ""
            
            # List of charsets to try in order
            # We start with the declared one, then UTF-8, then common Brazilian encodings
            charsets_to_try = []
            if declared_charset:
                charsets_to_try.append(declared_charset.lower())
            
            # Common ones if not already added
            for c in ["utf-8", "iso-8859-1", "windows-1252", "latin-1"]:
                if c not in charsets_to_try:
                    charsets_to_try.append(c)
            
            for charset in charsets_to_try:
                try:
                    # Try STRICT decoding first
                    return payload.decode(charset).strip()
                except (UnicodeDecodeError, LookupError):
                    continue
            
            # Last resort: decode with replacement to avoid crashing/empty body
            return payload.decode("utf-8", errors="replace").strip()

        html_body = ""
        plain_body = ""
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    # skip attachments
                    if "attachment" in content_disposition:
                        continue
                        
                    if content_type == "text/html":
                        payload = part.get_payload(decode=True)
                        html_body = safe_decode(payload, part.get_content_charset())
                    elif content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        plain_body = safe_decode(payload, part.get_content_charset())
                
                body = html_body if html_body else plain_body
            else:
                # Not multipart
                payload = email_message.get_payload(decode=True)
                if payload:
                    body = safe_decode(payload, email_message.get_content_charset())
        except Exception as e:
            logger.error(f"Error extracting body: {e}")
            
        return body.strip() or "[No readable body found]"
