import PySimpleGUI as sg

# ----- Functions----- #

def key(Name,Element):
    if Element == 'N':
        soln = f"-IN{nodal_head['headings'].index(Name)}{Element}-"
    elif Element == 'E':
        soln = f"-IN{element_head['headings'].index(Name)}{Element}-"
    return soln



# ---- Settings -------#

UI_pad = ((40,0),0) # ((Left Side, Right Side),(Above, Below)) in pixels


# ------ Menu Definition ------ #

menu_def = [
                ['File', ['Open', 'Save', 'Exit'  ] ],      
                ['Edit', ['Paste', ['Special', 'Normal', ], 'Undo', 'Preferences'] ],      
                ['Help', 'About...']
                ]

#------- Create dictionaries to house structural info ----------# 

nodal_head = {'headings' : ['Label', 'X-coor', 'Y-coor', 'X DOF Fixed', 'Y DOF Fixed', 'Z DOF Fixed', 'X Nodal Load', 'Y Nodal Load', 'Z Nodal Load',
                            'X Support Disp', 'Y Support Disp', 'Z Support Disp']}


element_head = {'headings' : ['Label', 'Node i', 'Node j', 'MOE (E)', 'Cross sectional Area (A)', 'Second Moment of Inertia (I)', 'Local Axial Distributed Load',
                              'Local Transverse Distributed Load', 'Element Type']}

nodal_dict = { 'Create New Node' : '',
                'Node1' : [1,2,3,4,5,6, 7,8,9,10,11,12],
               'Node2' : [1,2,3,4,5,6, 7,8,9,10,11,12] }


element_dict = { 'Create New Element' : '' }

base_units = {
                        'base_length' : 'inch',
                        'base_force' : 'lbf',
                        'base_angle' : 'rad',
                        'base_pressure' : 'psi'
                        }

node_table = sg.Table(values = list(nodal_dict.values())[1:], headings = nodal_head['headings'],
                    def_col_width = 12,
                    auto_size_columns=False,
                    display_row_numbers=False,
                    justification='right',
                    num_rows=5,
                    row_height=25,
                    key = '-NDTABLE-',
                    tooltip='This is a table')

element_table = sg.Table(values = list(element_dict.values())[1:], headings = element_head['headings'],
                    col_widths = [9,9,9,9,22,23,23,25,12],
                    auto_size_columns=False,
                    display_row_numbers=False,
                    justification='right',
                    num_rows=5,
                    row_height=25,
                    tooltip='This is a table')

# ----------- Create the 3 layouts this Window could display -----------#



layout1 = [ [sg.Text('This Layout Collects Data for Nodes')],
                    [sg.Text('Select which element you would like to edit/create:'), sg.InputCombo(list(nodal_dict.keys()), size=(20, 1), key = '-NOCOMBO-')],
                    [sg.Text('Input Nodal Location Information (cartesian coordinates)')],
                    [sg.Text('X-coor', pad = UI_pad), sg.Input(key = key('X-coor','N'), size = (10,1) ), sg.Text(f"{base_units['base_length']}")],
                    [sg.Text('Y-coor', pad = UI_pad), sg.Input(key = key('Y-coor','N'), size = (10,1) ), sg.Text(f"{base_units['base_length']}")],
                    [sg.Text('Input Nodal Boundary Condition Information (if applicable)')],
                    [ sg.Checkbox('X DOF Fixed', size=(10,1), key = key('X DOF Fixed','N'), pad = UI_pad ), sg.Checkbox('Y DOF Fixed', size=(10,1), key = key('Y DOF Fixed','N')),
                        sg.Checkbox('Z DOF Fixed', size=(10,1), key = key('Z DOF Fixed','N')) ],
                    [sg.Text('X Support Disp', pad = UI_pad), sg.Input(key = key('X Support Disp','N'), size = (10,1)), sg.Text(f"{base_units['base_length']}")],
                    [sg.Text('Y Support Disp', pad = UI_pad), sg.Input(key = key('Y Support Disp','N'), size = (10,1)), sg.Text(f"{base_units['base_length']}")],
                    [sg.Text('Z Support Disp', pad = UI_pad), sg.Input(key = key('Z Support Disp','N'), size = (10,1)), sg.Text(f"{base_units['base_angle']}")],
                    [sg.Text('Input Nodal Loads (if applicable)')],
                    [sg.Text('X Nodal Load', pad = UI_pad), sg.Input(key = key('X Nodal Load','N'), size = (10,1)), sg.Text(f"{base_units['base_force']}")],
                    [sg.Text('Y Nodal Load', pad = UI_pad), sg.Input(key = key('Y Nodal Load','N'), size = (10,1)), sg.Text(f"{base_units['base_force']}")],
                    [sg.Text('Z Nodal Load', pad = UI_pad), sg.Input(key = key('Z Nodal Load','N'), size = (10,1)), sg.Text(f"{base_units['base_force']} x {base_units['base_length']}")],
                    [sg.Button( button_text = 'Confirm Entries', pad = ((120,0),(20,0)) )]]

layout2 = [[sg.Text('This Layout Collects Data for Elements')],
                   [sg.Text('Property3'), sg.Input(key='-INx-')],
                   [sg.Text('Property4'), sg.Input(key='-INy-')]]

layout3 = [[sg.Text('This Layout Collects Data for Other')],
                   [sg.Text('Property5'), sg.Input(key='-INz-')],
                   [sg.Text('Property6'), sg.Input(key='-INw-')]]


# ------ Create dictionary tab that will display entered data and how it's stored------ #

tab1_layout =  [ [sg.T('Node Information')],
                            [sg.Table([[1,2,3], [4,5,6]], ['Col 1','Col 2','Col 3'], num_rows=2)] ]    

tab2_layout = [ [sg.T('Element Information')],
                            [element_table] ]    


# ----------- Create layout for persistent window (starting window) using Columns and a row of Buttons -------------#

layout = [
            [sg.Menu(menu_def) ],
            [sg.Button('Nodes'), sg.Button('Elements'), sg.Button('Other') ],
            [sg.Canvas( background_color = 'red', size = (400, 400) ), sg.Column(layout1, key='-Nodes-', vertical_alignment = 't'), sg.Column(layout2, visible=False, key='-Elements-'), sg.Column(layout3, visible=False, key='-Other-')],
            [sg.TabGroup([[sg.Tab('Node Data', tab1_layout, tooltip='tip'), sg.Tab('Element Data', tab2_layout)]], tooltip='TIP2'), sg.Button('Exit')]
            ]

window = sg.Window('Simple Structural Analysis Widget', layout)

layout = 'Nodes'  # The currently visible layout
ND,EL = (0,0) # session counter variables

#----- Event loop for actual window ------#

while True:
    event, values = window.read( )
    print(event, values)
    if event in (None, 'Exit'):
        break
    if event == 'Elements':
        window[f'-{layout}-'].update(visible=False)
        layout = event
        window[f'-{layout}-'].update(visible=True)
    elif event == 'Nodes':
        window[f'-{layout}-'].update(visible=False)
        layout = event
        window[f'-{layout}-'].update(visible=True)
    elif event == 'Other':
        window[f'-{layout}-'].update(visible=False)
        layout = event
        window[f'-{layout}-'].update(visible=True)
    elif event == 'Confirm Entries':
        if values['-NOCOMBO-'] == 'Create New Node':
            nodal_dict['Node1'][0] = 'Did I work'    
       
    print(ND)
        
window.close()