
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.units import inch, cm

def create_pdf(output_filename):
    print(f"Generating PDF: {output_filename}")
    doc = SimpleDocTemplate(
        output_filename, 
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    story = []

    # 1. Register Chinese Font
    # Microsoft JhengHei is standard for Traditional Chinese on Windows
    font_path = r"C:\Windows\Fonts\msjh.ttc"
    font_name = 'MicrosoftJhengHei'
    
    # Fallback to SimHei if JhengHei is missing
    if not os.path.exists(font_path):
        font_path = r"C:\Windows\Fonts\simhei.ttf"
        font_name = 'SimHei'
    
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            print(f"Registered font: {font_name}")
        except Exception as e:
            print(f"Error registering font: {e}")
            font_name = 'Helvetica' # Fallback to default
    else:
        print("Warning: No Chinese font found. Text may not render correctly.")
        font_name = 'Helvetica'

    # 2. Define Styles
    styles = getSampleStyleSheet()
    
    # Title Style
    style_title = ParagraphStyle(
        'ChineseTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=24,
        leading=30,
        spaceAfter=20,
        alignment=1 # Center
    )
    
    # Heading Style
    style_h2 = ParagraphStyle(
        'ChineseH2',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=16,
        leading=20,
        spaceBefore=15,
        spaceAfter=10,
        textColor="black"
    )
    
    # Body Style
    style_body = ParagraphStyle(
        'ChineseBody',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=18, # 1.5 spacing approx
        spaceAfter=10,
        firstLineIndent=20 # Indent first line of paragraphs
    )
    
    # Image Caption Style
    style_caption = ParagraphStyle(
        'Caption',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        leading=12,
        alignment=1, # Center
        textColor="grey"
    )

    # 3. Content Definition
    chapters = [
        {
            "title": "Chapter 1",
            "file": r"d:\writingPlan\chapter1_draft.md",
            "image": r"C:\Users\chienhua\.gemini\antigravity\brain\07522294-ab5b-4b9f-a516-eff3bd9cde4c\chapter1_spatial_overlap_meeting_1769674200309.png",
            "caption": "Figure 1: The Spatial Overlap - Kael and Elise make first contact."
        },
        {
            "title": "Chapter 2",
            "file": r"d:\writingPlan\chapter2_draft.md",
            "image": r"C:\Users\chienhua\.gemini\antigravity\brain\07522294-ab5b-4b9f-a516-eff3bd9cde4c\chapter2_combat_rewind_1769674330254.png",
            "caption": "Figure 2: Combat Rewind - A desperate alliance against the Iron Blood Gang."
        },
        {
            "title": "Chapter 3",
            "file": r"d:\writingPlan\chapter3_draft.md",
            "image": r"C:\Users\chienhua\.gemini\antigravity\brain\07522294-ab5b-4b9f-a516-eff3bd9cde4c\chapter3_paradox_handshake_1769745625853.png",
            "caption": "Figure 3: The Paradox Pact - A handshake across a thousand years."
        },
        {
            "title": "Chapter 4",
            "file": r"d:\writingPlan\chapter4_draft.md",
            "image": r"C:\Users\chienhua\.gemini\antigravity\brain\07522294-ab5b-4b9f-a516-eff3bd9cde4c\chapter4_infiltration_1769747160299.png",
            "caption": "Figure 4: The Infiltration - Elise copies the barrier's core design under Leonard's watch."
        },
        {
            "title": "Chapter 5",
            "file": r"d:\writingPlan\chapter5_draft.md",
            "image": r"C:\Users\chienhua\.gemini\antigravity\brain\07522294-ab5b-4b9f-a516-eff3bd9cde4c\chapter5_escape_dawn_1769747534152.png",
            "caption": "Figure 5: Freedom's Dawn - Elise escapes as history is rewritten."
        },
        {
            "title": "Chapter 6",
            "file": r"d:\writingPlan\chapter6_draft.md",
            "image": r"C:\Users\chienhua\.gemini\antigravity\brain\07522294-ab5b-4b9f-a516-eff3bd9cde4c\chapter6_mira_workshop_1769747965937.png",
            "caption": "Figure 6: The Workshop - Mira shares her forbidden research with Lia."
        },
        {
            "title": "Chapter 7",
            "file": r"d:\writingPlan\chapter7_draft.md",
            "image": r"C:\Users\chienhua\.gemini\antigravity\brain\07522294-ab5b-4b9f-a516-eff3bd9cde4c\chapter7_ash_meeting_1769748211667.png",
            "caption": "Figure 7: The Information Broker - Kael meets the mysterious Ash."
        },
        {
            "title": "Chapter 8",
            "file": r"d:\writingPlan\chapter8_draft.md",
            "image": r"C:\Users\chienhua\.gemini\antigravity\brain\07522294-ab5b-4b9f-a516-eff3bd9cde4c\chapter8_two_worlds_1769748438473.png",
            "caption": "Figure 8: Two Worlds - Kael and Elise see each other's timelines for the first time."
        },
        {
            "title": "Chapter 9",
            "file": r"d:\writingPlan\chapter9_draft.md",
            "image": r"C:\Users\chienhua\.gemini\antigravity\brain\07522294-ab5b-4b9f-a516-eff3bd9cde4c\chapter9_abyss_eye_1769748677161.png",
            "caption": "Figure 9: The Eye of the Abyss - Elise sees all possible futures."
        },
        {
            "title": "Chapter 10",
            "file": r"d:\writingPlan\chapter10_draft.md",
            "image": r"C:\Users\chienhua\.gemini\antigravity\brain\07522294-ab5b-4b9f-a516-eff3bd9cde4c\chapter10_hands_across_time_1769749280058.png",
            "caption": "Figure 10: Hands Across Time - Together, they will change fate."
        }
    ]

    # 4. Build Story
    # Add Cover Image
    cover_image = r"C:\Users\chienhua\.gemini\antigravity\brain\07522294-ab5b-4b9f-a516-eff3bd9cde4c\book_cover_1769751143255.png"
    if os.path.exists(cover_image):
        print(f"Adding cover: {cover_image}")
        try:
            img = Image(cover_image, width=6*inch, height=6*inch, kind='proportional')
            story.append(Spacer(1, 0.5*inch))
            story.append(img)
            story.append(PageBreak())
        except Exception as e:
            print(f"Error adding cover: {e}")
    
    # Add Title Page
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("《逆流的星刻鐘塔》", style_title))
    story.append(Paragraph("Chronicles of the Retrograde Tower", style_caption))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("完整版 · 第一卷 & 第二卷", style_caption))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("—— 奇幻時空穿越小說 ——", style_caption))
    story.append(PageBreak())

    for chapter in chapters:
        if os.path.exists(chapter["file"]):
            print(f"Processing {chapter['file']}...")
            
            with open(chapter["file"], "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Markdown Parsing
                if line.startswith("# "):
                    # Chapter Title
                    story.append(Paragraph(line[2:], style_title))
                    story.append(Spacer(1, 0.2*inch))
                elif line.startswith("## "):
                    # Section Header
                    story.append(Paragraph(line[3:], style_h2))
                else:
                    # Body Text
                    # Regex replacement for bold **text** to <b>text</b>
                    # Note: Reportlab uses <b>...</b> tags
                    line_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                    story.append(Paragraph(line_html, style_body))
            
            story.append(Spacer(1, 0.5 * inch))

            # Add Image at the end of the chapter
            if os.path.exists(chapter["image"]):
                print(f"Adding image: {chapter['image']}")
                try:
                    # Calculate aspect ratio to fit within 6x8 inches
                    img_width = 6 * inch
                    # We create an Image object to get original size
                    # But reportlab's Image flowable needs width/height
                    # We'll just set width and let height be proportional?
                    # 'kind=proportional' is default if one dim is not set? No.
                    # Let's just set width and fix height based on assumed aspect ratio or let reportlab handle it.
                    # Simpler:
                    img = Image(chapter["image"], width=6*inch, height=6*inch, kind='proportional') 
                    story.append(img)
                    story.append(Spacer(1, 0.1*inch))
                    story.append(Paragraph(chapter["caption"], style_caption))
                except Exception as e:
                    print(f"Error adding image: {e}")
            else:
                print(f"Image not found: {chapter['image']}")
            
            story.append(PageBreak())
        else:
            print(f"File not found: {chapter['file']}")

    # 5. Output
    try:
        doc.build(story)
        print(f"Successfully created: {output_filename}")
    except Exception as e:
        print(f"Error building PDF: {e}")

if __name__ == "__main__":
    create_pdf(r"d:\writingPlan\Chronicles_of_the_Retrograde_Tower_Complete.pdf")
