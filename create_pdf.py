
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
        }
    ]

    # 4. Build Story
    # Add Title Page
    story.append(Spacer(1, 3*inch))
    story.append(Paragraph("《逆流的星刻鐘塔》", style_title))
    story.append(Paragraph("Chronicles of the Retrograde Tower", style_caption))
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("Chapter 1 & 2 Draft", style_caption))
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
    create_pdf(r"d:\writingPlan\Chronicles_of_the_Retrograde_Tower_Chapters_1-2.pdf")
