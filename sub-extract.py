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
        return True
    except ffmpeg.Error as e:
        print(f'Error: {e.stderr.decode()}')
        return False

def extract_subtitles(video_file, output_dir, languages):
    if output_dir is None:
        output_dir = os.path.dirname(video_file)
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    extracted_count = 0
    for language in languages:
        stream_indices = get_subtitle_stream_indices(video_file, language)
        if not stream_indices:
            print(f"No subtitles found for language '{language}' in file '{video_file}'")
            continue
        for i, stream_index in enumerate(stream_indices):
            suffix = f"_{i}" if len(stream_indices) > 1 else ""
            temp_file = os.path.join(output_dir, f"{base_name}_{language}{suffix}.ass")
            output_file = os.path.join(output_dir, f"{base_name}_{language}{suffix}.srt")
            if convert_subtitles(video_file, temp_file, output_file, stream_index):
                extracted_count += 1
            if os.path.exists(temp_file):
                os.remove(temp_file)  # Deleting a temporary file
    return extracted_count

class WatchdogHandler(FileSystemEventHandler):
    def __init__(self, output_dir, languages):
        self.output_dir = output_dir
        self.languages = languages
        self.processed_files_count = 0
        self.extracted_subtitles_count = 0

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(('.mp4', '.mkv', '.avi')):
            print(f"New video file detected: {event.src_path}")
            # Wait until the file is completely copied
            self.wait_for_complete_copy(event.src_path)
            self.processed_files_count += 1
            subtitles_extracted = extract_subtitles(event.src_path, self.output_dir, self.languages)
            self.extracted_subtitles_count += subtitles_extracted

    def wait_for_complete_copy(self, file_path):
        while True:
            try:
                os.rename(file_path, file_path)
                print(f"File {file_path} is completely copied.")
                break
            except OSError:
                time.sleep(1)

def start_watching(directory, output_dir, languages):
    event_handler = WatchdogHandler(output_dir, languages)
    for filename in os.listdir(directory):
        if filename.endswith(('.mp4', '.mkv', '.avi')):
            file_path = os.path.join(directory, filename)
            print(f"Processing existing file: {file_path}")
            event_handler.wait_for_complete_copy(file_path)
            event_handler.processed_files_count += 1
            subtitles_extracted = extract_subtitles(file_path, output_dir, languages)
            event_handler.extracted_subtitles_count += subtitles_extracted
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=False)
    observer.start()
    try:
        print(f"Watching directory: {directory}")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        try:
            observer.stop()
        except KeyboardInterrupt:
            pass
        print_summary(event_handler.processed_files_count, event_handler.extracted_subtitles_count)

def print_summary(processed_files_count, extracted_subtitles_count):
    print("\nExiting application. Summary:")
    print(f"  Processed video files: {processed_files_count}")
    print(f"  Extracted subtitle files: {extracted_subtitles_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract subtitles from video files.")
    parser.add_argument("--watch", type=str, help="Directory to watch for new video files.")
    parser.add_argument("--output", type=str, default=None,
                        help="Directory to save the extracted subtitles. Default: Same directory as video file.")
    parser.add_argument("--languages", type=str, nargs='+', default=["rus", "eng", "zho", "chi"],
                        help="List of language codes (ISO 639-2). Default: ['rus', 'eng', 'zho', 'chi']")
    parser.add_argument("files", nargs='*', help="List of video files to process.")

    args = parser.parse_args()

    if args.files:
        processed_files_count = 0
        extracted_subtitles_count = 0
        for file in args.files:
            print(f"Processing file: {file}")
            processed_files_count += 1
            extracted_subtitles_count += extract_subtitles(file, args.output, args.languages)
        print_summary(processed_files_count, extracted_subtitles_count)
    elif args.watch:
        start_watching(args.watch, args.output, args.languages)
    else:
        parser.print_help()
