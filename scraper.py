from urllib.request import urlopen
import sqlite3
from tkinter import *
import queue
import datetime
import time
import multiprocessing
import os
import sys
import pickle
import threading
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
DRIVER_PATH = os.path.join(os.path.dirname(__file__), 'Drivers\chromedriver.exe') #File path for deliverable
#DRIVER_PATH = os.path.join(os.path.dirname(__file__), './chromedriver.exe') #File path for local testing

service = Service(executable_path=DRIVER_PATH)
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--blink-settings=imageEnabled=false")
driver = webdriver.Chrome(service=service, options=options)
action = ActionChains(driver)



#Global variable for all Selenium driver instances
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
        studentInfo = f'{fName} {lName}: {cards} cards'
        self.lbl = Label(studentFrame, text = studentInfo, width = 30, font = ('Arial', 16, 'bold'))
        self.btn = Button(studentFrame, text = "REFRESH", width = 10, command = self.refreshCards)
        if not isPrime:
            self.lbl.configure(bg = "gray")
            self.btn.configure(bg = "gray")
        self.lbl.grid(column = 0, row = rowLCV, sticky = 'news')
        self.btn.grid(column = 1, row = rowLCV, sticky = 'news', padx = 40)

    #function that controls refresh button behavior in main GUI display
    def refreshCards(self):
        print("beginning refresh for " + self.fName + " " + self.lName)
        refreshButtonAbility(False) #disables refresh buttons

        #refresh message creation
        topMessage = Toplevel()
        topMessage.title("")
        refreshMsg = Message(topMessage, text = "Refreshing your card count, please be patient.", font = ('Arial', 25, 'bold'))
        refreshMsg.pack(expand = True)
        topMessage.geometry('400x400')
        topX = window.winfo_x() + window.winfo_width()//2 - topMessage.winfo_width()//2
        topY = window.winfo_y() + window.winfo_height()//2 - topMessage.winfo_height()//2
        topMessage.geometry(f"+{topX}+{topY}")
        topMessage.update()
        topMessage.grab_set()
        
        href = STUDENT_HREFS[self.fName + " " + self.lName]
        driver.execute_script("window.open('%s', '_blank')" % href)
        driver.switch_to.window(driver.window_handles[-1])
        self.cards = (int)(driver.find_element(By.ID, 'cardsAvailableDetail').text)
        stuCur.execute("UPDATE Students SET cards = ? WHERE fName = ? AND lName = ?", (self.cards, self.fName, self.lName))
        stuDB.commit()
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        studentInfo = f'{self.fName} {self.lName}: {self.cards} cards'
        self.lbl.config(text = studentInfo)

        print("ending refresh for " + self.fName + " " + self.lName)
        topMessage.destroy()
        refreshButtonAbility(True) #reenables refresh buttons 
        

#SQLite 
stuDB = sqlite3.connect("Students.db")
stuCur = stuDB.cursor()
stuTable = "CREATE TABLE IF NOT EXISTS Students(fName CHAR(31),lName CHAR(31),cards INT, UNIQUE(fName, lName));"
stuCur.execute(stuTable)

#Tkinter widgets
window = Tk()
window.title("Digital Rewards Tracker")
window.geometry('350x200')

#window.iconbitmap("A+.ico") #Local testing 
window.iconbitmap(os.path.join(os.path.dirname(__file__), 'A+.ico')) #deliverable

WINDOW_HEIGHT = 800
WINDOW_WIDTH = 600

uNameLbl = Label(window, text="Username")
uNameLbl.grid(column = 0, row = 0)
userName = Entry(window, width = 30)
userName.grid(column = 1, row = 0)

passLbl = Label(window, text = "Password")
passLbl.grid(column = 0, row = 1)
password = Entry(window, show = "*", width = 30)
password.grid(column = 1, row = 1)

#Helper function that disables or enables all refresh buttons on main student UX
def refreshButtonAbility(isEnabled):
    for stu in studentEntries:
        if(isEnabled):
            stu.btn.config(state = NORMAL)
        else:
            stu.btn.config(state = DISABLED)

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
                print("STUDENT_HREFS loaded")
                file.close()
                print("within 12 hours of last update, skipping database refresh...")
                return
            if(timeDiff > timeout):
                print("Over 12 hours since last refresh")
            if(len(students) != studentCount):
                print("student count has changed since last run")
            print("Refreshing student information...")
    except:
        print("ERROR: Unsuccessful fetching of time stamp or student hrefs, proceeding with database refresh...")
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
    if(len(studentList) > 0):
        print("Student list generated...")
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
    def entryResize(self): #nested function handles dynamic resizing of student list 
        outerFrame.config(height = window.winfo_height() - 25, width = window.winfo_width())
        frameCanvas.config(height = window.winfo_height() - 25)
        
    #Main Frame to hold list of students
    outerFrame = Frame(window, bd = 5, relief = "flat")
    outerFrame.grid(row = 0, column = 0, sticky = "NSEW")
    outerFrame.bind("<Configure>", entryResize)

    #Canvas which manages the grid of students
    frameCanvas = Canvas(outerFrame, height = WINDOW_HEIGHT - 100, width = WINDOW_WIDTH - 100, bd = 5)
    frameCanvas.grid(row = 0, column = 0, sticky = "NSEW")

    #Scrollbar
    vsb = Scrollbar(outerFrame, orient = "vertical", command = frameCanvas.yview, width = 80)
    vsb.grid(row = 0, column = 1, sticky = 'NS')
    frameCanvas.configure(yscrollcommand = vsb.set)

    #Inner Frame that holds Student object widgets
    studentFrame = Frame(frameCanvas)
    records = stuCur.execute("SELECT * FROM Students ORDER BY fName ASC")
    studentFrame.rowconfigure(len(records.fetchall()))

    global studentEntries
    studentEntries = []
    toBeRemoved = queue.Queue()
    rowLCV = 1
    primeRow = True
    for row in stuCur.execute("SELECT * FROM Students ORDER BY fName ASC"):
        fName, lName, cards = row
        studentInfo = f'{fName} {lName}:  {cards}'
        try:
            stuHref = STUDENT_HREFS[str(fName) + " " + str(lName)]
        except KeyError:
            print("ERROR: student info not stored in HREFs. Check student records for " + str(fName) + " " + str(lName) + ". Removing student from db...")
            toBeRemoved.put( (str(fName), str(lName) ))
            continue
        stuEntry = Student(fName, lName, cards, stuHref, studentFrame, primeRow, rowLCV)
        primeRow = not primeRow
        studentEntries.append(stuEntry)
        rowLCV += 1
    while not toBeRemoved.empty():
        fName , lName = toBeRemoved.get()
        stuCur.execute("DELETE FROM Students WHERE fName = ? AND lName = ?", (str(fName), str(lName)))
        stuDB.commit()
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

#Function overrides [x] in window toolbar, prevents students from closing window without entering the pin
def customExit():
    exitConfirm = Toplevel()
    exitConfirm.title("DO NOT TOUCH")
    exitConfirm.geometry("300x300")
    warningLabel = Label(exitConfirm, text = "DO NOT TOUCH THE RED X", font = ('Impact', 50, 'bold'), wraplength = 300, justify = "center")
    warningLabel.grid()
    """
    exitLabel = Label(exitConfirm, text = "Enter pin:")
    exitLabel.grid(column = 0, row = 0)
    pinEntry = Entry(exitConfirm, show = "*")
    pinEntry.grid(column = 1, row = 0)
    warningLabel = Label(exitConfirm, text = "DO NOT TOUCH THE RED X")
    def checkPIN():
        if(pinEntry.get() == PIN):
            window.destroy()
            driver.quit()
            sys.exit()
        else:
            exitConfirm.destroy()
            return
    exitSubmit = Button(exitConfirm, text = "Submit", bg="red", fg="black", command = checkPIN)
    exitSubmit.grid(column = 0, row = 1)
    """
    exitConfirm.update()

    
submitButton = Button(window, text="Submit", width = 10, height=3, bg="red", fg="black", command = loginSub)
PIN = "1835"
submitButton.grid(column=0, row=2)
window.protocol("WM_DELETE_WINDOW", customExit)

while True:
    window.update_idletasks()
    window.update()
driver.quit()


