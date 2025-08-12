"""
Arquivo que contém o ponto principal de entrada do programa, a "função main".
main.py
"""

def main():
    """Entry point for the application"""
    import wx
    from app.windows import welcome_screen
    import app.global_variables as gv
    
    app = wx.App()
    
    gv.welcome_screen = welcome_screen.WelcomeWindow(None, 'LOH / LENHS')
    gv.welcome_screen.CenterOnScreen()
    gv.welcome_screen.Show()
    
    app.MainLoop()
