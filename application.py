from plistlib import UID
from urllib import response
from bson import ObjectId, json_util
import json
import bson
from flask import Flask, Response, jsonify, make_response, render_template, request, current_app, g, current_app
from flask_restful import Resource, Api
from flask_cors import CORS
from pymongo import MongoClient
import sqlite3 as sl
import json
from ariadne.asgi import GraphQL
from ariadne.constants import PLAYGROUND_HTML
from ariadne import MutationType, gql, QueryType, make_executable_schema, graphql_sync
from schema import type_defs

# These are the collections (tables) we are dealing with
PLANTS_COLLECTION = "plants"
SETTINGS_COLLECTION = "settings"

# https://blog.logrocket.com/build-graphql-api-python-flask-ariadne/
query = QueryType()
mutation = MutationType()


def get_database():

    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = "mongodb://localhost:27017"
    DATABASE = "grow_cube"
    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING)

    # Create the database for our example (we will use the same database throughout the tutorial
    return client[DATABASE]


# This is added so that many files can reuse the function get_database()
if __name__ == "__main__":
    # Get the database
    database = get_database()

# Thanks: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-flask.html

# EB looks for an 'application' callable by default.
application = Flask(__name__)
#application.config['SERVER_NAME'] = 'localhost:5000'
CORS(application)

delay = int(1000)

# Creating or accessing database
plantsdb = database[PLANTS_COLLECTION]
settingsdb = database[SETTINGS_COLLECTION]

# https://blog.logrocket.com/build-graphql-api-python-flask-ariadne/
# https://pymongo.readthedocs.io/en/stable/api/pymongo/cursor.html
# Define resolvers


@query.field("plants")
def plants(*_):
    return list(plantsdb.find({}))


@query.field("settings")
def settings(*_):
    return list(settingsdb.find({}))

# plant resolver (add new  place)


@mutation.field("add_plant")
def add_plant(_, info, commonName, genus, species):
    document = plantsdb.insert_one(
        {"commonName": commonName, "genus": genus, "species": species}
    )
    return plantsdb.find_one({"_id": ObjectId(document.inserted_id)})


@mutation.field("add_settings")
def add_settings(_, info, system, source, drain, food, air, LED):
    document = settingsdb.insert_one(
        {"system": system, "source": source, "drain": drain,
            "food": food, "air": air, "LED": LED}
    )
    return settingsdb.find_one({"_id": ObjectId(document.inserted_id)})


@mutation.field("update_settings")
def update_settings(_, info, id, system, source, drain, food, air, LED):
    document = settingsdb.update_one(
        {"_id": ObjectId(id)},
        {"system": system, "source": source, "drain": drain,
         "food": food, "air": air, "LED": LED},
        upsert=True
    )
    return settingsdb.find_one({"_id": ObjectId(document.inserted_id)})


schema = make_executable_schema(type_defs, [query, mutation])

# The type of endpoint (get, set, etc.) is usually just distinguished by the type of request (GET, POST, PUT, etc.)
# Create a GraphQL Playground UI for the GraphQL schema


@application.route("/graphql", methods=["GET"])
def graphql_playground():
    # Playground accepts GET requests only.
    # If you wanted to support POST you'd have to
    # change the method to POST and set the content
    # type header to application/graphql
    return PLAYGROUND_HTML

# Create a GraphQL endpoint for executing GraphQL queries


@application.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(
        schema, data, context_value={"request": request})
    status_code = 200 if success else 400
    return jsonify(result), status_code


@application.route('/device/<device_id>', methods=['POST'])
def flask_set_delay(device_id):
    body = request.json
    response = make_response()
    delay_on = body["delay_on"]
    delay_off = body["delay_off"]
    pulse_width = body["pulse_width"]

    try:
        settings.update_many({"_id": ObjectId(device_id)}, {
            "$set": {
                "system.delay_on": delay_on,
                "system.pulse_width": pulse_width,
                "system.delay_off": delay_off
            },
        },
            upsert=True)
        response.status_code = 200
    except:
        response = make_response("Invalid request")
        response.status_code = 400

    return response

# Should not be a POST for a Get command. Should only be GET


@application.route('/device/<device_number>', methods=['GET'])
def flask_query_delay(device_number):

    try:
        res = settings.find_one({"_id": ObjectId(device_number)})
    except:
        response = make_response(
            "Device id must be a valid 24 character hex string")
        response.status_code = 400

    if 'res' in locals():
        response_body = json.loads(json_util.dumps(res))
        print(response_body)
        response = make_response(response_body)
        response.content_type = "Application/JSON"
        response.status_code = 200

    return response


@application.route('/', methods=['GET'])
def welcome_screen():
    return current_app.send_static_file("App.html")


# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run(host="0.0.0.0")
