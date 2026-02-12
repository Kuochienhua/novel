import schedule
import time
import feedparser
import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
import logging
from sqlalchemy.orm import Session
from database import SessionLocal, Subscriber

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mailer.log"),
        logging.StreamHandler()
    ]
)

# 載入 .env 檔案
load_dotenv()

def get_subscribers():
    """從資料庫獲取所有活躍訂閱者"""
    db = SessionLocal()
    try:
        subscribers = db.query(Subscriber).filter(Subscriber.is_active == True).all()
        return [sub.email for sub in subscribers]
    finally:
        db.close()

def get_google_news_rss():
    """(同前) 獲取 Google News 台灣財經新聞 RSS"""
    rss_url = "https://news.google.com/rss/search?q=台灣+財經+when:1d&hl=zh-TW&gl=TW&ceid=TW:zh-TW"
    try:
        logging.info(f"正在擷取新聞: {rss_url}")
        feed = feedparser.parse(rss_url)
        if feed.bozo: return []
        return feed.entries[:20]
    except Exception as e:
        logging.error(f"獲取新聞錯誤: {e}")
        return []

def format_email_body(entries, custom_content=None):
    """將新聞或自訂內容轉換為 HTML (整合版)"""
    content_html = ""
    
    # 插入自訂內容 (如果有)
    if custom_content:
        content_html += f"""
        <div style="background: #fff; padding: 20px; border-left: 4px solid #3498db; margin-bottom: 30px;">
            <h3 style="margin-top:0;">🌟 編輯精選 / 特別通知</h3>
            <div style="font-size: 1.1em; color: #444;">{custom_content}</div>
        </div>
        """

    # 插入新聞內容 (如果有)
    if entries:
        content_html += "<h3>📰 今日熱門財經頭條</h3>"
        for entry in entries:
            title = entry.title
            link = entry.link
            pub_date = entry.published if 'published' in entry else ''
            source = entry.source.title if 'source' in entry else 'Google News'
            
            content_html += f"""
            <div style="margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px;">
                <a href="{link}" style="font-size: 1.1em; font-weight: bold; color: #2c3e50; text-decoration: none;" target="_blank">{title}</a>
                <div style="font-size: 0.85em; color: #888; margin-top: 5px;">
                    來源: {source} | 時間: {pub_date}
                </div>
            </div>
            """
    elif not custom_content:
         content_html += "<p>今日暫無法取得新聞資料。</p>"

    # 完整 HTML
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .footer {{ margin-top: 30px; font-size: 0.8em; color: #aaa; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📊 每日財經早報</h2>
                <div style="color: #666; font-size: 0.9em;">日期: {datetime.now().strftime('%Y年%m月%d日')}</div>
            </div>
            
            {content_html}

            <div class="footer">
                <p>本郵件由自動化財經機器人發送</p>
                <p>不想再收到？請回覆告知取消訂閱。</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_newsletter(custom_message=None):
    """發送電子報給所有訂閱者"""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
        logging.error("設定檔錯誤: 缺少 SMTP 相關設定")
        return

    # 1. 獲取內容
    news_entries = get_google_news_rss()
    if not news_entries and not custom_message:
        logging.warning("沒有內容可發送 (無新聞且無自訂訊息)")
        return
    
    email_body = format_email_body(news_entries, custom_message)
    
    # 2. 獲取收件人
    subscribers = get_subscribers()
    if not subscribers:
        logging.warning("沒有訂閱者")
        return

    logging.info(f"準備發送給 {len(subscribers)} 位訂閱者...")

    # 3. 建立連線 (為了效率，建議建立一次連線後迴圈發送，或使用 BCC 密件副本群發)
    # 這裡示範使用 BCC (密件副本) 一次發送，保護隱私且效率高
    # 注意：某些 SMTP Server 有收件人數量限制，若人數多建議分批發送
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['Subject'] = f"每日財經早報 ({datetime.now().strftime('%Y/%m/%d')})"
    msg.attach(MIMEText(email_body, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_password)
        
        # 使用 BCC 群發
        # 'To' 留空或填自己，實際收件人在 sendmail 的列表裡
        msg['To'] = smtp_user 
        
        # 發送
        server.sendmail(smtp_user, subscribers, msg.as_string())
        
        server.quit()
        logging.info("所有郵件發送完成！")
    except Exception as e:
        logging.error(f"發送失敗: {e}")

def job():
    send_newsletter()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--manual":
            # 手動輸入模式
            print("請輸入您想對讀者說的話 (支援 HTML，按 Enter 兩次結束):")
            lines = []
            while True:
                line = input()
                if line:
                    lines.append(line)
                else:
                    break
            message = "<br>".join(lines)
            send_newsletter(custom_message=message)
        elif sys.argv[1] == "--now":
            send_newsletter()
    else:
        # 排程模式
        schedule.every().day.at("07:30").do(job)
        logging.info("郵件排程服務已啟動 (07:30 發送)...")
        while True:
            schedule.run_pending()
            time.sleep(60)
