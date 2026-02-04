from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

class InvoicePDF:
    def __init__(self, invoice_data, settings_data):
        self.invoice_data = invoice_data
        # Ensure all settings values are strings (handle None from DB)
        self.settings = {k: (v if v is not None else "") for k, v in settings_data.items()}
        
        # Register standard font for unicode support (Windows)
        # Try finding Arial, fallback to Helvetica if not found (though less likely to support special chars)
        self.font_name = 'Helvetica'
        self.bold_font_name = 'Helvetica-Bold'
        
        try:
            # Common Windows Font Path
            font_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
            arial_path = os.path.join(font_dir, 'arial.ttf')
            arial_bd_path = os.path.join(font_dir, 'arialbd.ttf')
            
            if os.path.exists(arial_path):
                pdfmetrics.registerFont(TTFont('Arial', arial_path))
                self.font_name = 'Arial'
                
            if os.path.exists(arial_bd_path):
                pdfmetrics.registerFont(TTFont('Arial-Bold', arial_bd_path))
                self.bold_font_name = 'Arial-Bold'
            elif self.font_name == 'Arial':
                self.bold_font_name = 'Arial' # Fallback if bold missing
                
        except Exception as e:
            print(f"Warning: Could not load system font: {e}")

    def generate(self, filename):
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []
        styles = getSampleStyleSheet()
        
        # Define Custom Styles
        normal_style = ParagraphStyle('Normal_Custom', parent=styles['Normal'], fontName=self.font_name, fontSize=10, leading=14)
        white_bold_style = ParagraphStyle('Bold_Custom', parent=styles['Normal'], fontName=self.bold_font_name, fontSize=10, leading=14, textColor=colors.white)
        bold_style = ParagraphStyle('Bold_Custom', parent=styles['Normal'], fontName=self.bold_font_name, fontSize=10, leading=14)
        title_style = ParagraphStyle('Title_Custom', parent=styles['Heading1'], fontName=self.bold_font_name, fontSize=24, spaceAfter=20, alignment=2) # Right align
        
        # ------------------------------------------------------------------
        # Header Section: Sender Info (Left) | INVOICE Title (Right)
        # ------------------------------------------------------------------
        sender_info = [
            Paragraph(self.settings.get("sender_name", ""), bold_style),
            Paragraph(self.settings.get("sender_address_line1", ""), normal_style),
            Paragraph(self.settings.get("sender_address_line2", ""), normal_style),
            Paragraph(self.settings.get("sender_address_line3", ""), normal_style),
            Paragraph(f"Email: {self.settings.get('sender_email', '')}", normal_style),
            Paragraph(f"Phone Number: {self.settings.get('sender_phone', '')}", normal_style),
        ]
        
        invoice_title = [
            Paragraph("INVOICE", title_style),
            Paragraph(f"#{self.invoice_data['invoice_number']}", ParagraphStyle('InvNum', parent=normal_style, alignment=2, fontSize=12, textColor=colors.gray))
        ]
        
        header_data = [[sender_info, invoice_title]]
        header_table = Table(header_data, colWidths=[3.5*inch, 2.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.5*inch))
        
        # ------------------------------------------------------------------
        # Bill To & Details Section
        # ------------------------------------------------------------------
        # Bill To (Left)
        client_address = self.invoice_data['client']['address'] or ""
        client_address_lines = client_address.split('\n')
        bill_to_content = [
            Paragraph("Bill To:", ParagraphStyle('BillToLabel', parent=normal_style, textColor=colors.gray)),
            Paragraph(self.invoice_data['client']['name'], bold_style)
        ]
        for line in client_address_lines:
            bill_to_content.append(Paragraph(line, normal_style))
            
        # Invoice Details (Right) - Structure: [Label, Value]
        # We need a table style that right aligns the values and highlights the Balance Due
        
        # Helper to simplify label styling
        def detail_label(text):
            return Paragraph(text, ParagraphStyle('DetailLabel', parent=normal_style, alignment=2, textColor=colors.gray))
        def detail_value(text, style=None):
            return Paragraph(text, style if style else ParagraphStyle('DetailValue', parent=normal_style, alignment=2))

        details_data = [
            [detail_label("Invoice Date:"), detail_value(str(self.invoice_data['date_issued']))],
            [detail_label("Due Date:"), detail_value(str(self.invoice_data['due_date']))],
            [detail_label("Tax Identification Number:"), detail_value(self.settings.get('tax_id', ''))],
            [Paragraph("Balance Due:", ParagraphStyle('BalLabel', parent=bold_style, alignment=2)), 
             Paragraph(f"US${self.invoice_data['total_amount']:.2f}", ParagraphStyle('BalValue', parent=bold_style, alignment=2))]
        ]
        
        # Columns need to be wide enough. 
        # Left col (labels) ~ 1.5 inch, Right col (values) ~ 1.2 inch
        details_table = Table(details_data, colWidths=[2*inch, 1.2*inch])
        details_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'), # Align values right (though Paragraph handles text align, Table align helps placement)
            ('BACKGROUND', (0,3), (-1,3), colors.whitesmoke), # Balance Due Row Background (Light Gray)
            ('PADDING', (0,3), (-1,3), 6), # Extra padding for Balance Due
            ('BOTTOMPADDING', (0,0), (-1,-2), 2),
            ('TOPPADDING', (0,0), (-1,-2), 2),
        ]))
        
        mid_section_data = [[bill_to_content, details_table]]
        mid_table = Table(mid_section_data, colWidths=[3.0*inch, 3.2*inch])
        mid_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(mid_table)
        story.append(Spacer(1, 0.5*inch))
        
        # ------------------------------------------------------------------
        # Line Items Table
        # ------------------------------------------------------------------
        items_header = [
            Paragraph("Item", white_bold_style),
            Paragraph("Quantity", white_bold_style),
            Paragraph("Rate", white_bold_style),
            Paragraph("Amount", white_bold_style)
        ]
        
        items_data = [items_header]
        
        for item in self.invoice_data['line_items']:
            description = item[2] or ""
            quantity = str(item[3])
            rate = f"US${item[4]:.2f}"
            amount = f"US${item[5]:.2f}"
            
            # Use Paragraph for description to allow wrapping
            items_data.append([
                Paragraph(description, normal_style),
                Paragraph(quantity, normal_style),
                Paragraph(rate, normal_style),
                Paragraph(amount, normal_style)
            ])
            
        items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.Color(0.2, 0.2, 0.2)), # Dark Grey Background
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,-1), self.font_name),
            # ('GRID', (0,0), (-1,-1), 0.5, colors.grey), # Remove grid for cleaner look if needed, or keep? Sample shows no vertical lines usually.
            # Sample screenshot shows dark header strip.
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 10),
            ('LINEBELOW', (0,0), (-1,0), 0, colors.black),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.2*inch))
        
        # ------------------------------------------------------------------
        # Totals Section
        # ------------------------------------------------------------------
        vat_exempt = self.invoice_data.get('vat_exempt', False)
        
        if vat_exempt:
            vat_percent = 0.0
            subtotal = self.invoice_data['total_amount'] # No VAT included
            vat_amount = 0.0
        else:
            vat_percent = float(self.settings.get('vat_percentage', 11))
            # Logic: Subtotal = Total / (1 + VAT/100)
            subtotal = self.invoice_data['total_amount'] / (1 + vat_percent/100)
            vat_amount = self.invoice_data['total_amount'] - subtotal
        
        totals_data = [
            [Paragraph("Subtotal:", bold_style), Paragraph(f"US${subtotal:.2f}", normal_style)],
            [Paragraph(f"VAT ({vat_percent}%):", bold_style), Paragraph(f"US${vat_amount:.2f}", normal_style)],
            [Paragraph("Total:", bold_style), Paragraph(f"US${self.invoice_data['total_amount']:.2f}", bold_style)]
        ]

        if vat_exempt:
             totals_data.append([
                 Paragraph("VAT Exemption:", ParagraphStyle('VatExemptLabel', parent=bold_style, fontSize=8, textColor=colors.gray)),
                 Paragraph("under current Lebanese law,\nno VAT for export services", ParagraphStyle('VatExemptVal', parent=normal_style, fontSize=8, textColor=colors.gray))
             ])
        
        # Align to the right side of the page
        totals_table = Table(totals_data, colWidths=[1.5*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([   
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        
        # Create a container table to push totals to the right
        container_data = [[None, totals_table]]
        container_table = Table(container_data, colWidths=[3*inch, 3*inch])
        story.append(container_table)
        story.append(Spacer(1, 0.5*inch))
        
        # ------------------------------------------------------------------
        # Payment Instructions
        # ------------------------------------------------------------------
        story.append(Paragraph("Payment Instructions:", bold_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph("Please remit payment via international wire transfer to the following account:", normal_style))
        story.append(Spacer(1, 10))
        
        payment_info = [
            f"Account Holder Name: {self.settings.get('bank_account_holder', '')}",
            f"IBAN: {self.settings.get('bank_iban', '')}",
            f"Currency Code: USD",
            f"Account Number / Branch: {self.settings.get('bank_branch', '')}", # Keep if exists, or remove if user wanted just the header changed? User said 'remove Bank Branch from settings, add Account Holder'. 
                                                                               # Wait, user said 'remove the Account Number / Branch from the settings'.
                                                                               # And 'make the account hlder name be set also'.
            f"Swift code: {self.settings.get('bank_swift', '')}"
        ]
        
        # NOTE: I kept bank_branch key in DB but in UI it was replaced? 
        # In previous step I renamed the input field to 'bank_account_holder' but I might have left 'bank_branch' key in dictionary?
        # Let's check app.py. User said: "Remove Bank Branch, add Account Holder Name".
        # In app.py I mapped 'bank_account_holder' from form to 'bank_account_holder' key in DB.
        # But I removed 'bank_branch' from the form.
        # So 'bank_branch' in settings might be empty or old value. 
        # I should NOT display Account Number / Branch if user asked to remove it.
        # User said: "remove the Account Number / Branch from the settings"
        
        # Use the specific bank account holder name, defaulting to sender name if not set
        holder = self.settings.get('bank_account_holder') or self.settings.get('sender_name', '')

        payment_info_clean = [
            f"Account Holder Name: {holder}",
            f"IBAN: {self.settings.get('bank_iban', '')}",
            f"Currency Code: USD",
            f"Swift code: {self.settings.get('bank_swift', '')}"
        ]
        # User said "Make the account hlder name be set also for the payment instructions other than my name directly"
        # So I should show THAT one.
        # Let's use the explicit list below.

        for line in payment_info_clean:
             story.append(Paragraph(line, normal_style))
             
        story.append(Spacer(1, 10))
        story.append(Paragraph("Please note that all transfer fees should be covered by the sender.", ParagraphStyle('Italic', parent=normal_style, fontName=self.font_name, fontName_italic=self.font_name, face='Italic'))) 
        # Note: True italic for Arial requires ariali.ttf. If not registered, it might not slant.
        # For now, just keep normal or try oblique if ReportLab simulates it.
        
        doc.build(story)
