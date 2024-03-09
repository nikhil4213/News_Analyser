import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, render_template, request, flash, url_for, redirect,session, jsonify,make_response
# from flask import Flask , 
import requests
from bs4 import BeautifulSoup

import requests
import re
from nltk.tokenize import word_tokenize, sent_tokenize
from authlib.integrations.requests_client import OAuth2Session
from authlib.integrations.flask_client import OAuth
# oauth = OAuth2Session(client_id, client_secret, redirect_uri=redirect_uri)
from nltk.corpus import stopwords

import nltk
import json
import yake
url = 'https://www.indiatoday.in/india/story/pm-modi-srinagar-visit-updates-narendra-modi-srinagar-public-rally-projects-launch-2511584-2024-03-07 '

import re

load_dotenv()
app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600*24*7


nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

oauth = OAuth(app)
app.secret_key = 'your_secret_key_here'  # Set the secret key
client_id = '630606159234-p9u62ohjjdoqsngd5pgd7ob2salaivio.apps.googleusercontent.com'
client_secret = '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'
redirect_uri = 'http://localhost:5000/loginnew'

google = oauth.register(
    name='google',
    client_id='132542805869-5t1iu8gjjrlinlv6m0ubo82q38vfurhf.apps.googleusercontent.com',
    client_secret='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',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    refresh_token_url=None,
    refresh_token_params=None,
    redirect_uri='http://127.0.0.1:5000/authorize',
    client_kwargs={'scope': 'openid email profile'},
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
)

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    session['token'] = token
    return redirect(url_for('profile'))


def search_user_by_email(email):
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        table_name = 'users'
        query = f"SELECT * FROM {table_name} WHERE email = %s"
        cursor.execute(query, (email,))
        data = cursor.fetchall()

        return data

    except Exception as e:
        print("Error retrieving data from the table:", e)
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route('/profile')
def profile():
    token = session.get('token')
    if token is None:
        return redirect(url_for('login'))
    client_id='132542805869-5t1iu8gjjrlinlv6m0ubo82q38vfurhf.apps.googleusercontent.com',

    # Create an OAuth2Session instance with the access token
    oauth = OAuth2Session(client_id, token=token)



    # Make a request to the userinfo endpoint with the access token
    user_info = oauth.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
    user_data = search_user_by_email(user_info['email'])
    if user_info['email'] not in user_data:
        def instert_user_data(name, email):
            connection = None  # Initialize connection variable
            cursor = None  # Initialize cursor variable
            try:
                connection = psycopg2.connect(**db_config)
                cursor = connection.cursor()

                table_name = 'users'
                query = f"INSERT INTO {table_name} (name,email) VALUES (%s, %s)"

                cursor.execute(query, (name, email))
                connection.commit()
                print("Data inserted successfully.")

            except psycopg2.Error as e:
                print("Error inserting data into the table:", e)
                if connection:
                    connection.rollback()  # Rollback in case of error to maintain data integrity

            finally:
                if cursor:
                    cursor.close()
                if connection:
                    connection.close()
            print(user_info)
    response = make_response('Cookie set')
    response.set_cookie('my_cookie', value='example_value', max_age=3600)  # Expires after 1 hour (3600 seconds)
    print(response)
    session['user_info'] = user_info
    instert_user_data(user_info["name"],user_info["email"])
    redirect_ur = "data"
    return redirect(redirect_ur)

db_config = {
    'dbname': 'dhp2024_eima',
    'user': 'nikhil',
    'password': 'R22LAsJJfW1pByje7RTAukpuDFwJM9kX',
    'host': 'dpg-cnm9jfi1hbls739fjoa0-a',
    'port': '5432'
    }

connection = psycopg2.connect(**db_config)
cursor = connection.cursor()

cursor.execute("CREATE TABLE if not exists  url_data (id SERIAL PRIMARY KEY,url VARCHAR(255),date DATE DEFAULT CURRENT_DATE, email VARCHAR(255) DEFAULT 'example@example.com', main_heading text,num_words INTEGER,clean_text TEXT,num_sentences INTEGER,pos_counts JSONB,keywords_frequency JSONB,image_count INTEGER,headings_used TEXT)")
cursor.execute("create table if not exists users (id serial primary key, name varchar(255), email varchar(255))")
connection.commit()




def get_all_data_from_table():
    # connection = None  # Initialize connection variable
    # cursor = None  # Initialize cursor variable
    try:
        
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        table_name = 'url_data'
        query = f"SELECT * FROM {table_name}"

        cursor.execute(query)
        data = cursor.fetchall()

        return data
    except Exception as e:
        print("Error retrieving data from the table:", e)
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def insert_data_into_table(url, num_words, num_sentences, pos_counts, keywords_frequency, image_count, headings_used,clean_text, main_heading, email):
    connection = None  # Initialize connection variable
    cursor = None  # Initialize cursor variable
    try:
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        table_name = 'url_data'
        query = f"INSERT INTO {table_name} (url, num_words, num_sentences, pos_counts, keywords_frequency, image_count, headings_used, clean_text, main_heading, email ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s , %s)"

        cursor.execute(query, (url, num_words, num_sentences, pos_counts, json.dumps(keywords_frequency), image_count, json.dumps(headings_used),clean_text, main_heading, email))
        connection.commit()
        print("Data inserted successfully.")

    except psycopg2.Error as e:
        print("Error inserting data into the table:", e)
        if connection:
            connection.rollback()  # Rollback in case of error to maintain data integrity

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.get("/")
def home() :
    return redirect('data')






def get_clean_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find relevant content elements
    news_content = soup.find_all('div', class_=["news-content", "story-highlights", "description", "story-kicker","container","at_row","_next","clearfix"])
    
    # Extract text from content elements
    combined_text = ' '.join([element.get_text() for element in news_content])
    
    # Remove HTML tags
    clean_text = re.sub(r'<.*?>', '', combined_text)
    
    # Remove non-alphabetic characters except periods
    clean_text = re.sub(r'[^a-zA-Z\s.]', '', clean_text)
    
    # Remove multiple spaces and newlines
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Split text into sentences
    sentences = clean_text.split('.')
    
    # Filter sentences
    filtered_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and sentence[0].isupper():
            filtered_sentences.append(sentence + '.')  # Append period to each sentence
    
    # Join filtered sentences
    clean_text = ' '.join(filtered_sentences)
    
    return clean_text.strip()

def count_images_in_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    image_tags = soup.find_all('img')  # Find all image tags within the combined text
    image_count = len(image_tags)  # Count the number of image tags

    return image_count

def extract_headings(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Initialize a dictionary to store headings
    headings_used = {'h1': [], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []}

    # Extract text from h1, h2, h3, h4, h5, and h6 tags
    for tag in headings_used.keys():
        headings = soup.find_all(tag)
        for heading in headings:
            headings_used[tag].append(heading.get_text())

    return headings_used

@app.route("/data", methods=['POST', 'GET'])
def portal():
    url = ""
    num_words = 0
    num_sentences = 0
    pos_counts = {}
    clean_text = ""
    keywords_frequency = {}
    image_count = 0
    headings_used = {}
    main_heading = {}
    email = 'nologinuser'

    if request.method == "POST":
        print(request)
        url = request.form["Url"]
        clean_text = get_clean_text(url)
        num_words = len(word_tokenize(clean_text))
        
        # Extract text from URL
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_content = soup.find_all('div', class_=["news-content", "story-highlights", "description", "story-kicker","container","at_row","_next","clearfix"])
        combined_text = ' '.join([element.get_text() for element in news_content])
        
        # Count number of sentences
        num_sentences = len(sent_tokenize(combined_text))
        
        # Tokenize words and filter out stopwords
        words = word_tokenize(clean_text)
        stop_words = set(stopwords.words('english'))
        filtered_words = [word for word in words if word.lower() not in stop_words]
        
        # Tag filtered words with parts of speech
        pos_tags = nltk.pos_tag(filtered_words)
        pos_counts = {'NOUN': 0, 'PRONOUN': 0, 'VERB': 0, 'ADJECTIVE': 0, 'ADVERB': 0, 'Other_pos': 0}

        for word, pos in pos_tags:
            if pos.startswith('N'):  # Noun
                pos_counts['NOUN'] += 1
            elif pos.startswith('PR'):  # Pronoun
                pos_counts['PRONOUN'] += 1
            elif pos.startswith('V'):  # Verb
                pos_counts['VERB'] += 1
            elif pos.startswith('J'):  # Adjective
                pos_counts['ADJECTIVE'] += 1
            elif pos.startswith('RB'):  # Adverb
                pos_counts['ADVERB'] += 1
            else:
                pos_counts['Other_pos'] += 1
        
        # Convert pos_counts dictionary to JSON string
        pos_counts = json.dumps(pos_counts)
        
        # Extract SEO keywords
        keyword_extractor = yake.KeywordExtractor(lan="en", n=3, dedupLim=0.9, dedupFunc='seqm')

        keywords = keyword_extractor.extract_keywords(clean_text)
        keyword_extractor_2 = yake.KeywordExtractor(lan="en", n=2, dedupLim=0.9, dedupFunc='seqm')
        keyword_extractor_1 = yake.KeywordExtractor(lan="en", n=1, dedupLim=0.9, dedupFunc='seqm')

        keywords_2 = keyword_extractor_2.extract_keywords(clean_text)
        keywords_1 = keyword_extractor_1.extract_keywords(clean_text)

        keywords += keywords_2 + keywords_1
        
        # Count frequency of each keyword
        for keyword, _ in keywords:
            keywords_frequency[keyword] = clean_text.lower().count(keyword.lower())

        # Sort the keywords by frequency in descending order
        keywords_frequency = dict(sorted(keywords_frequency.items(), key=lambda item: item[1], reverse=True))
        
        # Count images in text
        image_count = count_images_in_text(url)

        # Extract headings from URL
        headings_used = extract_headings(url)
        user_info = session.get('user_info', {})
        if user_info :
            email = user_info['email']
    def get_main_heading_from_url(url):
        try:
            # Fetch the HTML content from the URL
            response = requests.get(url)
            
            # Check if the request was successful
            if response.status_code == 200:
                html_content = response.text
                
                # Parse the HTML content
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract the main heading
                main_heading_tag = soup.find('h1')
                main_heading = main_heading_tag.get_text(strip=True) if main_heading_tag else None
                
                return main_heading
            else:
                print("Failed to fetch URL:", response.status_code)
                return None
        except Exception as e:
            print("An error occurred:", e)
            return None
    main_heading = get_main_heading_from_url(url)
    user_info = session.get('user_info', {})
    
    insert_data_into_table(url, num_words, num_sentences, pos_counts, keywords_frequency, image_count, headings_used,clean_text, main_heading, email)

    print(user_info)
    return render_template("index.html", url=url, cleaned_text=clean_text,
                           num_words=num_words, num_sentences=num_sentences,
                           pos_counts=pos_counts, keywords_frequency=keywords_frequency,
                           image_count=image_count, headings_used=headings_used, user_info = user_info, main_heading = main_heading)

    
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")
# Define the logout route
@app.route('/logout')
def logout():
    session.pop('user_info', None)
    redirect_ur = 'data'
    return redirect(redirect_ur)


def get_url_by_email_from_table(email):
    connection = None  # Initialize connection variable
    cursor = None  # Initialize cursor variable
    try:
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()
        table_name = 'url_data'
        query = f"SELECT * FROM {table_name} WHERE email = '{email}'"  # Using f-string to interpolate email
        cursor.execute(query)
        data = cursor.fetchall()
        return data
    except Exception as e:
        print("Error retrieving data from the table:", e)
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
@app.route('/user')
def user():
    user_info = session.get('user_info', {})
    if user_info :
        email = user_info['email']
    if email:
        data = get_url_by_email_from_table(email)
        no_of_analysis = len(data)
        return render_template("user.html", data = data,no_of_analysis = no_of_analysis )
    else:
        redirect_ur = 'login'
        return redirect(redirect_ur)

def get_all_user_data_from_table():
    connection = None  # Initialize connection variable
    cursor = None  # Initialize cursor variable
    try:
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        table_name = 'users'
        query = f"SELECT * FROM {table_name}"

        cursor.execute(query)
        data = cursor.fetchall()

        return data
    except Exception as e:
        print("Error retrieving data from the table:", e)
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/dashboard')
def dashboard():
    user_info = session.get('user_info', {})
    if user_info :
        if user_info['email'] == 'sanjayasd45@gmail.com' or "nikhil7618987598@gmail.com" :
            all_url_data = get_all_data_from_table()
            all_user_data = get_all_user_data_from_table()
            print(all_user_data)
            return render_template("dashboard.html", data = all_url_data, all_user_data = all_user_data )
        msg = 'Your Are Not The Super User'
        return render_template("dashboard.html", msg = msg)
    return redirect('login')

if __name__ == '__main__':
    app.run(debug=True)