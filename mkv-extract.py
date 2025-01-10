import ffmpeg
import argparse
import os
import subprocess
import json

def get_subtitle_stream_indices(video_file, language):
    cmd = f"ffprobe -v error -select_streams s -show_entries stream=index:stream_tags=language -of json {video_file}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    streams = json.loads(result.stdout)["streams"]
    return [stream["index"] for stream in streams if stream.get("tags", {}).get("language", "") == language]

def convert_subtitles(video_file, temp_file, output_file, stream_index):
    try:
        # Удаляем существующий выходной файл, если он есть
        if os.path.exists(output_file):
            os.remove(output_file)

        # Извлекаем субтитры из указанного потока в формат .ass
        ffmpeg.input(video_file).output(temp_file, format='ass', map=f'0:{stream_index}').run(quiet=True, overwrite_output=True)
        # Конвертируем .ass в .srt
        ffmpeg.input(temp_file).output(output_file, format='srt').run(quiet=True, overwrite_output=True)
    except ffmpeg.Error as e:
        print(f'Error: {e.stderr.decode()}')

def extract_subtitles(video_file, output_dir, languages):
    if output_dir is None:
        output_dir = os.path.dirname(video_file)
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    for language in languages:
        stream_indices = get_subtitle_stream_indices(video_file, language)
        if stream_indices:
            for i, stream_index in enumerate(stream_indices):
                suffix = f"_{i}" if len(stream_indices) > 1 else ""
                temp_file = os.path.join(output_dir, f"{base_name}_{language}{suffix}.ass")
                output_file = os.path.join(output_dir, f"{base_name}_{language}{suffix}.srt")
                convert_subtitles(video_file, temp_file, output_file, stream_index)
                if os.path.exists(temp_file):
                    os.remove(temp_file)  # Удаление временного файла
        else:
            print(f"No subtitles found for language '{language}' in file '{video_file}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract subtitles from video files.")
    parser.add_argument("video_files", type=str, nargs='+', help="List of video file paths.")
    parser.add_argument("--output_dir", type=str, default=None, help="Directory to save the extracted subtitles. Default: Same directory as video file.")
    parser.add_argument("--languages", type=str, nargs='+', default=["rus", "eng", "chi", "zho"],
                        help="List of language codes (ISO 639-2). Default: ['rus', 'eng', 'chi', 'zho']")

    args = parser.parse_args()

    for video_file in args.video_files:
        extract_subtitles(video_file, args.output_dir, args.languages)
