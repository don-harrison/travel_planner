DestinationButton = '''
MDButton:
    style: "tonal"
    theme_width: "Custom"
    height: "56dp"
    size_hint_x: .5

    MDButtonIcon:
        x: self.width
        icon: "plus"

    MDButtonText:
        id: text
        text: "{text}"
'''