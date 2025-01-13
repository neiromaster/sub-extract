import time

import ffmpeg
import argparse
import os
import subprocess
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def get_subtitle_stream_indices(video_file, language):
    cmd = f"ffprobe -v error -select_streams s -show_entries stream=index:stream_tags=language -of json {video_file}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    try:
        if result.stdout:
            data = json.loads(result.stdout)
            if "streams" in data:
                streams = data["streams"]
                return [stream["index"] for stream in streams if stream.get("tags", {}).get("language", "") == language]
    except json.JSONDecodeError:
        pass
    return []

def convert_subtitles(video_file, temp_file, output_file, stream_index):
    try:
        # Delete the existing output file, if any
        if os.path.exists(output_file):
            os.remove(output_file)

        # Extract subtitles from the specified stream into .ass format
        ffmpeg.input(video_file).output(temp_file, format='ass', map=f'0:{stream_index}').run(quiet=True, overwrite_output=True)
        # Convert .ass to .srt
        ffmpeg.input(temp_file).output(output_file, format='srt').run(quiet=True, overwrite_output=True)
    except ffmpeg.Error as e:
        print(f'Error: {e.stderr.decode()}')

def extract_subtitles(video_file, output_dir, languages):
    if output_dir is None:
        output_dir = os.path.dirname(video_file)
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    for language in languages:
        stream_indices = get_subtitle_stream_indices(video_file, language)
        if not stream_indices:
            print(f"No subtitles found for language '{language}' in file '{video_file}'")
            continue
        for i, stream_index in enumerate(stream_indices):
            suffix = f"_{i}" if len(stream_indices) > 1 else ""
            temp_file = os.path.join(output_dir, f"{base_name}_{language}{suffix}.ass")
            output_file = os.path.join(output_dir, f"{base_name}_{language}{suffix}.srt")
            convert_subtitles(video_file, temp_file, output_file, stream_index)
            if os.path.exists(temp_file):
                os.remove(temp_file)  # Deleting a temporary file

class WatchdogHandler(FileSystemEventHandler):
    def __init__(self, output_dir, languages):
        self.output_dir = output_dir
        self.languages = languages

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(('.mp4', '.mkv', '.avi')):
            print(f"New video file detected: {event.src_path}")
            # Wait until the file is completely copied
            self.wait_for_complete_copy(event.src_path)
            extract_subtitles(event.src_path, self.output_dir, self.languages)

    def wait_for_complete_copy(self, file_path):
        previous_modification_time = -1
        while True:
            current_modification_time = os.path.getmtime(file_path)
            if current_modification_time == previous_modification_time:
                break
            previous_modification_time = current_modification_time
            time.sleep(1)

def start_watching(directory, output_dir, languages):
    event_handler = WatchdogHandler(output_dir, languages)
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=False)
    observer.start()
    try:
        print(f"Watching directory: {directory}")
        while True:
            time.sleep(1)  # Infinite loop to keep the script running
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract subtitles from video files.")
    parser.add_argument("video_files", type=str, nargs='*', help="List of video file paths.")
    parser.add_argument("--watch_dir", type=str, help="Directory to watch for new video files.")
    parser.add_argument("--output_dir", type=str, default=None, help="Directory to save the extracted subtitles. Default: Same directory as video file.")
    parser.add_argument("--languages", type=str, nargs='+', default=["rus", "eng", "zho", "chi"],
                        help="List of language codes (ISO 639-2). Default: ['rus', 'eng', 'zho', 'chi']")

    args = parser.parse_args()

    if args.watch_dir:
        start_watching(args.watch_dir, args.output_dir, args.languages)
    else:
        for video_file in args.video_files:
            extract_subtitles(video_file, args.output_dir, args.languages)
