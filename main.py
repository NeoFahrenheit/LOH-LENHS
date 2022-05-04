"""
Arquivo que contém o ponto principal de entrada do programa, a "função main".
main.py
"""

import wx
import welcome_screen
import global_variables as gv

if __name__ == '__main__':
    app = wx.App()

    gv.welcome_screen = welcome_screen.WelcomeWindow(None, 'LOH / LENHS')
    gv.welcome_screen.CenterOnScreen()
    gv.welcome_screen.Show()

    app.MainLoop()