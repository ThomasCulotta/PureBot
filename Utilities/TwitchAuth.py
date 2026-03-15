import requests
import json
import os
import time
import threading
from Utilities.FlushPrint import ptf, ptfDebug

class TwitchAuth:
    tokenFile = "twitch_tokens.json"
    oauthUrl = "https://id.twitch.tv/oauth2/token"
    refreshBufferSeconds = 600  # Refresh 10 minutes before expiration
    
    def __init__(self, clientId, clientSecret, authCode):
        self.clientId = clientId
        self.clientSecret = clientSecret
        self.authCode = authCode
        self.accessToken = None
        self.refreshToken = None
        self.expiresAt = None  # Unix timestamp when token expires
        self.refreshTimer = None
        
        # Load tokens from file once on initialization
        self._LoadTokensFromFile()
        
    def GetAccessToken(self):
        """
        Get a valid access token. Returns cached token if valid, or refreshes if expired.
        Returns the access token string or None if failed.
        """
        # Check if we have valid tokens in memory
        if self.accessToken and not self._IsTokenExpired():
            self._ScheduleTokenRefresh()
            return self.accessToken
        
        # Try refreshing token
        if self.refreshToken:
            if self._RefreshAccessToken():
                ptf("Refreshed access token using refresh token")
                self._ScheduleTokenRefresh()
                return self.accessToken
            ptf("Failed to refresh token, falling back to auth code")
        
        # Fall back to auth code
        if self._GetTokensFromAuthCode():
            ptf("Got new tokens using auth code")
            self._ScheduleTokenRefresh()
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
            
            self.accessToken = data['access_token']
            self.refreshToken = data['refresh_token']
            self.expiresAt = data['expires_at']
            ptf("Loaded tokens from file")
        except Exception as e:
            ptf(f"Error loading tokens from file: {e}")
    
    def _SaveTokensToFile(self):
        """Save tokens to JSON file."""
        try:
            data = {
                'access_token': self.accessToken,
                'refresh_token': self.refreshToken,
                'expires_at': self.expiresAt
            }
            with open(self.tokenFile, 'w') as f:
                json.dump(data, f)
            ptfDebug(f"Tokens saved to {self.tokenFile}")
        except Exception as e:
            ptf(f"Error saving tokens to file: {e}")
    
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
        if self._RefreshAccessToken():
            ptf("Token auto-refreshed successfully")
            self._ScheduleTokenRefresh()
        else:
            ptf("Token auto-refresh failed")
    
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
            
            response = requests.post(self.oauthUrl, params=params)
            
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
            if 'expires_in' in data:
                self.expiresAt = int(time.time() + data['expires_in'])
            
            self._SaveTokensToFile()
            return True
        except Exception as e:
            ptf(f"Error getting tokens ({grantType}): {e}")
            return False

