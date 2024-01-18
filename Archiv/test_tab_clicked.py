import PySimpleGUI as sg


font = ('Courier New', 11)
sg.theme('DarkBlue3')
sg.set_options(font=font)

multiline_options = {
    "size"              : (80, 10),
    "expand_x"          : True,
    "expand_y"          : True,
    "text_color"        : 'black',
    "enable_events"     : True,
    "border_width"      : 0,
    "background_color"  : '#454545',
    "do_not_clear"      : True,
    "auto_size_text"    : True,
}

items = ("facebook", "instagram", "twitter")
tab_group_layout = [
    [
        sg.Tab(
            f'{item.title()} Post',
            [
                [
                    sg.Multiline(
                        f"Click [Get Info] to populate data for {item} post",
                        key=f"post_{item}",
                        **multiline_options
                    )
                ]
            ],
            key=item
        )
        for item in items
    ]
]

layout = [
    [
        sg.TabGroup(tab_group_layout, change_submits=True, enable_events=True, key='-TABGROUP-'),   # Option change_submits=True replaced by enable_events=True
    ],
]
window = sg.Window("Title", layout)

while True:

    event, values = window.read()
    print(f'ENDE {event = }')
    print(f'ENDE {values = }')

    if event == sg.WINDOW_CLOSED:
        break
    elif event == '-TABGROUP-':
        print(f"Tab '{values[event]}' clicked")

window.close()
