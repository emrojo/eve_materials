import os
import logging
import uuid
import json

from uuid_encoder import UUIDEncoder
from uuid_validator import UUIDValidator
from eve import Eve
from flask import request, jsonify, abort, Response
from flask_bootstrap import Bootstrap
from eve_swagger import swagger
from bson import json_util

SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'development.py')

def create_app(settings):
  app = Eve(settings=settings, json_encoder=UUIDEncoder, validator=UUIDValidator)

  Bootstrap(app)
  app.register_blueprint(swagger)

  def set_uuid(resource_name, items):
    for item in items:
      item['_id'] = str(uuid.uuid4())

  app.on_insert += set_uuid

  # Very rudimentary validation method... just for development!
  @app.route('/materials/validate', methods=['POST'])
  def validate(**lookup):
    if not 'materials' in request.json:
      abort(422)

    validation_set = set(request.json['materials'])
    result_set = set()

    for material in app.data.driver.db.materials.find({'_id': { '$in': request.json['materials'] } }, { '_id': 1}):
      result_set.add(material['_id'])

    difference = validation_set - result_set
    diff_len = len(difference)

    if (diff_len == 0):
      return "ok"
    else:
      return "not ok - " + str(diff_len) + " materials not found"

  @app.route('/materials/bulk_get', methods=['POST'])
  def bulk_get(**lookup):
    if not 'materials' in request.json:
      abort(422)

    materials = []

    for material in app.data.driver.db.materials.find({'_id': { '$in': request.json['materials'] } }):
      materials.append(material)

    materials = json.dumps(materials, default=json_util.default)

    resp = Response(response=materials,
        status=200, \
        mimetype="application/json")

    return (resp)

  return app


if __name__ == '__main__':
  # enable logging to 'app.log' file
  handler = logging.FileHandler('app.log')

  # set a custom log format, and add request
  # metadata to each log line
  handler.setFormatter(logging.Formatter(
      '%(asctime)s %(levelname)s: %(message)s '
      '[in %(filename)s:%(lineno)d] -- ip: %(clientip)s, '
      'url: %(url)s, method:%(method)s'))

  app = create_app(SETTINGS_PATH)

  # the default log level is set to WARNING, so
  # we have to explictly set the logging level
  # to INFO to get our custom message logged.
  app.logger.setLevel(logging.INFO)

  # append the handler to the default application logger
  app.logger.addHandler(handler)

  app.run()