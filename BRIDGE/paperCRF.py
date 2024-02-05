import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from copy import deepcopy
from reportlab.platypus import Spacer

try:
# Register the font
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'BRIDGE/assets/fonts/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'BRIDGE/assets/fonts/DejaVuSans-Bold.ttf'))
except:
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'assets/fonts/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'assets/fonts/DejaVuSans-Bold.ttf'))
line_placeholder='_' * 30

def header_footer(canvas, doc):
    # Add two logos in the header


    # Draw the first logo
    canvas.drawInlineImage("assets/ISARIC_logo.png", 50, 730, width=69, height=30)  # adjust the width and height accordingly
    
    # For the second logo, make sure it's positioned after the first logo + some spacing
    canvas.drawInlineImage("assets/who_logo.png", 130, 730, width=98, height=30)  # adjust the width and height
    
    # Now, for the text, ensure it's positioned after the second logo + some spacing
    text_x_position = 270  # 160 + 100 + 10
    canvas.setFont("DejaVuSans", 8)
    canvas.drawString(text_x_position, 730, "PARTICIPANT IDENTIFICATION #: [___][___][___][___][___]-­‐ [___][___][___][___]")
    # Footer content

    canvas.setFont("DejaVuSans", 8)
    canvas.drawString(inch, 0.95 * inch, "ISARIC CORE CASE REPORT FORM ")
    canvas.setFont("DejaVuSans", 6)
    canvas.drawString(inch, 0.75 * inch, "Licensed under a Creative Commons Attribution-ShareAlike 4.0 International License by ISARIC on behalf of Oxford University.")

'''def format_choices(choices_str, field_type, threshold=65):
    """
    Format the choices string. If the combined length exceeds the threshold, use line breaks instead of commas.
    Prepend symbols based on the field type.
    """
    if field_type == 'radio':
        symbol = "○ "
    elif field_type in ['checkbox', 'dropdown']:
        symbol = "□ "
    else:
        symbol = ""
    if len(choices_str.split('|'))<=15:
        choices = [symbol + choice.split(',', 1)[-1].strip() for choice in choices_str.split('|')]
        combined_choices = '   '.join(choices).strip()
    else:
        
        combined_choices = line_placeholder
    
    
    if len(combined_choices) > threshold:
        combined_choices = '<br/>'.join(choices).strip()

    return combined_choices'''

def create_table(data):
    table = Table(data, colWidths=[2.5*inch, 4*inch])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (0, 0), (-1, 0))
    ])

    for idx, _ in enumerate(data):
        if len(data[idx]) == 1:  # it's a section
            style.add('BACKGROUND', (0, idx), (-1, idx), colors.grey)
            style.add('SPAN', (0, idx), (-1, idx))

    table.setStyle(style)
    return table

def generate_pdf(data_dictionary, output_pdf_path, version, db_name):
    
    root='https://raw.githubusercontent.com/ISARICResearch/DataPlatform/main/ARCH/'
    icc_version_path = root+version
    details = pd.read_csv(icc_version_path+'/paper_like_details.csv', encoding='latin-1')
    
    doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
    elements = []

    # Get the predefined styles
    styles = getSampleStyleSheet()
    
    normal_style = styles['Normal']
    normal_style.fontSize = 8
    normal_style.leading = 10
    normal_style.fontName = 'DejaVuSans'  # Use the registered font
    
    center_style = deepcopy(styles['Normal'])
    center_style.fontSize = 8
    center_style.leading = 10
    center_style.fontName = 'DejaVuSans'  # Use the registered font
    center_style.alignment = 1  # Center alignment

    header_style = styles['Heading1']
    header_style.fontSize = 10
    header_style.leading = 12
    header_style.fontName = 'DejaVuSans-Bold'  # Use the registered font


    title_style = styles['Title']
    title_style.fontSize = 14
    title_style.leading = 20
    title_style.fontName = 'DejaVuSans-Bold'
    
    # Add title and design description from the details DataFrame
    title_text = details[details['Paper-like section'] == 'Title']['Text'].values[0]
    elements.append(Paragraph(title_text, title_style))
    elements.append(Paragraph("<br/><br/>"))  # Add some space

    # Adding title and design description
    
    # Extracting the 'DESIGN OF THIS CASE REPORT FORM (CRF)' from the details dataset

    design_desc = details.loc[details['Paper-like section'] == 'DESIGN OF THIS CASE REPORT FORM (CRF)', 'Text'].values[0].replace('[PROJECT_NAME]',db_name) 
    elements.append(Paragraph('DESIGN OF THIS CASE REPORT FORM (CRF)', header_style))
    elements.append(Paragraph(design_desc, normal_style))
    
    elements.append(Paragraph("<br/><br/>"))  # Add some space
    
    # Add form presentation paragraphs
    
    # Filtering out rows that are not related to form details
    form_details = details[
        ~details['Text'].str.startswith("Timing /Events:") & 
        details['Paper-like section'].isin(['PRESENTATION FORM', 'DAILY FORM', 'OUTCOME FORM'])].copy()

    # Build the paragraphs with the desired format
    form_names_added = set()  # To keep track of form names already added
    presentation_paragraphs = []
    
    for _, row in form_details.iterrows():
        form_name = row['Paper-like section']
        text = row['Text']
    
        # Check if the form name has been added before
        if form_name not in form_names_added:
            presentation_paragraphs.append(f'<b>{form_name}:</b> {text}')
            form_names_added.add(form_name)
        else:
            presentation_paragraphs.append(f'{form_name}: {text}')
    
    # Joining the constructed paragraphs with line breaks and add to the elements list
    elements.append(Paragraph('<br/>'.join(presentation_paragraphs), normal_style))
    
    elements.append(Paragraph(details['Text'].loc[details['Paper-like section']=='Follow-up details'].iloc[0],normal_style))

    elements.append(Paragraph("<br/>"))  # Add some space
    elements.append(Spacer(1, 10)) 
    ###########################################################################
    details_event_table=details[(details['Text'].str.startswith("Timing /Events:")) | (details['Paper-like section']=='Timing /Events' ) ].copy()
    columns = ['Forms']+details_event_table['Text'].loc[details_event_table['Paper-like section']=='Timing /Events'].iloc[0].split(' | ')
    transformed_df = pd.DataFrame(columns=columns)
    transformed_df["Forms"] = details_event_table["Paper-like section"]
    for col in columns[1:]:
        if col in [event for event in columns if '(' in event]:
            transformed_df[col] = details_event_table["Text"].apply(lambda x: '(COMPLETE)' if col in x else '')
        else:
            transformed_df[col] = details_event_table["Text"].apply(lambda x: 'COMPLETE' if col in x else '')

    transformed_df = transformed_df.loc[transformed_df['Forms']!='Timing /Events' ]


    # Convert DataFrame data into a list of lists with Paragraphs for wrapping
    table_data = [[Paragraph(str(item), center_style) for item in row] for row in transformed_df.values.tolist()]
    # Add headers as well
    headers = [Paragraph(str(header), center_style) for header in transformed_df.columns.tolist()]
    table_data.insert(0, headers)
    
    # Calculate the available width for the table
    page_width = 8.5 * inch
    margin_width = 1 * inch  # Assuming a 1-inch margin on both sides
    table_width = page_width - 2 * margin_width  # subtracting both left and right margins
    num_columns = len(transformed_df.columns)
    col_width = table_width / num_columns
    
    table = Table(table_data, colWidths=[col_width for _ in range(num_columns)])
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Adjust the font size for all cells here
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    
    table.setStyle(style)
    
    elements.append(table)
    elements.append(Spacer(1, 30)) 
    ###########################################################################
    
    

    elements.append(Paragraph('GENERAL GUIDANCE', header_style))
    elements.append(Spacer(1, 12))    
    for entry in details['Text'].loc[details['Paper-like section']=='GENERAL GUIDANCE']:
        bullet_point = Paragraph("• " + entry.replace('circles ()','circles (○)').replace('square boxes ()','square boxes (□)'), styles['Normal'])
        elements.append(bullet_point)
    
    
    
    
    ###########################################################################
    elements.append(PageBreak())
    #doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
    #elements = []

    # Get the predefined styles
    styles = getSampleStyleSheet()
    


    data_dictionary['Section Header'].replace('', pd.NA, inplace=True)
    data_dictionary['Section Header'].fillna(method='ffill', inplace=True)


    # Grouping by 'Section Header' instead of 'Form Name'



    for form_name in data_dictionary['Form Name'].drop_duplicates():

        group = data_dictionary[data_dictionary['Form Name'] == form_name]

        # Add form name as a title for each table
        elements.append(Paragraph(form_name, header_style))
        data = []
        current_section = None

        for index, row in group.iterrows():

            # Add new section
            if row['Section Header'] != current_section and pd.notna(row['Section Header']):
                current_section = row['Section Header']
                data.append([Paragraph(current_section, header_style)])
                
            if row['Field Type'] in ['radio', 'dropdown', 'checkbox']:
                formatted_choices = format_choices(row['Choices, Calculations, OR Slider Labels'],row['Field Type'] )
                data.append([Paragraph(row['Field Label'], normal_style), Paragraph(formatted_choices, normal_style)])
            elif row['Text Validation Type OR Show Slider Number'] == 'date_dmy':
                date_str = """[<font color="lightgrey">_D_</font>][<font color="lightgrey">_D_</font>]/[<font color="lightgrey">_M_</font>][<font color="lightgrey">_M_</font>]/[_2_][_0_][<font color="lightgrey">_Y_</font>][<font color="lightgrey">_Y_</font>]"""
                data.append([Paragraph(row['Field Label'], normal_style), Paragraph(date_str, normal_style)]) # Placeholder for date input
            else:
                data.append([Paragraph(row['Field Label'], normal_style), line_placeholder])  # Placeholder for text input

        table = Table(data, colWidths=[2.5*inch, 4*inch])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 0), (-1, 0))
        ])

        for idx, _ in enumerate(data):
            if len(data[idx]) == 1:  # it's a section
                style.add('BACKGROUND', (0, idx), (-1, idx), colors.grey)
                style.add('SPAN', (0, idx), (-1, idx))

        table.setStyle(style)
        elements.append(table)


    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)

line_placeholder='_' * 30
def format_choices(choices_str, field_type, threshold=65):
    """
    Format the choices string. If the combined length exceeds the threshold, use line breaks instead of commas.
    Prepend symbols based on the field type.
    """
    if field_type == 'radio':
        symbol = "○ "
    elif field_type=='list':
        symbol="○ "
    elif field_type=='user_list':
        symbol="○ "            
    elif field_type == 'checkbox' :
        symbol = "□ "
    elif field_type=='dropdown':
        symbol="↧ "
    else: 
        symbol = ""
    if len(choices_str.split('|'))<=15:
        choices = [symbol + choice.split(',', 1)[-1].strip() for choice in choices_str.split('|')]
        combined_choices = '   '.join(choices).strip()
    else:
        combined_choices = line_placeholder
    if len(combined_choices) > threshold:
        combined_choices = "\n".join(choices).strip()
    return combined_choices


line_placeholder='_' * 30

def generate_pdf(data_dictionary, output_pdf_path, version, db_name):
    
    root='https://raw.githubusercontent.com/ISARICResearch/DataPlatform/main/ARCH/'
    icc_version_path = root+version
    details = pd.read_csv(icc_version_path+'/paper_like_details.csv', encoding='latin-1')
    
    doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
    elements = []

    # Get the predefined styles
    styles = getSampleStyleSheet()
    
    normal_style = styles['Normal']
    normal_style.fontSize = 8
    normal_style.leading = 10
    normal_style.fontName = 'DejaVuSans'  # Use the registered font
    
    center_style = deepcopy(styles['Normal'])
    center_style.fontSize = 8
    center_style.leading = 10
    center_style.fontName = 'DejaVuSans'  # Use the registered font
    center_style.alignment = 1  # Center alignment

    header_style = styles['Heading1']
    header_style.fontSize = 10
    header_style.leading = 12
    header_style.fontName = 'DejaVuSans-Bold'  # Use the registered font


    title_style = styles['Title']
    title_style.fontSize = 14
    title_style.leading = 20
    title_style.fontName = 'DejaVuSans-Bold'
    
    # Add title and design description from the details DataFrame
    title_text = details[details['Paper-like section'] == 'Title']['Text'].values[0]
    elements.append(Paragraph(title_text, title_style))
    elements.append(Paragraph("<br/><br/>"))  # Add some space

    # Adding title and design description
    
    # Extracting the 'DESIGN OF THIS CASE REPORT FORM (CRF)' from the details dataset

    design_desc = details.loc[details['Paper-like section'] == 'DESIGN OF THIS CASE REPORT FORM (CRF)', 'Text'].values[0].replace('[PROJECT_NAME]',db_name) 
    elements.append(Paragraph('DESIGN OF THIS CASE REPORT FORM (CRF)', header_style))
    elements.append(Paragraph(design_desc, normal_style))
    
    elements.append(Paragraph("<br/><br/>"))  # Add some space
    
    # Add form presentation paragraphs
    
    # Filtering out rows that are not related to form details
    form_details = details[
        ~details['Text'].str.startswith("Timing /Events:") & 
        details['Paper-like section'].isin(['PRESENTATION FORM', 'DAILY FORM', 'OUTCOME FORM'])].copy()

    # Build the paragraphs with the desired format
    form_names_added = set()  # To keep track of form names already added
    presentation_paragraphs = []
    
    for _, row in form_details.iterrows():
        form_name = row['Paper-like section']
        text = row['Text']
    
        # Check if the form name has been added before
        if form_name not in form_names_added:
            presentation_paragraphs.append(f'<b>{form_name}:</b> {text}')
            form_names_added.add(form_name)
        else:
            presentation_paragraphs.append(f'{form_name}: {text}')
    
    # Joining the constructed paragraphs with line breaks and add to the elements list
    elements.append(Paragraph('<br/>'.join(presentation_paragraphs), normal_style))
    
    elements.append(Paragraph(details['Text'].loc[details['Paper-like section']=='Follow-up details'].iloc[0],normal_style))

    elements.append(Paragraph("<br/>"))  # Add some space
    elements.append(Spacer(1, 10)) 
    ###########################################################################
    details_event_table=details[(details['Text'].str.startswith("Timing /Events:")) | (details['Paper-like section']=='Timing /Events' ) ].copy()
    columns = ['Forms']+details_event_table['Text'].loc[details_event_table['Paper-like section']=='Timing /Events'].iloc[0].split(' | ')
    transformed_df = pd.DataFrame(columns=columns)
    transformed_df["Forms"] = details_event_table["Paper-like section"]
    for col in columns[1:]:
        if col in [event for event in columns if '(' in event]:
            transformed_df[col] = details_event_table["Text"].apply(lambda x: '(COMPLETE)' if col in x else '')
        else:
            transformed_df[col] = details_event_table["Text"].apply(lambda x: 'COMPLETE' if col in x else '')

    transformed_df = transformed_df.loc[transformed_df['Forms']!='Timing /Events' ]


    # Convert DataFrame data into a list of lists with Paragraphs for wrapping
    table_data = [[Paragraph(str(item), center_style) for item in row] for row in transformed_df.values.tolist()]
    # Add headers as well
    headers = [Paragraph(str(header), center_style) for header in transformed_df.columns.tolist()]
    table_data.insert(0, headers)
    
    # Calculate the available width for the table
    page_width = 8.5 * inch
    margin_width = 1 * inch  # Assuming a 1-inch margin on both sides
    table_width = page_width - 2 * margin_width  # subtracting both left and right margins
    num_columns = len(transformed_df.columns)
    col_width = table_width / num_columns
    
    table = Table(table_data, colWidths=[col_width for _ in range(num_columns)])
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Adjust the font size for all cells here
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    
    table.setStyle(style)
    
    elements.append(table)
    elements.append(Spacer(1, 30)) 
    ###########################################################################
    
    

    elements.append(Paragraph('GENERAL GUIDANCE', header_style))
    elements.append(Spacer(1, 12))    
    for entry in details['Text'].loc[details['Paper-like section']=='GENERAL GUIDANCE']:
        bullet_point = Paragraph("• " + entry.replace('circles ()','circles (○)').replace('square boxes ()','square boxes (□)'), styles['Normal'])
        elements.append(bullet_point)
    
    
    
    
    ###########################################################################
    elements.append(PageBreak())
    #doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
    #elements = []

    # Get the predefined styles
    styles = getSampleStyleSheet()
    


    data_dictionary['Section Header'].replace('', pd.NA, inplace=True)
    data_dictionary['Section Header'].fillna(method='ffill', inplace=True)


    # Grouping by 'Section Header' instead of 'Form Name'



    for form_name in data_dictionary['Form Name'].drop_duplicates():

        group = data_dictionary[data_dictionary['Form Name'] == form_name]

        # Add form name as a title for each table
        elements.append(Paragraph(form_name, header_style))
        data = []
        current_section = None

        for index, row in group.iterrows():

            # Add new section
            if row['Section Header'] != current_section and pd.notna(row['Section Header']):
                current_section = row['Section Header']
                data.append([Paragraph(current_section, header_style)])
                
            if row['Field Type'] in ['radio', 'dropdown', 'checkbox']:
                formatted_choices = format_choices(row['Choices, Calculations, OR Slider Labels'],row['Field Type'] )
                data.append([Paragraph(row['Field Label'], normal_style), Paragraph(formatted_choices, normal_style)])
            elif row['Text Validation Type OR Show Slider Number'] == 'date_dmy':
                date_str = """[<font color="lightgrey">_D_</font>][<font color="lightgrey">_D_</font>]/[<font color="lightgrey">_M_</font>][<font color="lightgrey">_M_</font>]/[_2_][_0_][<font color="lightgrey">_Y_</font>][<font color="lightgrey">_Y_</font>]"""
                data.append([Paragraph(row['Field Label'], normal_style), Paragraph(date_str, normal_style)]) # Placeholder for date input
            else:
                data.append([Paragraph(row['Field Label'], normal_style), line_placeholder])  # Placeholder for text input

        table = Table(data, colWidths=[2.5*inch, 4*inch])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 0), (-1, 0))
        ])

        for idx, _ in enumerate(data):
            if len(data[idx]) == 1:  # it's a section
                style.add('BACKGROUND', (0, idx), (-1, idx), colors.grey)
                style.add('SPAN', (0, idx), (-1, idx))

        table.setStyle(style)
        elements.append(table)


    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)


def generate_completionguide(data_dictionary, output_pdf_path, version, db_name):
    data_dictionary=data_dictionary.copy()
    root='https://raw.githubusercontent.com/ISARICResearch/DataPlatform/main/ARCH/'
    icc_version_path = root+version
    details = pd.read_csv(icc_version_path+'/paper_like_details.csv', encoding='latin-1')
    
    doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
    elements = []

    # Get the predefined styles
    styles = getSampleStyleSheet()
    
    normal_style = styles['Normal']
    normal_style.fontSize = 8
    normal_style.leading = 10
    normal_style.fontName = 'DejaVuSans'  # Use the registered font
    
    center_style = deepcopy(styles['Normal'])
    center_style.fontSize = 8
    center_style.leading = 10
    center_style.fontName = 'DejaVuSans'  # Use the registered font
    center_style.alignment = 1  # Center alignment

    header_style = styles['Heading1']
    header_style.fontSize = 10
    header_style.leading = 12
    header_style.fontName = 'DejaVuSans-Bold'  # Use the registered font


    title_style = styles['Title']
    title_style.fontSize = 14
    title_style.leading = 20
    title_style.fontName = 'DejaVuSans-Bold'
    
    # Add title and design description from the details DataFrame
    title_text = "Completion Guide"

    elements.append(Paragraph("<br/><br/>"))  # Add some space


    #doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
    #elements = []

    # Get the predefined styles
    styles = getSampleStyleSheet()
    

    data_dictionary['Section'].replace('', pd.NA, inplace=True)
    data_dictionary['Section'].fillna(method='ffill', inplace=True)

    for index, row in data_dictionary.iterrows():
        elements.append(Paragraph(row['Question'], header_style))  # Add some space
        elements.append(Paragraph(row['Definition'], normal_style))  # Add some space
        elements.append(Paragraph(row['Completion Guideline'],normal_style))
        

    # Grouping by 'Section Header' instead of 'Form Name'



    '''for form_name in data_dictionary['Form'].drop_duplicates():

        group = data_dictionary[data_dictionary['Form'] == form_name]

        # Add form name as a title for each table
        elements.append(Paragraph(form_name, header_style))
        data = []
        current_section = None

        for index, row in group.iterrows():

            # Add new section
            if row['Section'] != current_section and pd.notna(row['Section']):
                current_section = row['Section']
                data.append([Paragraph(current_section, header_style)])
                
            if row['Type'] in ['radio', 'dropdown', 'checkbox']:
                formatted_choices = format_choices(row['Answer Options'],row['Type'] )
                data.append([Paragraph(row['Question'], normal_style),Paragraph(row['Definition'], normal_style),Paragraph(row['Completion Guideline'], normal_style)])
            elif row['Validation'] == 'date_dmy':
                date_str = """[<font color="lightgrey">_D_</font>][<font color="lightgrey">_D_</font>]/[<font color="lightgrey">_M_</font>][<font color="lightgrey">_M_</font>]/[_2_][_0_][<font color="lightgrey">_Y_</font>][<font color="lightgrey">_Y_</font>]"""
                data.append([Paragraph(row['Question'], normal_style),Paragraph(row['Definition'], normal_style),Paragraph(row['Completion Guideline'], normal_style)]) # Placeholder for date input
            else:
                data.append([Paragraph(row['Question'], normal_style),Paragraph(row['Definition'], normal_style),Paragraph(row['Completion Guideline'], normal_style) ])  # Placeholder for text input

        table = Table(data, colWidths=[inch,2*inch, 3*inch])
        #table = Table(data)                
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 0), (-1, 0))
        ])

        for idx, _ in enumerate(data):
            if len(data[idx]) == 1:  # it's a section
                style.add('BACKGROUND', (0, idx), (-1, idx), colors.grey)
                style.add('SPAN', (0, idx), (-1, idx))

        table.setStyle(style)
        elements.append(table)'''


    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)




def format_choices(choices_str, field_type, threshold=65):
    """
    Format the choices string. If the combined length exceeds the threshold, use line breaks instead of commas.
    Prepend symbols based on the field type.
    """
    if field_type == 'radio':
        symbol = "○ "
    elif field_type=='list':
        symbol="○ "
    elif field_type=='user_list':
        symbol="○ "            
    elif field_type == 'checkbox' :
        symbol = "□ "
    elif field_type=='dropdown':
        symbol="↧ "
    else: 
        symbol = ""
    if len(choices_str.split('|'))<=15:
        choices = [symbol + choice.split(',', 1)[-1].strip() for choice in choices_str.split('|')]
        combined_choices = '   '.join(choices).strip()
    else:
        combined_choices = line_placeholder
    if len(combined_choices) > threshold:
        combined_choices = "\n".join(choices).strip()
    return combined_choices

