from urllib.request import urlopen
import mechanicalsoup
from tkinter import *
from selenium import webdriver

loginUrl= "https://radius.mathnasium.com/Student"
driver = webdriver.Chrome('/')

"""browser = mechanicalsoup.StatefulBrowser()
loginPage = browser.open(loginUrl)
loginHtml = loginPage.soup
browser.select_form()
#browser.form.print_summary()"""

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

def parseStudents():
    print("shazbot")

def loginSub():
    """browser["UserName"] = userName.get()
    browser["Password"] = password.get()
    response = browser.submit_selected()
    regUrl = str(browser.url)"""
    if (regUrl.find("Login") == -1):
        window.geometry('1200x800')
        submitButton.destroy()
        passLbl.destroy()
        uNameLbl.destroy()
        userName.destroy()
        password.destroy()
        browser.refresh()
        parseStudents()
    else:
        errorLbl = Label(window, text = "ERROR: Unable to login")
        errorLbl.grid(column = 1, row = 2)
    #browser.launch_browser()
    
    

submitButton = Button(window, text="Submit", width = 10, height=3, bg="red", fg="black", command = loginSub)

submitButton.grid(column=0, row=2)
window.mainloop()


