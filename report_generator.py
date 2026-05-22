import os
from fpdf import FPDF
import io

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 114, 178) # Blue
        self.cell(0, 10, 'StatBot Pro - Data Analysis Report', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(messages):
    """
    Generates a PDF report from the chat history and returns it as a bytes buffer.
    """
    pdf = PDFReport()
    pdf.add_page()
    
    # Add content
    for msg in messages:
        role = "User Query" if msg["role"] == "user" else "StatBot Analysis"
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, role, 0, 1, 'L')
        
        pdf.set_font("Arial", '', 11)
        pdf.set_text_color(50, 50, 50)
        
        content = msg["content"]
        if isinstance(content, list):
            text_parts = [part["text"] for part in content if isinstance(part, dict) and "text" in part]
            content = "\\n".join(text_parts) if text_parts else str(content)
        
        # Replace unicode characters if needed or stick to basic ASCII mapping
        content = content.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, content)
        pdf.ln(5)
        
        # Add plots if any
        if "plots" in msg:
            for plot_path in msg["plots"]:
                if os.path.exists(plot_path) and plot_path.endswith(".png"):
                    try:
                        # Max width 180 to fit page
                        pdf.image(plot_path, w=180)
                        pdf.ln(5)
                    except Exception as e:
                        print(f"Failed to add image to PDF: {e}")
                        
    # Return as buffer
    buffer = io.BytesIO()
    # fpdf2 allows outputting to a bytes buffer via pdf.output(dest='S').encode('latin-1')
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin1')
    buffer.write(pdf_bytes)
    return buffer
