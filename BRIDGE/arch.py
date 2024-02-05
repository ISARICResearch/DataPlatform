from github import Github
import pandas as pd
import requests
import re
import numpy as np
from datetime import datetime

#ARC - Analysis and Research Compendium 



def getARCHVersions():

    # GitHub API URL for the contents of the repository
    repo_name = "ISARICResearch/DataPlatform"
    path = "ARCH"
    url = f"https://api.github.com/repos/{repo_name}/contents/{path}"

    # Make the request
    response = requests.get(url)
    folder_names=[]
    # Check if the request was successful
    if response.status_code == 200:
        contents = response.json()
        folder_names = [item['name'] for item in contents if item['type'] == 'dir']
        
    else:
        print("Failed to retrieve data:", response.status_code)
    
    versions=set(folder_names)
    parsed_versions = [tuple(map(int, version.split('ARCH')[1].split('.'))) for version in versions]
    most_recent_version = max(parsed_versions)
    most_recent_version_str = 'ARCH' + '.'.join(map(str, most_recent_version))
    #print(most_recent_version_str)    
    return list(versions),most_recent_version_str

def getVariableOrder(current_datadicc):
    current_datadicc['Sec_vari']=current_datadicc['Sec']+'_'+current_datadicc['vari']
    order=current_datadicc[['Sec_vari']]
    order=order.drop_duplicates().reset_index()
    return list(order['Sec_vari'])


def getARCH(version):   
    #sv_selected=version
    #v_selected=sv_selected.split('.')[0].replace(' ','%20')
    #sv_selected=sv_selected.replace(' ','%20')
    root='https://raw.githubusercontent.com/ISARICResearch/DataPlatform/main/ARCH/'
    datadicc_path = root+version+'/'+'ARCH.csv'

    try:
        datadicc = pd.read_csv(datadicc_path, encoding='Latin1')
        dependencies=getDependencies(datadicc) 
        datadicc = pd.merge(datadicc,dependencies[['Variable','Dependencies']],on = 'Variable')
        
        # Find preset columns
        preset_columns = [col for col in datadicc.columns if "preset_" in col]
        presets = []
        # Iterate through each string in the list
        for col in preset_columns:
            parts = col.split('_')[1:]  
            if len(parts) > 2:
                parts[1] = ' '.join(parts[1:])
                del parts[2:]
            presets.append(parts)


        return datadicc,presets
    except Exception as e:
        print(f"Failed to fetch remote file due to: {e}. Attempting to read from local file.")
    

def getDependencies(datadicc):
        mandatory=['subjid']
    
        #datadicc=pd.read_csv('C:/Users/egarcia/Documents/Projects/REDCap/ModifyREDCapProgramatically/data_dicc.csv')
        #dependencies=datadicc[['Variable / Field Name', 'Branching Logic (Show field only if...)']]
        dependencies=datadicc[['Variable', 'Skip Logic']]
        field_dependencies=[]
        for s in dependencies[ 'Skip Logic']:
            cont=0
            variable_dependencies=[]
            if type(s)!=float:       
                for i in s.split('['):
                    variable=(i[:i.find(']')])
                    if '(' in variable:
                        variable=(variable[:variable.find('(')])
                    if cont!=0:
                        variable_dependencies.append(variable)
                    cont+=1
            field_dependencies.append(variable_dependencies)            
        dependencies['Dependencies']=field_dependencies
        for i in dependencies['Variable']:
            if 'other' in i:
                if len(dependencies['Dependencies'].loc[dependencies['Variable']==i.replace('other','')])>=1:                
                    dependencies['Dependencies'].loc[dependencies['Variable']==i.replace('other','')].iloc[0].append(i)
                    #print(dependencies['Dependencies'].loc[dependencies['Variable / Field Name']==i.replace('other','')])
            
            if 'units' in i :
                if len(dependencies['Dependencies'].loc[dependencies['Variable']==i.replace('units','')])>=1:                
                    dependencies['Dependencies'].loc[dependencies['Variable']==i.replace('units','')].iloc[0].append(i)
                    #print(dependencies['Dependencies'].loc[dependencies['Variable / Field Name']==i.replace('other','')])
                    
            
            for m in mandatory:
                dependencies['Dependencies'].loc[dependencies['Variable']==i].iloc[0].append(m)
                
        return dependencies

def getTreeItems(datadicc,version):
    version=version.replace('ICC','ARCH')
    include_not_show=['otherl3','otherl2','route','route2','site','agent','agent2','warn','warn2','warn3','units','add','type','vol','site']

    dependencies=getDependencies(datadicc) 
    datadicc = pd.merge(datadicc,dependencies[['Variable','Dependencies']],on = 'Variable')
    datadicc[['Sec', 'vari', 'mod']] = datadicc['Variable'].str.split('_', n=2, expand=True)
    #datadicc[['Sec_name', 'Expla']] = datadicc['Section'].str.split('(', n=1, expand=True)
    datadicc[['Sec_name', 'Expla']] = datadicc['Section'].str.split(r'[(|:]', n=1, expand=True)

    datadicc['select units'] = (datadicc['Question'].str.contains('(select units)', case=False, na=False))
    mask_true = datadicc['select units'] == True
    for index, row in datadicc[mask_true].iterrows():
        mask_sec_vari = (datadicc['Sec'] == row['Sec']) & (datadicc['vari'] == row['vari'])
        datadicc.loc[mask_sec_vari, 'select units'] = True 
    
    forItem=datadicc[['Form','Sec_name','vari','mod','Question','Variable','Type']].loc[~datadicc['mod'].isin(include_not_show)]
    forItem= forItem[forItem['Sec_name'].notna()]

    tree = {'title': version, 'key': 'ARCH', 'children': []}
    seen_forms = set()
    seen_sections = {}
    primary_question_keys = {}  # To keep track of primary question nodes

    for index, row in forItem.iterrows():
        form = row['Form'].upper()
        sec_name = row['Sec_name'].upper()
        vari = row['vari']
        mod = row['mod']
        question = row['Question']
        Variable_name=row['Variable']
        #question_key = f"{form}-{sec_name}-{vari}-{mod}-{question}"
        question_key = f"{Variable_name}"

        # Add form node if not already added
        if form not in seen_forms:
            form_node = {'title': form, 'key': form, 'children': []}
            tree['children'].append(form_node)
            seen_forms.add(form)
            seen_sections[form] = set()

        # Add section node if not already added for this form
        if sec_name not in seen_sections[form]:
            sec_node = {'title': sec_name, 'key': f"{form}-{sec_name}", 'children': []}
            for child in tree['children']:
                if child['title'] == form:
                    child['children'].append(sec_node)
                    break
            seen_sections[form].add(sec_name)

        # Check if the question is a primary node or a child node
        if mod is None or pd.isna(mod):
            # Primary node
            primary_question_node = {'title': question, 'key': question_key, 'children': []}
            primary_question_keys[(form, vari)] = question_key
            for form_child in tree['children']:
                if form_child['title'] == form:
                    for sec_child in form_child['children']:
                        if sec_child['title'] == sec_name:
                            sec_child['children'].append(primary_question_node)
                            break
        else:
            # Child node of a primary node
            primary_key = primary_question_keys.get((form, vari))
            if primary_key:
                question_node = {'title': question, 'key': question_key}
                # Find the correct primary question node to add this question
                for form_child in tree['children']:
                    if form_child['title'] == form:
                        for sec_child in form_child['children']:
                            if sec_child['title'] == sec_name:
                                for primary_question in sec_child['children']:
                                    if primary_question['key'] == primary_key:
                                        primary_question['children'].append(question_node)
                                        break

    return tree

include_not_show=['otherl2','otherl3','route','route2','site','agent','agent2','warn','warn2','warn3','units','add','type','vol','site','0item','0otherl2',
                  '0addi','1item','1otherl2','1addi','2item','2otherl2','2addi','3item','3otherl2','3addi','4item','4otherl2','4addi']

def extract_parenthesis_content(text):
    match = re.search(r'\(([^)]+)\)', text)
    return match.group(1) if match else text

def getIncludeNotShow(selected_variables,current_datadicc):
    # Get the include not show for the selecte variables
    possible_vars_to_include = [f"{var}_{suffix}" for var in selected_variables for suffix in include_not_show]
    actual_vars_to_include = [var for var in possible_vars_to_include if var in current_datadicc['Variable'].values]
    selected_variables = list(selected_variables) + list(actual_vars_to_include)
    # Deduplicate the final list in case of any overlaps
    selected_variables = list(set(selected_variables))
    return current_datadicc.loc[current_datadicc['Variable'].isin(selected_variables)]

def getSelectUnits(selected_variables,current_datadicc):
    #current_datadicc[['Sec', 'vari', 'mod']] = current_datadicc['Variable'].str.split('_', n=2, expand=True)
    #current_datadicc[['Sec_name', 'Expla']] = current_datadicc['Section'].str.split(r'[(|:]', n=1, expand=True)
    current_datadicc['select units'] = (current_datadicc['Question'].str.contains('(select units)', case=False, na=False))
    mask_true = current_datadicc['select units'] == True
    for index, row in current_datadicc[mask_true].iterrows():
        mask_sec_vari = (current_datadicc['Sec'] == row['Sec']) & (current_datadicc['vari'] == row['vari'])
        current_datadicc.loc[mask_sec_vari, 'select units'] = True 


    selected_select_unit = current_datadicc.loc[current_datadicc['select units'] &
                                                current_datadicc['Variable'].isin(selected_variables)]
    
    selected_select_unit['count'] = selected_select_unit.groupby(['Sec', 'vari']).transform('size')

    select_unit_rows = []
    seen_variables = set()

    delete_this_variables_with_units=[]

    for _, row in selected_select_unit.iterrows():
        if row['count'] > 1:
            matching_rows = selected_select_unit[(selected_select_unit['Sec'] == row['Sec']) &
                                                (selected_select_unit['vari'] == row['vari'])]
            
            for dtvwu in matching_rows['Variable']:
                delete_this_variables_with_units.append(dtvwu)
            
            max_value = pd.to_numeric(matching_rows['Maximum'], errors='coerce').max()
            min_value = pd.to_numeric(matching_rows['Minimum'], errors='coerce').min()
            options = ' | '.join([f"{idx + 1},{extract_parenthesis_content(r['Question'])}" for idx, (_, r) in enumerate(matching_rows.iterrows())])

            row_value = row.copy()
            row_value['Variable'] = row['Sec'] + '_' + row['vari']
            row_value['Answer Options'] = None
            row_value['Type'] = 'text'
            row_value['Maximum'] = max_value
            row_value['Minimum'] = min_value
            row_value['Question'] = row['Question'].split('(')[0]
            row_value['Validation'] = None
            row_value['Validation'] = 'number'

            row_units = row.copy()
            row_units['Variable'] = row['Sec'] + '_' + row['vari'] + '_units'
            row_units['Answer Options'] = options
            row_units['Type'] = 'radio'
            row_units['Maximum'] = None
            row_units['Minimum'] = None
            row_units['Question'] = 'Select ' + row['Question'].split('(')[0] + 'units'
            row_units['Validation'] = None


            if row_value['Variable'] not in seen_variables:
                select_unit_rows.append(row_value)
                seen_variables.add(row_value['Variable'])

            if row_units['Variable'] not in seen_variables:
                select_unit_rows.append(row_units)
                seen_variables.add(row_units['Variable'])

    if len(select_unit_rows) > 0:
        icc_var_units_selected_rows = pd.DataFrame(select_unit_rows).reset_index(drop=True)
        icc_var_units_selected = icc_var_units_selected_rows
        return icc_var_units_selected,list(set(delete_this_variables_with_units)-set(icc_var_units_selected['Variable']))
    return None,None

def getListContent(current_datadicc,version):
    level2_answers=[]
    all_rows_lists=[]
    #datadiccDisease_lists = current_datadicc.loc[(((current_datadicc['Type']=='list') |(current_datadicc['Type']=='user_list') )&
    #                                            (current_datadicc['Variable'].isin(selected_variables)))]     
    datadiccDisease_lists = current_datadicc.loc[current_datadicc['Type']=='list']         
    root='https://raw.githubusercontent.com/ISARICResearch/DataPlatform/main/ARCH/'
    
    list_variable_choices=[]
    for _, row in datadiccDisease_lists.iterrows():
        if pd.isnull(row['List']):
            print('list witout corresponding repository file')

        else:
            list_path = root+version+'/Lists/'+row['List'].replace('_','/')+'.csv'
            try:
                list_options = pd.read_csv(list_path,encoding='latin1') 
            except Exception as e:
                print(f"Failed to fetch remote file due to: {e}. Attempting to read from local file.")
                
            list_options=list_options.sort_values(by=list_options.columns[0],ascending=True)
            list_choises=''
            list_variable_choices_aux=[]
            cont_lo=1
            for lo in list_options[list_options.columns[0]]:
                if cont_lo == 88:
                    cont_lo=89
                elif cont_lo == 99:
                    cont_lo =100
                try:
                    list_variable_choices_aux.append([cont_lo,lo])
                    list_choises+=str(cont_lo)+ ', '+lo+' | '
                except:
                    print('error')
                cont_lo+=1
            list_choises = list_choises+ '88, ' +'Other'
            arrows = ['','>', '->', '>->', '->->','>->->']     

            #row['Type']='radio'
            repeat_n = 5
            questions_for_this_list=[]
            other_info = current_datadicc.loc[(current_datadicc['Sec']==row['Sec'])&
                            (current_datadicc['vari']==row['vari'])&
                            (current_datadicc['Variable']!=row['Variable'])]
            
            #remove_other_info_from_diseaseDic = remove_other_info_from_diseaseDic+list(other_info['Variable'])
            for n in range(repeat_n):
                #########################################
                #########################################
                #########################################
                # Falta agregar las otras opciones con el mismo sec_var
                dropdown_row = row.copy()   
                dropdown_row['Variable'] = row['Sec'] +'_'+ row['vari']+'_'+str(n)+'item'
                #dropdown_row['Answer Options'] = list_choises.replace("| 88, Other","| 88_"+str(n)+", Other")
                dropdown_row['Answer Options'] = list_choises
                dropdown_row['Type'] = "dropdown"
                dropdown_row['Validation']='autocomplete'
                dropdown_row['Maximum'] = None  
                dropdown_row['Minimum'] = None  
                dropdown_row['List']=None
                if  row['Question']!= 'NSAIDs':
                    if n == 0:
                        if 'select' in row['Question'].lower():
                            dropdown_row['Question']=arrows[n]+ row['Question'] 
                        else:
                            dropdown_row['Question']=arrows[n]+'Select ' + row['Question'].lower() 
                    else:
                        if 'select' in row['Question'].lower():
                            dropdown_row['Question']=arrows[n]+ row['Question'].lower() +' '+str(n+1)
                        else:
                            dropdown_row['Question']=arrows[n]+'Select additional ' + row['Question'].lower() +' '+str(n+1)
                else:
                    if n==0:
                        if 'select' in row['Question'].lower():
                            dropdown_row['Question']=arrows[n]+ row['Question'] 
                        else:
                            dropdown_row['Question']=arrows[n]+'Select ' + row['Question'] 
                    else:
                        if 'select' in row['Question'].lower():
                            dropdown_row['Question']=arrows[n] + row['Question'] +' '+str(n+1)
                        else:
                            dropdown_row['Question']=arrows[n]+'Select additional ' + row['Question'] +' '+str(n+1)

                dropdown_row['mod']=str(n)+'item'
                dropdown_row['vari'] = row['vari']
                if n == 0:
                    dropdown_row['Skip Logic']= '['+row['Variable']+"]='1'"
                else:
                    dropdown_row['Skip Logic']= '['+row['Sec'] +'_'+ row['vari']+'_'+str(n-1)+'addi'+"]='1'" 

                other_row = row.copy()             
                other_row['Variable'] = row['Sec'] +'_'+ row['vari']+'_'+str(n)+'otherl2'
                other_row['Answer Options'] = None
                other_row['Type'] = 'text'
                other_row['Maximum'] = None  
                other_row['Minimum'] = None  
                other_row['Skip Logic']='['+dropdown_row['Variable'] +"]='88'"
                if row['Variable']=='inclu_disease':
                    other_row['Question']=arrows[n]+"Specify other infection the individual is suspected/confirmed to have"
                else:
                    if n ==0:
                        if row['Question'] !='NSAIDs':
                            if 'other' in row['Question'].lower():
                                other_row['Question']=arrows[n]+'Specify ' + row['Question'].lower()+''
                            else:
                                other_row['Question']=arrows[n]+'Specify other ' + row['Question'].lower()+''
                        else:
                            if 'other' in row['Question'].lower():
                                other_row['Question']=arrows[n]+'Specify ' + row['Question']
                            else:
                                other_row['Question']=arrows[n]+'Specify other ' + row['Question']
                    else:
                        if row['Question'] !='NSAIDs':
                            if 'other' in row['Question'].lower():
                                other_row['Question']=arrows[n]+'Specify ' + row['Question'].lower()+' '+str(n+1)
                            else:
                                other_row['Question']=arrows[n]+'Specify other ' + row['Question'].lower()+' '+str(n+1)
                        else:
                            if 'other' in row['Question'].lower():
                                other_row['Question']=arrows[n]+'Specify ' + row['Question']+' '+str(n+1)
                            else:
                                other_row['Question']=arrows[n]+'Specify other ' + row['Question']+' '+str(n+1)
                other_row['List']=None
                other_row['mod']=str(n)+'otherl2'
                other_row['vari'] = row['vari']
                questions_for_this_list.append(dropdown_row)
                questions_for_this_list.append(other_row)          

                if len (other_info)>1:
                    for index, oi in other_info.iterrows():
                        other_info_row = oi.copy()
                        if n ==0:
                            other_info_row['Question'] = arrows[n]+' '+oi['Question']
                        else:
                            other_info_row['Question'] = arrows[n]+' '+oi['Question']+' '+str(n+1)
                            other_info_row['Skip Logic']= '['+additional_row['Variable']+"]='1'"
                        other_info_row['Variable'] = oi['Sec'] +'_'+ oi['vari']+'_'+str(n)+oi['mod']
                        other_info_row['Skip Logic']= '['+additional_row['Variable']+"]='1'"
                        other_info_row['List']=None
                        other_info_row['mod']=str(n)+oi['mod']
                        other_info_row['vari'] = oi['vari']            
                        questions_for_this_list.append(other_info_row)

                elif len(other_info)==1:
                    oi=other_info.iloc[0] 
                    other_info_row = oi.copy()
                    if n==0:
                        other_info_row['Question'] = arrows[n]+''+oi['Question']
                    else:
                        other_info_row['Question'] = arrows[n]+''+oi['Question']+' '+str(n+1)
                        other_info_row['Skip Logic']= '['+additional_row['Variable']+"]='1'"
                    other_info_row['Variable'] = oi['Sec'] +'_'+ oi['vari']+'_'+str(n)+oi['mod']
                    other_info_row['List']=None
                    other_info_row['mod']=str(n)+oi['mod']
                    other_info_row['vari'] = oi['vari']            
                    questions_for_this_list.append(other_info_row)     


                if n < repeat_n-1:
                    additional_row = row.copy()
                    additional_row['Variable'] = row['Sec'] +'_'+ row['vari']+'_'+str(n)+'addi'
                    additional_row['Answer Options'] = row['Answer Options']
                    additional_row['Type'] = 'radio'
                    additional_row['Maximum'] = None  
                    additional_row['Minimum'] = None  
                    additional_row['Skip Logic']=dropdown_row['Skip Logic']
                    if additional_row['Question'] != 'NSAIDs':
                        additional_row['Question']=arrows[n]+'Any additional ' + additional_row['Question'].lower()+' ?'
                    else:
                        additional_row['Question']=arrows[n]+'Any additional ' + additional_row['Question']+' ?'
                    additional_row['List']=None
                    additional_row['mod']=str(n)+'addi'
                    additional_row['vari'] = row['vari']            
                    questions_for_this_list.append(additional_row)
                                        

            all_rows_lists.append(row)
            '''if len (other_info)>1:
                for index, oi in other_info.iterrows():
                    all_rows_lists.append(oi)
            elif len(other_info)==1:
                all_rows_lists.append(other_info.iloc[0])'''
            for qftl in questions_for_this_list :
                all_rows_lists.append(qftl)
            list_variable_choices.append([row['Variable'],list_variable_choices_aux])
    arc_list = pd.DataFrame(all_rows_lists).reset_index(drop=True)
    
    return arc_list,list_variable_choices



def getUserListContent(current_datadicc,version,user_checked_options=None,ulist_var_name=None):
    level2_answers=[]
    all_rows_lists=[]
    #datadiccDisease_lists = current_datadicc.loc[(((current_datadicc['Type']=='list') |(current_datadicc['Type']=='user_list') )&
    #                                            (current_datadicc['Variable'].isin(selected_variables)))]     
    datadiccDisease_lists = current_datadicc.loc[current_datadicc['Type']=='user_list']         
    root='https://raw.githubusercontent.com/ISARICResearch/DataPlatform/main/ARCH/'
    
    ulist_variable_choices=[]
    for _, row in datadiccDisease_lists.iterrows():
        if pd.isnull(row['List']):
            print('list witout corresponding repository file')

        else:
            list_path = root+version+'/Lists/'+row['List'].replace('_','/')+'.csv'
            try:
                list_options = pd.read_csv(list_path,encoding='latin1') 
            
            except Exception as e:
                print(f"Failed to fetch remote file due to: {e}. Attempting to read from local file.")

            '''user_selected_opt = user_list_options['Options'].loc[user_list_options['Variable']==row['Variable']].iloc[0]
            if user_selected_opt == '':
                l1_choices=default_options[row['Variable']]
            else:
                l1_choices=user_selected_opt'''
            list_options=list_options.sort_values(by=list_options.columns[0],ascending=True)
            default = True
            
            l2_choices=''
            l1_choices=''
            cont_lo=1
            ulist_variable_choices_aux=[]
            for lo in list_options[list_options.columns[0]]:
                if cont_lo == 88:
                    cont_lo=89
                elif cont_lo == 99:
                    cont_lo =100
                try:
                    
                    if user_checked_options is None:
                        
                        list_options['Selected'] = pd.to_numeric(list_options['Selected'], errors='coerce')

                        if list_options['Selected'].loc[list_options[list_options.columns[0]]==lo].iloc[0]==1:
                            l1_choices+=str(cont_lo)+ ', '+lo+' | '
                            ulist_variable_choices_aux.append([cont_lo,lo,1])
                        else:
                            l2_choices+=str(cont_lo)+ ', '+lo+' | '
                            ulist_variable_choices_aux.append([cont_lo,lo,0])
                    else:
                        if row['Variable'] == ulist_var_name:
                            if lo in list(user_checked_options['Option']):
                                l1_choices+=str(cont_lo)+ ', '+lo+' | '
                                ulist_variable_choices_aux.append([cont_lo,lo,1])
                            else:
                                l2_choices+=str(cont_lo)+ ', '+lo+' | '   
                                ulist_variable_choices_aux.append([cont_lo,lo,0])
                        else:
                            if list_options['Selected'].loc[list_options[list_options.columns[0]]==lo].iloc[0]==1:
                                l1_choices+=str(cont_lo)+ ', '+lo+' | '
                                ulist_variable_choices_aux.append([cont_lo,lo,1])
                            else:
                                l2_choices+=str(cont_lo)+ ', '+lo+' | '            
                                ulist_variable_choices_aux.append([cont_lo,lo,0])                                     
                                                    
                except Exception as e:
                    print(row['List']+f": Failed to add to lists of choices due to {e}.")
                cont_lo+=1
            l2_choices = l2_choices+ '88, ' +'Other' 
            ulist_variable_choices.append([row['Variable'],ulist_variable_choices_aux])
            
            #row['Type']='radio'
            row['Answer Options']=l1_choices

            dropdown_row = row.copy()   
            other_row = row.copy()    
            dropdown_row['Variable'] = row['Sec'] +'_'+ row['vari']+'_'+'otherl2'
            dropdown_row['Answer Options'] =l2_choices
            dropdown_row['Type'] = "dropdown"
            dropdown_row['Validation']='autocomplete'
            dropdown_row['Maximum'] = None  
            dropdown_row['Minimum'] = None  
            dropdown_row['List']=None
            if row['Variable']=='medi_medtype':
                dropdown_row['Question']= 'Select other agents administered while hospitalised or at discharge'
                other_row['Question']='Specify other agents administered while hospitalised or at discharge'
            else:
                dropdown_row['Question']='Select ' + row['Question']+''
                other_row['Question']='Specify other ' + row['Question']+''
            dropdown_row['mod']='otherl2'
            dropdown_row['Skip Logic']='['+row['Variable'] +"]='88'"
            
            other_row['Variable'] = row['Sec'] +'_'+ row['vari']+'_'+'otherl3'
            other_row['Answer Options'] = None
            other_row['Type'] = 'text'
            other_row['Maximum'] = None  
            other_row['Minimum'] = None  
            if row['Variable']!='inclu_disease':
                other_row['Skip Logic']='['+row['Sec'] +'_'+ row['vari']+'_'+'otherl2' +"]='88'"
            else:
                other_row['Skip Logic']='['+row['Variable'] +"]='88'"
            
            other_row['List']=None
            other_row['mod']='otherl3'
            
            all_rows_lists.append(row)
            if row['Variable']!='inclu_disease':
                all_rows_lists.append(dropdown_row)
            all_rows_lists.append(other_row)
            
    arc_list = pd.DataFrame(all_rows_lists).reset_index(drop=True)

    return arc_list,ulist_variable_choices


def generateDailyDataType(current_datadicc):
    datadiccDisease=current_datadicc.copy()
    daily_sections=list(datadiccDisease['Section'].loc[datadiccDisease['Form']=='daily'].unique())
    if len (daily_sections)>0:
        if 'ASSESSMENT' in daily_sections:
            daily_sections.remove('ASSESSMENT')
        if len(daily_sections)==1:
            datadiccDisease = datadiccDisease.loc[datadiccDisease['Variable']!='daily_data_type']
        elif len(daily_sections)>1:
            daily_type_dicc={"VITAL SIGNS & ASSESSMENTS": "1, Vital Signs & Assessments ",
                            "TREATMENTS & INTERVENTIONS": "2, Treatments & Interventions ",
                            "LABORATORY RESULTS":"3, Laboratory Results ",
                            "IMAGING": "4, Imaging "}
            daily_type_otions=''
            for daily_sec in daily_sections:
                for daily_type in daily_type_dicc:
                    if daily_sec.startswith(daily_type):
                        daily_type_otions+=daily_type_otions+daily_type_dicc[daily_type]+'|'
            daily_type_otions = daily_type_otions[:-1]
                        
            datadiccDisease['Answer Options'].loc[datadiccDisease['Variable']=='daily_data_type']=daily_type_otions 
        return datadiccDisease
    return current_datadicc   

def addTransformedRows(selected_variables, arc_var_units_selected,order):
    arc_var_units_selected['Sec_vari']=arc_var_units_selected['Sec']+'_'+arc_var_units_selected['vari']
    result = selected_variables.copy().reset_index(drop=True)
    arc_var_units_selected = arc_var_units_selected[result.columns]

    for _, row in arc_var_units_selected.iterrows():
        variable = row['Variable']

        if variable in result['Variable'].values:
            # Get the index for the matching variable in the result DataFrame
            match_index = result.index[result['Variable'] == variable].tolist()[0]
            # Update each column separately
            for col in result.columns:
                result.at[match_index, col] = row[col]
        else:
            # Identify the base variable name by splitting at the last underscore
            base_var = '_'.join(variable.split('_')[:-1])

            if base_var in result['Variable'].values:
                # Find the index of the base variable row
                #base_index = result.index[result['Variable'] == base_var].tolist()[0]
                base_index = result.index[result['Variable'].str.startswith(base_var)].max()
                row_df = pd.DataFrame([row]).reset_index(drop=True)
                # Insert the new row immediately after the base variable row
                result = pd.concat([result.iloc[:base_index + 1], row_df, result.iloc[base_index + 1:]]).reset_index(drop=True)


            else:
                # Variable to be added is not based on the base variable, use the order list
                variable_to_add = variable
                order_index = order.index(variable_to_add) if variable_to_add in order else None

                if order_index is not None:
                    # Find the next existing variable in 'result' from 'order'
                    insert_before_index = None
                    for next_variable in order[order_index + 1:]:
                        if next_variable in result['Variable'].values:
                            insert_before_index = result.index[result['Variable'] == next_variable][0]
                            break

                    # Create a DataFrame from the current row
                    row_df = pd.DataFrame([row]).reset_index(drop=True)

                    # Insert the row at the determined position or append if no next variable is found
                    if insert_before_index is not None:
                        result = pd.concat([result.iloc[:insert_before_index], row_df, result.iloc[insert_before_index:]]).reset_index(drop=True)
                    else:
                        result = pd.concat([result, row_df]).reset_index(drop=True)
                else:
                    # If the variable is not in the order list, append it at the end (or handle as needed)
                    row_df = pd.DataFrame([row]).reset_index(drop=True)
                    result = pd.concat([result, row_df]).reset_index(drop=True)


    return result

def customAlignment(datadicc):
    mask = (datadicc['Field Type'].isin(['checkbox', 'radio'])) & ((datadicc['Choices, Calculations, OR Slider Labels'].str.split('|').str.len() < 4)&
                                                                   (datadicc['Choices, Calculations, OR Slider Labels'].str.len()<=40))
    datadicc.loc[mask, 'Custom Alignment'] = 'RH'
    return datadicc
def generateCRF(datadiccDisease,db_name):
    datadiccDisease['Type'].loc[datadiccDisease['Type']=='user_list']='radio'
    datadiccDisease['Type'].loc[datadiccDisease['Type']=='list']='radio'
    datadiccDisease=datadiccDisease[['Form','Section','Variable',
                                    'Type','Question',
                                    'Answer Options', 
                                    'Validation', 
                                    'Minimum', 'Maximum', 
                                    'Skip Logic']]
        
    datadiccDisease.columns=["Form Name","Section Header","Variable / Field Name","Field Type","Field Label",
                "Choices, Calculations, OR Slider Labels","Text Validation Type OR Show Slider Number",
                "Text Validation Min","Text Validation Max","Branching Logic (Show field only if...)"]   
    redcap_cols=['Variable / Field Name', 'Form Name', 'Section Header', 'Field Type',
            'Field Label', 'Choices, Calculations, OR Slider Labels', 'Field Note',
            'Text Validation Type OR Show Slider Number', 'Text Validation Min',
            'Text Validation Max', 'Identifier?',
            'Branching Logic (Show field only if...)', 'Required Field?',
            'Custom Alignment', 'Question Number (surveys only)',
            'Matrix Group Name', 'Matrix Ranking?', 'Field Annotation']
    datadiccDisease = datadiccDisease.reindex(columns=redcap_cols)
    
    datadiccDisease['Field Type'].loc[datadiccDisease['Field Type'].isin(['date_dmy', 'number','integer', 'datetime_dmy'])]='text'
    datadiccDisease['Section Header'] = datadiccDisease['Section Header'].where(datadiccDisease['Section Header'] != datadiccDisease['Section Header'].shift(), np.nan) 
    # For the new empty columns, fill NaN values with a default value (in this case an empty string)
    datadiccDisease.fillna('', inplace=True)
    

    datadiccDisease=datadiccDisease.loc[datadiccDisease['Field Type'].isin([ 'text', 'notes', 'radio', 'dropdown', 'calc',
                                                                            'file', 'checkbox', 'yesno', 'truefalse', 'descriptive', 'slider'])]
    #datadiccDisease['Branching Logic (Show field only if...)']=['']*len(datadiccDisease)
    datadiccDisease['Section Header'].replace('', np.nan, inplace=True)      
    datadiccDisease = customAlignment(datadiccDisease)
    
    #date=datetime.today().strftime('%Y-%m-%d')
    #path='C:/Users/egarcia/OneDrive - Nexus365/Projects/CBCG/Outputs/'
    #datadiccDisease.to_csv(path+db_name+'_'+date+'.csv',index=False, encoding='utf8')
    return datadiccDisease