import json
import logging
from threading import Thread

#from bottle import Bottle
#from bottle import request, response

from flask import Flask, request

_alpaca_url_base = '/api/v1/telescope/0'

class AlpacaDeviceServer(Thread):
    def __init__(self, device, host='localhost', port=8000):
        super().__init__()

        self.device = device
        self.host = host
        self.port = port
        #self.app = Bottle()
        self.app = Flask(__name__)

        #self.app.route(_alpaca_url_base + '/<action>', method='GET',
        #               callback=self.core_get_action_handler)
        #self.app.route(_alpaca_url_base + '/<action>', method='PUT',
        #               callback=self.core_put_action_handler)
        #self.server_transaction_id = 0

        self.app.add_url_rule(_alpaca_url_base + '/<action>', methods=['GET'],
                              view_func=self.core_get_action_handler)
        self.app.add_url_rule(_alpaca_url_base + '/<action>', methods=['PUT'],
                              view_func=self.core_put_action_handler)
        self.server_transaction_id = 0

        # die if main dies
        self.daemon = True

   # @route(_alpaca_url_base + '/<action>', method='GET')
    def core_get_action_handler(self, action):
        #logging.debug(f'core_get_action_handler(): action = {action}')

        # methods common to all devices
#        logging.debug('get request:')
#        for k, v in request.query.items():
#            logging.debug(f'   {k} : {v}')

        resp = {}
        try:
            resp['ClientTransactionID'] = request.query['ClientTransactionID']
        except:
            logging.warning('request missing client id!')

        resp['ServerTransactionID'] = self.server_transaction_id
        self.server_transaction_id += 1

        action_resp = self.device.get_action_handler(action)

        resp['ErrorNumber'] = action_resp['ErrorNumber']
        resp['ErrorString'] = action_resp['ErrorString']
        resp['Value'] = action_resp['Value']

        #response.headers['Content-Type'] = 'application/json'
        return json.dumps(resp), 200, {'Content-Type' : 'application/json'}

    def core_put_action_handler(self, action):
        #logging.debug(f'core_put_action_handler(): action = {action}')

        # methods common to all devices
#        logging.debug('put request:')
#        for k, v in request.query.items():
#            logging.debug(f'   {k} : {v}')

        resp = {}
        try:
            resp['ClientTransactionID'] = request.form['ClientTransactionID']
        except:
            logging.warning('request missing client id!')

        resp['ServerTransactionID'] = self.server_transaction_id
        self.server_transaction_id += 1
        resp['ErrorNumber'] = 0
        resp['ErrorString'] = ''

        action_resp = self.device.put_action_handler(action, request.form)

        resp['ErrorNumber'] = action_resp['ErrorNumber']
        resp['ErrorString'] = action_resp['ErrorString']

        #response.headers['Content-Type'] = 'application/json'
        return json.dumps(resp), 200, {'Content-Type' : 'application/json'}

    def run(self):
        self.app.run(host=self.host, port=self.port) #, debug=True, quiet=True)

