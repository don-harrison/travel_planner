from kivymd.uix.button import MDButton, MDButtonIcon, MDButtonText
from kivy.metrics import dp

def add_tonal( text):
    text = MDButtonText(
    text=text,
    size_hint_x=1,
    valign="center",
    halign="center",
    ) 
    
    btn = MDButton(
        text,
        style="tonal",
        height=dp(56),
        size_hint_x=1
    )
    return btn
