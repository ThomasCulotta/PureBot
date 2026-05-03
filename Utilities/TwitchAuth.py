import requests
import json
import os
import time
import threading
import tempfile
from Utilities.FlushPrint import ptf, ptfDebug

class TwitchAuth:
    tokenFile = "twitch_tokens.json"
    oauthUrl = "https://id.twitch.tv/oauth2/token"
    refreshBufferSeconds = 600  # Refresh 10 minutes before expiration
    validateUrl = "https://id.twitch.tv/oauth2/validate"
    validateIntervalSeconds = 3600  # Validate every hour per Twitch requirements
    
    def __init__(self, clientId, clientSecret, authCode):
        self.clientId = clientId
        self.clientSecret = clientSecret
        self.authCode = authCode
        self.accessToken = None
        self.refreshToken = None
        self.expiresAt = None  # Unix timestamp when token expires
        self.refreshTimer = None
        self.validateTimer = None
        self._lock = threading.Lock()
        
        # Load tokens from file once on initialization
        self._LoadTokensFromFile()
        
    def GetAccessToken(self):
        """
        Get a valid access token. Returns cached token if valid, or refreshes if expired.
        Returns the access token string or None if failed.
        """
        with self._lock:
            # Check if we have valid tokens in memory
            if self.accessToken and not self._IsTokenExpired():
                self._ScheduleTokenRefresh()
                self._ScheduleValidation()
                return self.accessToken
            
            # Try refreshing token
            if self.refreshToken:
                if self._RefreshAccessToken():
                    ptf("Refreshed access token using refresh token")
                    self._ScheduleTokenRefresh()
                    self._ScheduleValidation()
                    return self.accessToken
                ptf("Failed to refresh token, falling back to auth code")
            
            # Fall back to auth code
            ptf("WARNING: Falling back to auth code exchange. Note: auth codes are single-use and this will fail if the code was already used.")
            if self._GetTokensFromAuthCode():
                ptf("Got new tokens using auth code")
                self._ScheduleTokenRefresh()
                self._ScheduleValidation()
                return self.accessToken
            
            ptf("Failed to obtain access token")
            return None
    
    def _IsTokenExpired(self):
        """Check if the current access token has expired."""
        if self.expiresAt is None:
            return True
        return time.time() >= self.expiresAt
    
    def _LoadTokensFromFile(self):
        """Load tokens from the JSON file if it exists and is valid."""
        if not os.path.exists(self.tokenFile):
            ptfDebug("Token file does not exist")
            return
        
        try:
            with open(self.tokenFile, 'r') as f:
                data = json.load(f)
            
            if not data or 'access_token' not in data or 'refresh_token' not in data or 'expires_at' not in data:
                ptf("Token file missing required fields")
                return
            
            with self._lock:
                self.accessToken = data['access_token']
                self.refreshToken = data['refresh_token']
                self.expiresAt = data['expires_at']
            ptf("Loaded tokens from file")
        except Exception as e:
            ptf(f"Error loading tokens from file: {e}")
    
    def _SaveTokensToFile(self):
        """Save tokens to JSON file."""
        with self._lock:
            try:
                data = {
                    'access_token': self.accessToken,
                    'refresh_token': self.refreshToken,
                    'expires_at': self.expiresAt
                }
                tmpfd, tmppath = tempfile.mkstemp(dir=os.path.dirname(self.tokenFile) or '.', suffix='.tmp')
                try:
                    with os.fdopen(tmpfd, 'w') as tmp:
                        json.dump(data, tmp)
                    os.replace(tmppath, self.tokenFile)
                    ptfDebug(f"Tokens saved to {self.tokenFile}")
                except Exception as e:
                    ptf(f"Error saving tokens to file: {e}")
                    try:
                        os.unlink(tmppath)
                    except OSError:
                        pass
            except Exception as e:
                ptf(f"Error saving tokens to file: {e}")
    
    def _ScheduleValidation(self):
        """Schedule periodic token validation (Twitch requires hourly validation)."""
        if self.validateTimer:
            self.validateTimer.cancel()
        
        self.validateTimer = threading.Timer(self.validateIntervalSeconds, self._ValidateToken)
        self.validateTimer.daemon = True
        self.validateTimer.start()
        ptfDebug(f"Token validation scheduled in {self.validateIntervalSeconds} seconds")
    
    def _ValidateToken(self):
        """Validate the current access token with Twitch (mandatory hourly check)."""
        ptfDebug("Validating access token")
        try:
            with self._lock:
                token = self.accessToken
            
            if not token:
                ptf("No access token to validate")
                self._ScheduleValidation()
                return
            
            response = requests.get(
                self.validateUrl,
                headers={"Authorization": f"OAuth {token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                ptfDebug(f"Token valid, expires in {data.get('expires_in', 'unknown')} seconds")
                # Update expiresAt from validate response (more accurate than our estimate)
                if 'expires_in' in data:
                    with self._lock:
                        self.expiresAt = int(time.time() + data['expires_in'])
                self._ScheduleValidation()
            elif response.status_code == 401:
                ptf("Token validation failed (401) — token revoked or expired. Forcing refresh.")
                with self._lock:
                    self.accessToken = None
                    self.expiresAt = None
                # Force a full refresh cycle
                self.GetAccessToken()
                self._ScheduleValidation()
            else:
                ptf(f"Token validation returned unexpected status {response.status_code}")
                self._ScheduleValidation()
        except requests.exceptions.RequestException as e:
            ptf(f"Token validation network error: {e}. Retrying in 300 seconds.")
            # Retry sooner on network errors
            self.validateTimer = threading.Timer(300, self._ValidateToken)
            self.validateTimer.daemon = True
            self.validateTimer.start()
    
    def _ScheduleTokenRefresh(self):
        """Schedule the token to be refreshed before it expires."""
        # Cancel any existing timer
        if self.refreshTimer:
            self.refreshTimer.cancel()
        
        if self.expiresAt is None:
            return
        
        # Calculate when to refresh (expiresAt minus buffer)
        refreshTime = self.expiresAt - self.refreshBufferSeconds
        delay = max(1, refreshTime - time.time())  # At least 1 second
        
        self.refreshTimer = threading.Timer(delay, self._AutoRefresh)
        self.refreshTimer.daemon = True
        self.refreshTimer.start()
        ptfDebug(f"Token refresh scheduled in {delay} seconds")
    
    def _AutoRefresh(self):
        """Automatically refresh the token (called by timer)."""
        ptfDebug("Auto-refreshing token")
        
        # Check if token was already refreshed by another code path
        with self._lock:
            if not self._IsTokenExpired():
                ptfDebug("Token still valid, skipping auto-refresh")
                self._ScheduleTokenRefresh()
                return
        
        # Retry with exponential backoff
        backoff_delays = [5, 30, 120]
        for attempt, delay in enumerate(backoff_delays, 1):
            with self._lock:
                if self._RefreshAccessToken():
                    ptf("Token auto-refreshed successfully")
                    self._ScheduleTokenRefresh()
                    return
            ptf(f"Token auto-refresh attempt {attempt}/{len(backoff_delays)} failed, retrying in {delay}s")
            time.sleep(delay)
        
        # All retries exhausted — try auth code as last resort
        with self._lock:
            ptf("WARNING: All refresh attempts failed. Trying auth code fallback.")
            if self._GetTokensFromAuthCode():
                ptf("Token obtained via auth code fallback")
                self._ScheduleTokenRefresh()
                return
        
        # Total failure — schedule recovery retry in 5 minutes
        ptf("CRITICAL: All token refresh attempts failed. Scheduling retry in 300 seconds.")
        self.refreshTimer = threading.Timer(300, self._AutoRefresh)
        self.refreshTimer.daemon = True
        self.refreshTimer.start()
    
    def _RefreshAccessToken(self):
        """Use refresh token to get a new access token."""
        if not self.refreshToken:
            return False
        
        return self._GetTokens(
            grantType='refresh_token',
            grantValue=self.refreshToken
        )
    
    def _GetTokensFromAuthCode(self):
        """Exchange auth code for access and refresh tokens."""
        if not self.authCode:
            ptf("No auth code available")
            return False
        
        return self._GetTokens(
            grantType='authorization_code',
            grantValue=self.authCode,
            redirectUri='http://localhost'
        )
    
    def _GetTokens(self, grantType, grantValue, redirectUri=None):
        """
        Get tokens from Twitch OAuth endpoint.
        
        Args:
            grantType: 'refresh_token' or 'authorization_code'
            grantValue: The refresh token or auth code
            redirectUri: Required for authorization_code grant type
        """
        try:
            ptfDebug(f"Requesting tokens with grant type: {grantType}")
            params = {
                'client_id': self.clientId,
                'client_secret': self.clientSecret,
                'grant_type': grantType
            }
            
            if grantType == 'refresh_token':
                params['refresh_token'] = grantValue
            elif grantType == 'authorization_code':
                params['code'] = grantValue
                if redirectUri:
                    params['redirect_uri'] = redirectUri
            
            response = requests.post(self.oauthUrl, data=params, timeout=10)
            
            if response.status_code != 200:
                ptf(f"Token request failed ({grantType}): {response.status_code} {response.text}")
                return False
            
            data = response.json()
            
            if 'access_token' not in data or 'refresh_token' not in data:
                ptf(f"Invalid token response ({grantType}): {data}")
                return False
            
            self.accessToken = data['access_token']
            self.refreshToken = data['refresh_token']
            
            # Calculate expiration time (store as integer seconds)
            expires_in = data.get('expires_in', 14400)  # Default 4 hours if missing
            self.expiresAt = int(time.time() + expires_in)
            
            self._SaveTokensToFile()
            return True
        except Exception as e:
            ptf(f"Error getting tokens ({grantType}): {e}")
            return False

