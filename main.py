import json

import PySimpleGUI as sg

import config
from actions import ACTIONS

sg.theme('Dark Teal 6')

def load_gamestate():
  try:
    with open(config.SAVEFILE,"r") as file:
      return json.load(file)
  except FileNotFoundError:
    from gamestate import GAMESTATE
    return GAMESTATE

GAMESTATE = load_gamestate()

def save_gamestate():
  GAMESTATE['Ticks'] = fTicks
  GAMESTATE['Credits'] = iCredits
  GAMESTATE['Forschungspunkte'] = iForschungspunkte
  with open(config.SAVEFILE, "w") as outfile: 
    json.dump(GAMESTATE, outfile)

def show_research(sAktuelle_Forschung):
  window['do_Research'].update(visible=False)
  window['already_researched'].update(visible=False)

  window['desc_Research'].update(visible=True, value=GAMESTATE['Forschung'][sAktuelle_Forschung]['beschreibung'])
  window['desc_dauer'].update(visible=True, value=f'Forschungsdauer: {GAMESTATE['Forschung'][sAktuelle_Forschung]['dauer']} Zyklen')

  if not bForschung_aktiv and not GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht']:
    window['do_Research'].update(visible=True)

  # if GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht']:
  window['already_researched'].update(visible=GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht'])

def do_research(sAktuelle_Forschung):
  global bForschung_aktiv
  global iCurrent_Value
  global iMax_Science
  window['do_Research'].update(visible=False)
  bForschung_aktiv = True
  iMax_Science = GAMESTATE['Forschung'][sAktuelle_Forschung]['dauer'] / config.TICK
  iCurrent_Value = 0
  window['Progressbar'].update(current_count=0, max=iMax_Science)
  window['Progressbar'].update(visible=True)
  window['Stop_Research'].update(visible=True)
  # 'ColForschung'

def get_materials_from_inventory():
  lMaterials = []
  for material, amount in GAMESTATE['Inventar'].items():
    lMaterials.append([sg.Text(material)])
  return lMaterials

def get_amounts_from_inventory():
  lAmounts = []
  for material, amount in GAMESTATE['Inventar'].items():
    lAmounts.append([sg.Text(amount)])
  return lAmounts

def add2log(sString):
  global sLog
  sTicks = f"{round(fTicks, 1)}"
  sLog = f"{sTicks}\t{sString}\n" + sLog
  window['Log'].update(value=sLog)


menu_def = [['&File', ['&Load', '&Save']]]

lTab_HQ = [[sg.Column([[sg.Text('HQ')], [sg.Text('PLACEHOLDER')]])]]

lTab_Science = [
  [
    sg.Column([
      [sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung']['Baumaterial']['erforscht'], key='imgBaumaterial'), sg.Button(button_text='Erforsche Baumaterial')],
      [sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung']['Eisenbarren']['erforscht'], key='imgEisenbarren'), sg.Button(button_text='Erforsche Eisenbarren')],
      [sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung']['Mondlander']['erforscht'], key='imgMondlander'), sg.Button(button_text='Erforsche Mondlander')],
      [sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung']['Rakete']['erforscht'], key='imgRakete'), sg.Button(button_text='Erforsche Rakete')],
      [sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung']['Raumsonde']['erforscht'], key='imgRaumsonde'), sg.Button(button_text='Erforsche Raumsonde')],
      [sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung']['Werkzeug']['erforscht'], key='imgWerkzeug'), sg.Button(button_text='Erforsche Werkzeug')],
    ], key='ColForschung'),
    sg.VerticalSeparator(),
    sg.Column([
      [sg.Text('WHAT TO RESEARCH', key='desc_Research', visible=False, size=(30, 6))],
      [sg.Text('', key='desc_Research', visible=False, size=(30, 6))],
      [sg.Text('', key='desc_dauer', visible=False)],
      [
        sg.Button('Erforschen', key='do_Research', visible=False),
        sg.Text('erforscht', key='already_researched', visible=False)
      ],
  [
    sg.ProgressBar(0, orientation='h', size=(20, 20), key='Progressbar', visible=False),
    sg.Button('Erforschen stoppen', key='Stop_Research', visible=False),
  ],
    ]),
  ],
]

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
      [sg.Button(button_text='Erforsche Baumaterial')],
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

sLog = '\n'.join(GAMESTATE['Log'])

LAYOUT = [[sg.Menu(menu_def, )],
  [
    [
      sg.Text(text='Cycle:', key='tCycles'),
      sg.Text(text='Credits:', key='tCredits'),
      sg.Text(text='Forschungspunkte:', key='tForschungspunkte'),
    ],
    # sg.Column(
    #   [
    #     [sg.Button(button_text='HQ')],
    #     [sg.Button(button_text='Forschung')],
    #     [sg.Button(button_text='Inventar')],
    #     [sg.Button(button_text='Planeten')],
    #     [sg.Button(button_text='Shop')],
    #   ]
    # ),
    sg.Column([
      [sg.TabGroup([
        [
          sg.Tab('HQ', lTab_HQ, key='TAB_HQ', image_source=r'images\TAB_HQ.png', image_subsample=config.IMAGE_SUBSAMPLE),
          sg.Tab('Forschung', lTab_Science, key='TAB_SCIENCE', image_source=r'images\TAB_SCIENCE.png', image_subsample=config.IMAGE_SUBSAMPLE),
          sg.Tab('Inventar', lTab_Inventory, key='TAB_INVENTORY', image_source=r'images\TAB_INVENTORY.png', image_subsample=config.IMAGE_SUBSAMPLE),
          sg.Tab('Planeten', lTab_Planets, key='TAB_PLANETS', image_source=r'images\TAB_PLANETS.png', image_subsample=config.IMAGE_SUBSAMPLE),
          sg.Tab('Shop', lTab_Shop, key='TAB_SHOP', image_source=r'images\TAB_SHOP.png', image_subsample=config.IMAGE_SUBSAMPLE),
        ]
      ], expand_x=True, expand_y=True, change_submits=True, enable_events=True, key='TabGroup_Main', tab_location='left')]
    ]),
    sg.Column([[sg.Image(r'images\TAB_HQ.png', key='image_Spalte3')]])
  ],

  [
    [
      sg.Column([
        [sg.Multiline(sLog, font=('Consolas', 8), disabled=True, size=(615, 50), key='Log')]
      ],
      size=(615, 50)
      )
    ]
  ]
]

fTicks = GAMESTATE['Ticks']
iCredits = GAMESTATE['Credits']
iForschungspunkte = GAMESTATE['Forschungspunkte']
inventory = GAMESTATE['Inventar']

bForschung_aktiv = False
iCurrent_Value = None
sAktuelle_Forschung = list(GAMESTATE['Forschung'].keys())[0]

window = sg.Window(config.TITLE, LAYOUT, size=config.WINDOW_SIZE, resizable=True)

while True:
  event, values = window.read(config.WINDOW_READ)
  fTicks += config.TICK
  window['tCycles'].update(f'Cycle: {fTicks:.1f}')
  window['tCredits'].update(f'Credits: {iCredits}')
  window['tForschungspunkte'].update(f'Forschungspunkte: {iForschungspunkte}')

  # print(f'START {event = }')
  # print(f'START {values = }')

  if event in (sg.WINDOW_CLOSED, 'Exit'):
    break

  if event == 'TabGroup_Main':
    window['image_Spalte3'].update(filename=rf'images\{values['TabGroup_Main']}.png')
    if values['TabGroup_Main'] == 'TAB_SCIENCE':
      show_research(sAktuelle_Forschung)

  elif event == 'HQ':
    window['TAB_HQ'].select()
    window['image_Spalte3'].update(filename=r'images\TAB_HQ.png')

  elif event == 'Forschung':
    window['TAB_SCIENCE'].select()
    window['image_Spalte3'].update(filename=r'images\TAB_SCIENCE.png')

  elif event == 'Inventar':
    window['TAB_INVENTORY'].select()
    window['image_Spalte3'].update(filename=r'images\TAB_INVENTORY.png')

  elif event == 'Planeten':
    window['TAB_PLANETS'].select()
    window['image_Spalte3'].update(filename=r'images\TAB_PLANETS.png')

  elif event == 'Shop':
    window['TAB_SHOP'].select()
    window['image_Spalte3'].update(filename=r'images\TAB_SHOP.png')

  elif 'Erforsche ' in event:
    _, sAktuelle_Forschung = event.split(' ')
    show_research(sAktuelle_Forschung)

  elif event == 'do_Research':
    # sLog = f"Erforsche '{sAktuelle_Forschung}'\n" + sLog
    # window['Log'].update(value=sLog)
    add2log(f"Erforsche '{sAktuelle_Forschung}'")
    do_research(sAktuelle_Forschung)

  elif event == 'Stop_Research':
    window['Progressbar'].update(visible=False)
    window['Stop_Research'].update(visible=False)
    window['do_Research'].update(visible=True)
    add2log(f"Forschung von '{sAktuelle_Forschung}' gestoppt")
    bForschung_aktiv = False

  elif event == 'Save':
    save_gamestate()

  elif event == 'Load':
    GAMESTATE = load_gamestate()
    fTicks = GAMESTATE['Ticks']
    iCredits = GAMESTATE['Credits']
    iForschungspunkte = GAMESTATE['Forschungspunkte']


  if bForschung_aktiv:
    iCurrent_Value += 1
    window['Progressbar'].update(current_count=iCurrent_Value)
    if iCurrent_Value == iMax_Science:
      print(f"Forschung von '{sAktuelle_Forschung}' beendet")
      sLog = f"Forschung von '{sAktuelle_Forschung}' beendet\n" + sLog
      window['Log'].update(value=sLog)
      bForschung_aktiv = False
      GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht'] = True
      # window['TABLEINV'].update(values=[list(GAMESTATE['Inventar'].values())])

      window['Progressbar'].update(visible=False)
      window['Stop_Research'].update(visible=False)
      window['already_researched'].update(visible=True)
      window[f'img{sAktuelle_Forschung}'].update(visible=True)


  if event != '__TIMEOUT__':
    print(f'ENDE {event = }')
    print(f'ENDE {values = }')
