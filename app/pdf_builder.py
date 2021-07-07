from app import app
from app.cme_models import CmeCourse

import io
from flask import url_for, redirect, send_file, jsonify, render_template
from flask_login import login_required, current_user

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import inch, letter, A4, landscape
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Table, BaseDocTemplate, PageTemplate,\
    Frame, Spacer, NextPageTemplate, ListFlowable, ListItem, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, TA_CENTER, TA_LEFT
from reportlab.lib.enums import TA_RIGHT


@app.route('/create_cme_certificate_pdf/<token>', methods=['GET', 'POST'])
@login_required
def create_cme_certificate_pdf(token):
    course = CmeCourse.verify_id_token(token)
    if not course:
        return redirect(url_for('continuing_medical_education'))
    output = io.BytesIO()
    styles = getSampleStyleSheet()
    # style_right = ParagraphStyle(name='right', parent=styles['Normal'], alignment=TA_RIGHT)
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), rightMargin=0, leftMargin=0, topMargin=0, bottomMargin=0,
                            title=f'{course.title.upper()} CERTIFICATE')

    elements = []

    #center_style = ParagraphStyle(name='center', alignment=TA_CENTER, fontSize=14, fontName='Arial')# , leading=10
    bg_logo = Image(url_for('static', filename='biogenix_labs_logo2.png', _external=True))
    bg_logo.drawHeight = 2.4 * inch * bg_logo.drawHeight / bg_logo.drawWidth
    bg_logo.drawWidth = 2.8 * inch
    g42h_logo = Image(url_for('static', filename='g42_healthcare_logo.png', _external=True))
    g42h_logo.drawHeight = 1.3 * inch * bg_logo.drawHeight / bg_logo.drawWidth
    g42h_logo.drawWidth = 1.4 * inch
    cme_pic1 = Image(url_for('static', filename='cme_pic1.png', _external=True))
    cme_pic1.drawHeight = 2.2 * inch * bg_logo.drawHeight / bg_logo.drawWidth
    cme_pic1.drawWidth = 1.6 * inch
    cme_pic2 = Image(url_for('static', filename='cme_pic2.png', _external=True))
    cme_pic2.drawHeight = 3.4 * inch * bg_logo.drawHeight / bg_logo.drawWidth
    cme_pic2.drawWidth = 3 * inch
    seal = Image(url_for('static', filename='seal.png', _external=True))
    seal.drawHeight = 2.6 * inch * bg_logo.drawHeight / bg_logo.drawWidth
    seal.drawWidth = 1.8 * inch


    head_data = [[cme_pic1, '', bg_logo, '', g42h_logo]]
    head = Table(head_data, colWidths=[150, 150, 200, 150, 150], rowHeights=[115])
    head.setStyle(TableStyle([('VALIGN', (0, 0), (0, 0), 'TOP'),
                             ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                              ('LEFTPADDING', (0, 0), (0, 0), -4),
                              ('TOPPADDING', (0, 0), (0, 0), -2),
                              ('VALIGN', (2, 0), (2, 0), 'BOTTOM'),
                             ('ALIGN', (2, 0), (2, 0), 'CENTER'),
                             ('VALIGN', (4, 0), (4, 0), 'TOP'),
                             ('ALIGN', (4, 0), (4, 0), 'LEFT'),
                             # ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                             # ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                             # ('INNERGRID', (0, -1), (0, -1), 0.25, colors.blue)
                             ]))

    styles.add(ParagraphStyle(name='style_1',
                              fontName='Helvetica-Bold',
                              fontSize=28,
                              alignment=TA_CENTER,
                              textColor=colors.HexColor("#ACD588"),
                              # backColor=colors.yellow,
                              # borderColor=colors.aquamarine,
                              # # borderPadding = (7, 2, 20),
                              # borderRadius=None,
                              # borderWidth=1,
                              ))
    styles.add(ParagraphStyle(name='style_2',
                              fontName='Helvetica-Bold',
                              fontSize=28,
                              alignment=TA_CENTER,
                              textColor=colors.HexColor("#3CC6EA"),
                              # backColor=colors.yellow,
                              # borderColor=colors.aquamarine,
                              # # borderPadding = (7, 2, 20),
                              # borderRadius = None,
                              # borderWidth = 1,
                            ))
    styles.add(ParagraphStyle(name='p',
                              fontName='Helvetica',
                              fontSize=18,
                              alignment=TA_CENTER,
                              textColor=colors.black,
                              # backColor=colors.yellow,
                              # borderColor=colors.aquamarine,
                              # # borderPadding = (7, 2, 20),
                              # borderRadius=None,
                              # borderWidth=1,
                              ))
    styles.add(ParagraphStyle(name='p2',
                              fontName='Helvetica',
                              fontSize=14,
                              alignment=TA_CENTER,
                              textColor=colors.black,
                              # backColor=colors.yellow,
                              # borderColor=colors.aquamarine,
                              # # borderPadding = (7, 2, 20),
                              # borderRadius=None,
                              # borderWidth=1,
                              ))

    cert_comp = Paragraph('CERTIFICATE OF COMPLETION', style=styles['style_1'])
    P1 = Paragraph('This is to confirm that', style=styles['p'])
    userp = Paragraph(current_user.name.upper(), style=styles['style_2'])
    P2 = Paragraph('completed the training activity of', style=styles['p'])
    course_title = Paragraph(course.title.upper(), style=styles['style_2'])
    P3 = Paragraph(f'published on {datetime.now().strftime("%B %d, %Y")} by Biogenix Laboratories in Abu Dhabi - United Arab Emirates', style=styles['p'])
    P4 = Paragraph('Category 1 activity according to Abu Dhabi Department of Health Guidelines', style=styles['p'])
    # n = -1
    # last_pt_passed = course.user_post_tests(current_user)[n] if course.user_post_tests(current_user)[n].passed() else course.user_post_tests(current_user)[n-1]
    issue_d = Paragraph(f"Issue date: {course.certificate_issue_date(current_user).strftime('%b %d, %Y')}", style=styles['p2'])
    foot_data = [[cme_pic2, '', [issue_d, seal]]]
    foot = Table(foot_data, colWidths=[300, 200, 300], rowHeights=[120])
    foot.setStyle(TableStyle([('VALIGN', (0, 0), (0, 0), 'BOTTOM'),
                              ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                              ('LEFTPADDING', (0, 0), (0, 0), -4),
                              ('BOTTOMPADDING', (0, 0), (0, 0), -4),
                              ('VALIGN', (2, 0), (2, 0), 'BOTTOM'),
                              ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                              # ('ALIGN', (4, 0), (4, 0), 'LEFT'),
                              # ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                              # ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black)
                              ]))
    main_tbl_ = [[head],
                 [cert_comp],
                 [P1],
                 [userp],
                 [P2],
                 [course_title],
                 [P3],
                 [P4],
                 [foot]]
    main_tbl = Table(main_tbl_, colWidths=[812, 812, 812, 812, 812, 812, 812, 812, 812], rowHeights=[120, 80, 40, 45, 40, 45, 40, 40, 130])
    main_tbl.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ebfafa")),
                                  # ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                                  # ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                  ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
                                  ('VALIGN', (0, 1), (0, -1), 'MIDDLE'),
                                  # ('VALIGN', (0, 0), (0, -1), 'TOP'),
                                  # ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),
                                  # ('VALIGN', (0, 5), (0, 5), 'BOTTOM'),
                                  ]))

    elements.append(main_tbl)

    # course_title_ = '<para align="center" ><font size="36" face="helvetica" color=""><b>' + course.title + '</b></font></para>'


    # elements.append(course_title)

    doc.build(elements)
    # doc.multiBuild(elements)
    output.seek(0)
    return send_file(output,
                     attachment_filename='pdf1' + datetime.now().strftime(
                         '%Y-%m-%d_%H-%M-%S') + '.pdf',
                     as_attachment=True)