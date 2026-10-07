import os
import shutil
import subprocess
from typing import Optional


def get_ffmpeg_executable() -> Optional[str]:
    """Discover ffmpeg executable from PATH or bundled imageio-ffmpeg."""
    # 1. System PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # 2. imageio-ffmpeg static binary
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def extract_audio(input_file: str, output_file: str, target_format: str = "mp3") -> bool:
    """Extract audio from video file and save as MP3 or M4A."""
    ffmpeg_bin = get_ffmpeg_executable()
    if not ffmpeg_bin or not os.path.exists(input_file):
        return False
    try:
        cmd = [ffmpeg_bin, "-y", "-i", input_file, "-vn"]
        if target_format.lower() in ("m4a", "aac"):
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        else:
            cmd.extend(["-c:a", "libmp3lame", "-q:a", "2"])
        cmd.append(output_file)

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        return res.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0
    except Exception:
        return False


def remux_video(
    input_file: str,
    output_file: str,
    target_format: str = "mp4",
    caption: Optional[str] = None
) -> bool:
    """Remux or transcode video to MP4, MKV, or WEBM container with optional caption metadata."""
    ffmpeg_bin = get_ffmpeg_executable()
    if not ffmpeg_bin or not os.path.exists(input_file):
        return False

    fmt = target_format.lower()
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    try:
        # A. WebM format: requires VP9 or VP8 video and Opus/Vorbis audio
        if fmt == "webm":
            cmd = [
                ffmpeg_bin, "-y", "-i", input_file,
                "-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0",
                "-deadline", "realtime", "-cpu-used", "5",
                "-c:a", "libopus", "-b:a", "128k"
            ]
            if caption:
                cmd.extend(["-metadata", f"comment={caption[:500]}"])
            cmd.append(output_file)
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
            return res.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0

        # B. Matroska (.mkv) or MP4 (.mp4): First attempt ultra-fast lossless stream copy
        copy_cmd = [ffmpeg_bin, "-y", "-i", input_file, "-c", "copy"]
        if caption:
            copy_cmd.extend(["-metadata", f"comment={caption[:500]}"])
        copy_cmd.append(output_file)

        res = subprocess.run(copy_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        if res.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            return True

        # Fallback to standard re-encode if stream copy fails
        encode_cmd = [
            ffmpeg_bin, "-y", "-i", input_file,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "192k"
        ]
        if caption:
            encode_cmd.extend(["-metadata", f"comment={caption[:500]}"])
        encode_cmd.append(output_file)

        res2 = subprocess.run(encode_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
        return res2.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0

    except Exception:
        return False
