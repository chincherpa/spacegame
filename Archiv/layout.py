import PySimpleGUI as sg

from inventory import INVENTORY

lTab_HQ = [
          [sg.Column([
            [sg.Text("HQ")],
            [sg.Text("PLACEHOLDER")]
          ])]
        ]

lTab_Science = [
          [sg.Column([
            [sg.Text("Forschung1")],
            [sg.Text("PLACEHOLDER1")]
          ]),
          sg.Column([
            [sg.Text("Forschung2")],
            [sg.Text("PLACEHOLDER2")],
            [sg.Button(button_text="Eisen +1")]
          ])
          ]
        ]

node_table = sg.Table(values = list(INVENTORY.values()), headings = list(INVENTORY.keys()),
                    def_col_width = 12,
                    auto_size_columns=False,
                    display_row_numbers=False,
                    justification='right',
                    num_rows=5,
                    row_height=25,
                    key = '-NDTABLE-',
                    tooltip='This is a table')

lTab_Inventory = [
  [sg.Text('Baumaterial')],
  [sg.Table(values = [1,2,3]#list(INVENTORY.values())#, headings = list(INVENTORY.keys()),
                    # def_col_width = 10,
                    # auto_size_columns=False,
                    # display_row_numbers=False,
                    # justification='right',
                    # num_rows=1,
                    # row_height=25,
                    # key = '-NDTABLE-',
                    # tooltip='This is a table'
                    )]
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
          ])]
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
      ]])
  ]])
]]