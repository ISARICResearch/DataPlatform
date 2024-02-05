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



app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://use.fontawesome.com/releases/v5.8.1/css/all.css'])

versions,recentVersion=arch.getARCHVersions()
currentVersion=recentVersion
current_datadicc,presets=arch.getARCH(recentVersion)
current_datadicc[['Sec', 'vari', 'mod']] = current_datadicc['Variable'].str.split('_', n=2, expand=True)
current_datadicc[['Sec_name', 'Expla']] = current_datadicc['Section'].str.split(r'[(|:]', n=1, expand=True)
tree_items_data=arch.getTreeItems(current_datadicc,recentVersion)

#List content Transformation
arch_lists,list_variable_choices=arch.getListContent(current_datadicc,currentVersion)
current_datadicc=arch.addTransformedRows(current_datadicc,arch_lists,arch.getVariableOrder(current_datadicc))

#User List content Transformation
arch_ulist,ulist_variable_choices=arch.getUserListContent(current_datadicc,currentVersion)
current_datadicc=arch.addTransformedRows(current_datadicc,arch_ulist,arch.getVariableOrder(current_datadicc))
initial_current_datadicc =  current_datadicc.to_json(date_format='iso', orient='split')
initial_ulist_variable_choices =  json.dumps(ulist_variable_choices)

print(versions)

# Navbar
navbar = dbc.NavbarSimple(
    brand="BRIDGE - BioResearch Integrated Data tool GEnerator",
    brand_href="#",
    #color="#E00047",
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

    ],
    style={
        "position": "fixed",
        "top": "4rem",  # Height of the navbar
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
    [html.H3("Pre-sets", id="settings-text-1"),
     preset_accordion
     ],style={"padding": "2rem"}
)

preset_column = dbc.Fade(
    preset_content,
    id="presets-column",
    is_in=False,  # Initially hidden
    style={
        "position": "fixed",
        "top": "4rem",
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
                    label="ARCH Version",
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
                    {'label': 'Completion Guide', 'value': 'completion_guide'},
                    {'label': 'REDCap Data Dictionary', 'value': 'redcap_csv'},
                    {'label': 'ISARIC Clinical Characterization XML', 'value': 'redcap_xml'},
                    # Add more files as needed
                ],
                value=['file1'],  # Default selected values
                inline=True
            )
        ], style={'margin-bottom': '20px'}),

        # Paperlike Files checkboxes
        html.Div([
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
        ]),
    ],
    style={"padding": "2rem"}
)

settings_column = dbc.Fade(
    settings_content,
    id="settings-column",
    is_in=False,  # Initially hidden
    style={
        "position": "fixed",
        "top": "4rem",
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
        'height': '75vh',     # Fixed height
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
        "top": "4rem",
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
                        )
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
        dcc.Store(id='current_datadicc-store',data=initial_current_datadicc),
        dcc.Store(id='ulist_variable_choices-store',data=initial_ulist_variable_choices),
        navbar,
        sidebar,
        settings_column,
        preset_column,
        tree_column,
        main_content,
        bridge_modals.variableInformation_modal(),
        dcc.Loading(id="loading-1",
                    type="default",
                    children=html.Div(id="loading-output-1")
    )
    ]
)

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
            if row['Type'] in ['radio', 'dropdown', 'checkbox','list','user_list']:
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
              [State('ulist_variable_choices-store','data'),State('modal', 'is_open')])
def display_selected(selected,ulist_variable_choices_saved,is_open):
    datatatata=json.loads(ulist_variable_choices_saved)
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
    Output('tree_items_container','children'),
    [Input(f'checklist-{key}', 'value') for key in grouped_presets.keys()],
    #[State('visibility-store', 'data')],
    prevent_initial_call=True
)
def update_output(*args):
    checked_values = args[:-1]
    #visibility_data = args[-1]    
    formatted_output = []
    for key, values in zip(grouped_presets.keys(), checked_values):
        if values:  # Check if the list of values is not empty
            for value in values:
                formatted_output.append([key, value.replace(' ', '_')])
    checked = []
    for ps in formatted_output:
        checked_key = 'preset_' + ps[0] + '_' + ps[1]
        if checked_key in current_datadicc:
            checked = checked+list(current_datadicc['Variable'].loc[current_datadicc[checked_key]==1])
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
    return tree_items

@app.callback(
    [Output('modal', 'is_open', allow_duplicate=True), Output('current_datadicc-store','data'),Output('ulist_variable_choices-store','data') ],
    [Input('modal_submit', 'n_clicks'), Input('modal_cancel', 'n_clicks'), Input('current_datadicc-store','data')], 
    [State('modal_title', 'children'),State('options-checklist','value')], 
    prevent_initial_call=True
)
def on_modal_button_click(submit_n_clicks, cancel_n_clicks,current_datadicc_saved,question,checked_options):
    ctx = callback_context
    current_datadicc=pd.read_json(current_datadicc_saved, orient='split')

    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'modal_submit':

        #return False, f"Processed value: {question.split('[')[1][:-1]}"  # Closes modal and updates output
        variable_submited = question.split('[')[1][:-1]
        ulist_variables = [i[0] for i in ulist_variable_choices]
        if variable_submited in ulist_variables:
            list_options_checked=[]
            for lo in checked_options:
                list_options_checked.append(lo.split('_'))

            list_options_checked=pd.DataFrame(data=list_options_checked,columns=['cod','Option'])

            #User List content Transformation
            arch_ulistSubmit,ulist_variable_choicesSubmit=arch.getUserListContent(current_datadicc,currentVersion,list_options_checked,variable_submited)
            current_datadicc=arch.addTransformedRows(current_datadicc,arch_ulistSubmit,arch.getVariableOrder(current_datadicc))

            print(list_options_checked)
            return False, current_datadicc.to_json(date_format='iso', orient='split'),json.dumps(ulist_variable_choicesSubmit)
        else:
            return False, dash.no_update, dash.no_update

    elif button_id == 'modal_cancel':
        # Just close the modal without doing anything else
        return False, dash.no_update, dash.no_update

    return dash.no_update

@app.callback(
    Output("loading-output-1", "children"),  
    [Input('crf_generate', 'n_clicks'),Input('selected_data-store','data')],  
    State('crf_name', 'value'),
    prevent_initial_call=True
)
def on_generate_click(n_clicks,json_data, crf_name):

    #global selected_variables
    
    if n_clicks is None:
        # Return empty or initial state if button hasn't been clicked
        return ""
    # Return the text from 'crf_name' input field
    if json_data is None:
        return 'No data available'
    selected_variables_fromData= pd.read_json(json_data, orient='split')

    path='C:/Users/egarcia/OneDrive - Nexus365/Projects/CBCG/Outputs/'
    date=datetime.today().strftime('%Y-%m-%d')
    '''
    paperCRF.generate_completionguide(selected_variables_fromData,path+crf_name+'_Completion_Guide_'+date+'.pdf',currentVersion, crf_name)
    datadiccDisease=arch.generateCRF(selected_variables_fromData,crf_name)
    datadiccDisease.to_csv(path+crf_name+'_'+date+'.csv',index=False, encoding='utf8')
    paperCRF.generate_pdf(datadiccDisease,path+crf_name+'_'+date+'.pdf',currentVersion, crf_name)
    '''
               
    '''# Create a PDF to Word converter
    cv = Converter('dataDiccs/'+crf_name+'_'+date+'.pdf')

    # Convert all pages of the PDF to a Word document
    cv.convert('dataDiccs/'+crf_name+'_'+date+'.docx')

    # Close the converter
    cv.close()'''



    return ""

if __name__ == "__main__":
    app.run_server(debug=True)