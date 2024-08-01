from urllib.request import urlopen
import re
import mechanicalsoup
import tkinter as tk

login_url="https://radius.mathnasium.com/Student"
browser = mechanicalsoup.StatefulBrowser()
login_page = browser.open(login_url)
login_html = login_page.soup
print(login_html)
browser.select_form()
#browser.form.print_summary()
window = tk.Tk()
browser["UserName"] = "placeholder"
browser["Password"] = "placeholder"
#response = browser.submit_selected()
#print(response.text)

