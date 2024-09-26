import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash import html, Input, Output, State
import dash_table
import pandas as pd
from dash.exceptions import PreventUpdate
import dash_ag_grid as dag
import arch
import dash_treeview_antd
import paperCRF
import json
import bridge_modals 
from dash import callback_context
#from pdf2docx import Converter
from datetime import datetime
import io
from zipfile import ZipFile
import re
import random
from urllib.parse import parse_qs, urlparse

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://use.fontawesome.com/releases/v5.8.1/css/all.css'],suppress_callback_exceptions=True)
app.title ='BRIDGE'

modified_list=[]

versions,recentVersion=arch.getARCHVersions()
currentVersion=recentVersion
current_datadicc,presets=arch.getARCH(recentVersion)
current_datadicc[['Sec', 'vari', 'mod']] = current_datadicc['Variable'].str.split('_', n=2, expand=True)
current_datadicc[['Sec_name', 'Expla']] = current_datadicc['Section'].str.split(r'[(|:]', n=1, expand=True)

for i in current_datadicc:
    print('#####################')
    print(i)

tree_items_data=arch.getTreeItems(current_datadicc,recentVersion)

#List content Transformation
arch_lists,list_variable_choices=arch.getListContent(current_datadicc,currentVersion)
current_datadicc=arch.addTransformedRows(current_datadicc,arch_lists,arch.getVariableOrder(current_datadicc))


#User List content Transformation
arch_ulist,ulist_variable_choices=arch.getUserListContent(current_datadicc,currentVersion,modified_list)



current_datadicc=arch.addTransformedRows(current_datadicc,arch_ulist,arch.getVariableOrder(current_datadicc))
arch_multilist,multilist_variable_choices=arch.getMultuListContent(current_datadicc,currentVersion)

current_datadicc=arch.addTransformedRows(current_datadicc,arch_multilist,arch.getVariableOrder(current_datadicc))
initial_current_datadicc =  current_datadicc.to_json(date_format='iso', orient='split')
initial_ulist_variable_choices =  json.dumps(ulist_variable_choices)
initial_multilist_variable_choices =  json.dumps(multilist_variable_choices)

print(versions)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="/assets/ISARIC_logo_wh.png", height="60px")),
                        dbc.Col(dbc.NavbarBrand("BRIDGE - BioResearch Integrated Data tool GEnerator", className="ms-2")),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="https://isaric.org/",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
        ]
    ),
    color="#BA0225",
    dark=True,
)

navbar_big = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="assets/ISARIC_logo_wh.png", height="100px")),
                        dbc.Col(dbc.NavbarBrand("BRIDGE - BioResearch Integrated Data tool GEnerator", className="ms-2")),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="https://isaric.org/",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
        ]
    ),
    color="#BA0225",
    dark=True,
)

# Sidebar with icons
sidebar = html.Div(
    [
        #dbc.NavLink(html.I(className="fas fa-home"), id="toggle-settings-1", n_clicks=0),
        #dbc.NavLink(html.I(className="fas fa-book"), id="toggle-settings-2", n_clicks=0),
        # Add more icons as needed

        dbc.NavLink(html.Img(src="/assets/icons/Settings_off.png", style={'width': '40px' },id='settings_icon'), id="toggle-settings-1", n_clicks=0),
        dbc.NavLink(html.Img(src="/assets/icons/preset_off.png", style={'width': '40px'},id='preset_icon'), id="toggle-settings-2", n_clicks=0),
        #dbc.NavLink(html.Img(src="/assets/icons/question_off.png", style={'width': '40px'},id='question_icon'), id="toggle-question", n_clicks=0),

    ],
    style={
        "position": "fixed",
        "top": "5rem",  # Height of the navbar
        "left": 0,
        "bottom": 0,
        "width": "4rem",
        "padding": "2rem 1rem",
        "background-color": "#dddddd",
        "display": "flex",
        "flexDirection": "column",
        "alignItems": "center",
        #"z-index": 2000
    }
)


arch_versions = versions
arch_versions_items = [dbc.DropdownMenuItem(version, id={"type": "dynamic-version", "index": i}) for i, version in enumerate(arch_versions)]

# Grouping presets by the first column
grouped_presets = {}
for key, value in presets:
    grouped_presets.setdefault(key, []).append(value)

# Creating the accordion items
accordion_items = []
for key, values in grouped_presets.items():
    # For each group, create a checklist
    checklist = dbc.Checklist(
        options=[{"label": value, "value": value} for value in values],
        value=[],
        id=f'checklist-{key}',
        switch=True,
    )
    # Create an accordion item with the checklist
    accordion_items.append(
        dbc.AccordionItem(
            title=key,
            children=checklist
        )
    )
preset_accordion = dbc.Accordion(accordion_items)
preset_content= html.Div(
    [html.H3("Templates", id="settings-text-1"),
     preset_accordion
     ],style={"padding": "2rem"}
)

preset_column = dbc.Fade(
    preset_content,
    id="presets-column",
    is_in=False,  # Initially hidden
    style={
        "position": "fixed",
        "top": "5rem",
        "left": "4rem",
        "bottom": 0,
        "width": "20rem",
        "background-color": "#dddddd",
        "z-index": 2001
    }
)


settings_content = html.Div(
    [
        html.H3("Settings", id="settings-text-2"),
        
        # ICC Version dropdown
        html.Div([
            dbc.InputGroup([
                dbc.DropdownMenu(
                    label="ARC Version",
                    children=arch_versions_items,
                    id="dropdown-arch-version-menu"
                ),
                dbc.Input(id="dropdown-arch_version_input", placeholder="name")
            ]),
            dcc.Store(id='selected-version-store'),
            dcc.Store(id='selected_data-store'),
            #dcc.Store(id='visibility-store', data={'display': 'block'})
        ], style={'margin-bottom': '20px'}),
        
        # Output Files checkboxes
        html.Div([
            html.Label("Output Files", htmlFor="output-files-checkboxes"),
            dbc.Checklist(
                id="output-files-checkboxes",
                options=[
                    {'label': 'ISARIC Clinical Characterization XML', 'value': 'redcap_xml'},
                    {'label': 'REDCap Data Dictionary', 'value': 'redcap_csv'},
                    {'label': 'Paper-like CRF', 'value': 'paper_like'},
                    #{'label': 'Completion Guide', 'value': 'completion_guide'},
                    
                    # Add more files as needed
                ],
                value=['file1'],  # Default selected values
                inline=True
            )
        ], style={'margin-bottom': '20px'}),



    ],
    style={"padding": "2rem"}
)
'''html.Div([
    html.Label("'Paperlike' Files", htmlFor="paperlike-files-checkboxes"),
    dbc.Checklist(
        id="paperlike-files-checkboxes",
        options=[
            {'label': 'pdf', 'value': 'PDF'},
            {'label': 'word', 'value': 'Word'},
            # Add more papers as needed
        ],
        value=['paper1'],  # Default selected values
        inline=True
    )
]),'''

settings_column = dbc.Fade(
    settings_content,
    id="settings-column",
    is_in=False,  # Initially hidden
    style={
        "position": "fixed",
        "top": "5rem",
        "left": "4rem",
        "bottom": 0,
        "width": "20rem",
        "background-color": "#dddddd",
        "z-index": 2001
    }
)

tree_items = html.Div(
    dash_treeview_antd.TreeView(
        id='input',
        multiple=False,
        checkable=True,
        checked=[],
        data=tree_items_data),id='tree_items_container',
    style={
        'overflow-y': 'auto',  # Vertical scrollbar when needed
        'height': '100%',     # Fixed height
        'width': '100%' ,       # Fixed width, or you can specify a value in px
        'white-space': 'normal',  # Allow text to wrap
        'overflow-x': 'hidden',     # Hide overflowed content
        'text-overflow': 'ellipsis',  # Indicate more content with an ellipsis
        'display': 'block'
    }
)

tree_column = dbc.Fade(
    tree_items,
    #html.Div("Hello"),
    id="tree-column",
    is_in=False,  # Initially hidden
    style={
        "position": "fixed",
        "top": "5rem",
        "left": "4rem",
        "bottom": 0,
        "width": "30rem",
        "background-color": "#ffffff",
        "z-index": 2
    }
)

column_defs = [{'headerName': "Question", 'field': "Question", 'wrapText': True}, 
                {'headerName': "Answer Options", 'field': "Answer Options", 'wrapText': True}]
    
row_data = [{'question': "", 'options': ""},
            {'question': "", 'options': ""}]


grid = html.Div(
    dag.AgGrid(
        id='CRF_representation_grid',
        columnDefs=column_defs,
        rowData=row_data,
        defaultColDef={"sortable": True, "filter": True, 'resizable': True},
        columnSize="sizeToFit",
        dashGridOptions={
            "rowDragManaged": True,
            "rowDragEntireRow": True,
            "rowDragMultiRow": True, "rowSelection": "multiple",
            "suppressMoveWhenRowDragging": True,
            "autoHeight": True
        },
        rowClassRules={
            "form-separator-row ": 'params.data.SeparatorType == "form"',
            'section-separator-row': 'params.data.SeparatorType == "section"',
        },
        style={
        'overflow-y': 'auto',  # Vertical scrollbar when needed
        'height': '99%',     # Fixed height
        'width': '100%' ,       # Fixed width, or you can specify a value in px
        'white-space': 'normal',  # Allow text to wrap
        'overflow-x': 'hidden',     # Hide overflowed content

    
    }
        
    ),
    style={
        'overflow-y': 'auto',  # Vertical scrollbar when needed
        'height': '75vh',     # Fixed height
        'width': '100%' ,       # Fixed width, or you can specify a value in px
        'white-space': 'normal',  # Allow text to wrap
        'overflow-x': 'hidden',     # Hide overflowed content
        'text-overflow': 'ellipsis'  # Indicate more content with an ellipsis
    
    }
)




# Main Content
main_content = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col([html.Div(),
                         
                         #tree_items,

                             html.Div(id='output-expanded', style={'display': 'none'})
                         ]
                        
                        , width=5),  # 45% width
                dbc.Col(
                    [
                        dbc.Row([html.Div(),
                                         grid]),  # 90% height
                        dbc.Row(
                            [
                                dbc.Col(dbc.Input(placeholder="CRF Name", type="text",id='crf_name')),
                                dbc.Col(dbc.Button("Generate", color="primary", id='crf_generate'))
                            ],
                            style={"height": "10%"}  # Remaining height for input and button
                        ),
                        dbc.Row(html.Div(["BRIDGE is being developed by ISARIC. For inquiries, support, or collaboration, please write to: ",html.A("data@isaric.org", href="mailto:data@isaric.org"),". ","Licensed under a ",
                                         html.A("Creative Commons Attribution-ShareAlike 4.0 ", 
                                                href="https://creativecommons.org/licenses/by-sa/4.0/", target="_blank"),
                                         "International License by ",
                                         html.A("ISARIC", href="https://isaric.org/", target="_blank"),
                                         " on behalf of Oxford University."]))
                    ],
                    width=7  # 55% width
                )
            ]
        )
    ],
    fluid=True,
    style={"margin-top": "4rem", "margin-left": "4rem","z-index": 1,"width":"90vw"}  # Adjust margin to accommodate navbar and sidebar
)
app.layout = html.Div(
    [
        dcc.Store(id='show-Take a Look at Our Other Tools', data=True),  # Store to manage which page to display
        dcc.Store(id='current_datadicc-store',data=initial_current_datadicc),
        dcc.Store(id='ulist_variable_choices-store',data=initial_ulist_variable_choices),
        dcc.Store(id='multilist_variable_choices-store',data=initial_multilist_variable_choices),
        #navbar,
        #sidebar,
        #settings_column,
        #preset_column,
        #tree_column,
        #main_content,
        dcc.Location(id='url', refresh=False),
        #html.H1(id='titleURL'),
        html.Div(id='page-content'),
        dcc.Download(id="download-dataframe-csv"),
        dcc.Download(id='download-compGuide-pdf'),
        dcc.Download(id='download-projectxml-pdf'),
        dcc.Download(id='download-paperlike-pdf'),
        bridge_modals.variableInformation_modal(),
        bridge_modals.researchQuestions_modal(),
        dcc.Loading(id="loading-1",
                    type="default",
                    children=html.Div(id="loading-output-1"),
        ),
        dcc.Store(id='selected-version-store'),
        dcc.Store(id='selected_data-store')
    ]
)



#################################
#######HOME PAGE##################
def home_page():
    return html.Div([
        navbar_big,
        # First Section: Big Slogan and Button
        html.Section([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H1("BRIDGE: Tailoring Case Reports for Every Outbreak", className="display-4", style={'font-weight': 'bold', 'color': 'white'}),
                        html.P("ISARIC BRIDGE streamlines the CRF creation process, generating data dictionaries and XML for REDCap, along with paper-like CRFs and completion guides.", style={'color': 'white'}),
                        dbc.Button("Create a CRF",  className="home-button", id='start-button'),
                        html.A("Visit GitHub",  target="_blank",href="https://github.com/ISARICResearch", style={'display': 'block', 'margin-top': '10px', 'color': 'white'})
                    ], style={'padding': '2rem'})
                ], md=6, style={'display': 'flex', 'align-items': 'center', 'background-color': '#475160'}),
                dbc.Col([
                    html.Img(src="/assets/home_main.png", style={'width': '100%'})
                ], md=6)
            ])
        ], style={'padding': '0', 'margin': '0', 'background-color': '#475160'}),

        html.Section([
            dbc.Row([
                dbc.Col([
                    html.H4("Accelerating Outbreak Research Response", className="mb-3"),
                    html.P("BRIDGE automates the creation of Case Report Forms (CRFs) for specific diseases and research contexts. It generates the necessary data dictionary and XML to create a REDCap database for data capture in the ARC structure. Learn more in our ", style={"font-size": "20px", "display": "inline"}),
                    html.A("guide for getting started.", href="https://isaricresearch.github.io/Training/bridge_starting.html", target="_blank", style={"font-size": "20px", "display": "inline"})
                ], md=9)
            ], className="my-5"),

        ], className="container"),
        

        html.Section([
            dbc.Row([
                dbc.Col([
                    dbc.Card([

                        dbc.CardBody([
                            html.H4("Choose", className="card-title"),
                            html.P([
                                "BRIDGE uses the machine-readable library ",
                                html.A("ARC", href="https://example.com", target="_blank"),
                                " and allows the user to choose the questions they want to include in the CRF. ",
                                "BRIDGE presents ARC as a tree structure with different levels: ARC version, forms, sections, and questions. Users navigate through this tree and select the questions they want to include in the CRF.",
                                html.Br(),
                                html.Br(),
                                "Additionally, users can start with one of our Presets, which are pre-selected groups of questions. They can click on the Pre-sets tab and select those they want to include in the CRF. All selected questions can be customized."
                            ], className="card-text")
                        ], className="card-body-fixed"),
                        dbc.CardImg(src="/assets/card1.png", bottom=True, className="card-img-small"),
                    ], className="mb-3")
                ], md=4),
                dbc.Col([
                    dbc.Card([

                        dbc.CardBody([
                            html.H4("Customize", className="card-title"),
                            html.P([
                                "BRIDGE allows customization of CRFs from chosen questions, as well as selection of measurement units and answer options where pertinent. ",
                                "Users click the relevant question, and a checkable list appears with options for the site or disease being researched.",
                                html.Br(),
                                html.Br(),
                                "This feature ensures that the CRF is tailored to specific needs, enhancing the precision and relevance of the data collected."
                            ], className="card-text")
                        ], className="card-body-fixed"),
                        dbc.CardImg(src="/assets/card2.png", bottom=True, className="card-img-small"),
                    ], className="mb-3")
                ], md=4),
                dbc.Col([
                    dbc.Card([

                        dbc.CardBody([
                            html.H4("Capture", className="card-title"),
                            html.P([
                                "BRIDGE generates files for creating databases within REDCap, including the data dictionary and XML needed to create a REDCap database for capturing data in the ARC structure. ",
                                "It also produces paper-like versions of the CRFs and completion guides. ",
                                html.Br(),
                                html.Br(),
                                "Once users are satisfied with their selections, they can name the CRF and click on generate to finalize the process, ensuring a seamless transition to data collection."
                            ], className="card-text")
                        ], className="card-body-fixed"),
                        dbc.CardImg(src="/assets/card3.png", bottom=True, className="card-img-small"),
                    ], className="mb-3")
                ], md=4),

            ], className="my-5")
        ], className="container"),
        html.Section([
            html.Div([
                html.Br(),
                html.H3("In partnership with:", className="text-center my-4"),
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Img(src="/assets/logos/FIOCRUZ_logo.png", className="img-fluid", style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src="/assets/logos/global_health.png", className="img-fluid", style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src="/assets/logos/puc_rio.png", className="img-fluid", style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src="/assets/logos/CONTAGIO_Logo.jpg", className="img-fluid", style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src="/assets/logos/LONG_CCCC.png", className="img-fluid", style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto")
                ], className="justify-content-center")  
            ])
        ]),

        
        html.Section([
            html.Div([
                html.Br(),
                html.H3("With funding from:", className="text-center my-4"),
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Img(src="/assets/logos/wellcome-logo.png", className="img-fluid", style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src="/assets/logos/billmelinda-logo.png", className="img-fluid", style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src="/assets/logos/uk-international-logo.png", className="img-fluid", style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src="/assets/logos/FundedbytheEU.png", className="img-fluid", style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto")
                ], className="justify-content-center")  
            ])
        ]),
        
        # Fourth Section: Other Tools
        # Section showcasing other tools
        html.Section([
            html.Div([
                html.H3("Take a Look at Our Other Tools", className="text-center my-4"),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardImg(src="/assets/logos/arc_logo.png", top=True),
                            dbc.CardBody([
                                html.H4("Analysis and Research Compendium (ARC)", className="card-title"),
                                html.P([
                                    "ARC is a comprehensive machine-readable document in CSV format, designed for use in Clinical Report Forms (CRFs) during disease outbreaks. ",
                                    "It includes a library of questions covering demographics, comorbidities, symptoms, medications, and outcomes. ",
                                    "Each question is based on a standardized schema, has specific definitions mapped to controlled terminologies, and has built-in quality control. ",
                                    "ARC is openly accessible, with version control via GitHub ensuring document integrity and collaboration."
                                ], className="card-text"),
                                html.A("Find Out More",  target="_blank",href="https://github.com/ISARICResearch/DataPlatform/tree/main/ARCH", style={'display': 'block', 'margin-top': '10px', 'color': '#BA0225'})
                            ], className="card-tools-fixed")
                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardImg(src="/assets/logos/fhirflat_logo.png", top=True),
                            dbc.CardBody([
                                html.H4("FHIRflat", className="card-title"),
                                html.P([
                                    "FHIRflat is a versatile library designed to transform FHIR resources in NDJSON or native Python dictionaries into a flat structure, which can be easily written to a Parquet file. ",
                                    "This facilitates reproducible analytical pipelines (RAP) by converting raw data into the FHIR R5 standard with ISARIC-specific extensions. ",
                                    "Typically, FHIR resources are stored in databases served by specialized FHIR servers. However, for RAP development, which demands reproducibility and data snapshots, a flat file format is more practical. ",
                                    
                                ], className="card-text")
,
                                html.A("Find Out More",  target="_blank",href="https://fhirflat.readthedocs.io/en/latest/", style={'display': 'block', 'margin-top': '10px', 'color': '#BA0225'})
                            ], className="card-tools-fixed")
                        ])
                    ], md=3),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardImg(src="/assets/logos/polyflame_logo.png", top=True),
                            dbc.CardBody([
                                html.H4("Polymorphic FLexible Analytics and Modelling Engine (PolyFLAME)", className="card-title"),
                                html.P([
                                    "PolyFLAME processes and transforms data using the FHIRflat library. ",
                                    "Once input data is brought into FHIRflat, it is represented as a (optionally zipped) folder of FHIR resources, with a parquet file corresponding to each resource: patient.parquet, encounter.parquet, and so on. ",
                                    "PolyFLAME is an easy-to-use library that can be utilized in Jupyter notebooks and other downstream code to query answers to common research questions in a reproducible analytical pipeline (RAP). "
                                ], className="card-text"),
                                html.A("Find Out More",  target="_blank",href="https://polyflame.readthedocs.io/en/latest/index.html", style={'display': 'block', 'margin-top': '10px', 'color': '#BA0225'})
                            ], className="card-tools-fixed"),
                            
                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardImg(src="/assets/logos/vertex_logo.png", top=True),
                            dbc.CardBody([
                                html.H4("Visual Evidence & Research Tool for Exploration (VERTEX)", className="card-title"),
                                html.P([
                                    "VERTEX is a web-based application designed to present graphs and tables based on relevant research questions that need quick answers during an outbreak. ",
                                    "VERTEX uses reproducible analytical pipelines, currently focusing on identifying the spectrum of clinical features in a disease and determining risk factors for patient outcomes. ",
                                    "New questions will be added by the ISARIC team and the wider scientific community, enabling the creation and sharing of new pipelines. ",
                                    "Users can download the code for ARC-structured data visualization through VERTEX."
                                ], className="card-text"),
                                html.A("Find Out More",  target="_blank",href="https://github.com/ISARICResearch/VERTEX", style={'display': 'block', 'margin-top': '10px', 'color': '#BA0225'})
                            ], className="card-tools-fixed")
                        ])
                    ], md=3)
                ], className="my-5")
            ], className="container")
        ], className="py-5"),

        html.Footer([
            html.Div([
                html.P([
                    "Licensed under a ",
                    html.A("Creative Commons Attribution-ShareAlike 4.0", 
                           href="https://creativecommons.org/licenses/by-sa/4.0/", target="_blank"),
                    " International License by ",
                    html.A("ISARIC", href="https://isaric.org/", target="_blank"),
                    " on behalf of Oxford University."
                ], className="text-center my-3")
            ], className="footer")
        ])
    ]),




def main_app():
    return html.Div([
        navbar,
        sidebar,
        settings_column,
        preset_column,
        tree_column,
        main_content,
    ])

@app.callback(Output('page-content', 'children'),
      Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/':
        return home_page()
    else:
        return main_app()

@app.callback(Output('url', 'pathname'),
      Input('start-button', 'n_clicks'))
def start_app(n_clicks):
    if n_clicks is None:
        return '/'
    else:
        return '/main'

####################
# get URL parameter
####################
@app.callback(
    [Output('crf_name', 'value')] + [Output(f'checklist-{key}', 'value') for key in grouped_presets.keys()],
    [Input('url', 'href')]
)
def update_output_based_on_url(href):
    if href is None:
        return [''] + [[] for _ in grouped_presets.keys()]

    # Parse the URL to extract the parameters
    parsed_url = urlparse(href)
    params = parse_qs(parsed_url.query)

    # Accessing the 'param' parameter
    param_value = params.get('param', [''])[0]  # Default to an empty string if the parameter is not present

    # Example: Split param_value by underscore
    group, value = param_value.split('_') if '_' in param_value else (None, None)

    # Prepare the outputs
    checklist_values = {key: [] for key in grouped_presets.keys()}

    if group in grouped_presets and value in grouped_presets[group]:
        checklist_values[group] = [value]

    # Return the value for 'crf_name' and checklist values
    return [value] + [checklist_values[key] for key in grouped_presets.keys()]


  

#################################

@app.callback(
    [Output("presets-column", "is_in"), 
     Output("settings-column", "is_in"),
     Output("tree-column", 'is_in'),
     Output("settings_icon", "src"),
     Output("preset_icon", "src")],
    [Input("toggle-settings-2", "n_clicks"), 
     Input("toggle-settings-1", "n_clicks")],
    [State("presets-column", "is_in"), 
     State("settings-column", "is_in")]
)
def toggle_columns(n_presets, n_settings, is_in_presets, is_in_settings):
    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Initialize the state of icons
    preset_icon_img = "/assets/icons/preset_off.png"
    settings_icon_img = "/assets/icons/Settings_off.png"

    # Toggle logic
    if button_id == "toggle-settings-2":
        # If settings is open, close it and open presets
        if is_in_settings:
            new_is_in_presets = True
            new_is_in_settings = False
        else:
            # Toggle the state of presets
            new_is_in_presets = not is_in_presets
            new_is_in_settings = False

        preset_icon_img = "/assets/icons/preset_on.png" if new_is_in_presets else "/assets/icons/preset_off.png"

    elif button_id == "toggle-settings-1":
        # If presets is open, close it and open settings
        if is_in_presets:
            new_is_in_settings = True
            new_is_in_presets = False
        else:
            # Toggle the state of settings
            new_is_in_settings = not is_in_settings
            new_is_in_presets = False

        settings_icon_img = "/assets/icons/Settings_on.png" if new_is_in_settings else "/assets/icons/Settings_off.png"

    else:
        # Default state if no button is clicked
        new_is_in_presets = is_in_presets
        new_is_in_settings = is_in_settings

    # Determine tree-column visibility
    is_in_tree = not (new_is_in_presets or new_is_in_settings)

    return new_is_in_presets, new_is_in_settings, is_in_tree, settings_icon_img, preset_icon_img





@app.callback([Output('CRF_representation_grid','columnDefs'),
               Output('CRF_representation_grid','rowData'),
               Output('selected_data-store','data')],
              [Input('input', 'checked')],
              [State('current_datadicc-store','data')],
              prevent_initial_call=True)

def display_checked(checked,current_datadicc_saved):
    current_datadicc=pd.read_json(current_datadicc_saved, orient='split')



    column_defs = [{'headerName': "Question", 'field': "Question", 'wrapText': True}, 
                    {'headerName': "Answer Options", 'field': "Answer Options", 'wrapText': True}]
        
    row_data = [{'question': "", 'options': ""},
                {'question': "", 'options': ""}]

    selected_variables = pd.DataFrame()
    if checked and len(checked) > 0:
        #selected_variables=current_datadicc.loc[current_datadicc['Variable'].isin(checked)]
        #global selected_variables
        selected_dependency_lists = current_datadicc['Dependencies'].loc[current_datadicc['Variable'].isin(checked)].tolist()
        flat_selected_dependency = set()
        for sublist in selected_dependency_lists:
            flat_selected_dependency.update(sublist)
        all_selected = set(checked).union(flat_selected_dependency)
        selected_variables = current_datadicc.loc[current_datadicc['Variable'].isin(all_selected)]    

        #############################################################
        #############################################################
        ## REDCAP Pipeline
        delete_this_variables_with_units=[]
        selected_variables=arch.getIncludeNotShow(selected_variables['Variable'],current_datadicc)

        #Select Units Transformation
        arc_var_units_selected, delete_this_variables_with_units=arch.getSelectUnits(selected_variables['Variable'],current_datadicc)
        if arc_var_units_selected is not None:
            selected_variables = arch.addTransformedRows(selected_variables,arc_var_units_selected,arch.getVariableOrder(current_datadicc))
            if len(delete_this_variables_with_units)>0: # This remove all the unit variables that were included in a select unit type question
                selected_variables = selected_variables.loc[~selected_variables['Variable'].isin(delete_this_variables_with_units)]


        selected_variables = arch.generateDailyDataType(selected_variables)
        
        #############################################################
        #############################################################


        last_form, last_section = None, None
        new_rows = []
        selected_variables=selected_variables.fillna('')
        for index, row in selected_variables.iterrows():
            # Add form separator
            if row['Form'] != last_form:
                new_rows.append({'Question': f"{row['Form'].upper()}", 'Answer Options': '', 'IsSeparator': True, 'SeparatorType': 'form'})
                last_form = row['Form']

            # Add section separator
            if row['Section'] != last_section and row['Section'] != '':
                new_rows.append({'Question': f"{row['Section'].upper()}", 'Answer Options': '', 'IsSeparator': True, 'SeparatorType': 'section'})
                last_section = row['Section']

            # Process the actual row
            if row['Type'] in ['radio', 'dropdown', 'checkbox','list','user_list','multi_list']:
                formatted_choices = paperCRF.format_choices(row['Answer Options'], row['Type'])
                row['Answer Options'] = formatted_choices
            elif row['Validation'] == 'date_dmy':
                #date_str = """[<font color="lightgrey">_D_</font>][<font color="lightgrey">_D_</font>]/[<font color="lightgrey">_M_</font>][<font color="lightgrey">_M_</font>]/[_2_][_0_][<font color="lightgrey">_Y_</font>][<font color="lightgrey">_Y_</font>]"""
                date_str = "[_D_][_D_]/[_M_][_M_]/[_2_][_0_][_Y_][_Y_]"
                row['Answer Options'] = date_str
            else:
                row['Answer Options'] = paperCRF.line_placeholder

            # Add the processed row to new_rows
            new_row = row.to_dict()
            new_row['IsSeparator'] = False
            new_rows.append(new_row)

        # Update selected_variables with new rows including separators
        selected_variables_for_TableVisualization = pd.DataFrame(new_rows)
        selected_variables_for_TableVisualization=selected_variables_for_TableVisualization.loc[selected_variables_for_TableVisualization['Type']!='group']
        # Convert to dictionary for row_data
        row_data = selected_variables_for_TableVisualization.to_dict(orient='records')

        column_defs = [{'headerName': "Question", 'field': "Question", 'wrapText': True}, 
                        {'headerName': "Answer Options", 'field': "Answer Options", 'wrapText': True}]

        


    return column_defs, row_data,  selected_variables.to_json(date_format='iso', orient='split')

@app.callback(Output('rq_modal', 'is_open'),
              [Input("toggle-question", "n_clicks")],
              prevent_initial_call=True)
def research_question(n_question):
    return True

@app.callback([
               Output('modal', 'is_open'),
               Output('modal_title','children'),
               Output('definition-text','children'),
               Output('completion-guide-text','children'),
               Output('options-checklist', 'style'), 
               Output('options-list-group', 'style'),
               Output('options-checklist','options'),
               Output('options-checklist','value'),
               Output('options-list-group','children')],
              [Input('input', 'selected')],
              [State('ulist_variable_choices-store','data'),State('multilist_variable_choices-store','data'),State('modal', 'is_open')])
def display_selected(selected,ulist_variable_choices_saved,multilist_variable_choices_saved,is_open):
    dict1 = json.loads(ulist_variable_choices_saved)
    dict2 = json.loads(multilist_variable_choices_saved)
    datatatata = dict1+dict2

    #datatatata=json.loads(ulist_variable_choices_saved)
    if (selected is not None):
        if len(selected)>0:
            if selected[0] in list(current_datadicc['Variable']):
                question=current_datadicc['Question'].loc[current_datadicc['Variable']==selected[0]].iloc[0]
                type=current_datadicc['Question'].loc[current_datadicc['Variable']==selected[0]].iloc[0]
                definition=current_datadicc['Definition'].loc[current_datadicc['Variable']==selected[0]].iloc[0]
                completion=current_datadicc['Completion Guideline'].loc[current_datadicc['Variable']==selected[0]].iloc[0]
                ulist_variables = [i[0] for i in datatatata]
                if selected[0] in ulist_variables:
                    for item in datatatata:
                        if item[0] == selected[0]:
                            options =  []
                            checked_items = []
                            for i in item[1]:     
                                options.append({"label":str(i[0])+', '+i[1],"value":str(i[0])+'_'+i[1]})   
                                if i[2]==1:
                                    checked_items.append(str(i[0])+'_'+i[1]) 
                      
   
                    return True,question+' ['+selected[0]+']',definition,completion, {"padding": "20px", "maxHeight": "250px", "overflowY": "auto"}, {"display": "none"},options,checked_items,[]
                else:
                    options =  []
                    answ_options=current_datadicc['Answer Options'].loc[current_datadicc['Variable']==selected[0]].iloc[0]
                    if isinstance(answ_options, str): 
                        for i in answ_options.split('|'):     
                            options.append(dbc.ListGroupItem(i))      
                    else:
                        options=[]                  
                    return True,question+' ['+selected[0]+']',definition,completion, {"display": "none"}, {"maxHeight": "250px", "overflowY": "auto"},[],[],options


                
        
    return False,'','','',{"display": "none"}, {"display": "none"},[],[],[]


@app.callback(Output('output-expanded', 'children'),
              [Input('input', 'expanded')])
def display_expanded(expanded):
    return 'You have expanded {}'.format(expanded)



@app.callback(
    Output('selected-version-store', 'data'),
    [Input({'type': 'dynamic-version', 'index': dash.ALL}, 'n_clicks')],
    [State('selected-version-store', 'data')]
)
def store_clicked_item(n_clicks, data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    else:
        button_id = ctx.triggered[0]['prop_id']
        # Splitting the ID string to extract the index part
        id_json = button_id.split(".")[0]  # This should give us the JSON part of the ID
        try:
            version_index = json.loads(id_json)["index"]
            return {'selected_version': arch_versions[version_index]}
        except json.JSONDecodeError:
            return dash.no_updatetree_itemsgrid

@app.callback(
    Output("dropdown-arch_version_input", "value"),
    [Input('selected-version-store', 'data')]
)
def update_input(data):
    if data is None:
        return dash.no_update
    return data.get('selected_version')


@app.callback(
    [Output('tree_items_container','children'),Output('current_datadicc-store','data',allow_duplicate=True),
     Output('ulist_variable_choices-store','data',allow_duplicate=True),Output('multilist_variable_choices-store','data',allow_duplicate=True)],
    [Input(f'checklist-{key}', 'value') for key in grouped_presets.keys()],
    #[State('visibility-store', 'data')],
    prevent_initial_call=True
)
def update_output(*args):

    templa_answer_opt_dict1=[]
    templa_answer_opt_dict2=[]

    checked_values = args
    #checked_values = args[:-1]
    #visibility_data = args[-1]    
    formatted_output = []
    for key, values in zip(grouped_presets.keys(), checked_values):
        if values:  # Check if the list of values is not empty
            for value in values:
                formatted_output.append([key, value.replace(' ', '_')])
    checked = []
    if len(formatted_output)>0:
        for ps in formatted_output:
            checked_key = 'preset_' + ps[0] + '_' + ps[1]
            if checked_key in current_datadicc:
                checked = checked+list(current_datadicc['Variable'].loc[current_datadicc[checked_key].notnull()])
    
            ##########Modificacion para template options in userlist
            template_ulist_var=current_datadicc.loc[current_datadicc['Type'].isin(['user_list','multi_list'])]
            template_ulist_lists=template_ulist_var['List']
            
            root='https://raw.githubusercontent.com/ISARICResearch/DataPlatform/main/ARCH/'
            #for t_u_list in template_ulist_lists:
            for index_tem_ul,row_tem_ul in template_ulist_var.iterrows():
                print(row_tem_ul['Variable'])
                dict1_options=[]
                dict2_options=[]
                t_u_list = row_tem_ul['List']
                list_path = root+currentVersion+'/Lists/'+t_u_list.replace('_','/')+'.csv'
                try:
                    list_options = pd.read_csv(list_path,encoding='latin1') 
                
                except Exception as e:
                    print(f"Failed to fetch remote file due to: {e}. Attempting to read from local file.")
                    continue
                
                
                #template_list_options=list_options.loc[list_options[checked_key]==1]
                list_options=list_options.sort_values(by=list_options.columns[0],ascending=True)
                cont_lo=1
                select_answer_options=''
    
                NOT_select_answer_options=''
                for index, row in list_options.iterrows():
                    if cont_lo == 88:
                        cont_lo=89
                    elif cont_lo == 99:
                        cont_lo =100
                    
                    
                    if checked_key in list_options.columns:
                        selected_column=checked_key
                    else:
                        selected_column='Selected'
    
                    if (row[selected_column]==1 ):
                        if row_tem_ul['Type']=='user_list':
                            dict1_options.append([str(cont_lo),str(row[list_options.columns[0]]),1])
                        elif row_tem_ul['Type']=='multi_list':
                            dict2_options.append([str(cont_lo),str(row[list_options.columns[0]]),1])
                        select_answer_options+=str(cont_lo)+', ' +str(row[list_options.columns[0]]) +' | '
                    else:
                        if row_tem_ul['Type']=='user_list':
                            dict1_options.append([str(cont_lo),str(row[list_options.columns[0]]),0])
                        elif row_tem_ul['Type']=='multi_list':
                            dict2_options.append([str(cont_lo),str(row[list_options.columns[0]]),0])                        
                        NOT_select_answer_options+=str(cont_lo)+', ' +str(row[list_options.columns[0]]) +' | '
                    cont_lo+=1     
                current_datadicc.loc[current_datadicc['Variable'] == row_tem_ul['Variable'], 'Answer Options'] = select_answer_options + '88, Other'
                if  row_tem_ul['Variable']+'_otherl2' in list(current_datadicc['Variable']):
                    current_datadicc.loc[current_datadicc['Variable'] == row_tem_ul['Variable']+'_otherl2', 'Answer Options'] = NOT_select_answer_options + '88, Other'
            
            
    
    
                if row_tem_ul['Type']=='user_list':
                    templa_answer_opt_dict1.append([row_tem_ul['Variable'],dict1_options] )
                elif row_tem_ul['Type']=='multi_list':     
                    templa_answer_opt_dict2.append([row_tem_ul['Variable'],dict2_options]   )      
    
                
    else:
        template_ulist_var=current_datadicc.loc[current_datadicc['Type'].isin(['user_list','multi_list'])]

        root='https://raw.githubusercontent.com/ISARICResearch/DataPlatform/main/ARCH/'
        #for t_u_list in template_ulist_lists:
        for index_tem_ul,row_tem_ul in template_ulist_var.iterrows():
            print(row_tem_ul['Variable'])
            dict1_options=[]
            dict2_options=[]
            t_u_list = row_tem_ul['List']
            list_path = root+currentVersion+'/Lists/'+t_u_list.replace('_','/')+'.csv'
            try:
                list_options = pd.read_csv(list_path,encoding='latin1') 

            except Exception as e:
                print(f"Failed to fetch remote file due to: {e}. Attempting to read from local file.")
                continue


            #template_list_options=list_options.loc[list_options[checked_key]==1]
            list_options=list_options.sort_values(by=list_options.columns[0],ascending=True)
            cont_lo=1
            select_answer_options=''

            NOT_select_answer_options=''
            for index, row in list_options.iterrows():
                if cont_lo == 88:
                    cont_lo=89
                elif cont_lo == 99:
                    cont_lo =100


                selected_column='Selected'

                if (row[selected_column]==1 ):
                    if row_tem_ul['Type']=='user_list':
                        dict1_options.append([str(cont_lo),str(row[list_options.columns[0]]),1])
                    elif row_tem_ul['Type']=='multi_list':
                        dict2_options.append([str(cont_lo),str(row[list_options.columns[0]]),1])
                    select_answer_options+=str(cont_lo)+', ' +str(row[list_options.columns[0]]) +' | '
                else:
                    if row_tem_ul['Type']=='user_list':
                        dict1_options.append([str(cont_lo),str(row[list_options.columns[0]]),0])
                    elif row_tem_ul['Type']=='multi_list':
                        dict2_options.append([str(cont_lo),str(row[list_options.columns[0]]),0])                        
                    NOT_select_answer_options+=str(cont_lo)+', ' +str(row[list_options.columns[0]]) +' | '
                cont_lo+=1     
            current_datadicc.loc[current_datadicc['Variable'] == row_tem_ul['Variable'], 'Answer Options'] = select_answer_options + '88, Other'
            if  row_tem_ul['Variable']+'_otherl2' in list(current_datadicc['Variable']):
                current_datadicc.loc[current_datadicc['Variable'] == row_tem_ul['Variable']+'_otherl2', 'Answer Options'] = NOT_select_answer_options + '88, Other'

            if row_tem_ul['Type']=='user_list':
                templa_answer_opt_dict1.append([row_tem_ul['Variable'],dict1_options] )
            elif row_tem_ul['Type']=='multi_list':     
                templa_answer_opt_dict2.append([row_tem_ul['Variable'],dict2_options]   )  
        ###########        

                



    tree_items = html.Div(
        dash_treeview_antd.TreeView(
            id='input',
            multiple=False,
            checkable=True,
            checked=checked,
            expanded=checked,
            data=tree_items_data),id='tree_items_container',
        style={
            'overflow-y': 'auto',  # Vertical scrollbar when needed
            'height': '75vh',     # Fixed height
            'width': '100%' ,       # Fixed width, or you can specify a value in px
            'white-space': 'normal',  # Allow text to wrap
            'overflow-x': 'hidden',     # Hide overflowed content
            'text-overflow': 'ellipsis',  # Indicate more content with an ellipsis
            #'display': visibility_data['display']
            #'display': 'none'
        }
    )

    #Check all list 


    return tree_items,current_datadicc.to_json(date_format='iso', orient='split'),json.dumps(templa_answer_opt_dict1), json.dumps(templa_answer_opt_dict2)

@app.callback(
    [Output('modal', 'is_open', allow_duplicate=True), Output('current_datadicc-store','data'),Output('ulist_variable_choices-store','data'),
     Output('multilist_variable_choices-store','data'),
     Output('tree_items_container','children',allow_duplicate=True) ],
    [Input('modal_submit', 'n_clicks'), Input('modal_cancel', 'n_clicks'), Input('current_datadicc-store','data')], 
    [State('modal_title', 'children'),State('options-checklist','value'),State('input', 'checked'),State('ulist_variable_choices-store','data'),State('multilist_variable_choices-store','data')], 
    
    prevent_initial_call=True
)
def on_modal_button_click(submit_n_clicks, cancel_n_clicks,current_datadicc_saved,question,checked_options,checked,ulist_variable_choices_saved,multilist_variable_choices_saved):

    dict1 = json.loads(ulist_variable_choices_saved)
    dict2 = json.loads(multilist_variable_choices_saved)

    ctx = callback_context
    current_datadicc=pd.read_json(current_datadicc_saved, orient='split')

    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'modal_submit':

        #return False, f"Processed value: {question.split('[')[1][:-1]}"  # Closes modal and updates output
        variable_submited = question.split('[')[1][:-1]
        modified_list.append(variable_submited)
        ulist_variables = [i[0] for i in ulist_variable_choices]
        multilist_variables = [i[0] for i in multilist_variable_choices]
        if (variable_submited in ulist_variables) | (variable_submited in multilist_variables) :
            list_options_checked=[]
            for lo in checked_options:
                list_options_checked.append(lo.split('_'))

            list_options_checked=pd.DataFrame(data=list_options_checked,columns=['cod','Option'])

            new_submited_options=[]
            new_submited_line=[]
            position=0
            for var_select in dict1:
                if (var_select[0]==variable_submited):
                    select_answer_options=''
                    NOT_select_answer_options=''
                    for option_var_select in (var_select[1]):
                        if (option_var_select[1] in (list(list_options_checked['Option']))):
                            new_submited_options.append([option_var_select[0],option_var_select[1],1])
                            select_answer_options+=str(option_var_select[0])+', ' +str(option_var_select[1]) +' | '
                        else:
                            new_submited_options.append([option_var_select[0],option_var_select[1],0])
                            NOT_select_answer_options+=str(option_var_select[0])+', ' +str(option_var_select[1]) +' | '
                    new_submited_line.append([var_select,new_submited_options])
                    dict1[position][1]=new_submited_line[0][1]
                    #current_datadicc['Answer Options'].loc[current_datadicc['Variable']==variable_submited].iloc[0]=select_answer_options+'88, Other'
                    current_datadicc.loc[current_datadicc['Variable'] == variable_submited, 'Answer Options'] = select_answer_options + '88, Other'
                    if  variable_submited+'_otherl2' in list(current_datadicc['Variable']):
                        current_datadicc.loc[current_datadicc['Variable'] == variable_submited+'_otherl2', 'Answer Options'] = NOT_select_answer_options + '88, Other'

                position+=1
            ulist_variable_choicesSubmit=dict1


            new_submited_options_multi_check=[]
            new_submited_line_multi_check=[]
            position_multi_check=0
            for var_select_multi_check in dict2:
                if (var_select_multi_check[0]==variable_submited):
                    select_answer_options_multi_check=''
                    NOT_select_answer_options_multi_check=''
                    for option_var_select_multi_check in (var_select_multi_check[1]):
                        if (option_var_select_multi_check[1] in (list(list_options_checked['Option']))):
                            new_submited_options_multi_check.append([option_var_select_multi_check[0],option_var_select_multi_check[1],1])
                            select_answer_options_multi_check+=str(option_var_select_multi_check[0])+', ' +str(option_var_select_multi_check[1]) +' | '
                        else:
                            new_submited_options_multi_check.append([option_var_select_multi_check[0],option_var_select_multi_check[1],0])
                            NOT_select_answer_options_multi_check+=str(option_var_select_multi_check[0])+', ' +str(option_var_select_multi_check[1]) +' | '
                    new_submited_line_multi_check.append([var_select_multi_check,new_submited_options_multi_check])
                    dict2[position_multi_check][1]=new_submited_line_multi_check[0][1]
                    #current_datadicc['Answer Options'].loc[current_datadicc['Variable']==variable_submited].iloc[0]=select_answer_options+'88, Other'
                    current_datadicc.loc[current_datadicc['Variable'] == variable_submited, 'Answer Options'] = select_answer_options_multi_check + '88, Other'
                    if  variable_submited+'_otherl2' in list(current_datadicc['Variable']):
                        current_datadicc.loc[current_datadicc['Variable'] == variable_submited+'_otherl2', 'Answer Options'] = NOT_select_answer_options_multi_check + '88, Other'                    
                position_multi_check+=1
            multilist_variable_choicesSubmit=dict2



            #User List content Transformation
            #arch_ulistSubmit,ulist_variable_choicesSubmit=arch.getUserListContent(current_datadicc,currentVersion,modified_list,list_options_checked,variable_submited)
            #Este ulist_variable_choicesSubmit multilist_variable_choicesSubmit
            #current_datadicc=arch.addTransformedRows(current_datadicc,arch_ulistSubmit,arch.getVariableOrder(current_datadicc))

            #arch_multilistSubmit,multilist_variable_choicesSubmit=arch.getMultuListContent(current_datadicc,currentVersion,list_options_checked,variable_submited)
            #current_datadicc=arch.addTransformedRows(current_datadicc,arch_multilistSubmit,arch.getVariableOrder(current_datadicc))

            print(list_options_checked)
            checked.append(variable_submited)
            tree_items = html.Div(
                dash_treeview_antd.TreeView(
                    id='input',
                    multiple=False,
                    checkable=True,
                    checked= current_datadicc['Variable'].loc[current_datadicc['Variable'].isin(checked)],
                    expanded=current_datadicc['Variable'].loc[current_datadicc['Variable'].isin(checked)],
                    data=tree_items_data),id='tree_items_container',
                style={
                    'overflow-y': 'auto',  # Vertical scrollbar when needed
                    'height': '75vh',     # Fixed height
                    'width': '100%' ,       # Fixed width, or you can specify a value in px
                    'white-space': 'normal',  # Allow text to wrap
                    'overflow-x': 'hidden',     # Hide overflowed content
                    'text-overflow': 'ellipsis',  # Indicate more content with an ellipsis
                    #'display': visibility_data['display']
                    #'display': 'none'
                }
            )            
            return False, current_datadicc.to_json(date_format='iso', orient='split'),json.dumps(ulist_variable_choicesSubmit), json.dumps(multilist_variable_choicesSubmit),tree_items
        else:
            return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
    

    elif button_id == 'modal_cancel':
        # Just close the modal without doing anything else
        return False, dash.no_update, dash.no_update, dash.no_update,dash.no_update

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update,dash.no_update

@app.callback(
    [Output("loading-output-1", "children"),
     Output("download-dataframe-csv", "data"),
     Output("download-compGuide-pdf", "data"),
     Output("download-projectxml-pdf","data"),
     Output("download-paperlike-pdf","data")]  ,
    [Input('crf_generate', 'n_clicks'),Input('selected_data-store','data')],  
    State('crf_name', 'value'),
    prevent_initial_call=True
)
def on_generate_click(n_clicks,json_data, crf_name):

    #global selected_variables

    ctx = dash.callback_context
    # Check which input triggered the callback
    if not ctx.triggered:
        trigger_id = 'No clicks yet'
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if n_clicks is None:
        # Return empty or initial state if button hasn't been clicked
        return "", None, None, None,None
    # Return the text from 'crf_name' input field
    if json_data is None:
        return 'No data available',None, None, None,None
    if trigger_id == 'crf_generate':
        selected_variables_fromData= pd.read_json(json_data, orient='split')
    
    
        date=datetime.today().strftime('%Y-%m-%d')
        
        #paperCRF.generate_completionguide(selected_variables_fromData,path+crf_name+'_Completion_Guide_'+date+'.pdf',currentVersion, crf_name)
        
        datadiccDisease=arch.generateCRF(selected_variables_fromData,crf_name)
    
        print('#############################')
        print('#############################')
        print('#############################')
        print('#############################')
        print('#############################')
        print('#############################')
        for cosa in datadiccDisease.columns:
            print(cosa)
        
        #datadiccDisease.to_csv(path+crf_name+'_'+date+'.csv',index=False, encoding='utf8')
        pdf_crf=paperCRF.generate_pdf(datadiccDisease,currentVersion, crf_name)
        
                   
        '''# Create a PDF to Word converter
        cv = Converter('dataDiccs/'+crf_name+'_'+date+'.pdf')
    
        # Convert all pages of the PDF to a Word document
        cv.convert('dataDiccs/'+crf_name+'_'+date+'.docx')
    
        # Close the converter
        cv.close()'''
    
        df=datadiccDisease.copy()
        output = io.BytesIO()
        df.to_csv(output, index=False, encoding='utf8')
        output.seek(0)
        pdf_data = paperCRF.generate_completionguide(selected_variables_fromData, currentVersion, crf_name)
    
        
        file_name = 'ISARIC Clinical Characterisation Setup.xml'  # Set the desired download name here
        file_path = 'BRIDGE/assets/config_files/'+file_name
        #file_path = 'assets/config_files/'+file_name# Change this for deploy
        # Open the XML file and read its content
        with open(file_path, 'rb') as file:  # 'rb' mode to read as binary
            content = file.read()
    
    
        return "",dcc.send_bytes(output.getvalue(), crf_name+'_DataDictionary_'+date+'.csv'),\
            dcc.send_bytes(pdf_data, crf_name+'_Completion_Guide_'+date+'.pdf'),\
                dcc.send_bytes(content, file_name),dcc.send_bytes(pdf_crf, crf_name+'_paperlike_'+date+'.pdf')
    else:
        return "", None, None, None,None


@app.callback(
    Output('row2_options', 'children'),
    [Input('row1_radios', 'value')]
)
def update_row2_options(selected_value):
    if selected_value == "Characterisation":
        options = [
            {"label": "What are the case defining features?", "value": "CD_Features"},
            {"label": "What is the spectrum of clinical features in this disease?", "value": "Spectrum_Clinical_Features"},
        ]
    elif selected_value == "Risk/Prognosis":
        options = [
            {"label": "What are the clinical features occurring in those with patient outcome?", "value": "Clinical_Features_Patient_Outcome"},
            {"label": "What are the risk factors for patient outcome?", "value": "Risk_Factors_Patient_Outcome"},
        ]
    elif selected_value == "Clinical Management":
        options = [
            {"label": "What treatment/intervention are received by those with patient outcome?", "value": "Treatment_Intervention_Patient_Outcome"},
            {"label":"What proportion of patients with clinical feature are receiving treatment/intervention?", "value": "Clinical_Features_Treatment_Intervention"},
            {"label":"What proportion of patient outcome recieved treatment/intervention?", "value": "Patient_Outcome_Treatment_Intervention"},
            {"label":"What duration of treatment/intervention is being used in patient outcome?", "value": "Duration_Treatment_Intervention_Patient_Outcome"},

        ]
    else:
        options = []


    question_options=html.Div(
            [
                dbc.RadioItems(
                    id="row2_radios",
                    className="btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-primary",
                    labelCheckedClassName="active",
                    options=options,
                    #value=options[0]['value'] if options else None,
                ),
                html.Div(id="rq_questions_div"),
            ],
            className="radio-group",
        )

    return question_options





def init_grid(dataframe,id_grid):
    # Define the new column definitions
    columnDefs = [
        #{'field': 'Form', "checkboxSelection": True},
        {'field': 'Form'},
        {'field': 'Section'},
        {'field': 'Question'},
    ]

    # Convert the DataFrame to a dictionary in a format suitable for Dash AgGrid
    # Use `records` to get a list of dict, each representing a row in the DataFrame
    rowData = dataframe.to_dict('records')

    return dag.AgGrid(
        id=id_grid,
        rowData=rowData,
        columnDefs=columnDefs,
        defaultColDef={'resizable': True},
        columnSize="sizeToFit",
        dashGridOptions={
            "rowDragManaged": True,
            "rowDragEntireRow": True,
            "rowDragMultiRow": True,
            "rowSelection": "multiple",
            "suppressMoveWhenRowDragging": True
        },
        # Since the rowClassRules were based on color, you might want to remove or modify this part
        # You can define new rules based on 'form', 'section', or 'label' if needed
        rowClassRules={},
        getRowId="params.data.id",  # Ensure your DataFrame includes an 'id' column for this to work
    )


def createFeatureSelection(id_so, title, feat_options):
    # This function creates a feature selection component with dynamic IDs.
    return html.Div([
        html.Div(id={'type': 'feature_title', 'index': id_so}, children=title, style={"cursor": "pointer"}),
        dbc.Fade(
            html.Div([
                dcc.Checklist(
                    id={'type': 'feature_selectall', 'index': id_so},
                    options=[{'label': 'Select all', 'value': 'all'}],
                    value=['all']
                ),
                dcc.Checklist(
                    id={'type': 'feature_checkboxes', 'index': id_so},
                    options=feat_options,
                    value=[option['value'] for option in feat_options],
                    style={'overflowY': 'auto', 'maxHeight': '100px'}
                )
            ]),
            id={'type': 'feature_fade', 'index': id_so},
            is_in=False,
            appear=False,
        )
    ])

def feature_text(current_datadicc,selected_variables,features):
        selected_variables=selected_variables.copy()
        selected_variables=selected_variables.loc[selected_variables['Variable'].isin(features['Variable'])]
        if (selected_variables is None):
            return ''
        else:
            text = ''
            selected_features = current_datadicc.loc[current_datadicc['Variable'].isin(selected_variables['Variable'])]
            for sec in selected_features['Section'].unique():
                # Add section title in bold and a new line
                text += f"\n\n**{sec}**\n"
                for label in selected_features['Question'].loc[selected_features['Section'] == sec]:
                    # Add each label as a bullet point with a new line
                    text += f"  - {label}\n"  
            return text      
def feature_accordion(features,id_feat,selected):
    feat_accordion_items = []
    cont=0

    for sec in features['Section'].unique():
        if  selected is None:
            selection=[]  
        else:
            selection=selected['Variable'].loc[selected['Section']==sec]      
        # For each group, create a checklist
        checklist = dbc.Checklist(
            #options=[{"label": value, "value": value} for value in features['Question'].loc[features['Section']==sec]],
            options=[{"label": row['Question'], "value": row['Variable']} for _, row in features.loc[features['Section'] == sec].iterrows()],
            value=selection,
            id=id_feat+'_'+f'checklist-{str(cont)}',
            switch=True,
        )
        cont+=1
        # Create an accordion item with the checklist
        feat_accordion_items.append(
            dbc.AccordionItem(
                title=sec.split(":")[0],
                #children=checklist
                children=html.Div(checklist, style={'height': '100px', 'overflowY': 'auto'})
            )
        )
    return dbc.Accordion(feat_accordion_items)

def paralel_elements(features,id_feat,current_datadicc,selected_variables):


    text=feature_text(current_datadicc,selected_variables,features)
    accord=feature_accordion(features,id_feat,selected=selected_variables)
    
    pararel_features=html.Div([
        # First column with the title and the Available Columns table
        html.Div([
            html.H5('Available Features', style={'textAlign': 'center'}),
            accord
            
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        
        # Second column with the buttons
        html.Div( style={'width': '1%', 'display': 'inline-block', 'textAlign': 'center'}),
        
        # Third column with the title and the Display Columns table
        html.Div([
            html.H5('Selected Features', style={'textAlign': 'center'}),
                dcc.Markdown(id=id_feat+'_text-content', children=text, style={'height': '300px', 'overflowY': 'scroll', 'border': '1px solid #ddd', 'padding': '10px', 'color': 'black'}),
    
        ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'}),
    ], style={'width': '100%', 'display': 'flex'})   
    return pararel_features



@app.callback(
    [Output('row3_tabs', 'children'),Output('selected_question','children')],
    [Input('row2_radios', 'value')],
    [State('selected_data-store','data')],
)
def update_row3_content(selected_value,json_data):
    caseDefiningVariables=arch.getResearchQuestionTypes(current_datadicc)

    research_question_elements=pd.read_csv('BRIDGE/assets/config_files/researchQuestions.csv')#change for deploy
    #research_question_elements=pd.read_csv('assets/config_files/researchQuestions.csv') 

    group_elements=[]
    for tq_opGroup in research_question_elements['Option Group'].unique():
        all_elements=[]
        for rq_element in research_question_elements['Relavent variable names on ARC'].loc[research_question_elements['Option Group']==tq_opGroup]:
            if type(rq_element)==str:
                for rq_aux in rq_element.split(';'):
                    #print(rq_element)
                    all_elements.append(rq_aux.strip())
        group_elements.append([tq_opGroup,all_elements])

    group_elements=pd.DataFrame(data=group_elements,columns=['Group Option','Variables'])


    if json_data is None:
        data = {
            'id': [1, 2, 3],
            'Form': ['Form A', 'Form B', 'Form C'],
            'Section': ['Section 1', 'Section 2', 'Section 3'],
            'Label': ['Label 1', 'Label 2', 'Label 3'],
        }
        selected_variables_fromData = None
        #accord=feature_accordion(caseDefiningVariables,'clinic_feat')
        #text=''
    else:
        selected_variables_fromData= pd.read_json(json_data, orient='split')
        selected_variables_fromData=selected_variables_fromData[['Variable','Form','Section','Question']]
        #selected_variables_caseDefining=selected_variables_fromData.loc[selected_variables_fromData['Variable'].isin(caseDefiningVariables['Variable'])]
        #accord=feature_accordion(caseDefiningVariables,'clinic_feat',selected=selected_variables_caseDefining)
        #text=feature_text(current_datadicc,selected_variables_caseDefining)    

    #grid_display = init_grid(pd.DataFrame(data),'selected_features_grid')
    tabs_content = []
    selected_question=''


    

    #feature_selector=createFeatureSelection('feature_selector',"Case Defining Features",caseDefiningVariables['Question'])
    if selected_value == "CD_Features":
        OptionGroup=["Case Defining Features"]
        #caseDefiningVariables = current_datadicc.loc[current_datadicc['Variable']==]
        caseDefiningVariables=group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_features=paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(list(caseDefiningVariables.iloc[0]))],'case_feat',current_datadicc,selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Features", children=[html.P(" "),paralel_elements_features]))
        selected_question="What are the [case defining features]?"
        
    elif selected_value == "Spectrum_Clinical_Features":
        OptionGroup=["Clinical Features"] 
        clinicalVariables=group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_features=paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(list(clinicalVariables.iloc[0]))],'clinic_feat',current_datadicc,selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Clinical Features", children=[html.P(" "),paralel_elements_features]))
        selected_question="What is the spectrum of [clinical features] in this disease?"
               
    elif selected_value == "Clinical_Features_Patient_Outcome":
        OptionGroup=["Clinical Features"] 
        clinicalVariables=group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_features=paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(list(clinicalVariables.iloc[0]))],'clinic_feat',current_datadicc,selected_variables_fromData)
        OptionGroup=["Patient Outcome"] 
        outcomeVariables=group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes=paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(list(outcomeVariables.iloc[0]))],'outcome',current_datadicc,selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Clinical Features", children=[html.P(" "),paralel_elements_features]))
        tabs_content.append(dbc.Tab(label="Patient Outcomes", children=[html.P(" "),paralel_elements_outcomes]))        
        selected_question="What are the [clinical features] occuring in those with [patient outcome]?"
        
    elif selected_value == "Risk_Factors_Patient_Outcome":
        OptionGroup=["Risk Factors: Demographics",
                    "Risk Factors: Socioeconomic","Risk Factors: Comorbidities"]    
        riskVariables=group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        allRiskVarr=[]
        for rv in riskVariables:
            allRiskVarr+=list(rv)
        paralel_elements_risk=paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(allRiskVarr)],'risk',current_datadicc,selected_variables_fromData)
        OptionGroup=["Patient Outcome"] 
        outcomeVariables=group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes=paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(list(outcomeVariables.iloc[0]))],'outcome',current_datadicc,selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Risk Factors", children=[html.P(" "),paralel_elements_risk]))
        tabs_content.append(dbc.Tab(label="Patient Outcomes", children=[html.P(" "),paralel_elements_outcomes]))   
        selected_question="What are the [risk factors] for [patient outcome]?"
     
    elif selected_value=="Treatment_Intervention_Patient_Outcome":

        OptionGroup=["Treatment/Intevention"] 
        TreatmentsVariables=group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_treatments=paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(list(TreatmentsVariables.iloc[0]))],'treatment',current_datadicc,selected_variables_fromData)
        OptionGroup=["Patient Outcome"] 
        outcomeVariables=group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes=paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(list(outcomeVariables.iloc[0]))],'outcome',current_datadicc,selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Treatments/Interventions", children=[html.P(" "),paralel_elements_treatments]))
        tabs_content.append(dbc.Tab(label="Patient Outcomes", children=[html.P(" "),paralel_elements_outcomes]))            


        selected_question="What [treatment/intervention] are received by those with  [patient outcome]?"                
    elif selected_value=="Clinical_Features_Treatment_Intervention":

        selected_question="What proportion of patients with [clinical feature] are receiving [treatment/intervention]?"  
         
        OptionGroup=["Clinical Features"] 
        clinicalVariables=group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_features=paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(list(clinicalVariables.iloc[0]))],'clinic_feat',current_datadicc,selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Clinical Features", children=[html.P(" "),paralel_elements_features]))
        OptionGroup=["Treatment/Intevention"] 
        TreatmentsVariables=group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_treatments=paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(list(TreatmentsVariables.iloc[0]))],'treatment',current_datadicc,selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Treatments/Interventions", children=[html.P(" "),paralel_elements_treatments]))

    elif selected_value=="Patient_Outcome_Treatment_Intervention":
        OptionGroup=["Treatment/Intevention"] 
        TreatmentsVariables=group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_treatments=paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(list(TreatmentsVariables.iloc[0]))],'treatment',current_datadicc,selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Treatments/Interventions", children=[html.P(" "),paralel_elements_treatments]))

        OptionGroup=["Patient Outcome"] 
        outcomeVariables=group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes=paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(list(outcomeVariables.iloc[0]))],'outcome',current_datadicc,selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Patient Outcomes", children=[html.P(" "),paralel_elements_outcomes]))        

        selected_question="What proportion of [patient outcome] recieved [treatment/intervention]?"      
    elif selected_value=="Duration_Treatment_Intervention_Patient_Outcome":
        OptionGroup=["Treatment/Intevention"] 
        TreatmentsVariables=group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_treatments=paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(list(TreatmentsVariables.iloc[0]))],'treatment',current_datadicc,selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Treatments/Interventions", children=[html.P(" "),paralel_elements_treatments]))

        OptionGroup=["Patient Outcome"] 
        outcomeVariables=group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes=paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(list(outcomeVariables.iloc[0]))],'outcome',current_datadicc,selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Patient Outcomes", children=[html.P(" "),paralel_elements_outcomes]))  
        selected_question="What duration of [treatment/intervention] is being used in [patient outcome]?"  

    
    parts = re.split(r'(\[.*?\])', selected_question)  # Split by text inside brackets, keeping the brackets

    styled_parts = []
    for part in parts:
        if part.startswith('[') and part.endswith(']'):
            # Text inside brackets, apply red color
            styled_parts.append(html.Span(part, style={'color': '#BA0225'}))
        else:
            # Regular text, no additional styling needed
            styled_parts.append(html.Span(part))
    # Add more conditions as necessary for other options

    return tabs_content,styled_parts



@app.callback(
    Output('case_feat_text-content', 'children'),
    #[Input('clinic_feat_checklist-0', 'value')],
    [Input(f'case_feat_checklist-{key}', 'value') for key in range(4)],
    #[State('selected_data-store','data')],
    prevent_initial_call=True
)
def update_Researh_questions_grid(*args):
    checked_values = args
    text = ''
    all_checked=[]
    for cck_v in checked_values:
        for element in cck_v:
            all_checked.append(element)
    selected_features = current_datadicc.loc[current_datadicc['Variable'].isin(all_checked)]
    for sec in selected_features['Section'].unique():
        # Add section title in bold and a new line
        text += f"\n\n**{sec}**\n"
        for label in selected_features['Question'].loc[selected_features['Section'] == sec]:
            # Add each label as a bullet point with a new line
            text += f"  - {label}\n"
    return text



@app.callback(
    Output('clinic_feat_text-content', 'children'),
    [Input(f'clinic_feat_checklist-{key}', 'value') for key in range(8)],
    prevent_initial_call=True
)
def update_ClenicalFeat_questions_grid(*args):
    checked_values = args
    text = ''
    all_checked=[]
    for cck_v in checked_values:
        for element in cck_v:
            all_checked.append(element)
    selected_features = current_datadicc.loc[current_datadicc['Variable'].isin(all_checked)]
    for sec in selected_features['Section'].unique():
        # Add section title in bold and a new line
        text += f"\n\n**{sec}**\n"
        for label in selected_features['Question'].loc[selected_features['Section'] == sec]:
            # Add each label as a bullet point with a new line
            text += f"  - {label}\n"
    return text


@app.callback(
    Output('outcome_text-content', 'children'),
    [Input(f'outcome_checklist-{key}', 'value') for key in range(4)],
    prevent_initial_call=True
)
def update_outcome_questions_grid(*args):
    checked_values = args
    text = ''
    all_checked=[]
    for cck_v in checked_values:
        for element in cck_v:
            all_checked.append(element)
    selected_features = current_datadicc.loc[current_datadicc['Variable'].isin(all_checked)]
    for sec in selected_features['Section'].unique():
        # Add section title in bold and a new line
        text += f"\n\n**{sec}**\n"
        for label in selected_features['Question'].loc[selected_features['Section'] == sec]:
            # Add each label as a bullet point with a new line
            text += f"  - {label}\n"
    return text

@app.callback(
    Output('risk_text-content', 'children'),
    [Input(f'risk_checklist-{key}', 'value') for key in range(7)],
    prevent_initial_call=True
)
def update_risk_questions_grid(*args):
    checked_values = args
    text = ''
    all_checked=[]
    for cck_v in checked_values:
        for element in cck_v:
            all_checked.append(element)
    selected_features = current_datadicc.loc[current_datadicc['Variable'].isin(all_checked)]
    for sec in selected_features['Section'].unique():
        # Add section title in bold and a new line
        text += f"\n\n**{sec}**\n"
        for label in selected_features['Question'].loc[selected_features['Section'] == sec]:
            # Add each label as a bullet point with a new line
            text += f"  - {label}\n"
    return text


@app.callback(
    Output('treatment_text-content', 'children'),
    [Input(f'treatment_checklist-{key}', 'value') for key in range(2)],
    prevent_initial_call=True
)
def update_risk_questions_grid(*args):
    checked_values = args
    text = ''
    all_checked=[]
    for cck_v in checked_values:
        for element in cck_v:
            all_checked.append(element)
    selected_features = current_datadicc.loc[current_datadicc['Variable'].isin(all_checked)]
    for sec in selected_features['Section'].unique():
        # Add section title in bold and a new line
        text += f"\n\n**{sec}**\n"
        for label in selected_features['Question'].loc[selected_features['Section'] == sec]:
            # Add each label as a bullet point with a new line
            text += f"  - {label}\n"
    return text

@app.callback(
    [Output('rq_modal', 'is_open',allow_duplicate=True), Output('row3_tabs', 'children',allow_duplicate=True),
     Output('row1_radios','value'),Output('row2_radios', 'value')],
    [Input('rq_modal_submit', 'n_clicks'), Input('rq_modal_cancel', 'n_clicks')],
    prevent_initial_call=True
)
def on_rq_modal_button_click(submit_n_clicks, cancel_n_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'rq_modal_submit' :
        return False, [],[],[]
    elif button_id == 'rq_modal_cancel':
        # Close the modal and clear its content
        return False, [],[],[]
    else:
        return dash.no_update

if __name__ == "__main__":
    #app.run_server(debug=True)
    app.run_server(debug=True, host='0.0.0.0', port='8080')#change for deploy