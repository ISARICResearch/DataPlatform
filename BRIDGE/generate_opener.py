import pandas as pd
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from copy import deepcopy
from reportlab.platypus import Spacer

def generate_opener(elements, details, db_name):

    if isinstance(db_name, list):
        db_name=db_name[0]
        

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
    title_text = title_text.replace('CORE', db_name).upper()
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


    return elements