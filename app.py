from __future__ import division, print_function
import sys
import requests
import os
import spacy 
from flask import Flask, redirect, url_for, request, render_template
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer
from flask import Flask, render_template, session
from flask_mysqldb import MySQL
import re
from bs4 import BeautifulSoup
import io
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
import os 
import numpy as np 
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

app = Flask(__name__, template_folder='templates')

app.secret_key = 'your secret key'

#college patterns
college_patterns = ['[A-Z.][a-z.]* University',
                'University of [A-Z][a-z]*',
                'Ecole [A-Z][a-z]*','[A-Z][a-z]* College','College of [A-Z][a-z]*','[A-Z][a-z]* Institute of [A-Z][a-z]*']
c_pattern = '({})'.format('|'.join(college_patterns))
#creating MYSQL Connection
mysql = MySQL(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'test'

#extracting text from pdf 
def extract_text_from_pdf(pdf_path):
    pages = convert_from_path(pdf_path,500)

    counter = 1

    for page in pages:
      filename = "page_"+str(counter)+".jpg"
      page.save(filename, 'JPEG') 
      counter = counter + 1

    limit = counter - 1

    finaltext =""
    for i in range(1, limit+1):
      filename = "page_"+str(i)+".jpg"
      text = str(((pytesseract.image_to_string(Image.open(filename)))))
      text = text.replace('-\n', '')

      finaltext=finaltext + text  

    return(finaltext)
#getting email
def get_email(resume_text):
    

    pattern = '[a-z0-9\.]+@[a-z0-9\.]+'

    email = re.findall(pattern,resume_text)
    return(email)

#loading the model 
MODEL_PATH = 'C:\\Users\\scsra\\Desktop\\Web Application\\ner'
nlp = spacy.load(MODEL_PATH)
nlp1= spacy.load('en_core_web_sm')

@app.route('/', methods=['GET']) 
def login():
    return render_template('login.html')

@app.route('/home',methods=['GET','POST']) 
def index():
  msg=''
  if request.method=='POST':
    username = request.form['email']
    password = request.form['password']

    cursor = mysql.connection.cursor()

    cursor.execute('SELECT * FROM login WHERE email = %s AND password = %s', (username,password))

    login = cursor.fetchone()

    if login:
      row = len(login)
      for i in range(row):
        session['loggedin'] = True
        session['id'] = login[0][i]
        session['username'] = login[0][i]
        return render_template('index.html')
    else:
      msg = 'Incorrect Username/Password'
  return render_template('login.html', msg = msg)

@app.route('/return',methods = ['GET'])
def return_home():
  return render_template('index.html')

@app.route('/logout')
def logout():
  session.pop('loggedin',None)
  session.pop('id',None)
  session.pop('username',None)

  return render_template('login.html')
@app.route('/predict', methods=['GET','POST'])
def upload():
    if request.method == 'POST':

      #cursor = mysql.connection.cursor()
      f = request.files['file']
      basepath = os.path.dirname(__file__)
      file_path = os.path.join(basepath, secure_filename(f.filename))
      f.save(file_path)

      #extracting text from pdf 
      text = extract_text_from_pdf(file_path)
      qualification =""
      name = ""
      institution = ""
      email = ""

      qualifications = []
      institutions = []
      names = []
      emails = []

      doc = nlp(text)
      

      emails = get_email(text)

      for ent in doc.ents:
        #qualifications
        if(ent.label_ == "QUALIFICATION"):
          qualifications.append(ent.text)

        #names
        elif(ent.label_ == "PERSON"):
            names.append(ent.text)

        #institutions

        elif(ent.label_ == "INSTITUTION"):
          institutions.append(ent.text)
       
      length = len(qualifications)
      if(length>0):
        for i in range(length):
          qualification = qualification + qualifications[i] + ","
      else:
        qualification = "NIL"
     


      len1 = len(names)
      if(len1>0):
          for i in range(len1):
            name = name + names[i] + " "
      else:
          name = "NIL"

      if(len(institutions)>0):
          for i in range(len(institutions)):
            institution = institution + institutions[i] + ","
      else:
          institution = "NIL"

      if(len(emails)>0):
        for i in range(len(emails)):
          email = email + emails[i] + ","
      else:
        email = "NIL"
      cursor = mysql.connection.cursor()

      cursor.execute("INSERT INTO info VALUES(%s,%s,%s,%s)",([name],[institution],[qualification],[email]))
  
      mysql.connection.commit()
      cursor.close()
      return render_template('result.html', qualification = qualification,institution = institution, name = name, email = email)
   
if __name__ == '__main__':
           app.run(port=1010,debug=False,threaded=False)
           


