import ebooklib
from ebooklib import epub
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from bs4 import BeautifulSoup

def epub_to_pdf(epub_path, pdf_path):
    book = epub.read_epub(epub_path)
    pdf = canvas.Canvas(pdf_path, pagesize=letter)
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text = soup.get_text()
            
            # Split text into pages (this is a simple approach)
            lines = text.split('\n')
            for i in range(0, len(lines), 40):  # 40 lines per page
                pdf.setFont("Helvetica", 12)
                y = 750
                for line in lines[i:i+40]:
                    pdf.drawString(50, y, line)
                    y -= 15
                pdf.showPage()
    
    pdf.save()

# Usage
epub_to_pdf('Canvas of Courage.epub', 'Canvas_of_Courage.pdf')