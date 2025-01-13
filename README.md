# Video Subtitles Extractor

This project provides a script to extract subtitles from video files in multiple languages with the option to watch a directory for new files.

## Requirements

Make sure you have the following libraries installed:

```bash
pip install ffmpeg-python watchdog
```

## Usage

### Running the script to extract subtitles from video files

```bash
python sub-extract.py <video_file_1> <video_file_2> ... --output_dir <output_directory> --languages <lang_1> <lang_2> ...
```

Parameters:
- `video_file_1`, `video_file_2`, ... - paths to the video files.
- `--output_dir` (optional) - directory to save the extracted subtitles. By default, subtitles are saved in the same directory as the video file.
- `--languages` (optional) - list of language codes in ISO 639-2 format. Default: `['rus', 'eng', 'zho', 'chi']`.

### Running the script in watch mode

```bash
python sub-extract.py --watch_dir <directory_to_watch> --output_dir <output_directory> --languages <lang_1> <lang_2> ...
```

Parameters:
- `--watch_dir` - directory to watch for new video files.
- `--output_dir` (optional) - directory to save the extracted subtitles. By default, subtitles are saved in the same directory as the video file.
- `--languages` (optional) - list of language codes in ISO 639-2 format. Default: `['rus', 'eng', 'zho']`.

### Converting the script to an executable with PyInstaller

To convert the script to an executable file using `PyInstaller`:

1. Install `PyInstaller`:

```bash
pip install pyinstaller
```

2. Run `PyInstaller` to convert the script to an exe file:

```bash
pyinstaller --onefile sub-extract.py
```

This will create an executable file `sub-extract.exe` in the `dist` directory.

### Optional
If you are using `uv` for project management, the script can be built with the following commands:

```bash
uv run pyinstaller --onefile sub-extract.py
```

## Examples

### Extracting subtitles from video files

```bash
python sub-extract.py example1.mp4 example2.mkv --output_dir ./subtitles --languages eng rus chi
```

### Watch mode for a directory

```bash
python sub-extract.py --watch_dir ./videos --output_dir ./subtitles --languages eng rus chi
```

This `README.md` file provides the basic instructions for using the script and converting it to an executable file. If you have any further requests or questions, feel free to let me know!
