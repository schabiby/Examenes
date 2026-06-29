# pdf_generator.py
from fpdf import FPDF
import pandas as pd
from data_manager import get_module_names, get_group_summary, get_group_details

class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Group Report", ln=True, align="C")
        self.ln(5)

    def chapter_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, title, ln=True)
        self.ln(2)

    def chapter_body(self, body):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, body)
        self.ln()

    def create_summary_table(self, df, courses):
        if df.empty:
            return
        self.set_font("Helvetica", "B", 10)
        headers = ["Student"] + [f"{c} Total" for c in courses] + ["Grand Total"]
        col_widths = [40] + [30] * len(courses) + [30]
        self.set_fill_color(200, 220, 255)
        self.set_text_color(0)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, header, border=1, align="C", fill=True)
        self.ln()
        self.set_font("Helvetica", "", 9)
        self.set_fill_color(240, 240, 240)
        fill = False
        for _, row in df.iterrows():
            self.cell(col_widths[0], 7, str(row["Student"]), border=1, align="L", fill=fill)
            for course in courses:
                self.cell(col_widths[courses.index(course)+1], 7, f"{row[f'{course} Total']:.2f}", border=1, align="R", fill=fill)
            self.cell(col_widths[-1], 7, f"{row['Grand Total']:.2f}", border=1, align="R", fill=fill)
            self.ln()
            fill = not fill
        self.ln(5)

    def create_detailed_marks(self, student_id, df, courses, module_names):
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 8, f"Student: {student_id}", ln=True)
        self.ln(2)
        self.set_font("Helvetica", "B", 9)
        headers = ["Module"] + courses
        col_widths = [30] + [35] * len(courses)
        self.set_fill_color(200, 220, 255)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, border=1, align="C", fill=True)
        self.ln()
        self.set_font("Helvetica", "", 9)
        self.set_fill_color(240, 240, 240)
        fill = False
        for mod in module_names:
            self.cell(col_widths[0], 6, mod, border=1, align="L", fill=fill)
            for course in courses:
                val = df.loc[mod, course]
                mark_str = f"{val:.2f}" if not pd.isna(val) else ""
                self.cell(col_widths[courses.index(course)+1], 6, mark_str, border=1, align="R", fill=fill)
            self.ln()
            fill = not fill
        self.ln(5)

def generate_pdf_report(groups, group_name):
    """Generate PDF for a specific group."""
    if group_name not in groups:
        return b""
    group = groups[group_name]
    courses = group["courses"]
    module_names = get_module_names(groups, group_name)
    pdf = PDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Group: {group_name}", ln=True, align="C")
    pdf.ln(5)

    # Summary
    pdf.chapter_title("Summary of Totals per Course")
    summary_df = get_group_summary(groups, group_name)
    if not summary_df.empty:
        pdf.create_summary_table(summary_df, courses)
    else:
        pdf.chapter_body("No data available.")

    # Detailed marks per student
    details = get_group_details(groups, group_name)
    for sid, df in details.items():
        pdf.add_page()
        pdf.chapter_title(f"Detailed Marks for {sid}")
        pdf.create_detailed_marks(sid, df, courses, module_names)

    return pdf.output(dest='S').encode('latin-1')