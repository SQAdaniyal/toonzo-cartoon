"""
Run locally to create a YouTube refresh token for the selected channel.
"""
import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

if not creds.refresh_token:
    raise RuntimeError(
        "Google did not return a refresh token. Revoke this app's access and "
        "run the script again with prompt=consent."
    )

output_dir = "local_secrets"
os.makedirs(output_dir, exist_ok=True)
token_path = os.path.join(output_dir, "YT_REFRESH_TOKEN.txt")
with open(token_path, "w", encoding="utf-8") as token_file:
    token_file.write(creds.refresh_token)

print(f"\nRefresh token saved locally to {token_path}.")
print("Do not paste it into chat or commit it to Git.")
