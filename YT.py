import os
import yt_dlp
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from datetime import datetime
import re
from tkinter.font import Font
import queue
import sys
import random
import colorsys
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, COMM
import requests


# Then use:
current_date = datetime.now().strftime("%d-%m-%y")

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, radius=10, padding=8, color="#007AFF", fg="#ffffff", hover_color="#0063CC", **kwargs):
        # Add disabled state color
        self.disabled_color = "#cccccc"
        self.disabled_fg = "#888888"
        self.state = 'normal'  # Add state tracking
        
        # Extract and store button-specific properties
        self.font = kwargs.pop('font', ('Helvetica', 12, 'bold'))
        self.text = text
        self.radius = radius
        self.padding = padding
        self.color = color
        self.hover_color = hover_color
        self.fg = fg
        self.current_color = self.color
        self.command = command
        
        # Calculate button dimensions
        if 'width' in kwargs:
            self.width = kwargs['width']
        else:
            # Create temporary label to measure text width
            temp = tk.Label(parent, text=text, font=self.font)
            temp.pack()
            text_width = temp.winfo_reqwidth()
            temp.destroy()
            self.width = text_width + (padding * 2)
        
        self.height = kwargs.pop('height', 35)
        
        # Initialize canvas with calculated dimensions
        kwargs['width'] = self.width
        kwargs['height'] = self.height
        kwargs['highlightthickness'] = kwargs.get('highlightthickness', 0)
        kwargs['bd'] = kwargs.get('bd', 0)
        
        super().__init__(parent, **kwargs)
        
        # Bind events
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)
        self.bind('<Configure>', self._on_resize)
        
        # Draw initial state
        self._draw()
    
    def _draw(self):
        try:
            self.delete('all')
            
            # Use disabled colors if state is disabled
            fill_color = self.disabled_color if self.state == 'disabled' else self.current_color
            text_color = self.disabled_fg if self.state == 'disabled' else self.fg
            
            # Draw rounded rectangle
            self.create_rounded_rect(
                1, 1,
                self.winfo_width() - 2,
                self.winfo_height() - 2,
                self.radius,
                fill=fill_color,
                outline=fill_color
            )
            
            # Draw text centered
            self.create_text(
                self.winfo_width() / 2,
                self.winfo_height() / 2,
                text=self.text,
                fill=text_color,
                font=self.font,
                justify=tk.CENTER
            )
        except tk.TclError:
            # Handle case where widget is being destroyed
            pass

    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        # Ensure radius isn't too large for the button
        radius = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
        
        # Create points for rounded rectangle
        points = [
            x1 + radius, y1,                  # Top left start
            x2 - radius, y1,                  # Top right start
            x2, y1,                          # Top right corner
            x2, y1 + radius,                 # Top right end
            x2, y2 - radius,                 # Bottom right start
            x2, y2,                          # Bottom right corner
            x2 - radius, y2,                 # Bottom right end
            x1 + radius, y2,                 # Bottom left start
            x1, y2,                          # Bottom left corner
            x1, y2 - radius,                 # Bottom left end
            x1, y1 + radius,                 # Top left start
            x1, y1                           # Top left corner
        ]
        
        return self.create_polygon(points, smooth=True, **kwargs)

    def _on_enter(self, e):
        if self.state != 'disabled':  # Only change color if not disabled
            self.current_color = self.hover_color
            self._draw()

    def _on_leave(self, e):
        if self.state != 'disabled':  # Only change color if not disabled
            self.current_color = self.color
            self._draw()

    def _on_click(self, e):
        if self.command and str(self['state']) != 'disabled':
            self.command()

    def _on_resize(self, e):
        self._draw()

    def configure(self, **kwargs):
        if 'state' in kwargs:
            self.state = kwargs['state']
            if self.state == 'disabled':
                self.current_color = self.disabled_color
            else:
                self.current_color = self.color
            self._draw()
            del kwargs['state']
        
        if 'text' in kwargs:
            self.text = kwargs['text']
            temp = tk.Label(self.master, text=self.text, font=self.font)
            temp.pack()
            text_width = temp.winfo_reqwidth()
            temp.destroy()
            new_width = text_width + (self.padding * 2)
            self.width = new_width
            super().configure(width=new_width)
            self._draw()
        
        super().configure(**{k:v for k,v in kwargs.items() if k not in ('text', 'state')})

    def config(self, **kwargs):
        return self.configure(**kwargs)

class AnimatedButton(RoundedButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.animation_frame = 0
        self.is_animating = False
        self.animation_frames = ["⏳", "⌛"]
        self.original_text = self.text
        self.animation_speed = 500  # milliseconds per frame
        self.animation_id = None

    def start_animation(self):
        """Start the loading animation"""
        if not self.is_animating:
            self.is_animating = True
            self.original_text = self.text
            self.configure(state='disabled')  # Ensure button is disabled when animation starts
            self.animate()

    def stop_animation(self):
        """Stop the loading animation"""
        if self.is_animating:
            self.is_animating = False
            if self.animation_id:
                self.after_cancel(self.animation_id)
                self.animation_id = None
            self.text = self.original_text
            self.configure(state='normal')  # Re-enable button when animation stops
            self._draw()

    def animate(self):
        """Animate the button"""
        if self.is_animating:
            # Update animation frame
            self.animation_frame = (self.animation_frame + 1) % len(self.animation_frames)
            
            # Update button text with animation frame
            self.text = f"{self.original_text} {self.animation_frames[self.animation_frame]}"
            self._draw()
            
            # Schedule next frame
            self.animation_id = self.after(self.animation_speed, self.animate)

    def _on_click(self, e):
        """Override click handler to start animation"""
        if self.command and self.state != 'disabled':  # Changed from str(self['state'])
            self.start_animation()
            self.configure(state='disabled')  # Disable button immediately after click
            self.command()

class MP3Converter:
    def __init__(self, root):
        self.root = root
        self.root.title("YTMP3 - YouTube & SoundCloud to MP3 Converter")
        self.root.geometry("550x420")
        self.root.resizable(True, True)
        self.root.minsize(550, 420)
        
        # Add dark mode state
        self.dark_mode = False
        
        # Color schemes
        self.color_schemes = {
            "light": {
                "bg": "#ffffff",
                "fg": "#1a1a1a",
                "button_bg": "#007AFF",
                "button_fg": "#ffffff",
                "button_active_bg": "#0063CC",
                "entry_bg": "#ffffff",
                "entry_fg": "#000000",
                "trough_color": "#e8e8e8",
                "progress_color": "#007AFF"
            },
            "dark": {
                "bg": "#1E1E2E",
                "fg": "#CDD6F4",
                "button_bg": "#89B4FA",
                "button_fg": "#1E1E2E",
                "button_active_bg": "#74C7EC",
                "entry_bg": "#313244",
                "entry_fg": "#CDD6F4",
                "trough_color": "#45475A",
                "progress_color": "#89B4FA"
            }
        }
        
        # Add these new attributes
        self.random_colors_enabled = False
        
        # Initialize with light mode
        self.current_theme = self.color_schemes["light"]
        self.root.configure(bg=self.current_theme["bg"])

        # Language configuration
        self.current_language = 'vi'  # Mặc định là tiếng Việt
        self.language = "vi"
        self.language_strings = {
            "en": {
                "title": "YouTube & SoundCloud to MP3 Converter",
                "url_label": "Paste YouTube or SoundCloud links (one per line):",
                "save_to": "Save to:",
                "choose_folder": "Choose Folder",
                "download": "Download MP3",
                "download_flac": "Download FLAC",
                "progress": "Download Progress",
                "help": "Help",
                "ready": "Ready to download!",
                "starting": "Starting downloads...",
                "success": "🎵 All downloads completed successfully!",
                "error_url": "Please enter at least one YouTube or SoundCloud URL!",
                "error_title": "Error",
                "success_title": "Success",
                "downloading": "⏳ Downloading: {}",
                "downloaded": "✅ Downloaded: {}",
                "failed": "❌ Failed: {}",
                "album": "Album: {}",
                "track": "    🎵 Track: {}",
                "invalid_urls": "The following entries are not valid YouTube or SoundCloud URLs:\n\n{}\n\nPlease enter valid URLs.",
                "cut": "Cut",
                "copy": "Copy",
                "paste": "Paste",
                "select_all": "Select All",
                "flac_format": "FLAC Format (High Quality)"
            },
            "vi": {
                "title": "Chuyển đổi YouTube & SoundCloud sang MP3",
                "url_label": "Dán liên kết YouTube hoặc SoundCloud (mỗi link một dòng):",
                "save_to": "Lưu tại:",
                "choose_folder": "Chọn thư mục",
                "download": "Tải MP3",
                "download_flac": "Tải FLAC",
                "progress": "Tiến trình tải",
                "help": "Trợ giúp",
                "ready": "Sẵn sàng tải!",
                "starting": "Đang bắt đầu tải xuống...",
                "success": "🎵 Tất cả tải xuống hoàn thành thành công!",
                "error_url": "Vui lòng nhập ít nhất một liên kết YouTube hoặc SoundCloud!",
                "error_title": "Lỗi",
                "success_title": "Thành công",
                "downloading": "⏳ Đang tải: {}",
                "downloaded": "✅ Tải thành công: {}",
                "failed": "❌ Tải thất bại: {}",
                "album": "Album: {}",
                "track": "    🎵 Bài hát: {}",
                "invalid_urls": "Các mục sau không phải là liên kết YouTube hoặc SoundCloud hợp lệ:\n\n{}\n\nVui lòng nhập URL hợp lệ.",
                "cut": "Cắt",
                "copy": "Sao chép",
                "paste": "Dán",
                "select_all": "Chọn tất cả",
                "flac_format": "Định dạng FLAC (Chất lượng cao)"
            }
        }

        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        # Application variables
        self.downloading_songs = []
        self.progress_var = tk.IntVar()
        self.save_path = os.path.expanduser("~/Downloads")
        
        # Download tracking
        self.total_downloads = 0
        self.completed_downloads = 0
        self.failed_downloads = 0
        self.download_lock = threading.Lock()
        
        # UI update queue to prevent freezing
        self.ui_queue = queue.Queue()
        self.root.after(50, self.process_ui_queue)  # Process UI updates more frequently

        # Font configuration
        self.title_font = Font(family="Helvetica", size=15, weight="bold")
        self.normal_font = Font(family="Helvetica", size=11)
        self.button_font = Font(family="Helvetica", size=12, weight="bold")

        # Main container
        self.main_frame = tk.Frame(self.root, bg=self.current_theme["bg"])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Add ffmpeg path
        if getattr(sys, 'frozen', False):
            # If running as compiled bundle
            self.ffmpeg_path = os.path.join(sys._MEIPASS, 'bin', 'ffmpeg')
        else:
            # If running as script
            self.ffmpeg_path = '/usr/local/bin/ffmpeg'  # Default system path

        # Build UI
        self.create_ui()
        
        # Track album info extraction to prevent redundant operations
        self.album_info_cache = {}

    def configure_styles(self):
        # Progress bar style
        self.style.configure("Custom.Horizontal.TProgressbar",
            thickness=10,
            troughcolor='#e8e8e8',
            background='#007AFF',
            bordercolor='#e8e8e8'
        )
        
        # Button style
        self.style.configure("Custom.TButton",
            font=("Helvetica", 11),
            borderwidth=1,
            relief="flat",
            background="#ffffff",
            foreground="#000000",
            padding=5
        )
        self.style.map("Custom.TButton",
            background=[('active', '#f0f0f0'), ('pressed', '#e0e0e0')]
        )
        
        # Frame style
        self.style.configure("Custom.TLabelframe",
            background="#ffffff",
            bordercolor="#d0d0d0",
            relief="solid",
            borderwidth=1
        )
        self.style.configure("Custom.TLabelframe.Label",
            font=("Helvetica", 11, "bold"),
            background="#ffffff",
            foreground="#000000"
        )

    def create_ui(self):
        # Header section
        header_frame = tk.Frame(self.main_frame, bg=self.current_theme["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Application title
        self.title_label = tk.Label(
            header_frame,
            text=self.language_strings[self.language]["title"],
            font=self.title_font,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"]
        )
        self.title_label.pack(side=tk.LEFT)

        # Dark mode toggle button
        self.theme_button = RoundedButton(
            header_frame,
            text="🌙" if not self.dark_mode else "☀️",
            command=self.toggle_theme,
            radius=8,
            padding=4,
            width=40,
            height=30,
            color=self.current_theme["button_bg"],
            hover_color=self.current_theme["button_active_bg"],
            fg=self.current_theme["button_fg"],
            font=self.normal_font
        )
        self.theme_button.pack(side=tk.RIGHT, padx=3)

        # Language toggle button
        self.lang_button = RoundedButton(
            header_frame,
            text="EN" if self.language == "vi" else "VI",
            command=self.toggle_language,
            radius=8,
            padding=4,
            width=40,
            height=30,
            color=self.current_theme["button_bg"],
            hover_color=self.current_theme["button_active_bg"],
            fg=self.current_theme["button_fg"],
            font=self.normal_font
        )
        self.lang_button.pack(side=tk.RIGHT, padx=3)

        # URL input section
        input_frame = ttk.LabelFrame(
            self.main_frame,
            style="Custom.TLabelframe"
        )
        input_frame.pack(fill=tk.X, pady=5)

        # URL input label
        self.url_label = tk.Label(
            input_frame,
            text=self.language_strings[self.language]["url_label"],
            font=self.normal_font,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
            anchor="w"
        )
        self.url_label.pack(fill=tk.X, padx=5, pady=(5, 2))

        # Text area with scrollbar
        url_frame = tk.Frame(input_frame, bg=self.current_theme["bg"])
        url_frame.pack(fill=tk.X, padx=8, pady=(0, 5))

        self.url_text = tk.Text(
            url_frame,
            height=2,
            font=self.normal_font,
            wrap=tk.WORD,
            bg=self.current_theme["entry_bg"],
            highlightthickness=1,
            highlightcolor=self.current_theme["progress_color"],
            padx=6,
            pady=6,
            fg=self.current_theme["fg"]
        )
        scrollbar = ttk.Scrollbar(url_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.url_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.url_text.yview)
        self.url_text.config(yscrollcommand=scrollbar.set)

        # Add format selection checkbox below URL box
        self.format_frame = tk.Frame(input_frame, bg=self.current_theme["bg"])
        self.format_frame.pack(fill=tk.X, padx=8, pady=(0, 5), anchor=tk.W)
        
        self.use_flac = tk.BooleanVar(value=False)
        self.format_checkbox = tk.Checkbutton(
            self.format_frame,
            text=self.language_strings[self.language]["flac_format"],
            variable=self.use_flac,
            command=self.update_download_button_text,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
            selectcolor=self.current_theme["entry_bg"],
            activebackground=self.current_theme["bg"],
            activeforeground=self.current_theme["fg"],
            font=self.normal_font
        )
        self.format_checkbox.pack(side=tk.LEFT)

        # Create and bind the context menu
        self.create_context_menu()
        self.url_text.bind('<Button-3>', self.show_context_menu)  # Right-click
        if sys.platform == 'darwin':  # macOS
            self.url_text.bind('<Button-2>', self.show_context_menu)  # Right-click on macOS

        # Save path section
        path_frame = tk.Frame(self.main_frame, bg=self.current_theme["bg"])
        path_frame.pack(fill=tk.X, pady=5)

        self.path_var = tk.StringVar()
        self.path_label = tk.Label(
            path_frame,
            textvariable=self.path_var,
            font=self.normal_font,
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
            anchor="w"
        )
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.update_path_label()

        self.choose_folder_button = RoundedButton(
            path_frame,
            text=self.language_strings[self.language]["choose_folder"],
            command=self.choose_directory,
            radius=8,
            padding=8,
            color=self.current_theme["button_bg"],
            hover_color=self.current_theme["button_active_bg"],
            fg=self.current_theme["button_fg"],
            font=self.normal_font
        )
        self.choose_folder_button.pack(side=tk.RIGHT)

        # Create a frame to contain the download button
        button_frame = tk.Frame(self.main_frame, bg=self.current_theme["bg"])
        button_frame.pack(pady=8)
        
        # Download button
        self.download_button = AnimatedButton(
            button_frame,
            text=self.language_strings[self.language]["download"],
            command=self.download_all_videos,
            radius=10,
            padding=25,
            color=self.current_theme["button_bg"],
            hover_color=self.current_theme["button_active_bg"],
            fg=self.current_theme["button_fg"],
            font=self.button_font
        )
        self.download_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Progress section
        self.progress_frame = ttk.LabelFrame(
            self.main_frame,
            text=self.language_strings[self.language]["progress"],
            style="Custom.TLabelframe"
        )
        self.progress_frame.pack(fill=tk.BOTH, expand=True, pady=3)

        # Download status
        status_frame = tk.Frame(self.progress_frame, bg=self.current_theme["bg"])
        status_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 5))

        self.song_list = tk.Text(
            status_frame,
            height=2,  # Increased height for better visibility
            font=self.normal_font,
            bg=self.current_theme["entry_bg"],
            wrap=tk.WORD,
            state=tk.DISABLED,
            padx=6,
            pady=4,
            fg=self.current_theme["fg"]
        )
        status_scrollbar = ttk.Scrollbar(status_frame)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.song_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scrollbar.config(command=self.song_list.yview)
        self.song_list.config(yscrollcommand=status_scrollbar.set)

        # Footer
        footer_frame = tk.Frame(self.main_frame, bg=self.current_theme["bg"])
        footer_frame.pack(fill=tk.X, pady=(3, 0))

        self.help_button = RoundedButton(
            footer_frame,
            text=self.language_strings[self.language]["help"],
            command=self.show_help,
            radius=8,
            padding=8,
            color=self.current_theme["button_bg"],
            hover_color=self.current_theme["button_active_bg"],
            fg=self.current_theme["button_fg"],
            font=self.normal_font
        )
        self.help_button.pack(side=tk.RIGHT)

        self.update_song_list(self.tr("ready"))

    def process_ui_queue(self):
        """Process UI update requests from the queue to prevent freezing"""
        try:
            # Process up to 5 updates at a time for better responsiveness
            for _ in range(5):
                if self.ui_queue.empty():
                    break
                
                # Get task with a timeout to prevent hanging
                try:
                    task = self.ui_queue.get(block=True, timeout=0.1)
                    task()
                    self.ui_queue.task_done()
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Error in UI queue processing: {str(e)}")
        finally:
            # Always schedule the next check (faster interval for better responsiveness)
            self.root.after(20, self.process_ui_queue)  # Reduced from 50ms to 20ms

    def tr(self, key):
        return self.language_strings[self.language][key]

    def toggle_language(self):
        # Toggle language
        self.language = "en" if self.language == "vi" else "vi"
        
        # Update button text to show the OTHER language (what you'll switch to next time)
        self.lang_button.config(text="VI" if self.language == "en" else "EN")
        
        # Update all UI text
        self.update_ui_text()
        
        # Recreate the context menu with new language
        self.create_context_menu()

    def update_ui_text(self):
        # Update window title
        self.root.title(self.tr("title"))
        
        # Update main title
        self.title_label.config(text=self.tr("title"))
        
        # Update URL label
        self.url_label.config(text=self.tr("url_label"))
        
        # Update path label
        self.update_path_label()
        
        # Update choose folder button
        self.choose_folder_button.config(text=self.tr("choose_folder"))
        
        # Update format checkbox
        self.format_checkbox.config(text=self.tr("flac_format"))
        
        # Update download button
        if not hasattr(self.download_button, 'is_animating') or not self.download_button.is_animating:
            if self.use_flac.get():
                self.download_button.configure(text=self.tr("download_flac"))
            else:
                self.download_button.configure(text=self.tr("download"))
        
        # Update help button
        self.help_button.config(text=self.tr("help"))
        
        # Update progress frame title
        self.progress_frame.config(text=self.tr("progress"))
        
        # Update status message if it's the default message
        current_text = self.song_list.get("1.0", tk.END).strip()
        if current_text in [self.tr("ready"), self.language_strings["en"]["ready"], self.language_strings["vi"]["ready"]]:
            self.update_song_list(self.tr("ready"))

    def update_path_label(self):
        self.path_var.set(f"{self.tr('save_to')} {self.save_path}")

    def choose_directory(self):
        directory = filedialog.askdirectory(initialdir=self.save_path)
        if directory:
            self.save_path = directory
            self.update_path_label()

    def normalize_url(self, raw_url):
        """Chuẩn hóa URL từ nhiều định dạng khác nhau thành URL chính thức"""
        # Bỏ khoảng trắng ở đầu và cuối URL
        url = raw_url.strip()
        
        # Xử lý URL có ký tự @ ở đầu
        if url.startswith('@'):
            # Kiểm tra xem sau @ có phải là URL đầy đủ không
            if url[1:].strip().startswith(('http://', 'https://', 'www.')):
                url = url[1:].strip()
            # Nếu @ là một phần của tên kênh YouTube
            else:
                # Giữ nguyên @ nếu nó là username của kênh
                pass
        
        # Xử lý URL thiếu phần domain (ví dụ: "watch?v=nsm32kHAaEA&list=...")
        if url.startswith('watch?v='):
            url = 'https://www.youtube.com/' + url
        
        # Chuyển YouTube mobile (m.youtube.com) sang desktop
        if 'm.youtube.com' in url:
            url = url.replace('m.youtube.com', 'www.youtube.com')
        
        # Chuyển YouTube Music sang link thường
        if 'music.youtube.com' in url:
            url = url.replace('music.youtube.com', 'www.youtube.com')
        
        # Đảm bảo URL YouTube có giao thức
        if 'youtube.com' in url or 'youtu.be' in url:
            if not url.startswith(('http://', 'https://')):
                if url.startswith('www.'):
                    url = 'https://' + url
                else:
                    url = 'https://www.' + url
        
        # Trích xuất video ID từ URL YouTube
        youtube_watch_pattern = re.compile(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})')
        youtube_match = youtube_watch_pattern.search(url)
        if youtube_match:
            video_id = youtube_match.group(1)
            # Tạo URL chuẩn với video ID
            return f"https://www.youtube.com/watch?v={video_id}"
        
        # Kiểm tra nếu URL là link rút gọn youtu.be
        youtu_be_pattern = re.compile(r'^(https?://)?(www\.)?youtu\.be/([a-zA-Z0-9_-]{11})')
        youtu_be_match = youtu_be_pattern.match(url)
        if youtu_be_match:
            video_id = youtu_be_match.group(3)
            return f"https://www.youtube.com/watch?v={video_id}"
        
        # Chuyển YouTube Shorts sang link chính
        shorts_pattern = re.compile(r'^(https?://)?(www\.|m\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})')
        shorts_match = shorts_pattern.match(url)
        if shorts_match:
            video_id = shorts_match.group(3)
            return f"https://www.youtube.com/watch?v={video_id}"
        
        # Kiểm tra nếu URL là ID video YouTube trực tiếp
        youtube_id_pattern = re.compile(r'^[a-zA-Z0-9_-]{11}$')
        if youtube_id_pattern.match(url):
            return f"https://www.youtube.com/watch?v={url}"
        
        # Đảm bảo URL SoundCloud có giao thức
        if 'soundcloud.com' in url and not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Nếu không có quy tắc nào áp dụng, trả về URL gốc
        return url

    def is_valid_url(self, url):
        """Check if the input is a valid YouTube or SoundCloud URL"""
        # Chuẩn hóa URL trước khi kiểm tra
        url = self.normalize_url(url)
        
        # Simple regex pattern for URL validation
        url_pattern = re.compile(
            r'^(https?://)?(www\.)?(youtube\.com|youtu\.be|soundcloud\.com)/.+',
            re.IGNORECASE
        )
        return bool(url_pattern.match(url))

    def validate_urls(self, urls):
        """Validate a list of URLs, returning valid ones and invalid ones"""
        valid_urls = []
        invalid_urls = []
        
        for raw_url in urls:
            if not raw_url.strip():  # Skip empty lines
                continue
            
            # Chuẩn hóa URL
            url = self.normalize_url(raw_url)
            
            if self.is_valid_url(url):
                valid_urls.append(url)  # Lưu URL đã chuẩn hóa
            else:
                invalid_urls.append(raw_url)  # Giữ nguyên URL gốc cho thông báo lỗi
        
        return valid_urls, invalid_urls

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 1)
            if total > 0:
                percentage = int((downloaded / total) * 100)
                title = d.get('info_dict', {}).get('title', 'Unknown')
                downloading_msg = f" {self.tr('downloading').format(title)} - {percentage}%"
                
                # Update the status message with percentage
                def update_status():
                    with self.download_lock:
                        for i, msg in enumerate(self.downloading_songs):
                            if title in msg and "" in msg:
                                self.downloading_songs[i] = downloading_msg
                                self.update_song_list()
                                break
                
                self.ui_queue.put(update_status)
        
        elif d['status'] == 'finished':
            title = None
            if 'info_dict' in d and 'title' in d['info_dict']:
                title = d['info_dict']['title']
            else:
                filename = d.get('filename', '').split('/')[-1]
                title = filename
            
            converting_msg = f"⚙️ Converting: {title}"
            
            def update_converting_status():
                with self.download_lock:
                    found = False
                    for i, msg in enumerate(self.downloading_songs):
                        if title in msg and "⏳" in msg:
                            self.downloading_songs[i] = converting_msg
                            found = True
                            self.update_song_list()
                    
                    if not found:
                        self.update_song_list()
            
            self.ui_queue.put(update_converting_status)

    def is_soundcloud_url(self, url):
        return 'soundcloud.com' in url.lower()

    def get_info(self, url, cache=True):
        """Get information about a URL with optional caching to prevent repeated API calls"""
        if cache and url in self.album_info_cache:
            return self.album_info_cache[url]
        
        try:
            ydl_opts = {
                'quiet': True, 
                'format': 'bestaudio/best',
                'socket_timeout': 60,  # Increased timeout to 120 seconds
                'nocheckcertificate': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                
                # Cache the result if requested
                if cache:
                    self.album_info_cache[url] = info_dict
                return info_dict
        except Exception as e:
            print(f"Error getting info: {str(e)}")
            
            # Tăng số lượng failed_downloads nếu không lấy được thông tin
            with self.download_lock:
                self.failed_downloads += 1
            
            return None

    def count_total_downloads(self, urls):
        """Count total downloads, but do this in a background thread"""
        # Initially set to number of URLs as minimum
        initial_count = len(urls)
        self.ui_queue.put(lambda: self.update_total_downloads(initial_count))
        
        # Start a thread to get the actual count
        threading.Thread(target=self._count_downloads_thread, args=(urls,), daemon=True).start()
        
        return initial_count
    
    def _count_downloads_thread(self, urls):
        """Background thread to count actual downloads including album tracks"""
        total = 0
        
        for url in urls:
            try:
                if self.is_soundcloud_url(url):
                    info = self.get_info(url)
                    if info:
                        if info.get('_type') == 'playlist':
                            # Count each track in the playlist
                            total += len(info.get('entries', []))
                        else:
                            # Single track
                            total += 1
                else:
                    # YouTube URL counts as 1
                    total += 1
            except Exception:
                # If we can't get info, still count it as 1
                total += 1
        
        # Update the total count in the UI thread
        self.ui_queue.put(lambda: self.update_total_downloads(max(total, len(urls))))

    def update_total_downloads(self, count):
        """Update the total download count and adjust progress bar"""
        with self.download_lock:
            old_total = self.total_downloads
            self.total_downloads = count
            
            # Adjust progress bar based on new total
            if old_total > 0 and self.completed_downloads > 0:
                overall_percent = (self.completed_downloads * 100) / self.total_downloads
                self.progress_var.set(int(overall_percent))

    def sanitize_filename(self, filename):
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def update_song_list(self, message=None):
        # Use UI queue to update song list safely
        def update():
            self.song_list.config(state=tk.NORMAL)
            self.song_list.delete(1.0, tk.END)
            
            if message:
                self.song_list.insert(tk.END, message)
                self.song_list.see("1.0")
            elif self.downloading_songs:
                # First, insert all songs
                for i, song in enumerate(self.downloading_songs):
                    self.song_list.insert(tk.END, f"{song}\n")
                
                # Then find the active download to scroll to
                for i, song in enumerate(self.downloading_songs):
                    # Check for active download or conversion
                    if "⏳" in song or "⚙️" in song:
                        self.song_list.see(f"{i+1}.0")
                        break
                    # Check for completed album
                    elif "Album:" in song and "Tải xong" in song:
                        self.song_list.see("1.0")
                        break
                else:
                    # If no active downloads found, scroll to top
                    self.song_list.see("1.0")
            else:
                self.song_list.insert(tk.END, self.tr("success"))
                self.song_list.see("1.0")
            
            self.song_list.config(state=tk.DISABLED)
        
        self.ui_queue.put(update)

    def add_downloading_song(self, song):
        # Use UI queue to update downloading songs safely
        def update():
            with self.download_lock:  # Lock to protect downloading_songs
                # Thêm bài hát vào danh sách
                self.downloading_songs.append(song)
                
                # Cập nhật danh sách và cuộn đến bài hát vừa thêm
                self.update_song_list()
                
                # Tìm vị trí của bài hát vừa thêm để cuộn đến
                position = f"{len(self.downloading_songs)}.0"
                self.song_list.config(state=tk.NORMAL)
                self.song_list.see(position)
                self.song_list.config(state=tk.DISABLED)
        
        self.ui_queue.put(update)

    def update_download_status(self, old_text, new_text):
        # Use UI queue to update download status safely
        def update():
            with self.download_lock:
                if old_text in self.downloading_songs:
                    index = self.downloading_songs.index(old_text)
                    self.downloading_songs[index] = new_text
                else:
                    self.downloading_songs.append(new_text)
                    index = len(self.downloading_songs) - 1
                
                # Update the list and scroll to the updated/new item
                self.song_list.config(state=tk.NORMAL)
                self.song_list.delete(1.0, tk.END)
                
                # Insert all songs
                for song in self.downloading_songs:
                    self.song_list.insert(tk.END, f"{song}\n")
                
                # Scroll to the updated/new item if it's an active download
                if "⏳" in new_text or "⚙️" in new_text:
                    self.song_list.see(f"{index+1}.0")
                elif "Album:" in new_text and "Tải xong" in new_text:
                    self.song_list.see("1.0")
                
                self.song_list.config(state=tk.DISABLED)
        
        self.ui_queue.put(update)

    def download_soundcloud_album(self, url):
        # Get album info (using cached version if available)
        info = self.get_info(url)
        if not info:
            error_msg = self.tr("failed").format(url)
            self.add_downloading_song(error_msg)
            return False
        
        album_title = info.get('title', 'Unknown Album')
        album_msg = self.tr("album").format(album_title)
        self.add_downloading_song(album_msg)
        
        album_path = os.path.join(self.save_path, self.sanitize_filename(album_title))
        os.makedirs(album_path, exist_ok=True)
        
        success = True
        if info.get('_type') == 'playlist':
            entries = info.get('entries', [])
            
            # Create a list of tracks to download
            track_downloads = []
            for entry in entries:
                track_title = entry.get('title', 'Unknown Track')
                track_msg = self.tr("track").format(track_title)
                self.add_downloading_song(track_msg)
                
                track_url = entry.get('webpage_url')
                if track_url:
                    track_downloads.append((track_url, track_msg))
            
            # Lưu số lượng bài hát trong album để theo dõi tiến trình
            album_tracks_count = len(track_downloads)
            
            # Điều chỉnh total_downloads để tính chính xác số lượng bài hát sẽ tải
            with self.download_lock:
                # Giảm đi 1 vì album chỉ tính là 1 download trong total_downloads ban đầu
                self.total_downloads = self.total_downloads - 1 + album_tracks_count
                # Cập nhật thanh tiến trình
                self.ui_queue.put(lambda: self.progress_var.set(int(self.completed_downloads * 100 / self.total_downloads) if self.total_downloads > 0 else 0))
                
                # Tạo hoặc cập nhật từ điển theo dõi album
                if not hasattr(self, 'albums_in_progress'):
                    self.albums_in_progress = {}
                self.albums_in_progress[album_title] = {
                    'total': album_tracks_count,
                    'completed': 0,
                    'failed': 0
                }
            
            # Now download each track (one at a time to avoid API rate limits)
            for idx, (track_url, track_msg) in enumerate(track_downloads):
                # Cập nhật số thứ tự để người dùng biết đang tải bài thứ mấy
                progress_msg = f"{track_msg} ({idx+1}/{album_tracks_count})"
                self.update_download_status(track_msg, progress_msg)
                
                # Tải bài hát
                track_success = self.download_track(track_url, album_path, progress_msg)
                
                # Cập nhật trạng thái album
                with self.download_lock:
                    if album_title in self.albums_in_progress:
                        if track_success:
                            self.albums_in_progress[album_title]['completed'] += 1
                        else:
                            self.albums_in_progress[album_title]['failed'] += 1
                            success = False
            
            # Album tải xong, nhưng CHỈ xóa nó khỏi albums_in_progress khi tất cả bài hát
            # đã được xử lý xong (hoặc thành công hoặc thất bại)
            with self.download_lock:
                if album_title in self.albums_in_progress:
                    album_stats = self.albums_in_progress[album_title]
                    total_processed = album_stats['completed'] + album_stats['failed']
                    
                    # Chỉ xóa khỏi danh sách khi đã xử lý đủ số bài
                    if total_processed >= album_stats['total']:
                        del self.albums_in_progress[album_title]
                        
                        
                        if self.language == 'vi':
                           album_summary = f"Album: {album_title} - Tải xong {album_stats['completed']}/{album_stats['total']} bài"
                        else:  # 'en' hoặc mặc định là tiếng Anh
                           album_summary = f"Album: {album_title} - Downloaded {album_stats['completed']}/{album_stats['total']} tracks"
            
                        self.update_download_status(album_msg, album_summary)
                        
                        # Check if we need to update the progress bar to 100%
                        if self.completed_downloads >= self.total_downloads:
                            # Check if there are no more albums in progress
                            if not self.albums_in_progress:
                                # No more albums, set progress to 100% if we've completed all downloads
                                self.progress_var.set(100)
        
        return success

    def download_track(self, url, output_path=None, track_msg=None):
        try:
            info = self.get_info(url, cache=False)
            if not info:
                error_msg = self.tr("failed").format(url)
                self.add_downloading_song(error_msg)
                
                with self.download_lock:
                    self.completed_downloads += 1
                
                return False
            
            title = info.get('title', 'Unknown Track')
            downloading_msg = self.tr("downloading").format(title)
            
            if not track_msg:
                self.add_downloading_song(downloading_msg)
            else:
                self.update_download_status(track_msg, downloading_msg)
            
            sanitized_title = self.sanitize_filename(title)
            
            if output_path:
                filename = os.path.join(output_path, sanitized_title)
            else:
                filename = os.path.join(self.save_path, f"{sanitized_title}")
            
            # Define metadata
            artist = info.get('artist', info.get('uploader', 'Unknown Artist'))
            title = info.get('title', 'Unknown Title')
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Choose audio format based on user selection
            audio_format = 'flac' if self.use_flac.get() else 'mp3'
            audio_quality = 'best' if self.use_flac.get() else '320'
            
            # Fixed ydl_opts with correct postprocessor args structure
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': filename,
                'progress_hooks': [self.progress_hook],
                'postprocessor_hooks': [self.postprocessor_hook],
                'socket_timeout': 60,
                'nocheckcertificate': True,
                'ffmpeg_location': self.ffmpeg_path,
                # Cache optimization
                'cachedir': False,  # Disable cache to avoid disk I/O
                'writethumbnail': True,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': audio_format,
                        'preferredquality': audio_quality,
                    },
                    {
                        'key': 'EmbedThumbnail',
                    },
                    {
                        'key': 'FFmpegMetadata',
                        'add_metadata': True,
                    },
                ],
                # Add custom metadata fields
                'add_metadata': True,
                # Correctly format the postprocessor_args as a flat list
                'postprocessor_args': [
                    '-metadata', f'title={title}',
                    '-metadata', f'artist={artist}',
                    '-metadata', f'album=Downloaded from YTMP3',
                    '-metadata', f'date={current_date}',
                    '-metadata', f'comment=Downloaded on {current_date}',
                    '-metadata', f'comment=Source: {url}',
                # Alternative fields for source URL to ensure compatibility with different players
                    '-metadata', f'Where from={url}',
                    '-metadata', f'copyright=Downloaded from: {url}',
                ]
            }
            
            # Add MP3-specific options if not using FLAC
            if not self.use_flac.get():
                ydl_opts['postprocessor_args'].extend([
                    '-b:a', '320k',  # Constant bitrate of 320kbps
                    '-ar', '48000',  # 48kHz sample rate
                    '-ac', '2'       # Stereo audio (2 channels)
                ])
            
            # Use with statement to ensure proper cleanup
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            return True
        
        except Exception as e:
            error_msg = f"{self.tr('failed').format(url)} ({str(e)[:50]})"
            self.update_download_status(downloading_msg if 'downloading_msg' in locals() else track_msg, error_msg)
            
            with self.download_lock:
                self.completed_downloads += 1
                self.failed_downloads += 1
            
            print(f"Download error: {str(e)}")
            return False

    def postprocessor_hook(self, d):
        """Hook to track post-processing progress"""
        if d['status'] == 'finished':
            if 'info_dict' in d:
                info_dict = d['info_dict']
                title = info_dict.get('title', '')
                
                # Update UI to show processing status
                processing_msg = f"⚙️ Converting: {title}"
                
                def update_processing_status():
                    with self.download_lock:

                        if self.language == 'vi':
                            processing_msg = f"⚙️ Đang xử lý: {title}"
                            processing_text = "⚙️ Đang xử lý"
                        else:
                            processing_msg = f"⚙️ Converting: {title}"
                            processing_text = "⚙️ Converting"

                        for i, msg in enumerate(self.downloading_songs):
                            if title in msg and (processing_text in msg or "⚙️ Converting" in msg or "⚙️ Đang xử lý" in msg):
                                self.downloading_songs[i] = processing_msg
                                break
                        self.update_song_list()
                
                self.ui_queue.put(update_processing_status)
            
            # Don't increment completed_downloads here, wait until the file is fully processed
            
            # Delay success message for UI update until after FFmpeg processing is complete
            threading.Timer(0.5, lambda: self.mark_download_complete(d)).start()

    def mark_download_complete(self, d):
        """Mark a download as complete after processing is finished"""
        title = d.get('info_dict', {}).get('title', 'Unknown')
        
        # Now mark as completed
        with self.download_lock:
            if self.total_downloads > 0:
                self.completed_downloads += 1
        
        success_msg = self.tr("downloaded").format(title)
        
        def update_final_status():
            with self.download_lock:
                for i, msg in enumerate(self.downloading_songs):
                    if title in msg and ("⚙️ Converting" in msg or "⚙️ Đang xử lý" in msg):
                        self.downloading_songs[i] = success_msg
                        break
                self.update_song_list()
        
        self.ui_queue.put(update_final_status)

    def download_video(self, url):
        try:
            if self.is_soundcloud_url(url):
                info = self.get_info(url)
                if info and info.get('_type') == 'playlist':
                    return self.download_soundcloud_album(url)
                else:
                    return self.download_track(url)
            
            # YouTube download logic
            info = self.get_info(url, cache=False)
            if not info:
                error_msg = self.tr("failed").format(url)
                self.add_downloading_song(error_msg)
                
                with self.download_lock:
                    self.completed_downloads += 1
                
                return False
            
            title = info.get('title', 'Unknown')
            artist = info.get('artist', info.get('uploader', 'Unknown Artist'))
            downloading_msg = self.tr("downloading").format(title)
            self.add_downloading_song(downloading_msg)

            sanitized_title = self.sanitize_filename(title)
            filename = os.path.join(self.save_path, f"{sanitized_title}")

            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Choose audio format based on user selection
            audio_format = 'flac' if self.use_flac.get() else 'mp3'
            audio_quality = 'best' if self.use_flac.get() else '320'
            
            # Use best audio format
            format_selection = 'bestaudio'
            
            # Simplified options focusing on basic functionality
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': filename,
                'progress_hooks': [self.progress_hook],
                'postprocessor_hooks': [self.postprocessor_hook],
                'socket_timeout': 60,
                'nocheckcertificate': True,
                'ffmpeg_location': self.ffmpeg_path,
                # Cache optimization
                'cachedir': False,  # Disable cache to avoid disk I/O
                'writethumbnail': True,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': audio_format,
                        'preferredquality': audio_quality,
                    },
                    {
                        'key': 'EmbedThumbnail',
                    },
                    {
                        'key': 'FFmpegMetadata',
                        'add_metadata': True,
                    },
                ],
                # Add custom metadata fields
                'add_metadata': True,
                # Correctly format the postprocessor_args as a flat list
                'postprocessor_args': [
                    '-metadata', f'title={title}',
                    '-metadata', f'artist={artist}',
                    '-metadata', f'album=Downloaded from YTMP3',
                    '-metadata', f'date={current_date}',
                    '-metadata', f'comment=Downloaded on {current_date}',
                    '-metadata', f'comment=Source: {url}',
                # Alternative fields for source URL to ensure compatibility with different players
                    '-metadata', f'Where from={url}',
                    '-metadata', f'copyright=Downloaded from: {url}',
                ]
            }
            
            # Add MP3-specific options if not using FLAC
            if not self.use_flac.get():
                ydl_opts['postprocessor_args'].extend([
                    '-b:a', '320k',  # Constant bitrate of 320kbps
                    '-ar', '48000',  # 48kHz sample rate
                    '-ac', '2'       # Stereo audio (2 channels)
                ])
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            return True
        except Exception as e:
            error_msg = f"{self.tr('failed').format(url)} ({str(e)[:50]})"
            self.update_download_status(downloading_msg if 'downloading_msg' in locals() else url, error_msg)
            
            with self.download_lock:
                self.completed_downloads += 1
                self.failed_downloads += 1
            
            print(f"Download error: {str(e)}")
            return False

    def download_all_videos(self):
        """Tải xuống tất cả video từ URLs được nhập"""
        # Get all non-empty lines from the text box
        raw_urls = self.url_text.get("1.0", tk.END).strip().split("\n")
        urls = [url for url in raw_urls if url.strip()]

        if not urls:
            self.download_button.stop_animation()  # Stop animation if no URLs
            messagebox.showerror(
                self.tr("error_title"),
                self.tr("error_url")
            )
            return
        
        # Validate URLs - quá trình này đã bao gồm việc chuẩn hóa URL
        valid_urls, invalid_urls = self.validate_urls(urls)
        
        # If there are invalid URLs, show an error message and stop animation
        if invalid_urls:
            self.download_button.stop_animation()
            invalid_message = "\n".join(invalid_urls[:5])
            if len(invalid_urls) > 5:
                invalid_message += f"\n... và {len(invalid_urls) - 5} URL khác"
            
            messagebox.showerror(
                self.tr("error_title"),
                self.tr("invalid_urls").format(invalid_message)
            )
            return
        
        if not valid_urls:
            self.download_button.stop_animation()
            messagebox.showerror(
                self.tr("error_title"),
                self.tr("error_url")
            )
            return

        # Disable download button immediately
        self.download_button.configure(state='disabled')
        
        # Thông báo về số URL hợp lệ đã tìm thấy
        if len(valid_urls) > 1:
            messagebox.showinfo(
                self.tr("success_title"),
                f"Đã tìm thấy {len(valid_urls)} link hợp lệ. Bắt đầu tải xuống..."
            )

        # Clear any cached album info
        self.album_info_cache = {}
        
        # Reset progress counters
        self.progress_var.set(0)
        self.downloading_songs = []
        self.failed_downloads = 0
        self.update_song_list(self.tr("starting"))
        
        # Disable download button and change its appearance
        self.download_button.configure(state='disabled')
        self.download_button.current_color = self.download_button.disabled_color
        self.download_button._draw()
        
        # Set initial count and start background counting
        self.total_downloads = self.count_total_downloads(valid_urls)
        self.completed_downloads = 0

        # Start downloads in separate threads
        for url in valid_urls:
            t = threading.Thread(target=self.download_video, args=(url,), daemon=True)
            t.start()

        # Create a separate thread to monitor download progress and completion
        threading.Thread(target=self.monitor_downloads, args=(valid_urls,), daemon=True).start()

    def monitor_downloads(self, urls):
        """Monitor download progress and update UI when complete"""
        check_interval = 0.5  # seconds
        max_checks = 14400  # 2 hours (2*60*60/0.5)
        checks = 0
        
        start_time = datetime.now()
        max_download_time = 60 * 120  # 2 hours maximum
        
        completion_detected = False
        last_completed = 0
        no_progress_count = 0
        
        while checks < max_checks:
            threading.Event().wait(check_interval)
            checks += 1
            
            elapsed_seconds = (datetime.now() - start_time).total_seconds()
            if elapsed_seconds > max_download_time:
                print(f"Download timed out after {max_download_time/60} minutes")
                break
            
            with self.download_lock:
                # Check all albums for completion
                all_albums_complete = True
                if hasattr(self, 'albums_in_progress') and self.albums_in_progress:
                    for album_name, stats in self.albums_in_progress.items():
                        total_processed = stats['completed'] + stats['failed']
                        print(f"Checking album {album_name}: {stats['completed']}/{stats['total']} completed, {stats['failed']} failed")
                        if total_processed < stats['total']:
                            all_albums_complete = False
                            break
                
                # Check for any active downloads or conversions
                tracks_in_progress = False
                for status in self.downloading_songs:
                    if any(indicator in status for indicator in ["⚙️ Converting", "⏳", "Đang tải"]):
                        tracks_in_progress = True
                        break
                
                # Update progress tracking
                if last_completed == self.completed_downloads:
                    no_progress_count += 1
                else:
                    no_progress_count = 0
                    last_completed = self.completed_downloads
                
                # Only consider downloads complete when:
                # 1. All regular downloads are complete
                # 2. All albums are complete
                # 3. No active conversions or downloads
                # 4. At least one download has completed
                download_complete = (
                    (self.completed_downloads >= self.total_downloads) and
                    all_albums_complete and 
                    (not tracks_in_progress) and
                    (self.completed_downloads > 0)
                )
                
                # Consider downloads stalled if no progress for 30 seconds
                stalled_downloads = (
                    no_progress_count > 60 and 
                    self.completed_downloads > 0 and 
                    not tracks_in_progress and
                    all_albums_complete  # Only consider stalled if albums are complete
                )
                
                if download_complete or stalled_downloads:
                    completion_detected = True
                    break
            
            # Debug output
            if hasattr(self, 'albums_in_progress') and self.albums_in_progress:
                print(f"Still waiting: completed={self.completed_downloads}, total={self.total_downloads}, albums_complete={all_albums_complete}, tracks_in_progress={tracks_in_progress}")

        print("Download monitor ended, scheduling finalize")
        
        # All downloads complete or stopped
        def finalize():
            print("Finalizing download process")
            
            # Stop the download button animation
            self.download_button.stop_animation()
            
            # Re-enable download button and restore its appearance
            self.download_button.configure(state='normal')
            self.download_button.current_color = self.download_button.color
            self.download_button._draw()
            
            try:
                # Show appropriate message
                if checks >= max_checks:
                    messagebox.showinfo(
                        self.tr("success_title"),
                        f"Đã hết thời gian chờ sau 2 giờ. Một số tệp có thể chưa tải xong."
                    )
                elif self.failed_downloads > 0:
                    if self.failed_downloads == self.total_downloads:
                        messagebox.showinfo(
                            self.tr("error_title"),
                            f"Tất cả {self.failed_downloads} tệp đều tải thất bại!"
                        )
                    else:
                        messagebox.showinfo(
                            self.tr("success_title"),
                            f"Đã tải {self.completed_downloads - self.failed_downloads} thành công và {self.failed_downloads} thất bại trong tổng số {self.total_downloads} tệp!"
                        )
                else:
                    messagebox.showinfo(
                        self.tr("success_title"),
                        self.tr("success")
                    )
                
                print("MessageBox showed successfully")
                
                # Cập nhật giao diện
                self.url_text.delete(1.0, tk.END)
                self.update_song_list(self.tr("ready"))
                
                # Reset counters
                self.total_downloads = 0
                self.completed_downloads = 0
                self.failed_downloads = 0
                
                # Clear the cache to free memory
                self.album_info_cache = {}
                if hasattr(self, 'albums_in_progress'):
                    self.albums_in_progress = {}
            
            except Exception as e:
                print(f"Error showing message box: {str(e)}")
        
        self.ui_queue.put(finalize)
        print("Finalize function put into queue correctly")

    def show_help(self):
        help_text = {
            "en": """How to use:
1. Paste YouTube or SoundCloud URLs (one per line)
2. Choose save folder (optional)
3. Check FLAC Format option for high-quality audio (optional)
4. Click Download MP3
5. Wait for completion

Features:
- YouTube videos to MP3/FLAC conversion
- SoundCloud tracks albums/playlists
- High-quality FLAC format option

Troubleshooting:
- Check internet connection
- Valid YouTube or SoundCloud URLs only
- For larger files, FLAC format will require more disk space
- Contact: info@sytinh.com""",
            
            "vi": """Hướng dẫn sử dụng:
1. Dán liên kết YouTube hoặc SoundCloud (mỗi dòng 1 link)
2. Chọn thư mục lưu (tùy chọn)
3. Chọn định dạng FLAC cho chất lượng âm thanh cao (tùy chọn)
4. Nhấn Tải MP3
5. Chờ hoàn thành

Tính năng:
- Tải video YouTube thành MP3/FLAC
- Tải bài hát album/playlist SoundCloud
- Tùy chọn định dạng FLAC chất lượng cao

Xử lý lỗi:
- Kiểm tra kết nối mạng
- Chỉ dùng link YouTube hoặc SoundCloud hợp lệ
- Đối với tệp lớn, định dạng FLAC sẽ chiếm nhiều dung lượng hơn
- Liên hệ: info@sytinh.com"""
        }

        help_window = tk.Toplevel(self.root)
        help_window.title(f"MP3 Converter Help - {self.language.upper()}")
        help_window.geometry("380x290")
        help_window.minsize(380, 290)
        
        # Create a frame to hold the content
        content_frame = tk.Frame(help_window, bg=self.current_theme["bg"])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create countdown label at the top
        countdown_text = "This window will close in 15s" if self.language == "en" else "Cửa sổ này sẽ tự đóng sau 15s"
        countdown_label = tk.Label(
            content_frame,
            text=countdown_text,
            font=("Helvetica", 10),
            fg="#FF5555",
            bg=self.current_theme["bg"]
        )
        countdown_label.pack(pady=(5, 0))
        
        # Text widget for help content
        text_widget = tk.Text(
            content_frame,
            font=self.normal_font,
            wrap=tk.WORD,
            padx=15,
            pady=15
        )
        text_widget.insert(tk.END, help_text[self.language])
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Timer to update countdown and close window
        seconds_remaining = 15
        
        def update_countdown():
            nonlocal seconds_remaining
            seconds_remaining -= 1
            if seconds_remaining > 0:
                new_text = f"This window will close in {seconds_remaining}s" if self.language == "en" else f"Cửa sổ này sẽ tự đóng sau {seconds_remaining}s"
                countdown_label.config(text=new_text)
                help_window.after(1000, update_countdown)
            else:
                help_window.destroy()
        
        # Start the countdown
        help_window.after(1000, update_countdown)

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label=self.tr("paste"), command=lambda: self.handle_menu_action("paste"))
        self.context_menu.add_command(label=self.tr("cut"), command=lambda: self.handle_menu_action("cut"))
        self.context_menu.add_command(label=self.tr("copy"), command=lambda: self.handle_menu_action("copy"))
        self.context_menu.add_separator()
        self.context_menu.add_command(label=self.tr("select_all"), command=lambda: self.handle_menu_action("select_all"))

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def handle_menu_action(self, action):
        try:
            if action == "cut":
                self.root.focus_get().event_generate("<<Cut>>")
            elif action == "copy":
                self.root.focus_get().event_generate("<<Copy>>")
            elif action == "paste":
                self.root.focus_get().event_generate("<<Paste>>")
            elif action == "select_all":
                self.url_text.tag_add(tk.SEL, "1.0", tk.END)
            self.url_text.mark_set(tk.INSERT, "1.0")
            self.url_text.see(tk.INSERT)
        except:
            pass  # Ignore any errors during clipboard operations

    def toggle_theme(self):
        """Modified toggle_theme to use random colors only on toggle"""
        self.dark_mode = not self.dark_mode
        
        if self.dark_mode:
            # Generate random dark theme colors once when toggling to dark mode
            self.current_theme = self.generate_random_dark_theme()
        else:
            # Switch back to light theme
            self.current_theme = self.color_schemes["light"]
        
        # Update theme button text
        self.theme_button.config(text="☀️" if self.dark_mode else "🌙")
        
        # Apply the theme
        self.apply_theme()

    def apply_theme(self):
        """Separated theme application logic for reuse"""
        # Update main window and frames
        self.root.configure(bg=self.current_theme["bg"])
        self.main_frame.configure(bg=self.current_theme["bg"])
        
        # Update format checkbox
        self.format_checkbox.configure(
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
            selectcolor=self.current_theme["entry_bg"],
            activebackground=self.current_theme["bg"],
            activeforeground=self.current_theme["fg"]
        )
        self.format_frame.configure(bg=self.current_theme["bg"])
        
        # Update all frames' backgrounds
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=self.current_theme["bg"])
                # Update children of regular frames
                for child in widget.winfo_children():
                    try:
                        if isinstance(child, (tk.Frame, tk.Label, tk.Checkbutton)):
                            # Only apply the properties that are supported
                            child_opts = {}
                            if 'bg' in child.config():
                                child_opts['bg'] = self.current_theme["bg"]
                            if 'fg' in child.config():
                                child_opts['fg'] = self.current_theme["fg"]
                            if child_opts:
                                child.configure(**child_opts)
                        elif isinstance(child, tk.Text):
                            child.configure(
                                bg=self.current_theme["entry_bg"],
                                fg=self.current_theme["fg"]
                            )
                    except tk.TclError:
                        # Skip this widget if it doesn't support the requested options
                        pass
            elif isinstance(widget, ttk.LabelFrame):
                # Update ttk styles instead of direct configuration
                self.style.configure(
                    "Custom.TLabelframe",
                    background=self.current_theme["bg"],
                    bordercolor=self.current_theme["trough_color"]
                )
                self.style.configure(
                    "Custom.TLabelframe.Label",
                    background=self.current_theme["bg"],
                    foreground=self.current_theme["fg"]
                )
        
        # Update title label
        self.title_label.configure(
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"]
        )
        
        # Update URL label and text area
        self.url_label.configure(
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"]
        )
        self.url_text.configure(
            bg=self.current_theme["entry_bg"],
            fg=self.current_theme["fg"]
        )
        
        # Update path label
        self.path_label.configure(
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"]
        )
        
        # Update song list
        self.song_list.configure(
            bg=self.current_theme["entry_bg"],
            fg=self.current_theme["fg"]
        )
        
        # Update progress bar style
        self.style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=self.current_theme["trough_color"],
            background=self.current_theme["progress_color"]
        )
        
        # Update ttk button style
        self.style.configure(
            "Custom.TButton",
            background=self.current_theme["button_bg"],
            foreground=self.current_theme["button_fg"]
        )
        self.style.map("Custom.TButton",
            background=[('active', self.current_theme["button_active_bg"])],
            foreground=[('active', self.current_theme["button_fg"])]
        )
        
        # Update all rounded buttons with new theme colors
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, RoundedButton):
                        child.color = self.current_theme["button_bg"]
                        child.hover_color = self.current_theme["button_active_bg"]
                        child.fg = self.current_theme["button_fg"]
                        if child.state != 'disabled':
                            child.current_color = child.color
                        child._draw()

    def generate_random_dark_theme(self):
        """Generate a random dark color scheme that maintains readability"""
        # Generate a random base hue
        hue = random.random()
        
        # Create a dark background with low saturation
        bg_hsv = (hue, 0.2, 0.15)  # Dark, slightly saturated background
        bg_rgb = colorsys.hsv_to_rgb(*bg_hsv)
        bg_color = "#{:02x}{:02x}{:02x}".format(
            int(bg_rgb[0] * 255),
            int(bg_rgb[1] * 255),
            int(bg_rgb[2] * 255)
        )
        
        # Create a lighter entry background
        entry_hsv = (hue, 0.15, 0.2)  # Slightly lighter than background
        entry_rgb = colorsys.hsv_to_rgb(*entry_hsv)
        entry_color = "#{:02x}{:02x}{:02x}".format(
            int(entry_rgb[0] * 255),
            int(entry_rgb[1] * 255),
            int(entry_rgb[2] * 255)
        )
        
        # Create vibrant button colors with complementary hue
        button_hue = (hue + 0.5) % 1.0  # Complementary color
        button_hsv = (button_hue, 0.6, 0.9)  # Vibrant button
        button_rgb = colorsys.hsv_to_rgb(*button_hsv)
        button_color = "#{:02x}{:02x}{:02x}".format(
            int(button_rgb[0] * 255),
            int(button_rgb[1] * 255),
            int(button_rgb[2] * 255)
        )
        
        # Create hover color (slightly darker button)
        hover_hsv = (button_hue, 0.7, 0.8)
        hover_rgb = colorsys.hsv_to_rgb(*hover_hsv)
        hover_color = "#{:02x}{:02x}{:02x}".format(
            int(hover_rgb[0] * 255),
            int(hover_rgb[1] * 255),
            int(hover_rgb[2] * 255)
        )
        
        return {
            "bg": bg_color,
            "fg": "#FFFFFF",  # Keep text white for readability
            "button_bg": button_color,
            "button_fg": "#000000",  # Keep button text black for contrast
            "button_active_bg": hover_color,
            "entry_bg": entry_color,
            "entry_fg": "#FFFFFF",  # Keep entry text white
            "trough_color": bg_color,
            "progress_color": button_color
        }

    def update_download_button_text(self):
        """Update download button text based on selected format"""
        if not hasattr(self.download_button, 'is_animating') or not self.download_button.is_animating:
            if self.use_flac.get():
                self.download_button.configure(text=self.tr("download_flac"))
            else:
                self.download_button.configure(text=self.tr("download"))

if __name__ == "__main__":
    root = tk.Tk()
    app = MP3Converter(root)
    root.mainloop()