from bson import ObjectId
from flask import Flask, jsonify, request, current_app, current_app
from pymongo import MongoClient
from ariadne.constants import PLAYGROUND_HTML
from ariadne import MutationType, QueryType, make_executable_schema, graphql_sync
from schema import type_defs

# These are the collections (tables) we are dealing with
PLANT_COLLECTION = "plants"
DEVICE_COLLECTION = "devices"
HOST = "0.0.0.0"

def get_database():
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = "mongodb://localhost:27017"
    DATABASE = "growCube"

    # Create a connection using MongoClient
    client = MongoClient(CONNECTION_STRING)

    # Create the database for our example
    return client[DATABASE]

# This is added so that many files can reuse the function get_database()
if __name__ == "__main__":
    # Get the database
    database = get_database()

# Thanks: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-flask.html
# https://blog.logrocket.com/build-graphql-api-python-flask-ariadne/

# `static_url_base_path` tells the server to serve the /static directory at the root path /
application = Flask(__name__, static_url_path='')

# Database collections
plantsdb = database[PLANT_COLLECTION]
devicesdb = database[DEVICE_COLLECTION]

# GraphQL config
query = QueryType()
mutation = MutationType()
schema = make_executable_schema(type_defs, [query, mutation])

# Define resolvers
@query.field("plants")
def plants(*_):
    return list(plantsdb.find({}))

@query.field("devices")
def devices(*_):
    return list(devicesdb.find({}))

@query.field("device")
def device(*_, id):
    return devicesdb.find_one({"_id": ObjectId(id)})

# Define mutations
@mutation.field("add_plant")
def add_plant(*_, commonName, genus, species):
    document = plantsdb.insert_one(
        {"commonName": commonName, "genus": genus, "species": species}
    )
    return plantsdb.find_one({"_id": ObjectId(document.inserted_id)})

@mutation.field("add_device")
def add_device(_, info, system, source, drain, food, air, LED):
    document = devicesdb.insert_one(
        {"system": system, "source": source, "drain": drain,
            "food": food, "air": air, "LED": LED}
    )
    return devicesdb.find_one({"_id": ObjectId(document.inserted_id)})

@mutation.field("update_device")
def update_device(_, info, id, system, source, drain, food, air, LED):
    document = devicesdb.replace_one(
        {"_id": ObjectId(id)},
        {"system": system, "source": source, "drain": drain,
         "food": food, "air": air, "LED": LED},
        upsert=True
    )

    id = document.upserted_id if document.upserted_id else id
    return devicesdb.find_one({"_id": ObjectId(id)})

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

# Serve vue app at root
@application.route('/', methods=['GET'])
def vue():
    return current_app.send_static_file("App.html")

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run(host=HOST)
