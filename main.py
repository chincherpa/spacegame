import PySimpleGUI as sg

import config
from inventory import INVENTORY
from science import SCIENCE
from gamestate import GAMESTATE
from actions import ACTIONS

sg.theme('Dark Teal 6')

def show_research(sCurrent_Research):
  window['desc_Research'].update(visible=True, value=SCIENCE[sCurrent_Research]['beschreibung'])
  window['desc_dauer'].update(visible=True, value=f'Forschungsdauer: {SCIENCE[sCurrent_Research]['dauer']} Zyklen')
  if not bScience_ongoing:
    window['do_Research'].update(visible=True)

def do_research(sCurrent_Research):
  window['do_Research'].update(visible=False)
  global bScience_ongoing
  global iCurrent_Value
  global iMax_Science
  bScience_ongoing = True
  iMax_Science = SCIENCE[sCurrent_Research]['dauer'] / config.TICK
  iCurrent_Value = 0
  print(f'{iMax_Science = }')
  window['Progressbar'].update(current_count=0, max=iMax_Science)
  window['Progressbar'].update(visible=True)
  window['Stop_Research'].update(visible=True)


lTab_HQ = [[sg.Column([[sg.Text('HQ')], [sg.Text('PLACEHOLDER')]])]]

lTab_Science = [
  [
    sg.Column([
      [sg.Button(button_text='Erforsche Eisen')],
      [sg.Button(button_text='Erforsche Rakete')],
      [sg.Button(button_text='Erforsche Mondlander')],
      [sg.Button(button_text='Erforsche Baumaterial')],
      [sg.Button(button_text='Erforsche Werkzeug')],
    ]),
    sg.VerticalSeparator(),
    sg.Column([
      [sg.Text('Beschreibung:')],
      [sg.Text('', key='desc_Research', visible=False, size=(30, 6))],
      [sg.Text('', key='desc_dauer', visible=False)],
      [sg.Button('Erforschen', key='do_Research', visible=False)],
    ]),
  ],
  [
    sg.ProgressBar(0, orientation='h', size=(20, 20), key='Progressbar', visible=False),
    sg.Button('Erforschen stoppen', key='Stop_Research', visible=False),
  ],
]


def get_materials_from_inventory():
  lMaterials = []
  for material, amount in INVENTORY.items():
    lMaterials.append([sg.Text(material)])
  return lMaterials


def get_amounts_from_inventory():
  lAmounts = []
  for material, amount in INVENTORY.items():
    lAmounts.append([sg.Text(amount)])
  return lAmounts


lTab_Inventory = [
  [sg.Text('Baumaterial')],
  [
    sg.Column(get_materials_from_inventory()),
    sg.Column(get_amounts_from_inventory()),
  ],
]

lTab_Erde = [
  [sg.Text('Erde')],
  [sg.Text(f'Astronauten auf der Erde {GAMESTATE['Astronauten']['Erde']}')],
]

lTab_Mond = [
  [sg.Text('Mond')],
  [sg.Text(f'Astronauten auf dem Mond {GAMESTATE['Astronauten']['Mond']}')],
]

lTab_Mars = [
  [sg.Text('Mars')],
  [sg.Text(f'Astronauten auf dem Mars {GAMESTATE['Astronauten']['Mars']}')],
]

lTab_Planets = [
  [
    sg.TabGroup(
      [
        [sg.Tab('Erde', lTab_Erde, key='TAB_Erde')],
        [sg.Tab('Mond', lTab_Mond, key='TAB_Mond')],
        [sg.Tab('Mars', lTab_Mars, key='TAB_Mars')],
      ],
      expand_x=True,
      expand_y=True,
    )
  ]
]

lTab_Shop = [
  [
    sg.Column([
      [sg.Button(button_text='Erforsche Eisen')],
      [sg.Button(button_text='Erforsche Rakete')],
      [sg.Button(button_text='Erforsche Mondlander')],
      [sg.Button(button_text='Erforsche Baumaterial')],
      [sg.Button(button_text='Erforsche Werkzeug')],
    ]),
    sg.VerticalSeparator(),
    sg.Column([
      [sg.Text('Beschreibung:')],
      [sg.Text('', key='desc_Research', visible=False, size=(30, 6))],
      [sg.Text('', key='desc_dauer', visible=False)],
      [sg.Button('Erforschen', key='do_Research', visible=False)],
    ]),
  ],
  [
    sg.ProgressBar(0, orientation='h', size=(20, 20), key='Progressbar', visible=False),
    sg.Button('Erforschen stoppen', key='Stop_Research', visible=False),
  ],
]

LAYOUT = [
  [
    [
      sg.Text(text='Cycle:', key='tCycles'),
      sg.Text(text='Credits:', key='tCredits'),
    ],
    sg.Column(
      [
        [sg.Button(button_text='HQ')],
        [sg.Button(button_text='Forschung')],
        [sg.Button(button_text='Inventar')],
        [sg.Button(button_text='Planeten')],
        [sg.Button(button_text='Shop')],
      ]
    ),
    sg.Column([
      [sg.TabGroup([
        [
          sg.Tab('HQ', lTab_HQ, key='TAB_HQ', image_source=r'images\hq.png', image_subsample=config.IMAGE_SUBSAMPLE),
          sg.Tab('Forschung', lTab_Science, key='TAB_SCIENCE', image_source=r'images\forschung.png', image_subsample=config.IMAGE_SUBSAMPLE),
          sg.Tab('Inventar', lTab_Inventory, key='TAB_INVENTORY', image_source=r'images\inventar.png', image_subsample=config.IMAGE_SUBSAMPLE),
          sg.Tab('Planeten', lTab_Planets, key='TAB_PLANETS', image_source=r'images\planeten.png', image_subsample=config.IMAGE_SUBSAMPLE),
          sg.Tab('Shop', lTab_Shop, key='TAB_SHOP', image_source=r'images\shop.png', image_subsample=config.IMAGE_SUBSAMPLE),
        ]
      ], expand_x=True, expand_y=True)]
    ]),
    sg.Column([[sg.Image(r'images\hq.png', key='image_Spalte3')]])
  ]
]

fTicks = 0
iCredits = config.START_CREDITS

# tab_keys = ('TAB_HQ','TAB_Erde','TAB_Mond', 'TAB_Mars')

inventory = INVENTORY
dGamestate = {}

bScience_ongoing = False
iCurrent_Value = None
sCurrent_Research = None

window = sg.Window(config.TITLE, LAYOUT, size=config.WINDOW_SIZE, resizable=True)

while True:
  event, values = window.read(config.WINDOW_READ)
  fTicks += config.TICK
  window['tCycles'].update(f'Cycle: {fTicks:.1f}')
  window['tCredits'].update(f'Credits: {iCredits}')

  if event != '__TIMEOUT__':
    print(f'{event = }')
    print(f'{values = }')

  if event in (sg.WINDOW_CLOSED, 'Exit'):
    break

  if event == 'HQ':
    window['TAB_HQ'].select()
    window['image_Spalte3'].update(filename=r'images\hq.png')

  elif event == 'Forschung':
    window['TAB_SCIENCE'].select()
    window['image_Spalte3'].update(filename=r'images\forschung.png')

  elif event == 'Inventar':
    window['TAB_INVENTORY'].select()
    window['image_Spalte3'].update(filename=r'images\inventar.png')

  elif event == 'Planeten':
    window['TAB_PLANETS'].select()
    window['image_Spalte3'].update(filename=r'images\planeten.png')

  elif event == 'Shop':
    window['TAB_SHOP'].select()
    window['image_Spalte3'].update(filename=r'images\shop.png')

  elif 'Erforsche ' in event:
    _, sCurrent_Research = event.split(' ')
    show_research(sCurrent_Research)

  elif event == 'do_Research':
    do_research(sCurrent_Research)

  elif event == 'Stop_Research':
    window['Progressbar'].update(visible=False)
    window['Stop_Research'].update(visible=False)
    window['do_Research'].update(visible=True)
    bScience_ongoing = False

  if bScience_ongoing:
    iCurrent_Value += 1
    window['Progressbar'].update(current_count=iCurrent_Value)
    if iCurrent_Value == iMax_Science:
      print('Forschung beendet')
      bScience_ongoing = False
      SCIENCE[sCurrent_Research]['erforscht'] = True
      # window['TABLEINV'].update(values=[list(INVENTORY.values())])

      window['Progressbar'].update(visible=False)
      window['Stop_Research'].update(visible=False)

  if event != '__TIMEOUT__':
    print(f'ENDE {event = }')
    print(f'ENDE {values = }')
