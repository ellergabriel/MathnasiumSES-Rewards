from urllib.request import urlopen
import mechanicalsoup
import sqlite3
from tkinter import *
import datetime
import multiprocessing
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

#Selenium 
loginUrl= "https://radius.mathnasium.com/Student"
DRIVER_PATH = './chromedriver.exe'
service = Service(executable_path=DRIVER_PATH)
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--blink-settings=imageEnabled=false")
driver = webdriver.Chrome(service=service, options=options)
action = ActionChains(driver)

#SQLite 
stuDB = sqlite3.connect("students.db")
stuCur = stuDB.cursor()
stuTable = "CREATE TABLE IF NOT EXISTS Students(fName CHAR(31),lName CHAR(31),cards INT, UNIQUE(fName, lName));"
stuCur.execute(stuTable)
stuCur.execute("SELECT * FROM Students ORDER BY fName ASC")
print(stuCur.fetchall())

#Tkinter widgets
window = Tk()
window.title("Digital Rewards Tracker")
window.geometry('350x200')
WINDOW_HEIGHT = 800
WINDOW_WIDTH = 1200

uNameLbl = Label(window, text="Username")
uNameLbl.grid(column = 0, row = 0)
userName = Entry(window, width = 30)
userName.grid(column = 1, row = 0)

passLbl = Label(window, text = "Password")
passLbl.grid(column = 0, row = 1)
password = Entry(window, show = "*", width = 30)
password.grid(column = 1, row = 1)

#Helper function for splitting student names into first and last 
def splitStudentName(student):
    index = student.rfind(" ")
    fName = student[0 : index]
    lName = student[index + 1:]
    return [fName, lName]

#Helper function that takes the generated studentList and prunes based on previously seen href literals
def pruneStudents(studentList):
    viewedRefs = {}
    lcv = 0
    while(lcv < len(studentList)):
        stuHref = studentList[lcv].get_attribute('href')
        if stuHref not in viewedRefs:
            viewedRefs[stuHref] = True
            lcv += 1
        else:
            studentList.pop(lcv)

#Function takes in list of Student profiles from Radius and opens each in a new tab, recording full name and card count
def recordStudent(students):
    driver.implicitly_wait(0)
    viewedStu={}
    startTime = datetime.datetime.now()
    for stu in students:
        driver.execute_script("window.open('%s', '_blank')" % stu.get_attribute('href'))
        driver.switch_to.window(driver.window_handles[-1])
        [fHolder, lHolder] = splitStudentName(driver.title)
        cards = (int)(driver.find_element(By.ID, 'cardsAvailableDetail').text)
        print(driver.title + " " + str(cards))
        stuCur.execute("INSERT OR IGNORE INTO Students(fName, lName, cards) values(?,?,?)",(fHolder, lHolder, cards))
        stuCur.execute("UPDATE Students SET cards = ? WHERE fName = ? AND lName = ?", (cards, fHolder, lHolder))
        stuDB.commit()
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    print(startTime.time())
    finishTime = datetime.datetime.now()
    print(finishTime.time())
        


#Function handles capturing student information for database entry/updates
def parseStudents():
    driver.implicitly_wait(5)
    studentReg = "//a[starts-with(@href, '/Student/Details')]"
    global studentList
    studentList = driver.find_elements(By.XPATH, studentReg)
    """debug prints"""
    #print("Pre-prune size: " + str(len(studentList)))
    pruneStudents(studentList)
    #print("Post-prune size: " + str(len(studentList)))
    #recordStudent(studentList)
    

#Function interacts with Student Management page, TODO: update to dynamically select enrollment filter
def generateStudents():
    print("Login successful")
    enrollFilterPath = "//div[@class='container']//div[@id='single-Grid-Page']/div[2]/div[1]/div[1]/div[3]/div[1]/span[1]"
    enFill = driver.find_element(By.XPATH, enrollFilterPath)
    enFill.click()
    for i in range(3): #manually scrolls through Enrollment Filters, should be fixed to dynamically find "enrolled"
        enFill.send_keys(Keys.DOWN)
    enFill.send_keys(Keys.ENTER)
    driver.find_element(By.ID, 'btnsearch').click()
    parseStudents()

#Function changes tkinter window to UX that students can interact with 
def createStudentDisplay():
    window.grid_rowconfigure(0, weight = 1)

    outerFrame = Frame(window, bg = "red")
    outerFrame.grid(row = 0, column = 0, sticky = "N")

    frameCanvas = Canvas(outerFrame, bg = "yellow")
    frameCanvas.grid(row = 0, column = 0, sticky = "news")
    
    rowWidgets = 1
    rowLCV = 0
    for row in stuCur.execute("SELECT * FROM Students ORDER BY fName ASC"):
        for col in range(rowWidgets):
            fName, lName, cards = row
            studentInfo = f'{fName} {lName}:  {cards}'
            #widg = Label(innerFrame, text = studentInfo, width = 30, font = ('Arial', 16, 'bold'))
            #widg.grid(column = col, row = rowLCV)
            rowLCV += 1
    
#Function access 'Student Management' page, handles login on intial boot 
def loginSub():
    uName = userName.get()
    pWord = password.get() 
    driver.get(loginUrl)
    driver.find_element(By.ID, "UserName").send_keys(uName)
    driver.find_element(By.ID, "Password").send_keys(pWord)
    driver.find_element(By.ID, "login").click()
    if not("Login" in driver.current_url):
        generateStudents()
        submitButton.destroy()
        passLbl.destroy()
        uNameLbl.destroy()
        userName.destroy()
        password.destroy()
        window.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')
        createStudentDisplay()
    else:
        errorLbl = Label(window, text = "ERROR: Unable to login")
        errorLbl.grid(column = 1, row = 2)
    #browser.launch_browser()
    
    

submitButton = Button(window, text="Submit", width = 10, height=3, bg="red", fg="black", command = loginSub)

submitButton.grid(column=0, row=2)
window.mainloop()
driver.quit()


