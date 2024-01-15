from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

# Define a simple resource
class HelloWorld(Resource):
    def get(self):
        return {'message': 'Hello, World!'}

# Add the resource to the API with a specific route
api.add_resource(HelloWorld, '/hello')

if __name__ == '__main__':
    app.run(debug=True)
