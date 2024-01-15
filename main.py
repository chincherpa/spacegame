import PySimpleGUI as sg

import config
from inventory import INVENTORY
from science import SCIENCE

lTab_HQ = [
          [sg.Column([
            [sg.Text("HQ")],
            [sg.Text("PLACEHOLDER")]
          ])]
        ]

lTab_Science = [
  [
    sg.Column([
      [sg.Button(button_text="Erforsche Eisen")],
      [sg.Button(button_text="Erforsche Rakete")],
      [sg.Button(button_text="Erforsche Mondlander")],
      [sg.Button(button_text="Erforsche Baumaterial")],
      [sg.Button(button_text="Erforsche Werkzeug")],

    ]),
    sg.VerticalSeparator(),
    sg.Column([
      [sg.Text('Beschreibung:')],
      [sg.Text('', key='desc_Research', visible=False, size=(30, 6))],
      [sg.Text('', key='desc_duration', visible=False)],
      [sg.Button('Erforschen', key='do_Research', visible=False)]
    ])
  ],
  [
    sg.ProgressBar(0, orientation='h', size=(20, 20), key='-PROGRESS BAR-', visible=False),
    sg.Button('Erforschen stoppen', key='Cancel_Science', visible=False)
  ]
]

table_inventory = sg.Table([
  list(INVENTORY.values())],
  list(INVENTORY.keys()),
  # num_rows=1,
  # def_col_width = 100,
  auto_size_columns=True,
  # display_row_numbers=False,
  justification='center',
  # num_rows=1,
  # row_height=25,
  key = '-TABLEINV-',
  # tooltip='This is a table'
)

lTab_Inventory = [
  [sg.Text('Baumaterial')],
  # [sg.Table(values = [1,2,3])]  #list(INVENTORY.values())#, headings = list(INVENTORY.keys()),
  [table_inventory]
  # [node_table]
          # [sg.Column([
          #   [sg.Text('Baumaterial')],
          #   [sg.Text('Staub')],
          #   [sg.Text('Gold')],
          #   [sg.Text('Eisen')],
          #   [sg.Text('Stein')],
          #   [sg.Text('Werkzeug')],
          #   [sg.Text('Wasser')],
          # ]),
          # sg.Column([
          #   [sg.Text(INVENTORY['buildingmaterial'])],
          #   [sg.Text(INVENTORY['dust'])],
          #   [sg.Text(INVENTORY['gold'])],
          #   [sg.Text(INVENTORY['iron'])],
          #   [sg.Text(INVENTORY['stone'])],
          #   [sg.Text(INVENTORY['tool'])],
          #   [sg.Text(INVENTORY['water'])],
          # ])
          # ]
        ]

lTab_Earth = [
  [sg.Text("Erde")],
  ]

lTab_Moon = [
  [sg.Text("Mond")],
  ]

lTab_Mars = [
  [sg.Text("Mars")],
  ]

lTab_Planets = [
          [sg.TabGroup([
            [sg.Tab("Erde", lTab_Earth, key='-TAB_EARTH-')],
            [sg.Tab("Mond", lTab_Moon, key='-TAB_MOON-')],
            [sg.Tab("Mars", lTab_Mars, key='-TAB_MARS-')
            ]
          ], expand_x=True, expand_y=True)]
        ]

LAYOUT = [[
    [sg.Text(text="Cycle:", key="tCycles"), sg.Text(text="Credits:", key="tCredits")],
  sg.Column([
    [sg.Button(button_text="HQ")],
    [sg.Button(button_text="Forschung")],
    [sg.Button(button_text="Inventar")],
    [sg.Button(button_text="Planeten")],
  ]),

  sg.Column([[
    sg.TabGroup([
      [
        sg.Tab("HQ", lTab_HQ, key='-TAB_HQ-'),
        sg.Tab("Forschung", lTab_Science, key='-TAB_SCIENCE-'), #, visible=False),
        sg.Tab("Inventar", lTab_Inventory, key='-TAB_INVENTORY-'), #, visible=False),
        sg.Tab("Planeten", lTab_Planets, key='-TAB_PLANETS-'), #, visible=False),
      ]], expand_x=True, expand_y=True)
  ]])
]]

window = sg.Window("Game", LAYOUT, size=config.WINDOW_SIZE, resizable=True)
fTicks = 0
iCredits = 500

# tab_keys = ('-TAB_HQ-','-TAB_EARTH-','-TAB_MOON-', '-TAB_MARS-')

inventory = INVENTORY
dGamestate = {
  
}

bScience_ongoing = False
iCurrent_Value = None
sCurrent_Research = None

def show_research(sCurrent_Research):
  window['desc_Research'].update(visible=True, value=SCIENCE[sCurrent_Research]['description'])
  window['desc_duration'].update(visible=True, value=f"Forschungsdauer: {SCIENCE[sCurrent_Research]['duration']} Zyklen")
  if not bScience_ongoing:
    window['do_Research'].update(visible=True)

def do_research(sCurrent_Research):
  window['do_Research'].update(visible=False)
  global bScience_ongoing
  global iCurrent_Value
  global iMax_Science
  bScience_ongoing = True
  iMax_Science = SCIENCE[sCurrent_Research]['duration'] / config.TICK
  iCurrent_Value = 0
  print(f'{iMax_Science = }')
  window['-PROGRESS BAR-'].update(current_count=0, max=iMax_Science)
  window['-PROGRESS BAR-'].update(visible=True)
  window['Cancel_Science'].update(visible=True)

while True:
  event, values = window.read(config.WINDOW_READ)
  fTicks += config.TICK
  window['tCycles'].update(f'Cycle: {fTicks:.1f}')
  window['tCredits'].update(f'Credits: {iCredits}')

  if event != '__TIMEOUT__':
    print(f'{event = }')
  if event in (
    sg.WINDOW_CLOSED, "Exit"):
    break
  if event == "HQ":
    window['-TAB_HQ-'].select()
  elif event == "Forschung":
    window['-TAB_SCIENCE-'].select()
  elif event == "Inventar":
    window['-TAB_INVENTORY-'].select()

  elif event == "Planeten":
    window['-TAB_PLANETS-'].select()

  elif 'Erforsche'in event:
    if 'Eisen' in event:
      sCurrent_Research = 'iron'
    if 'Rakete' in event:
      sCurrent_Research = 'rocket'
    if 'Mondlander' in event:
      sCurrent_Research = 'moonlander'
    if 'Baumaterial' in event:
      sCurrent_Research = 'buildingmaterial'
    if 'Werkzeug' in event:
      sCurrent_Research = 'tool'

    show_research(sCurrent_Research)

  elif event == 'do_Research':
    do_research(sCurrent_Research)

  elif event == 'Cancel_Science':
    window['-PROGRESS BAR-'].update(visible=False)
    window['Cancel_Science'].update(visible=False)
    window['do_Research'].update(visible=True)
    bScience_ongoing = False

  print(f'{bScience_ongoing = }')

  if bScience_ongoing:
    iCurrent_Value += 1
    print(f'{iCurrent_Value = }')
    window['-PROGRESS BAR-'].update(current_count=iCurrent_Value)
    if iCurrent_Value == iMax_Science:
      print('Forschung beendet')
      bScience_ongoing = False
      inventory[sCurrent_Research] += 1
      window['-TABLEINV-'].update(values=[list(INVENTORY.values())])

      window['-PROGRESS BAR-'].update(visible=False)
      window['Cancel_Science'].update(visible=False)


  print(inventory)


