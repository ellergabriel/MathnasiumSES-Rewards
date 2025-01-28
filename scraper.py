from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
import sqlite3
from tkinter import *
import queue
import datetime
import time
import os
import sys
import pickle
import glob as glob
import pandas as pd
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from gui import initializeGui, createRefreshMessage, customExit



#Selenium 
loginUrl= "https://radius.mathnasium.com/Student"
"""Local testing"""
DRIVER_PATH = os.path.join(os.path.dirname(__file__), './chromedriver.exe') #File path for local testing
"""Deliverable"""
#DRIVER_PATH = os.path.join(os.path.dirname(__file__), 'Drivers\chromedriver.exe') #File path for deliverable

service = Service(executable_path=DRIVER_PATH)
options = webdriver.ChromeOptions()
options.add_argument("--headless")
downloadPath = os.path.dirname(os.path.realpath(sys.argv[0])) #downloads files to local executable
prefs = {'download.default_directory' : downloadPath}
options.add_argument("--blink-settings=imageEnabled=false")
options.add_experimental_option('prefs', prefs)
print("Options set up, launching webdriver...")
main_driver = webdriver.Chrome(service=service, options=options)

#SQLite 
stuDB = sqlite3.connect("Students.db")
stuCur = stuDB.cursor()
stuTable = "CREATE TABLE IF NOT EXISTS Students(fName CHAR(31),lName CHAR(31),cards INT, UNIQUE(fName, lName));"
stuCur.execute(stuTable)

#Tkinter widgets
window = Tk()
userName, password, uNameLbl, passLbl  = initializeGui(window)
#! window.title("Digital Rewards Tracker")
#! window.geometry('350x200')

#! menubar = Menu(window)
#! """Debug function for testing menu implementation"""
#! def testMenu():
#!     print("Menu button is working")

#! def credentialsMenu():
#!     print("Opening credentials menu")

#! topMenu = Menu(window)

#! settingsMenu = Menu(topMenu, tearoff = 0)
#! topMenu.add_cascade(menu = settingsMenu, label = "Settings")
#! settingsMenu.add_command(label = "Credentials", command = credentialsMenu)
#! window.config(menu = topMenu)


#! """Local testing"""
#! window.iconbitmap("A+.ico")
#! """deliverable"""
#! #window.iconbitmap(os.path.join(os.path.dirname(__file__), 'A+.ico'))


#! uNameLbl = Label(window, text="Username")
#! uNameLbl.grid(column = 0, row = 0)
#! userName = Entry(window, width = 30)
#! userName.grid(column = 1, row = 0)

#! passLbl = Label(window, text = "Password")
#! passLbl.grid(column = 0, row = 1)
#! password = Entry(window, show = "*", width = 30)
#! password.grid(column = 1, row = 1)

WINDOW_HEIGHT = 800
WINDOW_WIDTH = 600

#Global variable for all Selenium driver instances
"""Pickle file must go in order as follows:
1. datetime object - last timestamp that the student list was parsed
2. integer - number of enrolled students
3. dictionary - STUDENT_HREFS with (full name, link to student page) key/value pairs
"""
PICKLE_FILE = 'timestamp.pkl'

#Class maintains each Student entry on the main display
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

        topMessage = createRefreshMessage(window)
        #! #refresh message creation
        #! topMessage = Toplevel()
        #! topMessage.title("")
        #! refreshMsg = Message(topMessage, text = "Refreshing your card count, please be patient.", font = ('Arial', 25, 'bold'))
        #! refreshMsg.pack(expand = True)
        #! topMessage.geometry('400x400')
        #! topX = window.winfo_x() + window.winfo_width()//2 - topMessage.winfo_width()//2
        #! topY = window.winfo_y() + window.winfo_height()//2 - topMessage.winfo_height()//2
        #! topMessage.geometry(f"+{topX}+{topY}")
        #! topMessage.update()
        #! topMessage.grab_set()
        
        href = STUDENT_HREFS[self.fName + " " + self.lName]
        main_driver.execute_script("window.open('%s', '_blank')" % href)
        main_driver.switch_to.window(main_driver.window_handles[-1])
        self.cards = (int)(main_driver.find_element(By.CSS_SELECTOR, "span[id='cardsAvailableDetail']").text)
        stuCur.execute("UPDATE Students SET cards = ? WHERE fName = ? AND lName = ?", (self.cards, self.fName, self.lName))
        stuDB.commit()
        main_driver.close()
        main_driver.switch_to.window(main_driver.window_handles[0])
        studentInfo = f'{self.fName} {self.lName}: {self.cards} cards'
        self.lbl.config(text = studentInfo)

        print("ending refresh for " + self.fName + " " + self.lName)
        topMessage.destroy()
        refreshButtonAbility(True) #reenables refresh buttons 

#Class for drivers used in multiprocessing   
class Subdriver():
    def __init__(self):
        service = Service(executable_path=DRIVER_PATH)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--blink-settings=imageEnabled=false")
        self.driver = webdriver.Chrome(service=service, options=options)

    def close(self):
        self.driver.quit()

    def run(self, students):
        stuDB = sqlite3.connect("Students.db")
        stuCur = stuDB.cursor()
        startTime = time.time()
        self.driver.get(loginUrl)
        while("Login" in self.driver.current_url and time.time() - startTime < 60):
            self.driver.find_element(By.ID, "UserName").send_keys(uName)
            self.driver.find_element(By.ID, "Password").send_keys(pword)
            self.driver.find_element(By.ID, "login").click()
            #self.driver.find_element(By.CSS_SELECTOR, "input[id='UserName']").send_keys(uName)
            #self.driver.find_element(By.CSS_SELECTOR, "input[id='Password']").send_keys(pWord)
            #self.driver.find_element(By.CSS_SELECTOR, "input[id='login']").click()
            if(time.time() - startTime >= 60):
                print("More than a minute to login on multithreading")
                self.driver.quit()
                return
        print("beginning recording on this thread")
        for stu in students:
            self.driver.get(stu)
            [fHolder, lHolder] = splitStudentName(self.driver.title)
            STUDENT_HREFS[self.driver.title] = stu

            #cards = (int)(self.driver.find_element(By.ID, 'cardsAvailableDetail').text)
            cards = (int)(self.driver.find_element(By.CSS_SELECTOR, "span[id='cardsAvailableDetail']").text)
            print(self.driver.title + " " + str(cards))
            stuCur.execute("INSERT OR IGNORE INTO Students(fName, lName, cards) values(?,?,?)",(fHolder, lHolder, cards))
            stuCur.execute("UPDATE Students SET cards = ? WHERE fName = ? AND lName = ?", (cards, fHolder, lHolder))
            stuDB.commit()
        self.driver.quit()


"""
Helper functions; does not interact with Selenium drivers
"""
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
"""DEPRECATED
def pruneStudents(studentList):
    viewedRefs = {}
    lcv = 0
    while(lcv < len(studentList)):
        stu = studentList[lcv].get_attribute('href')
        if stu not in viewedRefs:
            viewedRefs[stu] = True
            lcv += 1
        else:
            studentList.pop(lcv)
"""

"""
function that handles multithreading of different student records
Each subprocess will take partial list of students and perform selenium actions to record student stars
"""
def recordingRoutine(students, subdriver):
    subdriver.run(students)


"""
Essential functions; interacts with Selenium drivers
"""
#Function takes in list of Student profiles from Radius and opens each in a new tab, recording full name and card count
#Function uses pickling to determine last time the full student list was parsed as well as if students were dropped/added
def recordStudent(students):
    main_driver.implicitly_wait(0)
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
                print("Mass update not needed, skipping database refresh...")
                #return
            if(timeDiff > timeout):
                print("Over 12 hours since last refresh")
            if(len(students) != studentCount):
                print("student count has changed since last run")
            print("Refreshing student information...")
    except:
        print("ERROR: Unsuccessful fetching of time stamp or student hrefs, proceeding with database refresh...")
    print("parsing student information...")
    
    STUDENT_HREFS = {} #reset dictionary, previous unsuccessful unpickling sets variable as NoneType otherwise

    threads = []
    MAX_THREADS = 2
    numStud = len(students)
    partition = 0
    offset = int( numStud / MAX_THREADS)
    for i in range(MAX_THREADS):
        if(i == MAX_THREADS - 1): #end of list, catches any students who may be left out by truncation 
            partialList = students[partition:]
        else:
            partialList = students[partition : partition + offset]
        partition += offset
        th = threading.Thread(target=recordingRoutine, args =(partialList, Subdriver()))
        th.start()
        threads.append(th)
    for th in threads:
        th.join()
    finishTime = datetime.datetime.now()
    with open(PICKLE_FILE, 'wb+') as file:
        pickle.dump(finishTime, file)
        print(str(finishTime) + " time stamp has been pickled")
        pickle.dump(len(students), file)
        print("studentCount has been pickled")
        pickle.dump(STUDENT_HREFS, file)
        print("STUDENT_HREFS have been pickled")
        file.close()
    print("finish time: " + str(finishTime - startTime) + " using", (MAX_THREADS), "threads")
    
    """ Old code for single driver recording of stars
    for stu in students:
        #stu = stu.get_attribute('href')
        main_driver.execute_script("window.open('%s', '_blank')" % stu)
        main_driver.switch_to.window(main_driver.window_handles[-1])
        [fHolder, lHolder] = splitStudentName(main_driver.title)
        STUDENT_HREFS[main_driver.title] = stu

        cards = (int)(main_driver.find_element(By.ID, 'cardsAvailableDetail').text)
        print(main_driver.title + " " + str(cards))
        stuCur.execute("INSERT OR IGNORE INTO Students(fName, lName, cards) values(?,?,?)",(fHolder, lHolder, cards))
        stuCur.execute("UPDATE Students SET cards = ? WHERE fName = ? AND lName = ?", (cards, fHolder, lHolder))
        stuDB.commit()
        main_driver.close()
        main_driver.switch_to.window(main_driver.window_handles[0])
    """
    

"""function for handling >1 page of enrolled students; will replace parseStudents() once complete
    Pseudocode- Fill enrollment filter
                export to excel
                open xslx file
                parse student id numbers
                when recording student vals, use string appending to https://radius.mathnasium.com/Student/Details/{idNumber}
"""
def parseStudents():
    main_driver.implicitly_wait(10)
    global studentList
    studentList = []
    studentExcel = main_driver.find_element(By.ID, "btnExport")
    studentExcel.click()
    startTime = time.time()
    print("Waiting on excel file to download...")
    while(not glob.glob(os.path.join(downloadPath, "*.xlsx")) and time.time() - startTime < 30):
        if(time.time() - startTime >= 30):
            print("Program time out; too long to download excel file")
            break
    stuTemplate = "https://radius.mathnasium.com/Student/Details/"
    students = []
    excelFile = glob.glob(os.path.join(downloadPath, "*.xlsx"))
    for file in excelFile:
        print("file found")
        studentDF = pd.read_excel(file)
        studentIDList = studentDF['Student Id'].tolist()
        for id in studentIDList:
            students.append (stuTemplate + str(id))
        os.remove(file)
        print("file deleted")
    recordStudent(students)

"""Function handles recording URLs for student pages who are enrolled"""
def generateStudents():
    print("Login successful")
    """
    enrollFilterPath = "//div[@class='container']//div[@id='single-Grid-Page']/div[2]/div[1]/div[1]/div[3]/div[1]/span[1]" #ugly, make sure to fix
    enFill = main_driver.find_element(By.XPATH, enrollFilterPath)
    enFill.click()
    for i in range(3): #manually scrolls through Enrollment Filters, should be fixed to dynamically find "enrolled"
        enFill.send_keys(Keys.DOWN)
    enFill.send_keys(Keys.ENTER)
    main_driver.find_element(By.ID, 'btnsearch').click()
    """
    filter = main_driver.find_element(By.CSS_SELECTOR, "span[aria-owns='enrollmentFiltersDropDownList_listbox']")
    filter.click()
    for i in range(3):
        filter.send_keys(Keys.DOWN)
    filter.send_keys(Keys.ENTER)
    main_driver.find_element(By.CSS_SELECTOR, "button[id='btnsearch']").click()
    parseStudents()

"""
Deprecated functions from the alpha version 

#Function handles capturing student information for database entry/updates
def parseStudents():
    main_driver.implicitly_wait(5)
    studentReg = "//a[starts-with(@href, '/Student/Details')]"
    global studentList
    studentList = main_driver.find_elements(By.XPATH, studentReg)
    if(len(studentList) > 0):
        print("Student list generated...")
    pruneStudents(studentList)#clear student list of duplicates
    #recordStudent(studentList)
    
#Function interacts with Student Management page, TODO: update to dynamically select enrollment filter
def generateStudents():
    print("Login successful")
    enrollFilterPath = "//div[@class='container']//div[@id='single-Grid-Page']/div[2]/div[1]/div[1]/div[3]/div[1]/span[1]" #ugly, make sure to fix
    enFill = main_driver.find_element(By.XPATH, enrollFilterPath)
    enFill.click()
    for i in range(3): #manually scrolls through Enrollment Filters, should be fixed to dynamically find "enrolled"
        enFill.send_keys(Keys.DOWN)
    enFill.send_keys(Keys.ENTER)
    main_driver.find_element(By.ID, 'btnsearch').click()
    #parseStudents()
"""

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
            stu = STUDENT_HREFS[str(fName) + " " + str(lName)]
        except KeyError:
            print("ERROR: student info not stored in HREFs. Check student records for " + str(fName) + " " + str(lName) + ". Removing student from db...")
            toBeRemoved.put( (str(fName), str(lName) ))
            continue
        except NameError:
            print("STUDENT_HREFS not defined, check debug lines")
            return
        stuEntry = Student(fName, lName, cards, stu, studentFrame, primeRow, rowLCV)
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
    main_driver.set_page_load_timeout(45)
    main_driver.get(loginUrl)
    global uName, pword
    uName = userName.get()
    pword = password.get() 
    main_driver.find_element(By.ID, "UserName").send_keys(uName)
    main_driver.find_element(By.ID, "Password").send_keys(pword)
    main_driver.find_element(By.ID, "login").click()
    if not("Login" in main_driver.current_url):
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

submitButton = Button(window, text="Submit", width = 10, height=3, bg="red", fg="black", command = loginSub)
submitButton.grid(column=0, row=2)
#window.protocol("WM_DELETE_WINDOW", customExit)

while True:
    window.update_idletasks()
    window.update()
main_driver.quit()

