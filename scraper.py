from urllib.request import urlopen
import mechanicalsoup
import sqlite3
from tkinter import *
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

loginUrl= "https://radius.mathnasium.com/Student"
DRIVER_PATH = './chromedriver.exe'
service = Service(executable_path=DRIVER_PATH)
options = webdriver.ChromeOptions()
#options.add_argument("--headless=new")
driver = webdriver.Chrome(service=service, options=options)
action = ActionChains(driver)

stu_db = sqlite3.connect("students.db")
stu_cur = stu_db.cursor()
stu_table = """CREATE TABLE IF NOT EXISTS Students(
                fName CHAR(31),
                lName CHAR(31),
                cards INT
            );"""
stu_cur.execute(stu_table)
print(stu_cur.fetchall())

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

def recordStudent(students):
    driver.implicitly_wait(0)
    for stu in students:
        driver.execute_script("window.open('%s', '_blank')" %stu.get_attribute('href'))
        driver.switch_to.window(driver.window_handles[-1])
        print(driver.find_element(By.ID, 'cardsAvailableDetail').text)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        #action.key_down(Keys.CONTROL)
        #action.click(student)

#Function handles capturing student information for database entry/updates
def parseStudents():
    driver.implicitly_wait(5)
    studentReg = "a[@href=/Student/Details/]"
    studentList = driver.find_elements(By.XPATH, "//a[starts-with(@href, '/Student/Details')]")
    recordStudent(studentList)
    #studentTable = driver.find_element(By.CLASS_NAME, 'k-master-row')
    #driver.find_element(By.XPATH, "//table/div[@id='gridStudent']")
    #print(studentTable.get_attribute('innerHTML'))

#Function interacts with Student Management page, TODO: update to dynamically select enrollment filter
def generateStudents():
    print("Login successful")
    enrollFilterPath = "//div[@class='container']//div[@id='single-Grid-Page']/div[2]/div[1]/div[1]/div[3]/div[1]/span[1]"
    enFill = driver.find_element(By.XPATH, enrollFilterPath)
    enFill.click()
    for i in range(3) :
        enFill.send_keys(Keys.DOWN)
    enFill.send_keys(Keys.ENTER)
    driver.find_element(By.ID, 'btnsearch').click()
    parseStudents()
    
#Function access 'Student Management' page, handles login on intial boot 
def loginSub():
    uName = userName.get()
    pWord = password.get() 
    driver.get(loginUrl)
    driver.find_element(By.ID, "UserName").send_keys(uName)
    driver.find_element(By.ID, "Password").send_keys(pWord)
    driver.find_element(By.ID, "login").click()
    if not("Login" in driver.current_url):
        submitButton.destroy()
        passLbl.destroy()
        uNameLbl.destroy()
        userName.destroy()
        password.destroy()
        generateStudents()
        window.geometry('1200x800')
    else:
        errorLbl = Label(window, text = "ERROR: Unable to login")
        errorLbl.grid(column = 1, row = 2)
    #browser.launch_browser()
    
    

submitButton = Button(window, text="Submit", width = 10, height=3, bg="red", fg="black", command = loginSub)

submitButton.grid(column=0, row=2)
window.mainloop()
driver.quit()


