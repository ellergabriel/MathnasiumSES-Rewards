from urllib.request import urlopen
import sqlite3
from tkinter import *
from tkinter import ttk
from tkinter.ttk import Progressbar
import datetime
import multiprocessing
import os
import sys
import pickle
import chromedriver_binary
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
DRIVER_PATH = os.path.join(os.path.dirname(__file__), './chromedriver.exe')
service = Service(executable_path=DRIVER_PATH)
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--blink-settings=imageEnabled=false")
driver = webdriver.Chrome(service=service, options=options)
action = ActionChains(driver)

#Global variable to for all Selenium driver instances
"""Pickle file must go in order as follows:
1. datetime object - last timestamp that the student list was parsed
2. integer - number of enrolled students
3. dictionary - STUDENT_HREFS with (full name, link to student page) key/value pairs
"""
PICKLE_FILE = 'timestamp.pkl'

class Student():

    def __init__(self, fName, lName, cards, href, studentFrame, isPrime, rowLCV):
        self.fName = fName
        self.lName = lName
        self.cards = cards
        self.href = href
        studentInfo = f'{fName} {lName}:  {cards}'
        self.lbl = Label(studentFrame, text = studentInfo, width = 30, font = ('Arial', 16, 'bold'))
        if not isPrime:
            self.lbl.configure(bg = "gray")
        self.btn = Button(studentFrame, text = "REFRESH", command = self.refreshCards)
        self.lbl.grid(column = 0, row = rowLCV, sticky = 'news')
        self.btn.grid(column = 1, row = rowLCV, sticky = 'news', padx = 40)

    #function that controls refresh button behavior in main GUI display
    def refreshCards(self):
        href = STUDENT_HREFS[self.fName + " " + self.lName]
        driver.execute_script("window.open('%s', '_blank')" % href)
        driver.switch_to.window(driver.window_handles[-1])
        self.cards = (int)(driver.find_element(By.ID, 'cardsAvailableDetail').text)
        stuCur.execute("UPDATE Students SET cards = ? WHERE fName = ? AND lName = ?", (self.cards, self.fName, self.lName))
        stuDB.commit()
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        studentInfo = f'{self.fName} {self.lName}: {self.cards}'
        self.lbl.config(text = studentInfo)

#SQLite 
stuDB = sqlite3.connect("students.db")
stuCur = stuDB.cursor()
stuTable = "CREATE TABLE IF NOT EXISTS Students(fName CHAR(31),lName CHAR(31),cards INT, UNIQUE(fName, lName));"
#stuCur.execute(stuTable)
#stuCur.execute("SELECT * FROM Students ORDER BY fName ASC")
#print(stuCur.fetchall())

#Tkinter widgets
window = Tk()
window.title("Digital Rewards Tracker")
window.geometry('350x200')
WINDOW_HEIGHT = 800
WINDOW_WIDTH = 800

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
#Function uses pickling to determine last time the full student list was parsed as well as if students were dropped/added
def recordStudent(students):
    driver.implicitly_wait(0)
    startTime = datetime.datetime.now()
    timeout = 12 #hours
    
    global STUDENT_HREFS
    STUDENT_HREFS = {}
    try:
        with open(PICKLE_FILE, 'rb+') as file:
            lastTime = pickle.load(file)
            print("Last timestamp found")
            timeDiff = (startTime - lastTime).seconds / 3600 #converts time difference into hours
            print(str(timeDiff) + " hour time difference")
            studentCount = pickle.load(file)
            print("Student count found")
            if(timeDiff < timeout and len(students) == studentCount):
                STUDENT_HREFS = pickle.load(file)
                print("STUDENT_HREFS loaded: ")
                file.close()
                print("within 12 hours of last update, skipping database refresh...")
                return
            print("over 12 hours since last database update, refreshing student information...")
    except:
        print("ERROR: Unsuccessful fetching of time stamp or student hrefs, proceeding with database refresh...")
        #file.close()
    print("parsing student information...")
    
    STUDENT_HREFS = {} #reset dictionary, previous unsuccessful unpickling sets variable as NoneType otherwise
    for stu in students:
        stuHref = stu.get_attribute('href')
        driver.execute_script("window.open('%s', '_blank')" % stuHref)
        driver.switch_to.window(driver.window_handles[-1])
        [fHolder, lHolder] = splitStudentName(driver.title)
        STUDENT_HREFS[driver.title] = stuHref
        cards = (int)(driver.find_element(By.ID, 'cardsAvailableDetail').text)
        print(driver.title + " " + str(cards))
        stuCur.execute("INSERT OR IGNORE INTO Students(fName, lName, cards) values(?,?,?)",(fHolder, lHolder, cards))
        stuCur.execute("UPDATE Students SET cards = ? WHERE fName = ? AND lName = ?", (cards, fHolder, lHolder))
        stuDB.commit()
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    finishTime = datetime.datetime.now()
    with open(PICKLE_FILE, 'wb+') as file:
        pickle.dump(finishTime, file)
        print(str(finishTime) + " time stamp has been pickled")
        pickle.dump(len(students), file)
        print("studentCount has been pickled")
        pickle.dump(STUDENT_HREFS, file)
        print("STUDENT_HREFS have been pickled")
        file.close()
    
        


#Function handles capturing student information for database entry/updates
def parseStudents():
    driver.implicitly_wait(5)
    studentReg = "//a[starts-with(@href, '/Student/Details')]"
    global studentList
    studentList = driver.find_elements(By.XPATH, studentReg)
    pruneStudents(studentList)#clear student list of duplicates
    recordStudent(studentList)
    

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

    #Main Frame to hold list of students
    outerFrame = Frame(window, bd = 5, relief = "flat")
    outerFrame.grid(row = 0, column = 0, sticky = "NW")

    #Canvas which manages the grid of students
    frameCanvas = Canvas(outerFrame, height = WINDOW_HEIGHT - 100, width = WINDOW_WIDTH - 100, bd = 5)
    frameCanvas.configure(bg = "yellow")
    frameCanvas.grid(row = 0, column = 0)

    vsb = Scrollbar(outerFrame, orient = "vertical", command = frameCanvas.yview, width = 80)
    vsb.grid(row = 0, column = 1, sticky = 'NS')
    frameCanvas.configure(yscrollcommand = vsb.set)

    #Blue Inner Frame
    studentFrame = Frame(frameCanvas)
    records = stuCur.execute("SELECT * FROM Students ORDER BY fName ASC")
    print(len(records.fetchall()))
    studentFrame.rowconfigure(len(records.fetchall()))

    studentEntries = []
    rowLCV = 1
    primeRow = True
    for row in stuCur.execute("SELECT * FROM Students ORDER BY fName ASC"):
        fName, lName, cards = row
        studentInfo = f'{fName} {lName}:  {cards}'
        stuHref = STUDENT_HREFS[str(fName) + " " + str(lName)]
        stuEntry = Student(fName, lName, cards, stuHref, studentFrame, primeRow, rowLCV)
        primeRow = not primeRow
        studentEntries.append(stuEntry)
        rowLCV += 1
    frameCanvas.update_idletasks()
    frameCanvas.create_window((0,0), window = studentFrame, anchor = 'nw')
    frameCanvas.config(scrollregion=frameCanvas.bbox("all"))
    
    
#Function accesses 'Student Management' page, handles login on intial boot 
def loginSub():
    errorLbl = Label(window, text = "ERROR: Unable to login")
    uName = userName.get()
    pWord = password.get() 
    driver.get(loginUrl)
    driver.find_element(By.ID, "UserName").send_keys(uName)
    driver.find_element(By.ID, "Password").send_keys(pWord)
    driver.find_element(By.ID, "login").click()
    if not("Login" in driver.current_url):
        errorLbl.destroy()
        generateStudents()
        submitButton.destroy()
        passLbl.destroy()
        uNameLbl.destroy()
        userName.destroy()
        password.destroy()
        window.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')
        createStudentDisplay()
    else:
        errorLbl.grid(column = 1, row = 2)
    #browser.launch_browser()
    
    

submitButton = Button(window, text="Submit", width = 10, height=3, bg="red", fg="black", command = loginSub)

submitButton.grid(column=0, row=2)
window.mainloop()
driver.quit()


