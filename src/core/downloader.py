"""Download functionality using yt-dlp."""

import os
import glob
import subprocess
import shutil
import yt_dlp
import imageio_ffmpeg


class Downloader:
    """Handles video/audio downloads with yt-dlp."""
    
    def __init__(self, progress_callback, postprocessor_callback, log_callback):
        """
        Initialize downloader.
        
        Args:
            progress_callback: Called during download progress
            postprocessor_callback: Called during post-processing
            log_callback: Called for logging messages
        """
        self.progress_callback = progress_callback
        self.postprocessor_callback = postprocessor_callback
        self.log = log_callback
        self.is_cancelled = False
    
    def cancel(self):
        """Cancel the current download."""
        self.is_cancelled = True
    
    def _progress_hook(self, d):
        """Internal progress hook for yt-dlp."""
        if self.is_cancelled:
            raise Exception("Download cancelled by user.")
        
        if self.progress_callback:
            self.progress_callback(d)
    
    def _postprocessor_hook(self, d):
        """Internal post-processor hook for yt-dlp."""
        if self.postprocessor_callback:
            self.postprocessor_callback(d)
    
    def _get_deno_path(self):
        """Detect Deno executable path."""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Try assets folder first (for built app)
        deno = os.path.join(script_dir, 'assets', 'deno.exe')
        
        # Fallback to src/bin for development
        if not os.path.exists(deno):
            deno = os.path.join(script_dir, 'bin', 'deno.exe')
        
        return deno if os.path.exists(deno) else None
    
    def _parse_custom_args(self, args_string):
        """
        Parse custom yt-dlp arguments string.
        
        Supports formats like:
        - Simple flags: --no-warnings --ignore-errors
        - Key-value: --max-downloads 5 --rate-limit 1M
        
        Returns dict of yt-dlp options.
        """
        if not args_string or not args_string.strip():
            return {}
        
        custom_opts = {}
        parts = args_string.strip().split()
        i = 0
        
        while i < len(parts):
            arg = parts[i]
            
            if arg.startswith('--'):
                key = arg[2:].replace('-', '_')
                
                # Check if next part is a value or another flag
                if i + 1 < len(parts) and not parts[i + 1].startswith('--'):
                    value = parts[i + 1]
                    # Try to convert to appropriate type
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    custom_opts[key] = value
                    i += 2
                else:
                    # Boolean flag
                    custom_opts[key] = True
                    i += 1
            else:
                i += 1
        
        return custom_opts
    
    def _configure_deno(self):
        """Configure Deno JS runtime for yt-dlp."""
        deno = self._get_deno_path()
        
        if deno:
            try:
                subprocess.run([deno, '--version'], capture_output=True, check=False)
                self.log("Deno JS runtime configured")
                return {'js_runtimes': {'deno': {'args': [deno]}}}
            except Exception:
                pass
        
        self.log(f"⚠ Deno not found")
        self.log("  YouTube downloads may not work properly")
        return {}
    
    def download(self, url, audio, quality, fmt, playlist, compat, path, cookies_file=None, custom_args=None):
        """
        Download video or audio.
        
        Args:
            url: Video URL
            audio: True for audio-only
            quality: Quality setting (Best, 1080p, 720p, 480p)
            fmt: Output format (MP4, MP3, etc)
            playlist: Download entire playlist
            compat: Compatibility mode (convert to CFR)
            path: Download path
            cookies_file: Path to cookies.txt file (optional)
            custom_args: Custom yt-dlp arguments as string (optional)
            
        Returns:
            dict: {'success': bool, 'title': str, 'error': str or None}
        """
        self.is_cancelled = False
        os.makedirs(path, exist_ok=True)
        
        try:
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            self.log("FFmpeg ready")
            
            # Build format string
            if audio:
                fstr = 'bestaudio/best'
            elif quality == "Best":
                fstr = 'bestvideo+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
            else:
                h = quality.replace('p', '')
                fstr = f'bestvideo[height<={h}]+bestaudio[ext=m4a]/bestvideo[height<={h}]+bestaudio/best[height<={h}]'
            
            # Build yt-dlp options
            opts = {
                'ffmpeg_location': ffmpeg,
                'progress_hooks': [self._progress_hook],
                'postprocessor_hooks': [self._postprocessor_hook],
                'outtmpl': '%(title)s.%(ext)s',
                'format': fstr,
                'noplaylist': not playlist,
                'quiet': True,
                'cookiefile': cookies_file if cookies_file and os.path.exists(cookies_file) else None,
                'no_warnings': True,
                'paths': {'home': path}
            }
            
            # Configure post-processors
            if audio:
                opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': fmt.lower(),
                    'preferredquality': '192'
                }]
            else:
                opts['merge_output_format'] = fmt.lower()
                
                if compat:
                    self.log("Compatibility mode enabled - converting to CFR")
                    opts['postprocessors'] = [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': fmt.lower(),
                    }]
                    opts['postprocessor_args'] = [
                        '-c:v', 'libx264',
                        '-preset', 'veryfast',
                        '-crf', '23',
                        '-vsync', 'cfr',
                        '-c:a', 'aac',
                        '-b:a', '192k',
                        '-movflags', '+faststart'
                    ]
                else:
                    self.log("Using original format (may contain variable framerate)")
            
            # Configure Deno runtime
            deno_config = self._configure_deno()
            
            # Apply custom arguments if provided
            if custom_args:
                try:
                    # Parse custom arguments (simple key=value or --flag format)
                    custom_opts = self._parse_custom_args(custom_args)
                    if custom_opts:
                        opts.update(custom_opts)
                        self.log(f"Applied custom arguments: {custom_args}")
                except Exception as e:
                    self.log(f"⚠ Error parsing custom arguments: {e}")
            
            # Log cookies status
            if cookies_file and os.path.exists(cookies_file):
                self.log(f"Using cookies from: {os.path.basename(cookies_file)}")
            
            # Fetch video info
            self.log("Fetching video info...")
            try:
                info_opts = {'quiet': True, 'no_warnings': True, **deno_config}
                with yt_dlp.YoutubeDL(info_opts) as ydl_info:
                    info = ydl_info.extract_info(url, download=False)
            except Exception as e:
                self.log(f"⚠ Failed to fetch video info: {e}")
                raise
            
            # Livestream detection
            if info.get('is_live'):
                self.log("⚠ WARNING: This is a LIVE stream!")
                self.log("  Download will continue until you cancel it.")
            
            # Long video warning
            duration = info.get('duration', 0)
            if duration > 10800:  # 3 hours
                hours = duration / 3600
                self.log(f"⚠ WARNING: Very long video ({hours:.1f} hours)")
                self.log("  This may take significant time to process.")
                if compat:
                    self.log("  Tip: Disable compatibility mode for faster processing")
            
            # Quality fallback
            if not audio:
                formats = info.get('formats', [])
                available_heights = sorted(
                    set(f.get('height') for f in formats if f.get('height')),
                    reverse=True
                )
                
                if quality != "Best" and available_heights:
                    requested_h = int(quality.replace('p', ''))
                    if requested_h not in available_heights:
                        fallback = min(
                            [h for h in available_heights if h],
                            key=lambda x: abs(x - requested_h)
                        )
                        self.log(f"⚠ {quality} not available")
                        self.log(f"  Using {fallback}p instead")
                        h = fallback
                        fstr = f'bestvideo[height<={h}]+bestaudio[ext=m4a]/bestvideo[height<={h}]+bestaudio/best[height<={h}]'
                        opts['format'] = fstr
            
            # Disk space validation
            try:
                filesize = info.get('filesize') or info.get('filesize_approx', 0)
                if filesize:
                    filesize_gb = filesize / (1024**3)
                    free_space = shutil.disk_usage(path).free / (1024**3)
                    
                    if free_space < filesize_gb + 1:
                        self.log(f"⚠ WARNING: Low disk space!")
                        self.log(f"  Required: ~{filesize_gb:.1f} GB")
                        self.log(f"  Available: {free_space:.1f} GB")
                        if free_space < filesize_gb:
                            raise Exception(
                                f"Insufficient disk space ({free_space:.1f}GB available, "
                                f"{filesize_gb:.1f}GB needed)"
                            )
            except Exception as e:
                if "Insufficient disk space" in str(e):
                    raise
            
            # Download
            self.log("Downloading...")
            opts.update(deno_config)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')
                self.log(f"✓ {title[:60]}")
            
            return {'success': True, 'title': title, 'error': None}
            
        except Exception as e:
            if "cancelled" in str(e).lower():
                self.log("Cancelled")
                # Clean up temporary files (.part and .ytdl)
                try:
                    for part_file in glob.glob(os.path.join(path, '*.part')):
                        os.remove(part_file)
                    for ytdl_file in glob.glob(os.path.join(path, '*.ytdl')):
                        os.remove(ytdl_file)
                except Exception:
                    pass
                return {'success': False, 'title': None, 'error': 'Cancelled'}
            else:
                self.log(f"Error: {e}")
                return {'success': False, 'title': None, 'error': str(e)}
