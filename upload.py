"""Upload approved video files through the authorized YouTube Data API."""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import config

def _youtube():
    creds = Credentials(
        None,
        refresh_token=config.YT_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=config.YT_CLIENT_ID,
        client_secret=config.YT_CLIENT_SECRET,
    )
    return build("youtube", "v3", credentials=creds)


def get_video_statistics(video_ids: list) -> dict:
    """Return public view and engagement counts for uploaded videos."""
    yt = _youtube()
    statistics = {}
    for start in range(0, len(video_ids), 50):
        response = yt.videos().list(
            part="statistics", id=",".join(video_ids[start : start + 50])
        ).execute()
        for item in response.get("items", []):
            counts = item.get("statistics", {})
            statistics[item["id"]] = {
                "views": int(counts.get("viewCount", 0)),
                "likes": int(counts.get("likeCount", 0)),
                "comments": int(counts.get("commentCount", 0)),
            }
    return statistics


def get_channel_identity_and_recent_titles() -> tuple[str, list[str]]:
    """Return the authorized channel title and its latest uploaded video titles."""
    yt = _youtube()
    response = yt.channels().list(
        part="snippet,contentDetails", mine=True
    ).execute()
    channels = response.get("items", [])
    if not channels:
        raise RuntimeError("YouTube OAuth did not return an authorized channel")

    channel = channels[0]
    channel_title = channel.get("snippet", {}).get("title", "")
    uploads_playlist = (
        channel.get("contentDetails", {})
        .get("relatedPlaylists", {})
        .get("uploads")
    )
    if not uploads_playlist:
        raise RuntimeError("Could not find the authorized channel's uploads playlist")

    playlist = yt.playlistItems().list(
        part="snippet", playlistId=uploads_playlist, maxResults=50
    ).execute()
    titles = [
        item.get("snippet", {}).get("title", "")
        for item in playlist.get("items", [])
        if item.get("snippet", {}).get("title")
    ]
    return channel_title, titles


def upload_video(path: str, title: str, description: str, tags: list) -> str:
    yt = _youtube()
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:4900],
            "tags": tags[:30],
            "categoryId": config.CATEGORY_ID,
            "defaultLanguage": config.LANGUAGE[:2].lower(),
            "defaultAudioLanguage": config.LANGUAGE[:2].lower(),
        },
        "status": {
            "privacyStatus": config.PRIVACY_STATUS,
            "selfDeclaredMadeForKids": config.YOUTUBE_MADE_FOR_KIDS == "true",
        },
    }
    media = MediaFileUpload(path, chunksize=8 * 1024 * 1024, resumable=True)
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk(num_retries=5)
        if status:
            print(f"  Upload: {int(status.progress() * 100)}%")
    video_id = response["id"]
    print(f"  ✅ Uploaded: https://youtu.be/{video_id}")
    return video_id
