import PySimpleGUI as sg

# from inventory import INVENTORY
from layout import LAYOUT

window = sg.Window("Game", LAYOUT, size=(600, 400))
fTicks = 0
iCredits = 500

# tab_keys = ('-TAB_HQ-','-TAB_EARTH-','-TAB_MOON-', '-TAB_MARS-')

dGamestate = {
  
}

while True:
  event, values = window.read(1000)
  fTicks += 0.1
  window['tCycles'].update(f'Cycle: {fTicks:.1f}')
  window['tCredits'].update(f'Credits: {iCredits}')

  if event != '__TIMEOUT__':
    print(event)
  if event in (
    sg.WINDOW_CLOSED, "Exit"):
    break
  if event == "HQ":
    window['-TAB_HQ-'].update(visible=True)
    window['-TAB_SCIENCE-'].update(visible=False)
    window['-TAB_INVENTORY-'].update(visible=False)
    window['-TAB_PLANETS-'].update(visible=False)
  elif event == "Forschung":
    window['-TAB_HQ-'].update(visible=False)
    window['-TAB_SCIENCE-'].update(visible=True)
    window['-TAB_INVENTORY-'].update(visible=False)
    window['-TAB_PLANETS-'].update(visible=False)
  elif event == "Inventar":
    window['-TAB_HQ-'].update(visible=False)
    window['-TAB_SCIENCE-'].update(visible=False)
    window['-TAB_INVENTORY-'].update(visible=True)
    window['-TAB_PLANETS-'].update(visible=False)
  elif event == "Planeten":
    window['-TAB_HQ-'].update(visible=False)
    window['-TAB_SCIENCE-'].update(visible=False)
    window['-TAB_INVENTORY-'].update(visible=False)
    window['-TAB_PLANETS-'].update(visible=True)

