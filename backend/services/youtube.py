"""
YouTube audio extraction service using yt-dlp.
"""
import os
import yt_dlp


def extract_audio(youtube_url: str, output_dir: str) -> dict:
    """
    Download and extract audio from a YouTube URL.

    Args:
        youtube_url: The YouTube video URL.
        output_dir: Directory to save the extracted audio.

    Returns:
        dict with keys: 'audio_path', 'title', 'duration'
    """
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        video_id = info.get('id', 'audio')
        title = info.get('title', 'Unknown')
        duration = info.get('duration', 0)

    audio_path = os.path.join(output_dir, f"{video_id}.wav")

    return {
        'audio_path': audio_path,
        'title': title,
        'duration': duration,
        'video_id': video_id,
    }
