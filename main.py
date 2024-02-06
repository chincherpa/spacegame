import json

import PySimpleGUI as sg

import config
from actions import ACTIONS

sg.theme('Dark Teal 6')

bForschung_aktiv = False
bBauen_aktiv = False
iAktueller_Forschungsfortschritt = None
iAktueller_Baufortschritt = None

def load_gamestate():
  try:
    with open(config.SAVEFILE,"r") as file:
      return json.load(file)
  except FileNotFoundError:
    from gamestate import GAMESTATE
    return GAMESTATE

GAMESTATE = load_gamestate()

def dump_gamestate():
  GAMESTATE['Ticks'] = fTicks
  GAMESTATE['Credits'] = iCredits
  GAMESTATE['Forschungspunkte'] = iForschungspunkte
  with open(config.SAVEFILE, "w") as outfile: 
    json.dump(GAMESTATE, outfile)

def zeige_Forschung(sAktuelle_Forschung):
  window['do_research'].update(visible=False)
  window['already_researched'].update(visible=False)

  window['desc_research'].update(visible=True, value=GAMESTATE['Forschung'][sAktuelle_Forschung]['beschreibung'])
  window['desc_dauer'].update(visible=True, value=f'Forschungsdauer: {GAMESTATE['Forschung'][sAktuelle_Forschung]['dauer']} Zyklen')

  if not bForschung_aktiv and not GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht']:
    window['do_research'].update(visible=True)

  # if GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht']:
  window['already_researched'].update(visible=GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht'])

def zeige_bauen(sBauen):
  window['desc_bauen'].update(value=GAMESTATE['Werkstatt'][sBauen]['beschreibung'])
  window['desc_bauen'].update(value=f'Dauer: {GAMESTATE['Werkstatt'][sBauen]['dauer']} Zyklen')

def baue(sBauen):
  global bBauen_aktiv
  global iAktueller_Baufortschritt
  global iMax_Bauen
  window['do_research'].update(visible=False)
  bBauen_aktiv = True
  iMax_Bauen = GAMESTATE['Forschung'][sAktuelle_Forschung]['dauer'] / config.TICK
  iAktueller_Forschungsfortschritt = 0
  window['progressbar_Forschung'].update(current_count=0, max=iMax_Bauen)
  window['progressbar_Forschung'].update(visible=True)
  window['stop_research'].update(visible=True)

def erforsche(sAktuelle_Forschung):
  global bForschung_aktiv
  global iAktueller_Forschungsfortschritt
  global iMax_Forschung
  window['do_research'].update(visible=False)
  bForschung_aktiv = True
  iMax_Forschung = GAMESTATE['Forschung'][sAktuelle_Forschung]['dauer'] / config.TICK
  iAktueller_Forschungsfortschritt = 0
  window['progressbar_Forschung'].update(current_count=0, max=iMax_Forschung)
  window['progressbar_Forschung'].update(visible=True)
  window['stop_research'].update(visible=True)

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
  sLog = f"{round(fTicks, 1)}\t{sString}\n" + sLog
  window['Log'].update(value=sLog)

menu_def = [['&File', ['&Load', '&Save']]]

lTab_HQ = [
    # sg.Column([
    # ])
      [sg.Text(f'Astronauten auf der Erde: {GAMESTATE['Astronauten']['Erde']}')],
      [sg.Text(f'Astronauten auf dem Mond: {GAMESTATE['Astronauten']['Mond']}', visible=GAMESTATE['Planeten']['Mond']['entdeckt'])],
      [sg.Text(f'Astronauten auf dem Mars: {GAMESTATE['Astronauten']['Mars']}', visible=GAMESTATE['Planeten']['Mars']['entdeckt'])],
      [sg.Text('Sende eine Raumsonde in den Weltraum, um etwas zu entdecken', visible=not GAMESTATE['Planeten']['Mond']['entdeckt'])],
      [sg.Button('Starte Raumsonde', key='starte_raumsonde', visible=bool(GAMESTATE['Raumschiffe']['Erde']['Mondlander']['Anzahl']))],
  ]

lTab_Forschung = [
  [
    sg.Column([
      [
        sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung']['Baumaterial']['erforscht'], key='img_Baumaterial'),
        sg.Button(button_text='Erforsche Baumaterial', visible=GAMESTATE['Forschung']['Eisenbarren']['erforscht'])
      ],
      [
        sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung']['Eisenbarren']['erforscht'], key='img_Eisenbarren'),
        sg.Button(button_text='Erforsche Eisenbarren')
      ],
      [
        sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung']['Mondlander']['erforscht'], key='img_Mondlander'),
        sg.Button(button_text='Erforsche Mondlander', visible=GAMESTATE['Forschung']['Raumsonde']['erforscht'])
      ],
      [
        sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung']['Rakete']['erforscht'], key='img_Rakete'),
        sg.Button(button_text='Erforsche Rakete', visible=GAMESTATE['Forschung']['Mondlander']['erforscht'])
      ],
      [
        sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung']['Raumsonde']['erforscht'], key='img_Raumsonde'),
        sg.Button(button_text='Erforsche Raumsonde')
      ],
      [
        sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung']['Werkzeug']['erforscht'], key='img_Werkzeug'),
        sg.Button(button_text='Erforsche Werkzeug', visible=GAMESTATE['Forschung']['Eisenbarren']['erforscht'])
      ],
    ]),
    sg.VerticalSeparator(),
    sg.Column([
      [sg.Text('', key='desc_research', visible=False, size=(30, 6))],
      [sg.Text('', key='desc_dauer', visible=False)],
      [
        sg.Button('Erforschen', key='do_research', visible=False),
        sg.Text('erforscht', key='already_researched', visible=False)
      ],
  [
    sg.ProgressBar(0, orientation='h', size=(20, 20), key='progressbar_Forschung', visible=False),
    sg.Button('Erforschen stoppen', key='stop_research', visible=False),
  ],
    ]),
  ],
]

lForschung_auf_Erde = ['Raumsonde', 'Mondlander', 'Rakete']  # , 'Weltraumstation']

lTab_Werkstatt = [
  [
    sg.Column([
      [sg.Button('Baue Raumsonde', key='baue_Raumsonde', visible=GAMESTATE['Forschung']['Raumsonde']['erforscht'])],
      [sg.Button('Baue Mondlander', key='baue_Mondlander', visible=GAMESTATE['Forschung']['Mondlander']['erforscht'])],
      [sg.Button('Baue Rakete', key='baue_Rakete', visible=GAMESTATE['Forschung']['Rakete']['erforscht'])],
    ]),
    sg.VerticalSeparator(),
    sg.Column([
      [sg.Text('', key='desc_bauen', visible=False, size=(30, 6))],
      [sg.Text('', key='desc_bauen', visible=False)],
      [
        sg.Button('Bauen', key='do_bauen', visible=False),
      ],
      [
        sg.Button('Bauen abbrechen', key='stop_bauen', visible=bBauen_aktiv),
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
        [sg.Tab('Erde', lTab_Erde, key='tab_erde')],
        [sg.Tab('Mond', lTab_Mond, key='tab_mond')],
        [sg.Tab('Mars', lTab_Mars, key='tab_mars')],
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
      [sg.Text('', key='desc_fsfsdfsdf', visible=False, size=(30, 6))],
      [sg.Button('Kaufen', key='do_kaufen', visible='wenn credits reichen')],
    ]),
  ],
]

sLog = '\n'.join(GAMESTATE['Log'])
print(sLog)

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
          sg.Tab('Forschung', lTab_Forschung, key='TAB_FORSCHUNG', image_source=r'images\TAB_FORSCHUNG.png', image_subsample=config.IMAGE_SUBSAMPLE),
          sg.Tab('Werkstatt', lTab_Werkstatt, key='TAB_WERKSTATT', image_source=r'images\TAB_WERKSTATT.png', image_subsample=config.IMAGE_SUBSAMPLE),
          sg.Tab('Inventar', lTab_Inventory, key='TAB_INVENTAR', image_source=r'images\TAB_INVENTAR.png', image_subsample=config.IMAGE_SUBSAMPLE),
          sg.Tab('Planeten', lTab_Planets, key='TAB_PLANETEN', image_source=r'images\TAB_PLANETEN.png', image_subsample=config.IMAGE_SUBSAMPLE),
          sg.Tab('Shop', lTab_Shop, key='TAB_SHOP', image_source=r'images\TAB_SHOP.png', image_subsample=config.IMAGE_SUBSAMPLE),
        ]
      ], expand_x=True, expand_y=True, change_submits=True, enable_events=True, key='TabGroup_Main', tab_location='top')]
    ]),
    sg.Column([[sg.Image(r'images\TAB_HQ.png', key='img_Spalte3')]])
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
    dump_gamestate()
    break

  if event == 'TabGroup_Main':
    window['img_Spalte3'].update(filename=rf'images\{values['TabGroup_Main']}.png')
    if values['TabGroup_Main'] == 'TAB_FORSCHUNG':
      zeige_Forschung(sAktuelle_Forschung)

  elif event == 'HQ':
    window['tab_HQ'].select()
    window['img_Spalte3'].update(filename=r'images\TAB_HQ.png')

  elif event == 'Forschung':
    window['tab_Forschung'].select()
    window['img_Spalte3'].update(filename=r'images\TAB_FORSCHUNG.png')

  elif event == 'Inventar':
    window['tab_Inventar'].select()
    window['img_Spalte3'].update(filename=r'images\TAB_INVENTAR.png')

  elif event == 'Planeten':
    window['tab_Planeten'].select()
    window['img_Spalte3'].update(filename=r'images\TAB_PLANETEN.png')

  elif event == 'Shop':
    window['tab_Shop'].select()
    window['img_Spalte3'].update(filename=r'images\TAB_SHOP.png')

  elif 'Erforsche ' in event:
    _, sAktuelle_Forschung = event.split(' ')
    zeige_Forschung(sAktuelle_Forschung)

  elif 'Baue ' in event:
    _, sBauen = event.split(' ')
    baue(sBauen)

  elif event == 'do_research':
    add2log(f"Erforsche '{sAktuelle_Forschung}'")
    erforsche(sAktuelle_Forschung)

  elif event == 'stop_research':
    window['progressbar_Forschung'].update(visible=False)
    window['stop_research'].update(visible=False)
    window['do_research'].update(visible=True)
    add2log(f"Forschung von '{sAktuelle_Forschung}' gestoppt")
    bForschung_aktiv = False

  elif event == 'starte_bauen':
    add2log(f"Baue '{sBauen}'")
    baue(sBauen)

  elif event == 'stop_bauen':
    print('stop_bauen')

  elif event == 'Save':
    dump_gamestate()

  elif event == 'Load':
    GAMESTATE = load_gamestate()
    fTicks = GAMESTATE['Ticks']
    iCredits = GAMESTATE['Credits']
    iForschungspunkte = GAMESTATE['Forschungspunkte']

  elif event == 'refreshwindow':
    print('window.refresh()')
    print(GAMESTATE['Forschung'][sAktuelle_Forschung])
    window.refresh()

  if bForschung_aktiv:
    iAktueller_Forschungsfortschritt += 1
    window['progressbar_Forschung'].update(current_count=iAktueller_Forschungsfortschritt)
    if iAktueller_Forschungsfortschritt == iMax_Forschung:
      add2log(f"Forschung von '{sAktuelle_Forschung}' beendet")
      bForschung_aktiv = False
      GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht'] = True

      window['progressbar_Forschung'].update(visible=False)
      window['stop_research'].update(visible=False)
      window['already_researched'].update(visible=True)
      window[f'img_{sAktuelle_Forschung}'].update(visible=True)
      for sForschung in lForschung_auf_Erde:
        window[f'baue_{sForschung}'].update(visible=GAMESTATE['Forschung'][sForschung]['erforscht'])

      # window.refresh()

  if bBauen_aktiv:
    iAktueller_Forschungsfortschritt += 1
    # window['progressbar_Bauen'].update(current_count=iAktueller_Forschungsfortschritt)
    # if iAktueller_Forschungsfortschritt == iMax_Forschung:
    #   print(f"Forschung von '{sAktuelle_Forschung}' beendet")
    #   sLog = f"Forschung von '{sAktuelle_Forschung}' beendet\n" + sLog
    #   window['Log'].update(value=sLog)
    #   bForschung_aktiv = False
    #   GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht'] = True

    #   window['progressbar_Bauen'].update(visible=False)
    #   window['stop_research'].update(visible=False)
    #   window[f'img_{sAktuelle_Forschung}'].update(visible=True)
    #   for sForschung in lForschung_auf_Erde:
    #     window[f'baue_{sForschung}'].update(visible=GAMESTATE['Forschung'][sForschung]['erforscht'])

      # window.refresh()


  if event != '__TIMEOUT__':
    print(f'ENDE {event = }')
    print(f'ENDE {values = }')
