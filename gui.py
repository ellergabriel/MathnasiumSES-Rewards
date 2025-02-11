from tkinter import Label, Menu, Entry, Toplevel, Message
import os
def initializeGui(window):
    # Window setup
    window.title("Digital Rewards Tracker")
    window.geometry('350x200')
    
    # Username and password fields
    uNameLbl = Label(window, text="Username")
    uNameLbl.grid(column=0, row=0)
    userName = Entry(window, width=30)
    userName.grid(column=1, row=0)

    passLbl = Label(window, text="Password")
    passLbl.grid(column=0, row=1)
    password = Entry(window, show="*", width=30)
    password.grid(column=1, row=1)

    # Menu
    menubar = Menu(window)
    topMenu = Menu(window)
    settingsMenu = Menu(topMenu, tearoff=0)
    topMenu.add_cascade(menu = settingsMenu, label = "Settings")
    settingsMenu.add_command(label = "Credentials", command=credentialsMenu)
    window.config(menu = topMenu)

    """Local testing"""
    #window.iconbitmap("A+.ico")
    """deliverable"""
    window.iconbitmap(os.path.join(os.path.dirname(__file__), 'A+.ico'))
    
    return userName, password, uNameLbl, passLbl

def createRefreshMessage(window):
    topMessage = Toplevel()
    topMessage.title("")
    refreshMsg = Message(topMessage, text="Refreshing your card count, please be patient.", font=('Arial', 25, 'bold'))
    refreshMsg.pack(expand=True)
    topMessage.geometry('400x400')
    
    topX = window.winfo_x() + window.winfo_width() // 2 - 200
    topY = window.winfo_y() + window.winfo_height() // 2 - 200
    topMessage.geometry(f"+{topX}+{topY}")
    
    topMessage.update()
    topMessage.grab_set()
    
    return topMessage

# Function overrides [x] in window toolbar, prevents students from closing window without entering the pin
def customExit():
    exitConfirm = Toplevel()
    exitConfirm.title("DO NOT TOUCH")
    exitConfirm.geometry("300x300")
    warningLabel = Label(exitConfirm, text = "DO NOT TOUCH THE RED X", font = ('Impact', 50, 'bold'), wraplength = 300, justify = "center")
    warningLabel.grid()
    exitConfirm.update()
    
def testMenu():
    print("Menu button is working")

def credentialsMenu():
    print("Opening credentials menu")