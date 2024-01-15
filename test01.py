import PySimpleGUI as sg

q1 = [[
  sg.Column([
    [
  sg.Text(text="Cycle:", key="t1")], [
  sg.Button(button_text="HQ")], [
  sg.Button(button_text="Forschung")], [
  sg.Button(button_text="Inventar")]]),

  sg.Column([[
    sg.TabGroup([
      [
        sg.Tab("HQ", [
          [sg.Column([
            [sg.Text("HQ")],
            [sg.Text("PLACEHOLDER")]
          ])]
        ], border_width=3),

      sg.Tab("Planeten", [
        [sg.TabGroup([
          [sg.Tab("Erde",
            [
              [sg.Text("Erde")],
            ]
          , key='-TAB_EARTH-')],
          [sg.Tab("Mond",
            [
            [sg.Text("Mond")],
            ], key='-TAB_MOON-')],
          [sg.Tab("Mars",
            [
              [sg.Text("Mars")],
            ], key='-TAB_MARS-')
          ]
        ])]
      ], border_width=5)
    ]])
  ]])]]

window =sg.Window("Game", q1)
ticks = 0
while True:
  event, values = window.read(1000)
  ticks += 0.1
  window['t1'].update(f'Cycle: {ticks:.1f}')
  if event != '__TIMEOUT__':
    print(event)
  if event in (sg.WINDOW_CLOSED, "Exit"):
    break

