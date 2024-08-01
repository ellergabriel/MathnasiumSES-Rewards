from urllib.request import urlopen
import re
import mechanicalsoup
from tkinter import *

login_url="https://radius.mathnasium.com/Student"
browser = mechanicalsoup.StatefulBrowser()
login_page = browser.open(login_url)
login_html = login_page.soup
print(login_html)
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

def clicked():
    browser["UserName"] = userName.get()
    browser["Password"] = password.get()
    response = browser.submit_selected()
    browser.launch_browser()

submitButton = Button(window, text="Submit", width = 25, height=5, bg="red", fg="black", command = clicked)

submitButton.grid(column=0, row=2)
window.mainloop()


