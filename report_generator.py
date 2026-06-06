import os
import io
from datetime import datetime
from fpdf import FPDF


class PDFReport(FPDF):
    """Premium branded PDF report for StatBot Pro."""

    def __init__(self, session_id: str = ""):
        super().__init__()
        self.session_id = session_id
        self.generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def header(self):
        # Background accent bar
        self.set_fill_color(30, 10, 60)
        self.rect(0, 0, 210, 22, "F")

        self.set_font("Helvetica", "B", 14)
        self.set_text_color(167, 139, 250)  # Purple accent
        self.cell(0, 12, "StatBot Pro", ln=False, align="L")

        self.set_font("Helvetica", "", 9)
        self.set_text_color(180, 180, 200)
        self.cell(0, 12, "Data Analysis Report", ln=True, align="R")

        self.set_draw_color(124, 58, 237)
        self.set_line_width(0.5)
        self.line(10, 22, 200, 22)
        self.ln(6)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(40, 40, 60)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(1)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 140)
        self.cell(0, 8, f"Page {self.page_no()}  |  Generated: {self.generated_at}", align="C")

    def chapter_label(self, role: str):
        """Print a role badge (User / StatBot)."""
        if role == "user":
            self.set_fill_color(30, 10, 60)
            self.set_text_color(167, 139, 250)
            label = "USER QUERY"
        else:
            self.set_fill_color(10, 40, 30)
            self.set_text_color(52, 211, 153)  # Green
            label = "STATBOT ANALYSIS"

        self.set_font("Helvetica", "B", 8)
        self.cell(35, 7, label, fill=True, border=0, ln=False, align="C")
        self.ln(9)

    def write_body(self, text: str):
        """Write body text safely (handles unicode via replacement)."""
        # Replace characters that Latin-1 cannot encode
        safe_text = text.encode("latin-1", errors="replace").decode("latin-1")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(220, 220, 230)
        self.multi_cell(0, 6, safe_text)
        self.ln(3)

    def separator(self):
        self.set_draw_color(30, 30, 50)
        self.set_line_width(0.2)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)


def generate_pdf_report(messages: list, session_id: str = "") -> io.BytesIO:
    """
    Generates a premium PDF report from the chat history.
    Returns a BytesIO buffer ready for st.download_button.
    """
    pdf = PDFReport(session_id=session_id)
    pdf.set_auto_page_break(auto=True, margin=18)

    # ── Cover / Title Page ──────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(10, 5, 25)
    pdf.rect(0, 0, 210, 297, "F")

    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(167, 139, 250)
    pdf.cell(0, 14, "StatBot Pro", ln=True, align="C")

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(200, 200, 220)
    pdf.cell(0, 10, "Autonomous Data Analysis Report", ln=True, align="C")

    pdf.ln(8)
    pdf.set_draw_color(124, 58, 237)
    pdf.set_line_width(1)
    pdf.line(50, pdf.get_y(), 160, pdf.get_y())

    pdf.ln(10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 140)
    pdf.cell(0, 8, f"Generated: {pdf.generated_at}", ln=True, align="C")
    if session_id:
        pdf.cell(0, 8, f"Session: {session_id[:16]}...", ln=True, align="C")

    total_messages = len(messages)
    user_count = sum(1 for m in messages if m.get("role") == "user")
    pdf.ln(4)
    pdf.cell(0, 8, f"Total Exchanges: {user_count} queries | {total_messages - user_count} responses", ln=True, align="C")

    # ── Conversation Pages ───────────────────────────────────────────────────
    pdf.add_page()

    for i, msg in enumerate(messages):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")

        # Normalize content
        if isinstance(content, list):
            text_parts = [
                part.get("text", "") for part in content
                if isinstance(part, dict) and "text" in part
            ]
            content = "\n".join(text_parts) if text_parts else str(content)
        content = str(content).strip()

        pdf.chapter_label(role)
        pdf.write_body(content)

        # Embed PNG plots if they exist
        if "plots" in msg:
            for plot_path in msg["plots"]:
                if os.path.exists(plot_path) and plot_path.lower().endswith(".png"):
                    try:
                        # Check if there's enough space on the page, else add page
                        if pdf.get_y() > 200:
                            pdf.add_page()
                        pdf.image(plot_path, x=15, w=180)
                        pdf.ln(5)
                    except Exception as e:
                        pdf.set_text_color(200, 80, 80)
                        pdf.set_font("Helvetica", "I", 9)
                        pdf.cell(0, 6, f"[Chart could not be embedded: {e}]", ln=True)
                        pdf.ln(2)

        pdf.separator()

    # ── Output to buffer ─────────────────────────────────────────────────────
    buffer = io.BytesIO()
    pdf_bytes = pdf.output(dest="S")
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode("latin-1")
    buffer.write(pdf_bytes)
    buffer.seek(0)
    return buffer
