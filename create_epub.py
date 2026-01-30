# -*- coding: utf-8 -*-
"""
EPUB 電子書生成腳本
《逆流的星刻鐘塔》Chronicles of the Retrograde Tower
"""

from ebooklib import epub
import os
import re

def parse_markdown_to_html(md_content):
    """將 Markdown 轉換為 HTML"""
    html = md_content
    
    # 處理章節標題 (# 標題)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # 處理小節標題 (## 標題)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    
    # 處理粗體 (**文字**)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # 處理斜體 (*文字*)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # 處理分隔線 (---)
    html = re.sub(r'^---+$', r'<hr/>', html, flags=re.MULTILINE)
    
    # 處理段落
    paragraphs = html.split('\n\n')
    formatted = []
    for p in paragraphs:
        p = p.strip()
        if p:
            if not p.startswith('<h') and not p.startswith('<hr'):
                p = f'<p>{p}</p>'
            formatted.append(p)
    
    html = '\n'.join(formatted)
    
    # 處理段落內換行
    html = html.replace('\n', '<br/>')
    html = html.replace('<br/><br/>', '</p><p>')
    
    return html

def create_epub():
    """創建 EPUB 電子書"""
    
    # 創建 EPUB 書籍
    book = epub.EpubBook()
    
    # 設定元數據
    book.set_identifier('retrograde-tower-2024')
    book.set_title('逆流的星刻鐘塔 Chronicles of the Retrograde Tower')
    book.set_language('zh-TW')
    book.add_author('作者')
    
    # 添加描述
    book.add_metadata('DC', 'description', 
        '一部跨越千年時空的奇幻小說。當末日廢墟中的拾荒者凱爾，' +
        '與黃金時代的貴族少女艾莉西亞建立了神秘的連結，' +
        '兩人必須合作改變歷史，阻止世界的毀滅。')
    
    # CSS 樣式
    style = '''
    @charset "UTF-8";
    
    body {
        font-family: "Noto Serif TC", "Source Han Serif TC", "Songti SC", serif;
        line-height: 1.8;
        margin: 2em;
        text-align: justify;
    }
    
    h1 {
        font-size: 1.8em;
        text-align: center;
        margin: 2em 0 1em 0;
        padding-bottom: 0.5em;
        border-bottom: 2px solid #333;
    }
    
    h2 {
        font-size: 1.3em;
        margin: 1.5em 0 0.8em 0;
        color: #444;
    }
    
    p {
        text-indent: 2em;
        margin: 0.8em 0;
    }
    
    strong {
        font-weight: bold;
    }
    
    em {
        font-style: italic;
    }
    
    hr {
        border: none;
        border-top: 1px solid #ccc;
        margin: 2em 0;
    }
    
    .title-page {
        text-align: center;
        margin-top: 30%;
    }
    
    .title-page h1 {
        font-size: 2.5em;
        border: none;
        margin-bottom: 0.5em;
    }
    
    .title-page .subtitle {
        font-size: 1.2em;
        color: #666;
        margin-bottom: 2em;
    }
    
    .title-page .author {
        font-size: 1em;
        margin-top: 3em;
    }
    
    .volume-title {
        text-align: center;
        margin-top: 40%;
    }
    
    .volume-title h1 {
        font-size: 2em;
        border: none;
    }
    '''
    
    # 添加 CSS
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style
    )
    book.add_item(nav_css)
    
    # 創建封面頁
    cover_content = '''
    <html>
    <head><link rel="stylesheet" href="style/nav.css" type="text/css"/></head>
    <body>
        <div class="title-page">
            <h1>逆流的星刻鐘塔</h1>
            <p class="subtitle">Chronicles of the Retrograde Tower</p>
            <p class="subtitle">完整版 · 第一卷 & 第二卷</p>
            <p class="author">—— 奇幻時空穿越小說 ——</p>
        </div>
    </body>
    </html>
    '''
    
    cover_page = epub.EpubHtml(title='封面', file_name='cover.xhtml', lang='zh-TW')
    cover_page.content = cover_content
    cover_page.add_item(nav_css)
    book.add_item(cover_page)
    
    # 創建卷頁
    volume1_content = '''
    <html>
    <head><link rel="stylesheet" href="style/nav.css" type="text/css"/></head>
    <body>
        <div class="volume-title">
            <h1>第一卷</h1>
            <p>逃離死亡</p>
        </div>
    </body>
    </html>
    '''
    
    volume1_page = epub.EpubHtml(title='第一卷', file_name='volume1.xhtml', lang='zh-TW')
    volume1_page.content = volume1_content
    volume1_page.add_item(nav_css)
    book.add_item(volume1_page)
    
    volume2_content = '''
    <html>
    <head><link rel="stylesheet" href="style/nav.css" type="text/css"/></head>
    <body>
        <div class="volume-title">
            <h1>第二卷</h1>
            <p>枯竭的根源</p>
        </div>
    </body>
    </html>
    '''
    
    volume2_page = epub.EpubHtml(title='第二卷', file_name='volume2.xhtml', lang='zh-TW')
    volume2_page.content = volume2_content
    volume2_page.add_item(nav_css)
    book.add_item(volume2_page)
    
    # 章節列表
    chapters_info = [
        ("第一章：廢鐵與黃金的交響曲", r"d:\writingPlan\chapter1_draft.md"),
        ("第二章：重疊的避難所", r"d:\writingPlan\chapter2_draft.md"),
        ("第三章：悖論計畫", r"d:\writingPlan\chapter3_draft.md"),
        ("第四章：靴帶悖論", r"d:\writingPlan\chapter4_draft.md"),
        ("第五章：逃亡之夜", r"d:\writingPlan\chapter5_draft.md"),
        ("第六章：新生的代價", r"d:\writingPlan\chapter6_draft.md"),
        ("第七章：禁忌的理論", r"d:\writingPlan\chapter7_draft.md"),
        ("第八章：星刻鐘塔", r"d:\writingPlan\chapter8_draft.md"),
        ("第九章：深淵之眼", r"d:\writingPlan\chapter9_draft.md"),
        ("第十章：命運的分歧", r"d:\writingPlan\chapter10_draft.md"),
    ]
    
    # 創建章節
    epub_chapters = []
    
    for i, (title, filepath) in enumerate(chapters_info, 1):
        # 讀取 Markdown
        with open(filepath, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 轉換為 HTML
        html_content = parse_markdown_to_html(md_content)
        
        # 創建章節頁面
        chapter_html = f'''
        <html>
        <head>
            <link rel="stylesheet" href="style/nav.css" type="text/css"/>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        '''
        
        chapter = epub.EpubHtml(
            title=title,
            file_name=f'chapter{i}.xhtml',
            lang='zh-TW'
        )
        chapter.content = chapter_html
        chapter.add_item(nav_css)
        
        book.add_item(chapter)
        epub_chapters.append(chapter)
    
    # 創建後記頁
    afterword_content = '''
    <html>
    <head><link rel="stylesheet" href="style/nav.css" type="text/css"/></head>
    <body>
        <h1>後記</h1>
        <p>感謝您閱讀《逆流的星刻鐘塔》第一卷與第二卷。</p>
        <p>這是一個關於時間、命運與選擇的故事。凱爾與艾莉西亞的旅程才剛剛開始——他們將繼續尋找阻止「大抽取」的方法，創造一個全新的未來。</p>
        <p>第三卷《創造新的未來》，敬請期待。</p>
        <hr/>
        <p style="text-align: center; color: #888;">— 全書完 · 待續 —</p>
    </body>
    </html>
    '''
    
    afterword = epub.EpubHtml(title='後記', file_name='afterword.xhtml', lang='zh-TW')
    afterword.content = afterword_content
    afterword.add_item(nav_css)
    book.add_item(afterword)
    
    # 設定目錄結構
    book.toc = (
        epub.Link('cover.xhtml', '封面', 'cover'),
        (
            epub.Section('第一卷：逃離死亡'),
            tuple(epub_chapters[:5])
        ),
        (
            epub.Section('第二卷：枯竭的根源'),
            tuple(epub_chapters[5:])
        ),
        epub.Link('afterword.xhtml', '後記', 'afterword'),
    )
    
    # 添加導航
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # 設定書脊（閱讀順序）
    book.spine = [
        'nav',
        cover_page,
        volume1_page,
        *epub_chapters[:5],
        volume2_page,
        *epub_chapters[5:],
        afterword
    ]
    
    # 輸出 EPUB
    output_path = r"d:\writingPlan\Chronicles_of_the_Retrograde_Tower.epub"
    epub.write_epub(output_path, book, {})
    
    print(f"EPUB 電子書已生成: {output_path}")
    return output_path

if __name__ == "__main__":
    create_epub()
