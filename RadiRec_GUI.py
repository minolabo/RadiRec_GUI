#
# RadiRec GUI v1.0
# Copyright (C) 2026 minolabo
#
# Based on rec_radiko_ts.sh by uru (https://github.com/uru2/rec_radiko_ts)
# Original Script Copyright (C) 2017-2026 uru (https://twitter.com/uru_2)
# License: MIT
#

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
import subprocess
import datetime
import threading
import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import base64
import time
import secrets
import json
import re
import platform
import shutil
import tempfile

# RadikoConstants
CONFIG_FILE = 'config.json'
# Define authorize key value (from https://radiko.jp/apps/js/playerCommon.js)
AUTHKEY_VALUE = 'bcd151073c03b352e1ef2fd66c32209da9ca0afa'


class RadikoRecorderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RadiRec GUI v1.0")
        self.root.geometry("620x700")

        # Variables
        self.mode_var = tk.StringVar(value="url")
        self.station_var = tk.StringVar()
        self.start_time_var = tk.StringVar(value=datetime.datetime.now().strftime("%Y%m%d%H%M"))
        self.duration_var = tk.StringVar(value="60")
        self.url_var = tk.StringVar()
        self.mail_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.filename_template_var = tk.StringVar(value="{DATE}_{TIME}_{TITLE}")
        
        self.stations_data = [] # List of (id, name, area_id)
        self.authtoken = None
        self.area_id = None
        self.radiko_session = None

        self.load_config()
        self.create_widgets()

        # Save config on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.mail_var.set(config.get('mail', ''))
                    self.pass_var.set(config.get('password', ''))
                    self.filename_template_var.set(config.get('template', "{DATE}_{TIME}_{TITLE}"))
            except Exception as e:
                print(f"Config load error: {e}")

    def save_config(self):
        config = {
            'mail': self.mail_var.get(),
            'password': self.pass_var.get(),
            'template': self.filename_template_var.get()
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Config save error: {e}")

    def on_close(self):
        self.save_config()
        self.root.destroy()

    def create_widgets(self):
        # Mode Selection
        frame_mode = ttk.LabelFrame(self.root, text="モード選択", padding=10)
        frame_mode.pack(fill="x", padx=10, pady=5)
        ttk.Radiobutton(frame_mode, text="URLから録音", variable=self.mode_var, value="url", command=self.toggle_mode).pack(side="left", padx=5)
        ttk.Radiobutton(frame_mode, text="日時指定録音", variable=self.mode_var, value="manual", command=self.toggle_mode).pack(side="left", padx=5)

        # Manual Recording Frame
        self.frame_manual = ttk.LabelFrame(self.root, text="録音設定", padding=10)
        self.frame_manual.pack(fill="x", padx=10, pady=5)

        ttk.Label(self.frame_manual, text="放送局:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.combo_station = ttk.Combobox(self.frame_manual, textvariable=self.station_var, width=30, state="readonly")
        self.combo_station.grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(self.frame_manual, text="放送局一覧取得", command=self.get_stations_thread).grid(row=0, column=2, padx=5, pady=2)

        ttk.Label(self.frame_manual, text="開始日時 (YYYYMMDDHHMM):").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(self.frame_manual, textvariable=self.start_time_var).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(self.frame_manual, text="現在時刻", command=self.set_now).grid(row=1, column=2, padx=5, pady=2)

        ttk.Label(self.frame_manual, text="録音時間 (分):").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(self.frame_manual, textvariable=self.duration_var, width=10).grid(row=2, column=1, sticky="w", padx=5, pady=2)

        # URL Recording Frame
        self.frame_url = ttk.LabelFrame(self.root, text="URL設定", padding=10)

        ttk.Label(self.frame_url, text="番組URL:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(self.frame_url, textvariable=self.url_var, width=50).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(self.frame_url, text="クリップボードから貼り付け", command=self.paste_url).grid(row=0, column=2, padx=5, pady=2)

        # Config / Naming Options
        frame_opts = ttk.LabelFrame(self.root, text="設定・オプション", padding=10)
        frame_opts.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_opts, text="メールアドレス:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(frame_opts, textvariable=self.mail_var, width=30).grid(row=0, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(frame_opts, text="パスワード:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(frame_opts, textvariable=self.pass_var, show="*", width=30).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(frame_opts, text="ファイル名規則:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(frame_opts, textvariable=self.filename_template_var, width=40).grid(row=2, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(frame_opts, text="{DATE}{TIME}{TITLE}{STATION} が使用可能", font=("", 8), foreground="gray").grid(row=3, column=1, sticky="w", padx=5)

        # LOG
        frame_log = ttk.LabelFrame(self.root, text="実行ログ", padding=10)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)
        self.text_log = tk.Text(frame_log, height=12)
        self.text_log.pack(fill="both", expand=True)

        # Run Button
        ttk.Button(self.root, text="録音開始", command=self.run_recording_thread).pack(pady=10)
        
        self.toggle_mode()

    def toggle_mode(self):
        if self.mode_var.get() == "manual":
            self.frame_url.pack_forget()
            self.frame_manual.pack(fill="x", padx=10, pady=5, after=self.root.children.get("!labelframe"))
        else:
            self.frame_manual.pack_forget()
            self.frame_url.pack(fill="x", padx=10, pady=5, after=self.root.children.get("!labelframe"))

    def set_now(self):
        self.start_time_var.set(datetime.datetime.now().strftime("%Y%m%d%H%M"))

    def paste_url(self):
        try:
            clipboard = self.root.clipboard_get()
            self.url_var.set(clipboard)
            self.log("クリップボードからURLを貼り付けました。")
        except Exception as e:
            self.log("クリップボードが空か、読み取りに失敗しました。")

    def log(self, message):
        self.text_log.insert(tk.END, message + "\n")
        self.text_log.see(tk.END)

    def http_request(self, url, headers=None, data=None, method='GET'):
        if headers is None: headers = {}
        if data is not None and isinstance(data, dict):
            data = urllib.parse.urlencode(data).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req) as res:
            return res.read(), res.headers

    def get_stations_thread(self):
        threading.Thread(target=self.get_stations, daemon=True).start()

    def get_stations(self):
        self.log("放送局情報を取得中...")
        try:
            url = "https://radiko.jp/v3/station/region/full.xml"
            content, _ = self.http_request(url)
            root = ET.fromstring(content)
            
            display_values = []
            self.stations_data = []
            for station in root.findall(".//station"):
                sid = station.find("id").text
                name = station.find("name").text
                area_id = station.find("area_id").text
                timefree = station.find("timefree").text
                if timefree == "1":
                    self.stations_data.append({"id": sid, "name": name, "area_id": area_id})
                    display_values.append(f"{sid} : {name}")
            
            self.root.after(0, lambda: self.combo_station.configure(values=display_values))
            if display_values:
                self.root.after(0, lambda: self.combo_station.current(0))
            self.log(f"{len(display_values)} 局を取得しました。")
        except Exception as e:
            self.log(f"放送局取得エラー: {e}")

    def radiko_login(self, mail, password):
        self.log("ログイン中...")
        try:
            url = "https://radiko.jp/v4/api/member/login"
            data = {"mail": mail, "pass": password}
            content, _ = self.http_request(url, data=data, method='POST')
            import json
            res = json.loads(content)
            if res.get("radiko_session"):
                self.radiko_session = res["radiko_session"]
                return True
        except Exception as e:
            self.log(f"ログインエラー: {e}")
        return False

    def radiko_authorize(self):
        self.log("認証中...")
        try:
            # Auth 1
            headers = {
                'X-Radiko-App': 'pc_html5',
                'X-Radiko-App-Version': '0.0.1',
                'X-Radiko-Device': 'pc',
                'X-Radiko-User': 'dummy_user'
            }
            _, res_headers = self.http_request("https://radiko.jp/v2/api/auth1", headers=headers)
            
            authtoken = res_headers.get('X-Radiko-AuthToken')
            keyoffset = int(res_headers.get('X-Radiko-KeyOffset'))
            keylength = int(res_headers.get('X-Radiko-KeyLength'))
            
            # Partial key
            partial_key = base64.b64encode(AUTHKEY_VALUE[keyoffset:keyoffset+keylength].encode('utf-8')).decode('utf-8')
            
            # Auth 2
            headers = {
                'X-Radiko-Device': 'pc',
                'X-Radiko-User': 'dummy_user',
                'X-Radiko-AuthToken': authtoken,
                'X-Radiko-PartialKey': partial_key
            }
            auth2_url = "https://radiko.jp/v2/api/auth2"
            if self.radiko_session:
                auth2_url += f"?radiko_session={self.radiko_session}"
            
            content, _ = self.http_request(auth2_url, headers=headers)
            self.authtoken = authtoken
            self.area_id = content.decode('utf-8').split(',')[0].strip()
            self.log(f"認証成功 (Area: {self.area_id})")
            return True
        except Exception as e:
            self.log(f"認証エラー: {e}")
        return False

    def get_program_title(self, station_id, from_time):
        try:
            # Radiko's day boundary is 5:00 AM.
            # If from_time is between 00:00:00 and 04:59:59, the program belongs to the previous day's XML.
            dt_base = datetime.datetime.strptime(from_time[:8], "%Y%m%d")
            if int(from_time[8:12]) < 500:
                dt_base -= datetime.timedelta(days=1)
            
            date_str = dt_base.strftime("%Y%m%d")
            ft_full = from_time
            if len(ft_full) == 12: ft_full += "00"
            
            # Find area_id
            area_id = None
            if not self.stations_data:
                self.get_stations() # Ensure stations_data is loaded
                
            for s in self.stations_data:
                if s["id"] == station_id:
                    area_id = s["area_id"]
                    break
            
            if not area_id: return "Unknown_Title"
            
            api_url = f"https://api.radiko.jp/program/v3/date/{date_str}/area/{area_id}.xml"
            content, _ = self.http_request(api_url)
            root = ET.fromstring(content)
            
            # Find station node
            station_node = root.find(f".//station[@id='{station_id}']")
            if station_node is None: return "Unknown_Title"

            # Search for the program that contains ft_full
            # Note: FT might be slightly different if not exact, we look for ft <= time < to
            for prog in station_node.findall(".//prog"):
                p_ft = prog.get("ft")
                p_to = prog.get("to")
                if p_ft <= ft_full < p_to:
                    title = prog.find("title").text
                    title = re.sub(r'[\\/:*?"<>|]', '_', title)
                    return title

        except Exception as e:
            self.log(f"番組名取得エラー: {e}")
        return "Unknown_Title"

    def run_recording_thread(self):
        threading.Thread(target=self.run_recording, daemon=True).start()

    def run_recording(self):
        mail = self.mail_var.get()
        password = self.pass_var.get()
        
        if mail and password:
            if not self.radiko_login(mail, password):
                self.log("プレミアムログインに失敗しました。通常モードで続行します。")
                self.radiko_session = None

        if not self.radiko_authorize():
            self.log("認証に失敗しました。終了します。")
            return

        station_id = ""
        from_time = ""
        to_time = ""

        if self.mode_var.get() == "manual":
            sel = self.station_var.get()
            station_id = sel.split(" : ")[0] if " : " in sel else sel
            from_time = self.start_time_var.get()
            if len(from_time) == 12: from_time += "00"
            
            duration_min = int(self.duration_var.get() or 0)
            dt_start = datetime.datetime.strptime(from_time, "%Y%m%d%H%M%S")
            dt_end = dt_start + datetime.timedelta(minutes=duration_min)
            to_time = dt_end.strftime("%Y%m%d%H%M%S")
        else:
            url = self.url_var.get()
            try:
                if "#!/ts/" in url:
                    parts = url.split("#!/ts/")[1].split("/")
                    station_id = parts[0]
                    from_time = parts[1]
                elif "sid=" in url and "t=" in url:
                    import urllib.parse as up
                    parsed = up.urlparse(url)
                    qs = up.parse_qs(parsed.query)
                    station_id = qs['sid'][0]
                    from_time = qs['t'][0]
                
                if len(from_time) == 12: from_time += "00"
                self.log(f"URL解析: {station_id}, {from_time}")
                dt_start = datetime.datetime.strptime(from_time, "%Y%m%d%H%M%S")
                # Length from API? for now 1 hour default if URL mode
                dt_end = dt_start + datetime.timedelta(hours=1)
                to_time = dt_end.strftime("%Y%m%d%H%M%S")
            except:
                self.log("URL解析エラー")
                return

        # Fetch Title for naming
        self.log("詳細情報を取得中...")
        title = self.get_program_title(station_id, from_time)
        
        # Folder & Filename construction
        station_dir = os.path.join(os.getcwd(), station_id)
        if not os.path.exists(station_dir):
            os.makedirs(station_dir)
            self.log(f"フォルダ作成: {station_id}")
            
        template = self.filename_template_var.get()
        filename = template.replace("{DATE}", from_time[:8])\
                           .replace("{TIME}", from_time[8:12])\
                           .replace("{TITLE}", title)\
                           .replace("{STATION}", station_id)
        
        output_file = os.path.join(station_dir, f"{filename}.m4a")

        # Recording logic
        try:
            # 1. Get Station Area ID
            station_area_id = None
            for s in self.stations_data:
                if s["id"] == station_id:
                    station_area_id = s["area_id"]
                    break
            
            if not station_area_id:
                url = f"https://radiko.jp/v3/station/region/full.xml"
                content, _ = self.http_request(url)
                root = ET.fromstring(content)
                station_node = root.find(f".//station[id='{station_id}']")
                if station_node is not None:
                    station_area_id = station_node.find("area_id").text

            # 2. Get HLS URL
            url = f"https://radiko.jp/v3/station/stream/pc_html5/{station_id}.xml"
            content, _ = self.http_request(url)
            root = ET.fromstring(content)
            
            is_premium = self.radiko_session is not None
            target_areafree = "1" if is_premium and self.area_id != station_area_id else "0"
            
            hls_urls = []
            for url_node in root.findall(".//url"):
                if url_node.get("timefree") == "1" and url_node.get("areafree") == target_areafree:
                    hls_urls.append(url_node.find("playlist_create_url").text)
            
            if not hls_urls:
                fallback = root.find(".//url[@timefree='1']/playlist_create_url")
                if fallback is not None: hls_urls = [fallback.text]

            self.log(f"録音開始: {title} ({station_id})")
            
            # FFmpeg detection
            ffmpeg_path = "ffmpeg"
            # 1. Check local directory (mostly for Windows portable)
            local_bin = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
            if os.path.exists(os.path.join(os.getcwd(), local_bin)):
                ffmpeg_path = os.path.abspath(local_bin)
            else:
                # 2. Check system PATH
                path_bin = shutil.which("ffmpeg")
                if path_bin:
                    ffmpeg_path = path_bin
            
            self.log(f"FFmpeg path: {ffmpeg_path}")

            lsid = secrets.token_hex(16)
            ffmpeg_headers = f"X-Radiko-Authtoken: {self.authtoken}\r\nX-Radiko-AreaId: {self.area_id}"
            
            dt_from = datetime.datetime.strptime(from_time, "%Y%m%d%H%M%S")
            dt_to = datetime.datetime.strptime(to_time, "%Y%m%d%H%M%S")
            total_duration = int((dt_to - dt_from).total_seconds())
            
            
            # Chunk processing
            tmp_dir = tempfile.gettempdir()
            # Windows temp sometimes has issues, but standard lib is safest for cross-platform
            if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)
            tmp_base = f"radiko_tmp_{secrets.token_hex(4)}"
            filelist_path = os.path.join(tmp_dir, f"{tmp_base}_list.txt")
            
            chunk_files = []
            seek_ts = dt_from
            left_sec = total_duration
            chunk_no = 0
            
            success = False
            for hls_url in hls_urls:
                self.log(f"使用URL: {hls_url}")
                chunk_files = []
                seek_ts = dt_from
                left_sec = total_duration
                
                try:
                    while left_sec > 0:
                        l = min(300, left_sec)
                        if l == left_sec and l % 5 != 0:
                            l = ((l // 5) + 1) * 5
                        
                        chunk_seek = seek_ts.strftime("%Y%m%d%H%M%S")
                        chunk_end = (seek_ts + datetime.timedelta(seconds=l)).strftime("%Y%m%d%H%M%S")
                        chunk_file = os.path.join(tmp_dir, f"{tmp_base}_{chunk_no}.m4a")
                        
                        stream_url = (f"{hls_url}?station_id={station_id}&start_at={from_time}&ft={from_time}"
                                      f"&seek={chunk_seek}&end_at={chunk_end}&to={chunk_end}&l={l}&lsid={lsid}&type=c")
                        
                        cmd = [
                            ffmpeg_path,
                            "-headers", ffmpeg_headers,
                            "-http_seekable", "0",
                            "-seekable", "0",
                            "-i", stream_url,
                            "-acodec", "copy",
                            "-vn",
                            "-bsf:a", "aac_adtstoasc",
                            "-y",
                            chunk_file
                        ]
                        
                        
                        self.log(f"ダウンロード中... ({int((total_duration-left_sec)/total_duration*100)}%)")
                        
                        startupinfo = None
                        if platform.system() == "Windows":
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            startupinfo.wShowWindow = subprocess.SW_HIDE
                            
                        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                              text=True, encoding='utf-8', errors='replace',
                                              startupinfo=startupinfo)
                        err_out = ""
                        for line in proc.stdout:
                            if "error" in line.lower() or "400" in line:
                                err_out += line
                        proc.wait()
                        
                        if proc.returncode != 0:
                            self.log(f"エラー発生: {err_out.strip()}")
                            raise Exception("Download failed")
                        
                        chunk_files.append(chunk_file)
                        left_sec -= l
                        seek_ts += datetime.timedelta(seconds=l)
                        chunk_no += 1
                    
                    # Concat
                    with open(filelist_path, "w", encoding="utf-8") as f:
                        for cf in chunk_files:
                            p = cf.replace("\\", "/")
                            f.write(f"file '{p}'\n")
                    
                    self.log("ファイルを結合中...")
                    concat_cmd = [ffmpeg_path, "-f", "concat", "-safe", "0", "-i", filelist_path, "-c", "copy", "-y", output_file]
                    
                    startupinfo = None
                    if platform.system() == "Windows":
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        startupinfo.wShowWindow = subprocess.SW_HIDE

                    subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
                    success = True
                    break
                except Exception as e:
                    self.log(f"リトライ中: {e}")
                    for cf in chunk_files:
                        if os.path.exists(cf): os.remove(cf)
                    continue

            # Cleanup
            if os.path.exists(filelist_path): os.remove(filelist_path)
            for cf in chunk_files:
                if os.path.exists(cf): os.remove(cf)

            if success:
                self.log(f"録音成功: {os.path.basename(output_file)}")
            else:
                self.log("録音に失敗しました。")

        except Exception as e:
            self.log(f"エラー: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RadikoRecorderGUI(root)
    root.mainloop()
