import PySimpleGUI as sg

from science import SCIENCE
from gamestate import GAMESTATE


def create_research_layout():
    return [
        [
            sg.Button(button_text=name, key=f'Erforsche {name}', 
                     visible=not data.get('erforschbar nach', '') or GAMESTATE['Forschung'][data.get('erforschbar nach', '')]['erforscht']),
            sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung'][name]['erforscht'], key=f'img_{name}')
        ]
        for name, data in SCIENCE.items()
    ]

# Verwendung:
research_layout = create_research_layout()
print(research_layout)