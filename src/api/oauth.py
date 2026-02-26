"""
EVE ESI OAuth authentication for personal character data.

Handles the OAuth flow to get authenticated access to your character's:
- Current location
- Assets and inventory
- Market transactions
- Mining ledger
- Jump history
- etc.
"""
from __future__ import annotations

import webbrowser
import secrets
import hashlib
import base64
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
from typing import Optional
import requests
import os

# EVE SSO endpoints
AUTH_URL = "https://login.eveonline.com/v2/oauth/authorize"
TOKEN_URL = "https://login.eveonline.com/v2/oauth/token"
VERIFY_URL = "https://login.eveonline.com/oauth/verify"

# Your application should be registered at https://developers.eveonline.com/
# For now, using localhost callback for development
CALLBACK_HOST = "localhost"
CALLBACK_PORT = 8888
REDIRECT_URI = f"http://{CALLBACK_HOST}:{CALLBACK_PORT}/callback"

# Required scopes for full character access
SCOPES = [
    "esi-location.read_location.v1",
    "esi-location.read_ship_type.v1",
    "esi-location.read_online.v1",
    "esi-skills.read_skills.v1",
    "esi-skills.read_skillqueue.v1",
    "esi-wallet.read_character_wallet.v1",
    "esi-wallet.read_corporation_wallet.v1",
    "esi-search.search_structures.v1",
    "esi-clones.read_clones.v1",
    "esi-characters.read_contacts.v1",
    "esi-characters.read_standings.v1",
    "esi-killmails.read_killmails.v1",
    "esi-corporations.read_corporation_membership.v1",
    "esi-assets.read_assets.v1",
    "esi-planets.manage_planets.v1",
    "esi-fleets.read_fleet.v1",
    "esi-ui.open_window.v1",
    "esi-ui.write_waypoint.v1",
    "esi-characters.write_contacts.v1",
    "esi-fittings.read_fittings.v1",
    "esi-fittings.write_fittings.v1",
    "esi-markets.structure_markets.v1",
    "esi-corporations.read_structures.v1",
    "esi-characters.read_loyalty.v1",
    "esi-markets.read_character_orders.v1",
    "esi-characters.read_opportunities.v1",
    "esi-characters.read_chat_channels.v1",
    "esi-characters.read_medals.v1",
    "esi-characters.read_blueprints.v1",
    "esi-characters.read_corporation_roles.v1",
    "esi-location.read_station_structures.v1",
    "esi-universe.read_structures.v1",
    "esi-bookmarks.read_character_bookmarks.v1",
    "esi-contracts.read_character_contracts.v1",
    "esi-clones.read_implants.v1",
    "esi-characters.read_fatigue.v1",
    "esi-industry.read_character_jobs.v1",
    "esi-industry.read_corporation_jobs.v1",
]

TOKEN_FILE = "data/token.json"


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handles the OAuth callback from EVE SSO."""
    
    code: Optional[str] = None
    state: Optional[str] = None
    
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/callback":
            params = parse_qs(parsed.query)
            OAuthCallbackHandler.code = params.get("code", [None])[0]
            OAuthCallbackHandler.state = params.get("state", [None])[0]
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>EVE Login Success</title></head>
                <body style="font-family: Arial; text-align: center; margin-top: 50px;">
                    <h1>Authentication Successful!</h1>
                    <p>You can close this window and return to the application.</p>
                </body>
                </html>
            """)
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        # Suppress server logs
        pass


def generate_pkce() -> tuple[str, str]:
    """Generate PKCE code verifier and challenge."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return verifier, challenge


def start_oauth_flow(client_id: str) -> dict:
    """
    Start OAuth flow and return tokens.
    Opens browser for user to authenticate with EVE.
    Returns dict with access_token, refresh_token, character info, etc.
    """
    # Generate PKCE challenge
    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_urlsafe(32)
    
    # Build authorization URL
    auth_params = {
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "scope": " ".join(SCOPES),
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    auth_url = f"{AUTH_URL}?{urlencode(auth_params)}"
    
    print(f"\nOpening browser for EVE authentication...")
    print(f"If browser doesn't open, visit: {auth_url}\n")
    webbrowser.open(auth_url)
    
    # Start local server to receive callback
    server = HTTPServer((CALLBACK_HOST, CALLBACK_PORT), OAuthCallbackHandler)
    print(f"Waiting for authentication callback on {REDIRECT_URI}...")
    
    # Handle one request (the callback)
    server.handle_request()
    server.server_close()
    
    if not OAuthCallbackHandler.code:
        raise Exception("No authorization code received")
    
    if OAuthCallbackHandler.state != state:
        raise Exception("State mismatch - possible CSRF attack")
    
    # Exchange code for tokens
    token_data = {
        "grant_type": "authorization_code",
        "code": OAuthCallbackHandler.code,
        "client_id": client_id,
        "code_verifier": code_verifier,
    }
    
    resp = requests.post(TOKEN_URL, data=token_data, timeout=15)
    resp.raise_for_status()
    tokens = resp.json()
    
    # Verify token and get character info
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    verify_resp = requests.get(VERIFY_URL, headers=headers, timeout=15)
    verify_resp.raise_for_status()
    character_info = verify_resp.json()
    
    # Combine tokens and character info
    result = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "expires_at": time.time() + tokens["expires_in"],
        "character_id": character_info["CharacterID"],
        "character_name": character_info["CharacterName"],
        "character_owner_hash": character_info["CharacterOwnerHash"],
        "scopes": character_info.get("Scopes", "").split(),
    }
    
    return result


def refresh_access_token(client_id: str, refresh_token: str) -> dict:
    """
    Use refresh token to get a new access token.
    Returns updated token dict.
    """
    token_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }
    
    resp = requests.post(TOKEN_URL, data=token_data, timeout=15)
    resp.raise_for_status()
    tokens = resp.json()
    
    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token", refresh_token),
        "expires_at": time.time() + tokens["expires_in"],
    }


def save_tokens(token_data: dict):
    """Save tokens to file."""
    os.makedirs("data", exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)


def load_tokens() -> Optional[dict]:
    """Load tokens from file."""
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None


def ensure_valid_token(client_id: str) -> dict:
    """
    Ensure we have a valid access token.
    Loads from file if available, refreshes if expired, or starts new OAuth flow.
    Returns current token data.
    """
    tokens = load_tokens()
    
    # No saved tokens - start OAuth flow
    if not tokens:
        print("No saved authentication found. Starting login process...")
        tokens = start_oauth_flow(client_id)
        save_tokens(tokens)
        print(f"✓ Authenticated as {tokens['character_name']}")
        return tokens
    
    # Token expired - refresh it
    if time.time() >= tokens.get("expires_at", 0):
        print("Access token expired. Refreshing...")
        try:
            refreshed = refresh_access_token(client_id, tokens["refresh_token"])
            tokens.update(refreshed)
            save_tokens(tokens)
            print("✓ Token refreshed")
        except Exception as e:
            print(f"Failed to refresh token: {e}")
            print("Starting new login process...")
            tokens = start_oauth_flow(client_id)
            save_tokens(tokens)
            print(f"✓ Authenticated as {tokens['character_name']}")
    
    return tokens


def get_authenticated_session(client_id: str) -> tuple[requests.Session, dict]:
    """
    Get an authenticated requests session and character info.
    Returns (session, character_info)
    """
    tokens = ensure_valid_token(client_id)
    
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {tokens['access_token']}",
        "User-Agent": "eve-arbitrage-bot/2.0 (personal-tracker)",
    })
    
    return session, tokens
