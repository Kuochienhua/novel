import customtkinter as ctk
import google.generativeai as genai
import os
import threading
import re
import requests
import json
import base64
import io
from google.api_core import exceptions
from tkinter import filedialog
import asyncio
import edge_tts
from PIL import Image as PILImage, ImageDraw, ImageFont

# PDF 與 EPUB 相關匯入
from ebooklib import epub
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.units import cm

# 設定介面主題
class NovelAIGenerator(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("逆流書匠 - AI 小說自動生成器 v1.4")
        self.geometry("1100x900") # 稍微加大視窗以容納更多功能

        # 預設 API Key
        self.default_api_key = 'AIzaSyDKl4QXACRnPISYSiK_1tIjpdFQw7r1vO0'
        # 核心模型 (根據測試結果更新)
        self.text_model_name = 'gemini-2.5-flash'
        self.image_model_name = 'imagen-4.0-fast-generate-001' # 更新為可用版本

        # 設定板塊
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 側邊欄 (Sidebar) - 改為可捲動以容納更多設定 ---
        self.sidebar_frame = ctk.CTkScrollableFrame(self, width=240, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Novel Architect", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.api_label = ctk.CTkLabel(self.sidebar_frame, text="Gemini API Key:")
        self.api_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        self.api_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="輸入 API Key...", show="*")
        self.api_entry.insert(0, self.default_api_key)
        self.api_entry.grid(row=2, column=0, padx=20, pady=(5, 10))

        self.check_quota_btn = ctk.CTkButton(self.sidebar_frame, text="🔍 檢查額度/連線", command=self.check_api_status)
        self.check_quota_btn.grid(row=3, column=0, padx=20, pady=10)

        self.load_btn = ctk.CTkButton(self.sidebar_frame, text="📖 載入舊專案/大綱", fg_color="#3498db", hover_color="#2980b9", command=self.load_project)
        self.load_btn.grid(row=4, column=0, padx=20, pady=10)

        self.gen_outline_btn = ctk.CTkButton(self.sidebar_frame, text="✨ 生成/更新大綱", command=self.generate_outline)
        self.gen_outline_btn.grid(row=5, column=0, padx=20, pady=10)

        self.gen_cover_btn = ctk.CTkButton(self.sidebar_frame, text="🎨 生成封面插圖", fg_color="#9b59b6", hover_color="#8e44ad", command=self.generate_cover)
        self.gen_cover_btn.grid(row=6, column=0, padx=20, pady=10)

        self.gen_audio_btn = ctk.CTkButton(self.sidebar_frame, text="🎧 合併全書語音", fg_color="#e67e22", hover_color="#d35400", command=self.merge_audio)
        self.gen_audio_btn.grid(row=7, column=0, padx=20, pady=10)

        self.save_btn = ctk.CTkButton(self.sidebar_frame, text="📁 開啟目錄", command=self.open_dir)
        self.save_btn.grid(row=8, column=0, padx=20, pady=10)

        self.load_chapter_btn = ctk.CTkButton(self.sidebar_frame, text="📄 載入章節檔修改", fg_color="#16a085", hover_color="#1abc9c", command=self.load_chapter)
        self.load_chapter_btn.grid(row=9, column=0, padx=20, pady=10)

        # 封面預覽小視窗 (在側邊欄下方)
        self.cover_label = ctk.CTkLabel(self.sidebar_frame, text="尚未生成封面", width=180, height=180, fg_color="gray30", corner_radius=10)
        self.cover_label.grid(row=10, column=0, padx=20, pady=10)

        # 側邊欄匯出功能
        self.pdf_btn = ctk.CTkButton(self.sidebar_frame, text="📄 匯出全書 PDF", fg_color="#e74c3c", hover_color="#c0392b", command=self.export_pdf)
        self.pdf_btn.grid(row=11, column=0, padx=20, pady=5)

        self.epub_btn = ctk.CTkButton(self.sidebar_frame, text="📚 匯出全書 EPUB", fg_color="#2980b9", hover_color="#2471a3", command=self.export_epub)
        self.epub_btn.grid(row=12, column=0, padx=20, pady=5)

        # 語音語言選擇
        self.tts_label = ctk.CTkLabel(self.sidebar_frame, text="語音語言:", anchor="w")
        self.tts_label.grid(row=13, column=0, padx=20, pady=(10, 0))
        self.tts_lang_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["中文 (台灣)", "日本語", "English"], command=self.change_tts_lang)
        self.tts_lang_menu.grid(row=14, column=0, padx=20, pady=(5, 10))
        self.current_tts_voice = "zh-TW-HsiaoChenNeural"
        self.current_target_lang = "繁體中文"

        # 讀者年齡層
        self.age_label = ctk.CTkLabel(self.sidebar_frame, text="讀者年齡層:", anchor="w")
        self.age_label.grid(row=15, column=0, padx=20, pady=(10, 0))
        self.age_option = ctk.CTkOptionMenu(self.sidebar_frame, values=[
            "幼童 (3-6歲)", 
            "兒童 (7-12歲)", 
            "青少年 (13-18歲)", 
            "青年 (19-29歲)", 
            "壯年 (30-39歲)", 
            "中堅 (40-49歲)", 
            "熟齡 (50-59歲)", 
            "銀髮族 (60歲+)"
        ])
        self.age_option.set("青年 (19-29歲)")
        self.age_option.grid(row=16, column=0, padx=20, pady=(5, 10))

        # 顯示模式
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="顯示模式:", anchor="w")
        self.appearance_mode_label.grid(row=17, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light"], command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=18, column=0, padx=20, pady=(5, 10))

        # 書籍設定 (章節數與字數)
        self.config_label = ctk.CTkLabel(self.sidebar_frame, text="--- 書籍詳細設定 ---", font=ctk.CTkFont(weight="bold"))
        self.config_label.grid(row=19, column=0, padx=20, pady=(10, 5))
        
        self.total_chapters_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="預計總章節數", width=180)
        self.total_chapters_entry.insert(0, "20") # 預設 20 章
        self.total_chapters_entry.grid(row=20, column=0, padx=20, pady=5)
        
        self.words_per_chapter_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="每章預計字數", width=180)
        self.words_per_chapter_entry.insert(0, "2000") # 預設 2000 字
        self.words_per_chapter_entry.grid(row=21, column=0, padx=20, pady=5)

        # --- 主工作區 ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # 輸入設定
        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self.title_entry = ctk.CTkEntry(self.input_frame, placeholder_text="小說標題 (例如：逆流的星刻鐘塔)", width=350)
        self.title_entry.pack(side="left", padx=(0, 10))

        self.chapter_entry = ctk.CTkEntry(self.input_frame, placeholder_text="章節 (如: 1)", width=80)
        self.chapter_entry.pack(side="left", padx=5)

        self.chapter_name_entry = ctk.CTkEntry(self.input_frame, placeholder_text="章節名稱 (選填)", width=200)
        self.chapter_name_entry.pack(side="left", padx=5)

        self.gen_chapter_btn = ctk.CTkButton(self.input_frame, text="🚀 開始寫作", fg_color="#2ecc71", hover_color="#27ae60", command=self.generate_chapter)
        self.gen_chapter_btn.pack(side="left", padx=5)

        self.update_audio_btn = ctk.CTkButton(self.input_frame, text="💾 儲存並更新音檔", fg_color="#3498db", hover_color="#2980b9", command=self.save_and_update_audio)
        self.update_audio_btn.pack(side="left", padx=10)

        # 輸出預覽區
        self.textbox = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(size=14))
        self.textbox.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

    def log(self, text):
        """執行緒安全的 Log 方法"""
        self.after(0, self._append_text, text)

    def _append_text(self, text):
        self.textbox.insert("end", text + "\n")
        self.textbox.see("end")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def change_tts_lang(self, choice):
        mapping = {
            "中文 (台灣)": ("zh-TW-HsiaoChenNeural", "繁體中文"),
            "日本語": ("ja-JP-NanamiNeural", "日本語 (Japanese)"),
            "English": ("en-US-GuyNeural", "English")
        }
        res = mapping.get(choice, ("zh-TW-HsiaoChenNeural", "繁體中文"))
        self.current_tts_voice = res[0]
        self.current_target_lang = res[1]
        self.log(f"🌐 介面連動：語音已切換為 {choice}，AI 寫作語言已設為 {self.current_target_lang}")

    def get_project_path(self, filename=""):
        """獲取並確保專案目錄存在，返回完整路徑"""
        title = self.title_entry.get().strip() or "未命名小說"
        # 移除標題中的非法字元用作資料夾名稱
        folder_name = re.sub(r'[\\/:*?"<>|]', '_', title)
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        
        if filename:
            return os.path.join(folder_name, filename)
        return folder_name

    def save_project_config(self):
        """保存目前專案的設定 (章節數、字數等)"""
        config = {
            "total_chapters": self.total_chapters_entry.get(),
            "words_per_chapter": self.words_per_chapter_entry.get(),
            "target_lang": self.current_target_lang,
            "age_group": self.age_option.get(),
            "tts_choice": self.tts_lang_menu.get()
        }
        config_path = self.get_project_path("config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    def load_project_config(self):
        """載入專案設定檔案"""
        config_path = self.get_project_path("config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self.total_chapters_entry.delete(0, "end")
            self.total_chapters_entry.insert(0, config.get("total_chapters", "20"))
            self.words_per_chapter_entry.delete(0, "end")
            self.words_per_chapter_entry.insert(0, config.get("words_per_chapter", "2000"))
            
            # 回復語言與年齡層
            if "age_group" in config: self.age_option.set(config["age_group"])
            if "tts_choice" in config: self.change_tts_lang(config["tts_choice"])
            self.log("⚙️ 已恢復專案設定（章節數、字數與偏好）。")

    def open_dir(self):
        project_dir = self.get_project_path()
        os.startfile(os.path.abspath(project_dir))

    def load_project(self):
        """載入舊的小說大綱檔案並自動偵測進度"""
        file_path = filedialog.askopenfilename(
            title="選擇小說大綱檔案",
            filetypes=[("Markdown 檔案", "*.md"), ("所有檔案", "*.*")]
        )
        
        if not file_path:
            return

        try:
            filename = os.path.basename(file_path)
            # 嘗試從檔名提取標題 (假設檔名是 [Title]_outline.md)
            title = filename.replace("_outline.md", "")
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 更新介面
            self.title_entry.delete(0, "end")
            self.title_entry.insert(0, title)
            
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", content)
            
            self.log(f"✅ 已載入專案：《{title}》")
            
            # 加載設定
            self.load_project_config()
            
            # 自動偵測目前寫到第幾章
            self.detect_current_progress()
            
            # 嘗試載入封面 (如果有的話)
            cover_path = self.get_project_path(f"book_cover_{title}.png")
            if os.path.exists(cover_path):
                img = PILImage.open(cover_path)
                self.update_cover_ui(img)
                self.log("🎨 已自動載入封面插圖。")
                
        except Exception as e:
            self.log(f"❌ 載入失敗: {str(e)}")

    def int_to_chinese(self, n):
        """將 1-99 的數字轉為中文數字 (如 15 -> 十五)"""
        units = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
        if n < 10: return units[n]
        if n == 10: return "十"
        if n < 20: return "十" + units[n % 10]
        return units[n // 10] + "十" + units[n % 10]

    def detect_current_progress(self):
        """掃描專案目錄，找出最新的章節檔案"""
        project_dir = self.get_project_path()
        files = os.listdir(project_dir)
        
        max_chapter = 0
        chapter_pattern = re.compile(r"chapter(\d+)_draft\.md")
        
        for f in files:
            match = chapter_pattern.match(f)
            if match:
                num = int(match.group(1))
                if num > max_chapter:
                    max_chapter = num
        
        next_chapter = max_chapter + 1
        self.chapter_entry.delete(0, "end")
        self.chapter_entry.insert(0, str(next_chapter))
        self.log(f"📈 偵測到目前進度：已完成 {max_chapter} 章，準備撰寫第 {next_chapter} 章。")

        # --- 強化：從大綱提取預定標題 (支援中文數字、加粗、多種符號) ---
        outline_content = self.textbox.get("1.0", "end")
        next_zh = self.int_to_chinese(next_chapter)
        
        # 構造多種可能的匹配模式
        # 1. 阿拉伯數字: 第 15 章
        # 2. 中文數字: 第十五章
        # 3. 支援加粗 ** 或 ## 
        patterns = [
            rf"(?:\*\*|#)?\s*第\s*{next_chapter}\s*[章|回][:：]\s*([^*#\n\r]+)",
            rf"(?:\*\*|#)?\s*第\s*{next_zh}\s*[章|回][:：]\s*([^*#\n\r]+)",
            rf"Chapter\s*{next_chapter}\s*[:：]\s*([^*#\n\r]+)"
        ]
        
        found_title = None
        for p in patterns:
            match = re.search(p, outline_content, re.IGNORECASE)
            if match:
                found_title = match.group(1).strip()
                # 去掉尾部的 **
                found_title = re.sub(r"\*\*$", "", found_title).strip()
                break
        
        self.chapter_name_entry.delete(0, "end")
        if found_title:
            self.chapter_name_entry.insert(0, found_title)
            self.log(f"📋 已從大綱提取預定標題：{found_title}")

    def load_chapter(self):
        """載入特定的章節 .md 檔案進行修改"""
        file_path = filedialog.askopenfilename(
            title="選擇章節檔案",
            filetypes=[("Markdown 檔案", "chapter*_draft.md"), ("所有 Markdown", "*.md")]
        )
        if not file_path:
            return

        try:
            filename = os.path.basename(file_path)
            chapter_match = re.search(r"chapter(\d+)", filename)
            
            if chapter_match:
                self.chapter_entry.delete(0, "end")
                self.chapter_entry.insert(0, chapter_match.group(1))
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 修正：更強大的標題提取邏輯 (支援全半角冒號、不同空格、中英文格式)
            # 匹配 # 第 X 章：名稱 或 # Chapter X: Name
            first_line = content.split('\n')[0]
            name_match = re.search(r"[：:]\s*(.+)$", first_line)
            
            if name_match:
                title_val = name_match.group(1).strip()
                self.chapter_name_entry.delete(0, "end")
                self.chapter_name_entry.insert(0, title_val)
            else:
                # 備用：如果沒有冒號，嘗試直接拿第一行去掉 # 符號
                alt_title = first_line.replace("#", "").strip()
                self.chapter_name_entry.delete(0, "end")
                self.chapter_name_entry.insert(0, alt_title)
            
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", content)
            self.log(f"📄 已載入章節檔: {filename}。您可以直接在下方修改內容。")
        except Exception as e:
            self.log(f"❌ 載入章節失敗: {str(e)}")

    def save_and_update_audio(self):
        """儲存目前文字框內容到對應章節，並重新生成音檔"""
        chapter_num = self.chapter_entry.get()
        chapter_name = self.chapter_name_entry.get() or "未命名章節"
        if not chapter_num:
            self.log("❌ 請確認章節編號以便儲存。")
            return
        
        content = self.textbox.get("1.0", "end").strip()
        if not content:
            self.log("❌ 沒有內容可以儲存。")
            return

        def task():
            txt_filename = self.get_project_path(f"chapter{chapter_num}_draft.md")
            audio_filename = self.get_project_path(f"chapter{chapter_num}.mp3")
            
            # 確保內容包含標題
            full_content = content
            if not content.startswith("# "):
                full_content = f"# 第 {chapter_num} 章：{chapter_name}\n\n" + content

            try:
                # 1. 儲存文字
                with open(txt_filename, "w", encoding="utf-8") as f:
                    f.write(full_content)
                self.log(f"💾 文字內容已更新至: {txt_filename}")
                
                # 2. 重新合成語音
                self.log(f"🎙️ 正在重新合成語音 (含標題): {audio_filename}...")
                audio_text = f"第 {chapter_num} 章：{chapter_name}。" + re.sub(r'[#*`\-]', '', content)
                asyncio.run(self.text_to_speech(audio_text, audio_filename))
                self.log(f"✅ 章節 {chapter_num} 語音已更新。")
            except Exception as e:
                self.log(f"❌ 更新失敗: {str(e)}")

        threading.Thread(target=task).start()

    def check_api_status(self, silent=False):
        api_key = self.api_entry.get()
        if not api_key:
            if not silent: self.log("❌ 錯誤：請輸入 API Key")
            return False
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.text_model_name)
            model.generate_content("Hi", generation_config={"max_output_tokens": 10}) 
            if not silent: self.log(f"✅ API 測試成功：連線正常 ({self.text_model_name})。")
            return True
        except exceptions.ResourceExhausted:
            self.log("⚠️ 警告：API 額度已用盡。")
            return False
        except Exception as e:
            self.log(f"❓ API 測試失敗: {str(e)}")
            return False

    def generate_outline(self):
        title = self.title_entry.get() or "未命名小說"
        age_group = self.age_option.get()
        total_ch = self.total_chapters_entry.get()
        words_ch = self.words_per_chapter_entry.get()
        
        self.log(f"📖 正在為「{age_group}」構思《{title}》大綱...")
        self.log(f"📋 設定：預計總共 {total_ch} 章，每章約 {words_ch} 字。")
        
        def task():
            prompt = (
                f"請為《{title}》創作一份完整的小說大綱。\n"
                f"目標讀者為「{age_group}」，請調整語言風格。\n"
                f"書籍規劃：總共預計撰寫 {total_ch} 章，每章字數目標為 {words_ch} 字。\n"
                f"大綱要求：請列出每一章的預定標題 (格式如：第 1 章：[標題]) 與劇情要點。\n"
                f"同時提供一個插畫建議（用於生成封面）。請使用{self.current_target_lang}撰寫。"
            )
            result = self.get_ai_response(prompt)
            if result:
                self.textbox.delete("1.0", "end")
                self.textbox.insert("1.0", result)
                
                # 自動建立專案目錄並存檔
                filename = self.get_project_path(f"{title}_outline.md")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(result)
                
                # 保存設定
                self.save_project_config()
                self.log(f"💾 大綱已存檔。正在自動切換至第一章進度...")
                
                # 更新 UI 跳轉到第一章
                self.detect_current_progress()
        
        threading.Thread(target=task).start()

    def generate_cover(self):
        title = self.title_entry.get() or "未命名小說"
        outline = self.textbox.get("1.0", "end").strip()
        
        if not outline:
            self.log("❌ 請先生成大綱，以便 AI 根據內容設計封面。")
            return
            
        self.log(f"🎨 正在為《{title}》生成封面插圖...")
        
        def task():
            # 1. 產生繪圖提示詞 (使用 Gemini)
            prompt_gen = f"根據以下小說大綱，為其生成一段專業的封面插畫描述（英文，約 100 字，用於 AI 繪圖）。風格需為高品質奇幻風格。大綱內容：\n{outline[:500]}"
            image_prompt = self.get_ai_response(prompt_gen)
            
            if not image_prompt:
                return

            self.log(f"🖼️ 繪圖指令已生成。正在繪製 (使用 Imagen 4.0)...")
            
            try:
                # 2. 直接使用 REST API 呼叫 Imagen 4.0 (解決 SDK 404 問題)
                api_key = self.api_entry.get()
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.image_model_name}:predict?key={api_key}"
                
                payload = {
                    "instances": [
                        {"prompt": image_prompt}
                    ],
                    "parameters": {
                        "sampleCount": 1
                    }
                }
                
                response = requests.post(url, json=payload, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    if "predictions" in data and len(data["predictions"]) > 0:
                        # 取得 Base64 數據
                        img_b64 = data["predictions"][0]["bytesBase64Encoded"]
                        img_data = base64.b64decode(img_b64)
                        img = PILImage.open(io.BytesIO(img_data))
                        
                        # --- 新增：疊加中文字標題 ---
                        try:
                            # 建立可編輯副本
                            draw = ImageDraw.Draw(img)
                            # 尋找繁體中文字型 (Windows 常見路徑)
                            font_path = r"C:\Windows\Fonts\msjh.ttc" # 微軟正黑體
                            if not os.path.exists(font_path):
                                font_path = r"C:\Windows\Fonts\simhei.ttf" # 備用黑體
                            
                            if os.path.exists(font_path):
                                # 計算字體大小 (約圖片寬度的 1/8)
                                font_size = int(img.width / 10)
                                font = ImageFont.truetype(font_path, font_size)
                                
                                # 文字陰影/外框效果 (簡單疊加)
                                text_x = img.width // 2
                                text_y = img.height // 4 # 放在上方 1/4 處
                                
                                # 繪製文字 (置中)
                                draw.text((text_x, text_y), title, font=font, fill="white", anchor="mm", stroke_width=2, stroke_fill="black")
                                self.log("✍️ 已成功在封面上疊加書名。")
                        except Exception as font_e:
                            self.log(f"⚠️ 文字疊加失敗 (字型問題): {str(font_e)}")

                        # 儲存
                        save_path = self.get_project_path(f"book_cover_{title}.png")
                        img.save(save_path)
                        
                        # 更新 UI
                        self.update_cover_ui(img)
                        self.log(f"✅ 封面生成成功！已存至: {save_path}")
                    else:
                        self.log(f"❌ 繪圖失敗：回應數據中無圖像資料。")
                else:
                    self.log(f"❌ 繪圖失敗 (HTTP {response.status_code}): {response.text}")
                    
            except Exception as e:
                self.log(f"❌ 繪圖出錯: {str(e)}")

        threading.Thread(target=task).start()

    def update_cover_ui(self, pil_img):
        # 縮放圖片以適應標籤
        ratio = min(180 / pil_img.width, 180 / pil_img.height)
        new_size = (int(pil_img.width * ratio), int(pil_img.height * ratio))
        img_resized = pil_img.resize(new_size, PILImage.LANCZOS)
        
        # 轉換為 CTkImage
        ctk_img = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=new_size)
        
        # 更新標籤
        self.cover_label.configure(image=ctk_img, text="")
        self.cover_label.image = ctk_img

    def get_ai_response(self, prompt):
        if not self.check_api_status(silent=True):
            return None
        try:
            api_key = self.api_entry.get()
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.text_model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            self.log(f"❌ AI 故障: {str(e)}")
            return None

    def generate_chapter(self):
        title = self.title_entry.get() or "未命名小說"
        chapter_num = self.chapter_entry.get()
        chapter_name = self.chapter_name_entry.get() or "未命名章節"
        
        if not chapter_num:
            self.log("❌ 請輸入章節。")
            return

        self.log(f"✍️ 正在寫作《{title}》第 {chapter_num} 章：{chapter_name}...")
        
        def task():
            age_group = self.age_option.get()
            words_goal = self.words_per_chapter_entry.get()
            # 強化 Prompt，要求 AI 直接輸出內容，並使用當前選定的語言
            prompt = (
                f"你是一位頂尖的奇幻小說家。請直接開始寫作《{title}》的第 {chapter_num} 章，章節名稱為「{chapter_name}」。\n"
                f"目標讀者年齡層：{age_group}。\n"
                f"寫作規範：\n"
                f"- 請針對 {age_group} 調整遣詞用字、文法複雜度與敘事語氣。\n"
                f"- 本章目標字數約為 {words_goal} 字。\n"
                f"- 語言必須使用「{self.current_target_lang}」。\n"
                "- 禁止輸出任何開場白、廢話、或確認訊息。直接從第一行開始顯示小說正文。\n"
                "- 使用 Markdown 格式。"
            )
            result = self.get_ai_response(prompt)
            if result:
                self.textbox.delete("1.0", "end")
                self.log(result)
                
                # 儲存文字 (加上標題)
                txt_filename = self.get_project_path(f"chapter{chapter_num}_draft.md")
                full_content = f"# 第 {chapter_num} 章：{chapter_name}\n\n" + result
                with open(txt_filename, "w", encoding="utf-8") as f:
                    f.write(full_content)
                
                # 移除 Markdown 標籤以利語音讀取 (加上章節標題讀報)
                audio_text = f"第 {chapter_num} 章：{chapter_name}。" + re.sub(r'[#*`\-]', '', result)
                audio_filename = self.get_project_path(f"chapter{chapter_num}.mp3")
                
                self.log(f"🎙️ 正在轉換語音 (含標題): {audio_filename}...")
                try:
                    asyncio.run(self.text_to_speech(audio_text, audio_filename))
                    self.log(f"✅ 第 {chapter_num} 章文字與語音已存檔。")
                except Exception as e:
                    self.log(f"⚠️ 語音生成失敗: {str(e)}")

        threading.Thread(target=task).start()

    async def text_to_speech(self, text, output_file):
        """呼叫 edge-tts 產生語音檔案 (支援多語言)"""
        communicate = edge_tts.Communicate(text, self.current_tts_voice)
        await communicate.save(output_file)

    def get_all_chapters(self):
        """獲取並按順序排列所有章節 md 檔案 (從專案目錄)"""
        project_dir = self.get_project_path()
        files = [f for f in os.listdir(project_dir) if f.startswith("chapter") and f.endswith("_draft.md")]
        files.sort(key=lambda x: int(re.search(r'(\d+)', x).group(1)))
        return [os.path.join(project_dir, f) for f in files]

    def export_pdf(self):
        """匯出全書 PDF 功能"""
        title = self.title_entry.get() or "未命名小說"
        files = self.get_all_chapters()
        if not files:
            self.log("❌ 找不到章節檔案，無法匯出。")
            return

        self.log(f"🚀 開始生成 PDF: {title}.pdf...")
        
        def task():
            try:
                output_filename = self.get_project_path(f"{title}.pdf")
                doc = SimpleDocTemplate(output_filename, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
                story = []
                
                # 註冊字體
                font_path = r"C:\Windows\Fonts\msjh.ttc"
                font_name = 'MicrosoftJhengHei'
                if not os.path.exists(font_path):
                    font_path = r"C:\Windows\Fonts\simhei.ttf"; font_name = 'SimHei'
                
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                else:
                    font_name = 'Helvetica'

                styles = getSampleStyleSheet()
                style_title = ParagraphStyle('CTitle', parent=styles['Heading1'], fontName=font_name, fontSize=24, alignment=1, spaceAfter=20)
                style_body = ParagraphStyle('CBody', parent=styles['Normal'], fontName=font_name, fontSize=11, leading=18, firstLineIndent=20)

                # 添加封面圖 (如果有)
                cover_image = self.get_project_path(f"book_cover_{title}.png")
                if os.path.exists(cover_image):
                    img = RLImage(cover_image, width=15*cm, height=15*cm, kind='proportional')
                    story.append(Spacer(1, 2*cm))
                    story.append(img)
                    story.append(PageBreak())

                # 添加標題頁
                story.append(Spacer(1, 5*cm))
                story.append(Paragraph(f"《{title}》", style_title))
                story.append(PageBreak())

                # 處理各章節
                for f in files:
                    with open(f, "r", encoding="utf-8") as r:
                        lines = r.readlines()
                    for line in lines:
                        line = line.strip()
                        if not line: continue
                        if line.startswith("# "):
                            story.append(Paragraph(line[2:], style_title))
                        else:
                            # 處理 Markdown 加粗
                            line_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                            story.append(Paragraph(line_html, style_body))
                    story.append(PageBreak())

                doc.build(story)
                self.log(f"✅ PDF 成功匯出：{output_filename}")
            except Exception as e:
                self.log(f"❌ PDF 匯出失敗: {str(e)}")

        threading.Thread(target=task).start()

    def export_epub(self):
        """匯出全書 EPUB 功能"""
        title = self.title_entry.get() or "未命名小說"
        files = self.get_all_chapters()
        if not files:
            self.log("❌ 找不到章節檔案，無法匯出。")
            return

        self.log(f"🚀 開始生成 EPUB: {title}.epub...")

        def task():
            try:
                book = epub.EpubBook()
                book.set_title(title)
                book.set_language('zh-TW')
                
                # 添加封面圖
                cover_image = self.get_project_path(f"book_cover_{title}.png")
                if os.path.exists(cover_image):
                    with open(cover_image, 'rb') as f:
                        book.set_cover("cover.png", f.read())

                chapters = []
                for i, f in enumerate(files, 1):
                    with open(f, "r", encoding="utf-8") as r:
                        content = r.read()
                    # 簡單轉 HTML
                    html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
                    html_content = html_content.replace('\n', '<p>').replace('</p>', '') # 極簡處理
                    
                    c = epub.EpubHtml(title=f"第 {i} 章", file_name=f'chap_{i}.xhtml', lang='zh-TW')
                    c.content = f'<html><body>{html_content}</body></html>'
                    book.add_item(c)
                    chapters.append(c)

                book.toc = tuple(chapters)
                book.spine = ['nav'] + chapters
                book.add_item(epub.EpubNcx())
                book.add_item(epub.EpubNav())

                output_path = self.get_project_path(f"{title}.epub")
                epub.write_epub(output_path, book, {})
                self.log(f"✅ EPUB 成功匯出：{output_path}")
            except Exception as e:
                self.log(f"❌ EPUB 匯出失敗: {str(e)}")

        threading.Thread(target=task).start()

    def merge_audio(self):
        """合併所有章節的文字並產出一個完整的大音檔 (或是合併 MP3)"""
        title = self.title_entry.get() or "未命名小說"
        self.log(f"🧶 正在整理全書內容以產生完整語音檔...")
        
        def task():
            files = [f for f in os.listdir() if f.startswith("chapter") and f.endswith("_draft.md")]
            # 按章節順序排序
            files.sort(key=lambda x: int(re.search(r'(\d+)', x).group(1)))
            
            full_text = ""
            for f in files:
                with open(f, "r", encoding="utf-8") as reader:
                    content = reader.read()
                    clean = re.sub(r'[#*`\-]', '', content)
                    full_text += f"\n接下來是 {f.replace('_draft.md', '')}\n" + clean
            
            if not full_text:
                self.log("❌ 找不到任何章節檔案。")
                return

            output_file = self.get_project_path(f"{title}_full_audio.mp3")
            self.log(f"🎙️ 正在產生全書語音 (這可能需要幾分鐘): {output_file}...")
            
            try:
                # 由於檔案可能很大，切成小段落處理或直接處理 (edge-tts 支援長文本)
                asyncio.run(self.text_to_speech(full_text, output_file))
                self.log(f"🎊 全書語音合成成功：{output_file}")
            except Exception as e:
                self.log(f"❌ 全書語音合成失敗: {str(e)}")

        threading.Thread(target=task).start()

if __name__ == "__main__":
    app = NovelAIGenerator()
    app.mainloop()
