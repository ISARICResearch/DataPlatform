import dash
from dash import html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd





def researchQuestions_modal():
    questions_themes_group = html.Div(
        [
            dbc.RadioItems(
                id="row1_radios",
                className="btn-group",
                inputClassName="btn-check",
                labelClassName="btn btn-outline-primary",
                labelCheckedClassName="active",
                options=[
                    {"label": "Characterisation", "value": "Characterisation"},
                    {"label": "Risk/Prognosis", "value": "Risk/Prognosis"},
                    {"label": "Clinical Management", "value": "Clinical Management"},
                ],
                #value="Characterisation",
            ),
            html.Div(id="rq_themes_div"),
        ],
        className="radio-group",
    )    

    tabs_content = []
    
    tabs_content.append(dbc.Tab(id='tab_features',label="Features", children=[html.P("Content for Clinical Features")]))
    tabs_content.append(dbc.Tab(id='tab_clinifeat',label="Clinical Features", children=[html.P("Content for Features")]))
    tabs_content.append(dbc.Tab(id='tab_riskfac',label="Risk Factors", children=[html.P("Content for Risk Factors")]))
    tabs_content.append(dbc.Tab(id='tab_treatment',label="Treatments/Interventions", children=[html.P("Content for Treatments/Intervention")]))
    tabs_content.append(dbc.Tab(id='tab_outcomes',label="Patient Outcome", children=[html.P("Content for Patient Outcome")]))
    

    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Research Question", id='rq_modal_title')),
            dbc.ModalBody(
                [
                    dbc.Row(
                        dbc.Col(
                            questions_themes_group,
                            width=6,
                        ),
                    justify="center"
                    ),
                    dbc.Row(dbc.Col(id="row2_options",width=10),justify="center"),  
                    dbc.Row(
                        [
                            dbc.Col(html.H4("Your Selection:",id='selected_question', className="text-center mt-4"), width=12),
                            dbc.Col(dbc.Tabs(id="row3_tabs"), width=12, className="mt-3")
                            
                        ],
                        justify="center"
                    ),
                ]
            ),
            dbc.ModalFooter(
                html.Div(
                    [dbc.Button("Submit", id='rq_modal_submit', className="me-1", n_clicks=0),
                     dbc.Button("Cancel", id='rq_modal_cancel', className="me-1", n_clicks=0)]
                )
            ),
        ],
        id='rq_modal',
        is_open=False,
        size="xl"
    )

def variableInformation_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Row Details", id='modal_title')),
            dbc.ModalBody(
                [
                    html.H5("Definition:"), 
                    html.P("Your definition text here", id='definition-text'),
                    html.H5("Options:"), 
                    dbc.Checklist(
                        options=[
                            {"label": "Option 1", "value": 1},
                            {"label": "Option 2", "value": 2},
                        ],
                        id='options-checklist',
                        value=[1],
                        style={"padding": "20px"}
                    ),
                    dbc.ListGroup(
                        [
                            dbc.ListGroupItem("Item 1"),
                            dbc.ListGroupItem("Item 2"),
                        ],
                        id='options-list-group',
                        style={"display": "none"} 
                    ),

                    html.H5("Completion Guide:"), 
                    html.P("Completion guide text here", id='completion-guide-text')
                ]
            ),
            dbc.ModalFooter(
                html.Div(
                    [dbc.Button("Submit", id='modal_submit', className="me-1", n_clicks=0),
                    dbc.Button("Cancel", id='modal_cancel', className="me-1", n_clicks=0)]
                 )
            ),
        ],
        id='modal',
        is_open=False,
        size="xl"
    )

