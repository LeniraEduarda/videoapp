from wsgiref.simple_server import make_server
from bson.json_util import dumps
from pyramid.config import Configurator
from pyramid.view import view_config

from json import loads
from bson.objectid import ObjectId

try:
    # for python 2
    from urlparse import urlparse
except ImportError:
    # for python 3
    from urllib.parse import urlparse

from gridfs import GridFS
from pymongo import MongoClient


# configures the application
def main(**settings):
    """ This function returns a Pyramid WSGI application.
   """
    config = Configurator(settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)

    client = MongoClient('mongodb://admin:EDUARDa8@127.0.0.1:27017/videoapp?authSource=admin&readPreference=primary&appname=MongoDB%20Compass%20Community&ssl=false')

    def add_db(request):
        db = client
        return db

    def add_fs(request):
        return GridFS(request.db)

    config.add_request_method(add_db, 'db', reify=True)
    config.add_request_method(add_fs, 'fs', reify=True)

    config.add_route('videos', '/videos')
    config.add_route('video', '/videos/{id}')
    config.add_route('like', '/videos/{id}/like')
    config.add_route('unlike', '/videos/{id}/unlike')
    config.add_route('add_video', '/add')

    # other routes and more config...
    config.scan()
    return config.make_wsgi_app()

# receive a title and theme from the request and enter it in the database:
@view_config(request_method='POST', route_name='add_video', renderer="json")
def add_video(request):
    print(request.params['title'])
    vid_dict = {'title': request.params['title'], 'theme': request.params['theme'], 'likes': 0, 'unlikes': 0}
    id = request.db['videoapp']['videos'].insert_one(vid_dict)

    # result = request.db['videoapp']['videos'].find_one({"_id": ObjectId(str(id))})
    return 'Success!'

# List videos from database:
@view_config(route_name='videos', renderer="json")
def videos(request):
    result = request.db['videoapp']['videos'].find()

    return loads(dumps(result))

# return a video by id
@view_config(route_name='video', renderer="json")
def video(request):
    id = request.matchdict['id']
    result = request.db['videoapp']['videos'].find_one({"_id": ObjectId(id)})
    return loads(dumps(result))

# Add likes by id
@view_config(route_name='like', renderer="json")
def like(request):
    id = request.matchdict['id']

    result = request.db['videoapp']['videos'].find_one({"_id": ObjectId(id)})
    old_value = loads(dumps(result))['likes']
    new_value = old_value + 1
    query = {"_id": ObjectId(id)}
    new = {"$set": {"likes": new_value}}
    request.db['videoapp']['videos'].update_one(query, new)

    result = request.db['videoapp']['videos'].find_one({"_id": ObjectId(id)})

    return loads(dumps(result))

# Add unlikes by id:
@view_config(route_name='unlike', renderer="json")
def unlike(request):
    id = request.matchdict['id']

    result = request.db['videoapp']['videos'].find_one({"_id": ObjectId(id)})
    old_value = loads(dumps(result))['unlikes']
    new_value = old_value + 1
    query = {"_id": ObjectId(id)}
    new = {"$set": {"unlikes": new_value}}
    request.db['videoapp']['videos'].update_one(query, new)

    result = request.db['videoapp']['videos'].find_one({"_id": ObjectId(id)})

    return loads(dumps(result))

# Starts the server
if __name__ == '__main__':
    app = main()
    server = make_server('10.10.0.103', 6543, app)
    server.serve_forever()