# ProfePulse

## David Restrepo, Sebastián Castaño & Miguel Arcila

## How to install? 
### Download as a zip file or with git clone the repository with this command:
### git clone https://github.com/Miguel107/ProfePulse.git
### Create a file named keys.env in the main project folder. It should look like this
 OPENAI_API_KEY = 'your_openai_api_key'
 
 EMAIL_HOST= 'smtp.gmail.com'
 
 EMAIL_HOST_USER= 'your_gmail'
 
 EMAIL_HOST_PASSWORD= 'your_password_app'


## How to run it?
### 1. Go to the directory
### 2. pip install -r requirements.txt
### 3. python manage.py makemigrations
### 4. python manage.py migrate
### 5. python manage.py runserver
### Open your web browser and go to http://127.0.0.1:8000/
