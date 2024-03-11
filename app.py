import os  # Import the os module for interacting with the operating system
import psycopg2  # Import the psycopg2 module for connecting to PostgreSQL databases
from dotenv import load_dotenv  # Import the load_dotenv function from the dotenv module for loading environment variables from .env file.
from flask import Flask, render_template, request, flash, url_for, redirect, session, jsonify, make_response  # Import various components from the Flask framework
import requests  # Import the requests module for making HTTP requests
from bs4 import BeautifulSoup  # Import the BeautifulSoup class from the bs4 module for web scraping
import re  # Import the re module for regular expressions
from nltk.tokenize import word_tokenize, sent_tokenize  # Import functions from the nltk.tokenize module for tokenizing words and sentences
from authlib.integrations.requests_client import OAuth2Session  # Import the OAuth2Session class from the authlib module for OAuth2 authorization
from authlib.integrations.flask_client import OAuth  # Import the OAuth class from the authlib module for OAuth authorization
import nltk  # Import the nltk library for natural language processing tasks
import json  # Import the json module for working with JSON data
import yake  # Import the KeywordExtractor class from the yake module for keyword extraction


load_dotenv()  # Load environment variables from the .env file into the operating system's environment

app = Flask(__name__, static_url_path='/static')  # Create a Flask application instance
app.secret_key = os.environ.get('SECRET_KEY')  # Set the secret key for the Flask application
app.config['PERMANENT_SESSION_LIFETIME'] = 3600*24*7  # Set the lifetime of the session

nltk.download('punkt')  # Download the Punkt tokenizer models
nltk.download('stopwords')  # Download the stopwords corpus
nltk.download('averaged_perceptron_tagger')  # Download the averaged_perceptron_tagger models

oauth = OAuth(app)  # Initialize OAuth for the Flask application
# Initialize a dictionary named db_config
db_config = {
    # Assign the value of the environment variable named 'DB_NAME' to the key 'dbname'
    'dbname': os.environ.get('DB_NAME'),
    # Assign the value of the environment variable named 'USER_NAME' to the key 'user'
    'user': os.environ.get('USER_NAME'),
    # Assign the value of the environment variable named 'PASSWORD' to the key 'password'
    'password': os.environ.get('PASSWORD'),
    # Assign the value of the environment variable named 'HOST' to the key 'host'
    'host': os.environ.get('HOST'),
    # Assign the string '5432' directly to the key 'port', typically representing the default port for PostgreSQL databases
    'port': '5432'
    }

# Define the configuration for Google OAuth
google = oauth.register(
    name='google',
    client_id='132542805869-5t1iu8gjjrlinlv6m0ubo82q38vfurhf.apps.googleusercontent.com',  # Google client ID
    client_secret='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',  # Google client secret
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    redirect_uri='https://new-extractor.onrender.com/authorize',  # Redirect URI for Google OAuth
    client_kwargs={'scope': 'openid email profile'},
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
)

@app.route('/login')  # Define the route for user login
def login():
    redirect_uri = url_for('authorize', _external=True)  # Set the redirect URI for authorization
    return google.authorize_redirect(redirect_uri)  # Redirect the user to Google authorization page

@app.route('/authorize')  # Define the route for authorization
def authorize():
    token = google.authorize_access_token()  # Authorize access token
    session['token'] = token  # Store the token in the session
    return redirect(url_for('profile'))  # Redirect the user to the profile page after authorization


#this function performs a database query to retrieve user data based on the provided email address and returns the results, handling potential errors along the way and ensuring proper cleanup of resources.
def search_user_by_email(email):
    connection = None  # Initialize the database connection variable
    cursor = None  # Initialize the cursor variable
    try:
        connection = psycopg2.connect(**db_config)  # Connect to the PostgreSQL database
        cursor = connection.cursor()  # Create a cursor object
        table_name = 'users'  # Specify the name of the users table
        query = f"SELECT * FROM {table_name} WHERE email = %s"  # SQL query to search for user by email
        cursor.execute(query, (email,))  # Execute the SQL query
        data = cursor.fetchall()  # Fetch all the results
        return data  # Return the user data
    
    except Exception as e:
        print("Error retrieving data from the table:", e)
        return []  # Return an empty list in case of error

    finally:
        if cursor:
            cursor.close()  # Close the cursor
        if connection:
            connection.close()  # Close the database connection


@app.route('/profile')  # Define the route for user profile
def profile():
    token = session.get('token')  # Get the token from the session and store the information temperary 
    if token is None:
        return redirect(url_for('login'))  # Redirect to login page if token is not found
    client_id = '132542805869-5t1iu8gjjrlinlv6m0ubo82q38vfurhf.apps.googleusercontent.com'  # Set the Google client ID
    oauth = OAuth2Session(client_id, token=token)  # Create an OAuth2Session instance with the access token

    user_info = oauth.get('https://www.googleapis.com/oauth2/v3/userinfo').json()  # Get user info from userinfo endpoint
    user_data = search_user_by_email(user_info['email'])  # Search for user data by email
    if user_info['email'] not in user_data:
        def insert_user_data(name, email):
            connection = None  # Initialize connection variable
            cursor = None  # Initialize cursor variable
            try:
                connection = psycopg2.connect(**db_config)  # Connect to the PostgreSQL database
                cursor = connection.cursor()  # Create a cursor object

                table_name = 'users'  # Specify the name of the users table
                query = f"INSERT INTO {table_name} (name,email) VALUES (%s, %s)"  # SQL query to insert user data

                cursor.execute(query, (name, email))  # Execute the SQL query
                connection.commit()  # Commit the transaction
                print("Data inserted successfully.")  # Print success message

            except psycopg2.Error as e:
                print("Error inserting data into the table:", e)  # Print error message
                if connection:
                    connection.rollback()  # Rollback the transaction in case of error

            finally:
                if cursor:
                    cursor.close()  # Close the cursor
                if connection:
                    connection.close()  # Close the database connection

    response = make_response('Cookie set')  # Create a response object
    response.set_cookie('my_cookie', value='example_value', max_age=3600 * 24)  # Set a cookie with a maximum age
    session['user_info'] = user_info  # Store the user info in the session (Sessions are typically used to store user-specific data across multiple HTTP requests)
    all_user_data = get_all_user_data_from_table()  # Get all user data from the database
    check = False  # Initialize check variable

    if user_info['email'] in [item[2] for item in all_user_data]:  # Check if user email is in the list of user emails
        check = True  # Set check to True if user email is found

    if not check:
        insert_user_data(user_info["name"], user_info["email"])  # Insert user data if not found in the database

    redirect_ur = "data"  # Set the redirect URL
    return redirect(redirect_ur)  # Redirect the user to the specified URL

def get_all_data_from_table():
    connection = None  # Initialize connection variable
    cursor = None  # Initialize cursor variable
    try:
        connection = psycopg2.connect(**db_config)  # Connect to the PostgreSQL database
        cursor = connection.cursor()  # Create a cursor object

        table_name = 'url_data'  # Specify the name of the URL data table
        query = f"SELECT * FROM {table_name}"  # SQL query to retrieve all data from the table

        cursor.execute(query)  # Execute the SQL query
        data = cursor.fetchall()  # Fetch all the results

        return data  # Return the data

    except Exception as e:
        print("Error retrieving data from the table:", e)
        return []  # Return an empty list in case of error

    finally:
        if cursor:
            cursor.close()  # Close the cursor
        if connection:
            connection.close()  # Close the database connection

def insert_data_into_table(url, num_words, num_sentences, pos_counts, keywords_frequency, image_count, headings_used, clean_text, main_heading, email):
    connection = None  # Initialize connection variable
    cursor = None  # Initialize cursor variable
    try:
        connection = psycopg2.connect(**db_config)  # Connect to the PostgreSQL database
        cursor = connection.cursor()  # Create a cursor object

        table_name = 'url_data'  # Specify the name of the URL data table
        query = f"INSERT INTO {table_name} (url, num_words, num_sentences, pos_counts, keywords_frequency, image_count, headings_used, clean_text, main_heading, email ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s , %s)"  # SQL query to insert data into the table

        cursor.execute(query, (url, num_words, num_sentences, pos_counts, json.dumps(keywords_frequency), image_count, json.dumps(headings_used), clean_text, main_heading, email))  # Execute the SQL query
        connection.commit()  # Commit the transaction
        print("Data inserted successfully.")  # Print success message

    except psycopg2.Error as e:
        print("Error inserting data into the table:", e)  # Print error message
        if connection:
            connection.rollback()  # Rollback the transaction in case of error

    finally:
        if cursor:
            cursor.close()  # Close the cursor
        if connection:
            connection.close()  # Close the database connection

@app.get("/")  # Define the route for the home page
def home():
    return redirect('data')  # Redirect the user to the data page

# Function to extract clean text from a URL
def get_clean_text(url):
    response = requests.get(url)  # Send a GET request to the URL
    soup = BeautifulSoup(response.text, 'html.parser')  # Create a BeautifulSoup object

    # Find relevant content elements
    news_content = soup.find_all('div', class_=["news-content", "story-highlights", "description", "story-kicker", "container", "at_row", "_next", "clearfix"])

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

# Function to count images in text extracted from a URL
def count_images_in_text(url):
    response = requests.get(url)  # Send a GET request to the URL
    soup = BeautifulSoup(response.text, 'html.parser')  # Create a BeautifulSoup object

    image_tags = soup.find_all('img')  # Find all image tags within the combined text
    image_count = len(image_tags)  # Count the number of image tags

    return image_count

# Function to extract headings from a URL
def extract_headings(url):
    response = requests.get(url)  # Send a GET request to the URL
    soup = BeautifulSoup(response.text, 'html.parser')  # Create a BeautifulSoup object

    # Initialize a dictionary to store headings
    headings_used = {'h1': [], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []}

    # Extract text from h1, h2, h3, h4, h5, and h6 tags
    for tag in headings_used.keys():
        headings = soup.find_all(tag)
        for heading in headings:
            headings_used[tag].append(heading.get_text())

    return headings_used

# Function to extract the main heading from a URL
def get_main_heading_from_url(url):
    try:
        response = requests.get(url)  # Send a GET request to the URL
        
        # Check if the request was successful
        if response.status_code == 200:
            html_content = response.text  # Get the HTML content
            
            # Parse the HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract the main heading
            main_heading_tag = soup.find('h1')
            main_heading = main_heading_tag.get_text(strip=True) if main_heading_tag else None
            
            return main_heading  # Return the main heading
        else:
            print("Failed to fetch URL:", response.status_code)
            return None
    except Exception as e:
        print("An error occurred:", e)
        return None

@app.route("/data", methods=['POST', 'GET'])  # Define the route for the data page
def portal():
    url = ""  # Initialize URL variable
    num_words = 0  # Initialize number of words variable
    num_sentences = 0  # Initialize number of sentences variable
    pos_counts = {}  # Initialize part-of-speech counts dictionary
    clean_text = ""  # Initialize clean text variable
    keywords_frequency = {}  # Initialize keywords frequency dictionary
    image_count = 0  # Initialize image count variable
    headings_used = {}  # Initialize headings used dictionary
    main_heading = {}  # Initialize main heading dictionary
    email = 'nologinuser'  # Initialize email variable

    if request.method == "POST":
        url = request.form["Url"]  # Get the URL from the form
        clean_text = get_clean_text(url)  # Extract clean text from the URL
        num_words = len(word_tokenize(clean_text))  # Count the number of words
        
        # Extract text from URL
        response = requests.get(url)  # Send a GET request to the URL
        soup = BeautifulSoup(response.text, 'html.parser')  # Create a BeautifulSoup object
        news_content = soup.find_all('div', class_=["news-content", "story-highlights", "description", "story-kicker", "container", "at_row", "_next", "clearfix"])  # Find relevant content elements
        combined_text = ' '.join([element.get_text() for element in news_content])  # Combine text from content elements
        
        # Count number of sentences
        num_sentences = len(sent_tokenize(combined_text))  # Count the number of sentences
        
        # Tokenize words and filter out stopwords
        words = word_tokenize(clean_text)  # Tokenize words
        stop_words = set(stopwords.words('english'))  # Get English stopwords
        filtered_words = [word for word in words if word.lower() not in stop_words]  # Filter out stopwords
        
        # Tag filtered words with parts of speech
        pos_tags = nltk.pos_tag(filtered_words)  # Tag parts of speech
        pos_counts = {'NOUN': 0, 'PRONOUN': 0, 'VERB': 0, 'ADJECTIVE': 0, 'ADVERB': 0, 'Other_pos': 0}  # Initialize part-of-speech counts dictionary

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

        user_info = session.get('user_info', {})  # Get user info from session
        if user_info:
            email = user_info['email']  # Get user email from user info

        main_heading = get_main_heading_from_url(url)  # Extract main heading from URL

        user_info = session.get('user_info', {})  # Get user info from session
        if clean_text != '':
            insert_data_into_table(url, num_words, num_sentences, pos_counts, keywords_frequency, image_count, headings_used, clean_text, main_heading, email)  # Insert data into table if clean text is not empty
    
    return render_template("index.html", url=url, cleaned_text=clean_text,
                           num_words=num_words, num_sentences=num_sentences,
                           pos_counts=pos_counts, keywords_frequency=keywords_frequency,
                           image_count=image_count, headings_used=headings_used, main_heading=main_heading)

@app.route("/about")  # Define the route for the about page
def about():
    return render_template("about.html")  # Render the about page template

@app.route("/contact")  # Define the route for the contact page
def contact():
    return render_template("contact.html")  # Render the contact page template

@app.route('/logout')  # Define the route for user logout
def logout():
    session.pop('user_info', None)  # Remove user info from the session
    redirect_ur = 'data'  # Set the redirect URL
    return redirect(redirect_ur)  # Redirect the user to the specified URL
import psycopg2  # Import the psycopg2 library for PostgreSQL database interaction

def get_url_by_email_from_table(email, db_config):
    connection = None  # Initialize connection variable
    cursor = None  # Initialize cursor variable
    try:
        connection = psycopg2.connect(**db_config)  # Establish a connection to the database using provided configuration
        cursor = connection.cursor()  # Create a cursor object to execute queries
        table_name = 'url_data'  # Specify the name of the table to query
        query = f"SELECT * FROM {table_name} WHERE email = '{email}'"  # Construct a SQL query to fetch data based on email
        cursor.execute(query)  # Execute the query
        data = cursor.fetchall()  # Fetch all the rows returned by the query
        return data  # Return the fetched data
    except Exception as e:
        print("Error retrieving data from the table:", e)  # Print an error message if an exception occurs
        return []  # Return an empty list if an error occurs
    finally:
        if cursor:
            cursor.close()  # Close the cursor to release database resources
        if connection:
            connection.close()  # Close the database connection
from flask import session, render_template, redirect  # Import necessary modules

@app.route('/user')  # Decorator to define a route '/user' for the user function
def user():
    user_info = session.get('user_info', {})  # Retrieve user information from the session, defaulting to an empty dictionary
    if user_info:  # Check if user_info is not empty
        email = user_info['email']  # Extract email from user_info dictionary
    if email:  # Check if email is not empty
        data = get_url_by_email_from_table(email)  # Call the get_url_by_email_from_table function to fetch data for the user's email
        no_of_analysis = len(data)  # Calculate the number of analyses
        return render_template("user.html", data=data, no_of_analysis=no_of_analysis)  # Render the user.html template with the fetched data and number of analyses
    else:
        redirect_ur = 'login'  # Define the redirection URL as 'login'
        return redirect(redirect_ur)  # Redirect the user to the login page



def get_all_user_data_from_table():
    connection = None  # Initialize connection variable
    cursor = None  # Initialize cursor variable
    try:
        connection = psycopg2.connect(**db_config)  # Establish a connection to the database using provided configuration
        cursor = connection.cursor()  # Create a cursor object to execute queries

        table_name = 'users'  # Specify the name of the table to query
        query = f"SELECT * FROM {table_name}"  # Construct a SQL query to fetch all data from the table

        cursor.execute(query)  # Execute the query
        data = cursor.fetchall()  # Fetch all the rows returned by the query

        return data  # Return the fetched data
    except Exception as e:
        print("Error retrieving data from the table:", e)  # Print an error message if an exception occurs
        return []  # Return an empty list if an error occurs
    finally:
        if cursor:
            cursor.close()  # Close the cursor to release database resources
        if connection:
            connection.close()  # Close the database connection

   

@app.route('/dashboard')  # Decorator to define a route '/dashboard' for the dashboard function
def dashboard():
    user_info = session.get('user_info', {})  # Retrieve user information from the session, defaulting to an empty dictionary
    if user_info:  # Check if user_info is not empty
        if user_info['email'] in ['sanjayasd45@gmail.com', 'kushal@sitare.org', 'nikhil7618987598@gmail.com']:
            # Check if the user's email is in the list of super users
            all_url_data = get_all_data_from_table()  # Fetch all URL data from the table
            all_user_data = get_all_user_data_from_table()  # Fetch all user data from the table
            return render_template("dashboard.html", data=all_url_data, all_user_data=all_user_data)
            # Render the dashboard.html template with the fetched data
        msg = 'You Are Not The Super User'  # Message for non-super users
        return render_template("error.html", msg=msg)  # Render the error.html template with the error message
    return redirect('login')  # Redirect the user to the login page if user_info is empty
