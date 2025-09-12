import json
import time

import config
from actions import ACTIONS
from materials import MATERIALS
from science import SCIENCE

def load_gamestate():
  print('load_gamestate()')
  try:
    with open(config.SAVEFILE, "r") as file:
      print('config.SAVEFILE gefunden')
      return json.load(file)
  except FileNotFoundError:
    from gamestate import GAMESTATE
    print('GAMESTATE importiert')
    return GAMESTATE

GAMESTATE = load_gamestate()

for name, data in SCIENCE.items():
  print(f'{name = }')
  if name == 'Eisenbarren':
    continue
  print(f'{GAMESTATE['Forschung'][data['erforschbar nach']]['erforscht'] = }')




#       [
#         sg.Button(button_text=name, key=f'Erforsche {name}', visible=name == 'Eisenbarren' or GAMESTATE['Forschung'][data['erforschbar nach']]['erforscht'] or
#                   (data.get('erforschbar nach', '') and GAMESTATE['Forschung'].get(data.get('erforschbar nach', ''), {}).get('erforscht', False))),
#         sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung'][name]['erforscht'], key=f'img_{name}')
#       ]
#       for name, data in SCIENCE.items()
#     ]),
#     sg.VerticalSeparator(),
#     sg.Column([
#       [sg.Text('', key='desc_research', visible=False, size=(30, 6))],
#       [sg.Text('', key='desc_dauer', visible=False)],
#       [sg.Text('', key='desc_costs', visible=False)],
#       [sg.Text('', key='comment', visible=False)],
#       [
#         sg.Button('Erforschen', key='do_research', visible=False),
#         sg.Text('erforscht', key='already_researched', visible=False)
#       ],
#       [
#         sg.ProgressBar(0, orientation='h', size=(20, 20), key='progressbar_Forschung', visible=False),
#         sg.Button('Erforschen stoppen', key='stop_research', visible=False),
#       ],
#     ]),
#   ],
# ]
