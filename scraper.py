from urllib.request import urlopen
import mechanicalsoup
from tkinter import *
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By 

loginUrl= "https://radius.mathnasium.com/Student"
DRIVER_PATH = './chromedriver.exe'
service = Service(executable_path=DRIVER_PATH)
options = webdriver.ChromeOptions()
#options.add_argument("--headless=new")
driver = webdriver.Chrome(service=service, options=options)

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
    uName = userName.get()
    pWord = password.get() 
    driver.get(loginUrl)
    radUName = driver.find_element(By.ID, "UserName")
    radPass = driver.find_element(By.ID, "Password")
    radUName.send_keys(uName)
    radPass.send_keys(pWord)
    if (True): #(regUrl.find("Login") == -1)
        window.geometry('1200x800')
        submitButton.destroy()
        passLbl.destroy()
        uNameLbl.destroy()
        userName.destroy()
        password.destroy()
        parseStudents()
    else:
        errorLbl = Label(window, text = "ERROR: Unable to login")
        errorLbl.grid(column = 1, row = 2)
    #browser.launch_browser()
    
    

submitButton = Button(window, text="Submit", width = 10, height=3, bg="red", fg="black", command = loginSub)

submitButton.grid(column=0, row=2)
window.mainloop()
driver.quit()


