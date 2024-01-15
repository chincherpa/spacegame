import PySimpleGUI as sg

def hide(key, settings):

    setting = not settings[key]
    settings[key] = setting
    window[key].update(visible=setting)

def layout(settings):

    selection1 = [
        [sg.Text("Select item1:")]] + [
        [sg.Checkbox(f"Item {j*3+i+1}")
            for i in range(3)] for j in range(3)
    ]

    selection2 = [
        [sg.Text("Select item2:")]] + [
        [sg.Checkbox(f"Item {j*3+i+1}")
            for i in range(4)] for j in range(2)
    ]

    form = [
        [sg.Text('Selection'), sg.Button("Item 1"), sg.Button("Item 2")],
        [sg.pin(sg.Column(selection1, visible=settings['Col 1'], key='Col 1'), shrink=False)],
        [sg.pin(sg.Column(selection2, visible=settings['Col 2'], key='Col 2'), shrink=False)],
    ]

    return form

settings = {'Col 1':True, 'Col 2':False}

sg.theme('DarkBlue')
window = sg.Window('Title', layout(settings), size=(250, 260),
    use_default_focus=False, finalize=True)

for key, element in window.AllKeysDict.items():  # remove dash box from elements
    element.Widget.configure(takefocus=0)

while True:

    event, values = window.read()

    if event == sg.WINDOW_CLOSED:
        break
    elif event in ("Item 1", "Item 2"):
        key = 'Col 1' if event == 'Item 1' else 'Col 2'
        hide(key, settings)

window.close()