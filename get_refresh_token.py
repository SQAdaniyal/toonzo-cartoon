"""
EK BAAR chalayein naya refresh token lene ke liye (upload + comment permission).
"""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

print("\n" + "=" * 60)
print("YEH GITHUB SECRET (YT_REFRESH_TOKEN) MEIN UPDATE KAREIN:")
print("=" * 60)
print(f"YT_REFRESH_TOKEN = {creds.refresh_token}")
print("=" * 60)
