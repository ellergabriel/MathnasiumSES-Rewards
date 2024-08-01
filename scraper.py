from urllib.request import urlopen
import re
import mechanicalsoup
from tkinter import *

loginUrl="https://radius.mathnasium.com/Student"
browser = mechanicalsoup.StatefulBrowser()
loginPage = browser.open(loginUrl)
loginHtml = loginPage.soup
print(loginHtml)
browser.select_form()
#browser.form.print_summary()
window = Tk()
window.title("Digital Rewards Tracker")
window.geometry('350x200')

uNameLbl = Label(window, text="Username")
uNameLbl.grid(column = 0, row = 0)
userName = Entry(window, width = 30)
userName.grid(column = 1, row = 0)

passLbl = Label(window, text = "Password")
passLbl.grid(column = 0, row = 1)
password = Entry(window, show = "*", width = 30)
password.grid(column = 1, row = 1)

def loginSub():
    browser["UserName"] = userName.get()
    browser["Password"] = password.get()
    #response = browser.submit_selected()
    #browser.launch_browser()
    window.geometry('1200x800')

submitButton = Button(window, text="Submit", width = 25, height=5, bg="red", fg="black", command = loginSub)

submitButton.grid(column=0, row=2)
window.mainloop()


