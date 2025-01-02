from flask import Flask, request, render_template, jsonify
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os
import logging

# Load the environment variables from the .env file
load_dotenv()

# Retrieve the username and password from environment variables
username = os.getenv('ES_USER')
password = os.getenv('ES_PASSWORD')

# Elasticsearch configuration
ES_CONFIG = {
    'host': 'localhost',  # Replace with your Elasticsearch host
    'port': 9200,  # Replace with your Elasticsearch port
    'scheme': 'http',
    'basic_auth': (username, password)  # Replace with your Elasticsearch username and password
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

# Test connection
try:
    print(f"Connected to ElasticSearch cluster {es.info().body['cluster_name']}")
except Exception as e:
    raise ConnectionError("Failed to connect to Elasticsearch. Check your configuration and server status.") from e

# Flask App
app = Flask(__name__)

# Enable debug-level logging
logging.basicConfig(level=logging.DEBUG)

# Max number of results for autocomplete
MAX_SIZE = 15

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_indices", methods=["GET"])
def get_indices():
    """Fetch all indices from Elasticsearch"""
    try:
        indices = es.indices.get_alias(index="*").keys()
        app.logger.info(f"Fetched indices: {indices}")
        return jsonify(sorted(indices))
    except Exception as e:
        app.logger.error(f"Error fetching indices: {e}")
        return jsonify([]), 500

@app.route("/get_fields", methods=["GET"])
def get_fields():
    """Fetch fields for a specific index"""
    index = request.args.get("index")
    if not index:
        return jsonify([]), 400

    try:
        mapping = es.indices.get_mapping(index=index)
        fields = mapping[index]['mappings'].get('properties', {}).keys()
        app.logger.info(f"Fetched fields for index {index}: {fields}")
        return jsonify(sorted(fields))
    except Exception as e:
        app.logger.error(f"Error fetching fields for index {index}: {e}")
        return jsonify([]), 500

@app.route("/search", methods=["GET"])
def search_autocomplete():
    query = request.args.get("q", "").strip().lower()
    index = request.args.get("index")
    field = request.args.get("field")

    app.logger.debug(f"Received query: {query}, index: {index}, field: {field}")

    if not query or not index or not field:
        return jsonify([])

    # Determine the field type (text or keyword)
    field_type = "text"  # Default to text
    try:
        mapping = es.indices.get_mapping(index=index)
        field_mapping = mapping[index]['mappings']['properties'].get(field, {})
        field_type = field_mapping.get('type', 'text')
    except Exception as e:
        app.logger.error(f"Error determining field type for {field}: {e}")

    # Elasticsearch query for autocomplete
    if field_type == "text":
        search_query = {
            "match": {
                field: {
                    "query": query,
                    "fuzziness": "AUTO"  # Allow for minor spelling errors
                }
            }
        }
    elif field_type == "keyword":
        search_query = {
            "wildcard": {
                field: {
                    "value": f"*{query}*"
                }
            }
        }

    try:
        response = es.search(index=index, body={"query": search_query}, size=MAX_SIZE)
        results = []
        for hit in response["hits"]["hits"]:
            value = hit["_source"].get(field, "Unknown")
            if isinstance(value, list):
                value = ", ".join(value)  # Join list values into a single string
            results.append({"id": hit["_id"], "value": value})
        app.logger.debug(f"Suggestions: {results}")
        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Error during Elasticsearch search: {e}")
        return jsonify([]), 500

@app.route("/get_document", methods=["GET"])
def get_document():
    doc_id = request.args.get("id")
    index = request.args.get("index")

    app.logger.debug(f"Received request for document ID: {doc_id}, index: {index}")

    if not doc_id or not index:
        return jsonify({})

    try:
        response = es.get(index=index, id=doc_id)
        document = response["_source"]
        # Convert list values to comma-separated strings for display
        for key, value in document.items():
            if isinstance(value, list):
                document[key] = ", ".join(value)
        app.logger.debug(f"Fetched document: {document}")
        return jsonify(document)
    except Exception as e:
        app.logger.error(f"Error fetching document: {e}")
        return jsonify({}), 500

if __name__ == "__main__":
    app.run(debug=True)