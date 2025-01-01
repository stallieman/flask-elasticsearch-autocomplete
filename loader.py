import csv
from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv()

# Retrieve the username and password from environment variables
username = os.getenv('ES_USER')
password = os.getenv('ES_PASSWORD')

if not username or not password:
    raise ValueError("Elasticsearch username or password not found in environment variables.")

# Elasticsearch configuration
ES_CONFIG = {
    'host': 'localhost',
    'port': 9200,
    'scheme': 'http',
    'basic_auth': (username, password)
}

# Connect to Elasticsearch
es = Elasticsearch(
    hosts=[{
        'host': ES_CONFIG['host'],
        'port': ES_CONFIG['port'],
        'scheme': ES_CONFIG['scheme']
    }],
    basic_auth=ES_CONFIG['basic_auth']
)

# Define the index name
INDEX_NAME = 'movies'

# Create the index if it doesn't exist
if not es.indices.exists(index=INDEX_NAME):
    es.indices.create(index=INDEX_NAME)

# Load the CSV file
file_path = '/Users/marcostalman/Projecten/flask-elasticsearch-autocomplete/IMDB_Movies_Dataset.csv'

def load_csv_to_elasticsearch(file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        actions = []
        for line in reader:
            action = {
                "_index": INDEX_NAME,
                "_source": {
                    "Title": line["Title"],
                    "Average Rating": line["Average Rating"],
                    "Director": line["Director"],
                    "Writer": line["Writer"],
                    "Metascore": line["Metascore"],
                    "Cast": line["Cast"],
                    "Release Date": line["Release Date"],
                    "Country of Origin": line["Country of Origin"],
                    "Languages": line["Languages"],
                    "Budget": line["Budget"],
                    "Worldwide Gross": line["Worldwide Gross"],
                    "Runtime": line["Runtime"]
                }
            }
            actions.append(action)
        helpers.bulk(es, actions)

# Load the data into Elasticsearch
load_csv_to_elasticsearch(file_path)
print(f"Data loaded into Elasticsearch index '{INDEX_NAME}' successfully.")