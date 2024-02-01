import dash
from dash import html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

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
                    html.P("Your completion guide text here", id='completion-guide-text')
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

