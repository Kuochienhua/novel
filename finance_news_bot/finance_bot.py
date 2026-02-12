import schedule
import time
import feedparser
import smtplib
import os
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# 載入 .env 檔案
load_dotenv()

def get_google_news_rss():
    """
    獲取 Google News 台灣財經新聞 RSS
    使用搜尋關鍵字 '台灣 財經' 並限定時間為過去 24 小時
    """
    # Google News RSS URL (搜尋: 台灣 財經, 限定過去 1 天)
    rss_url = "https://news.google.com/rss/search?q=台灣+財經+when:1d&hl=zh-TW&gl=TW&ceid=TW:zh-TW"
    
    try:
        logging.info(f"正在擷取新聞: {rss_url}")
        feed = feedparser.parse(rss_url)
        
        if feed.bozo:
            logging.error(f"RSS 解析錯誤: {feed.bozo_exception}")
            return []
            
        logging.info(f"成功取得 {len(feed.entries)} 則新聞")
        return feed.entries[:20] # 取前 20 則
    except Exception as e:
        logging.error(f"獲取新聞時發生錯誤: {e}")
        return []

def format_email_body(entries):
    """
    將新聞轉換為 HTML 格式
    """
    html = """
    <html>
    <head>
        <style>
            body { font-family: sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            .date { color: #666; font-size: 0.9em; }
            .news-item { margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px; }
            .news-title { font-size: 1.1em; font-weight: bold; color: #2c3e50; text-decoration: none; }
            .news-meta { font-size: 0.85em; color: #888; margin-top: 5px; }
            .footer { margin-top: 30px; font-size: 0.8em; color: #aaa; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📊 每日台灣財經新聞快報</h2>
                <div class="date">日期: {}</div>
            </div>
    """.format(datetime.now().strftime('%Y年%m月%d日 %H:%M'))

    if not entries:
        html += "<p>今日暫無法取得新聞資料，請檢查網路連線或來源。</p>"
    else:
        for entry in entries:
            # 清理標題 (Google News 有時會包含來源名稱在標題後，如 " - 媒體名稱")
            title = entry.title
            link = entry.link
            pub_date = entry.published if 'published' in entry else ''
            source = entry.source.title if 'source' in entry else 'Google News'
            
            html += f"""
            <div class="news-item">
                <a href="{link}" class="news-title" target="_blank">{title}</a>
                <div class="news-meta">
                    來源: {source} | 時間: {pub_date}
                </div>
            </div>
            """

    html += """
            <div class="footer">
                本郵件由自動化財經機器人發送
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_email():
    """
    發送電子郵件
    """
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("RECIPIENT_EMAIL")

    if not all([smtp_server, smtp_port, smtp_user, smtp_password, recipient]):
        logging.error("缺少必要的環境變數，請檢查 .env 設定")
        return

    logging.info("開始準備發送郵件...")
    news_entries = get_google_news_rss()
    
    if not news_entries:
        logging.warning("沒有新聞可發送")
        return

    email_body = format_email_body(news_entries)
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = recipient
    msg['Subject'] = f"每日財經早報 ({datetime.now().strftime('%Y/%m/%d')})"
    msg.attach(MIMEText(email_body, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_user, recipient, text)
        server.quit()
        logging.info(f"郵件已成功發送至 {recipient}")
    except Exception as e:
        logging.error(f"發送郵件時發生錯誤: {e}")

def job():
    """
    排程任務
    """
    logging.info("執行排程任務: 搜集新聞並發信")
    send_email()

def run_scheduler():
    """
    主程式迴圈
    """
    # 設定每天早上 07:30 執行
    # 您可以根據需求修改這裡的時間
    schedule_time = "07:30"
    schedule.every().day.at(schedule_time).do(job)
    
    logging.info(f"程式已啟動。預計每天 {schedule_time} 發送新聞。")
    logging.info("按 Ctrl+C 可停止程式。")

    # 為了測試，啟動時先檢查是否要立即跑一次 (可選)
    # job() 
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        logging.info("收到立即執行指令...")
        job()
    else:
        run_scheduler()
