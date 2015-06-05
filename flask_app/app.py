import logbook
from flask import (abort, current_app, Flask, jsonify, request,
                   send_from_directory)
from itsdangerous import TimedSerializer, BadSignature

from apiclient.discovery import build
from httplib2 import Http
from oauth2client.client import OAuth2WebServerFlow

_logger = logbook.Logger(__name__)

app = Flask(__name__)

app.config.update({
    'OAUTH2_CLIENT_ID': 'XXXXXXXXX',
    'OAUTH2_CLIENT_SECRET': 'XXXXXXX',
})


@app.route("/")
def index():
    return send_from_directory(current_app.static_folder, 'index.html')


@app.route("/login", methods=['POST'])
def login():

    auth_code = (request.json or {}).get('authorizationCode')
    if auth_code is None:
        abort(401)

    user_info = _get_oauth2_identity(auth_code)
    if not user_info:
        abort(401)

    token = _get_token_serializer().dumps({'user_info': user_info})

    return jsonify({
        'auth_token': token,
        'user_info': user_info,
    })


@app.route("/reauth", methods=['POST'])
def reauth():
    token = (request.json or {}).get('auth_token')
    if token is None:
        abort(401)
    try:
        token_data = _get_token_serializer().loads(
            token, max_age=_MAX_TOKEN_AGE)
    except BadSignature:
        abort(401)

    return jsonify({
        'auth_token': token,
        'user_info': token_data['user_info'],
    })


def _get_token_serializer():
    return TimedSerializer(current_app.config['SECRET_KEY'])

def _get_oauth2_identity(auth_code):

    client_id = current_app.config.get('OAUTH2_CLIENT_ID')
    client_secret = current_app.config.get('OAUTH2_CLIENT_SECRET')
    if not client_id:
        _logger.error('No OAuth2 client id configured')
        return

    if not client_secret:
        _logger.error('No OAuth2 client secret configured')
        return

    flow = OAuth2WebServerFlow(
        client_id=client_id,
        client_secret=client_secret,

        scope='https://www.googleapis.com/auth/userinfo.profile',
        redirect_uri=request.host_url[:-1])

    credentials = flow.step2_exchange(auth_code)

    info = _get_user_info(credentials)
    _logger.debug('Found user info: {}', info)
    return info


def _get_user_info(credentials):
    http_client = Http()
    if credentials.access_token_expired:
        credentials.refresh(http_client)
    credentials.authorize(http_client)
    service = build('oauth2', 'v2', http=http_client)
    return service.userinfo().get().execute()


if __name__ == "__main__":
    app.config.update({
        'DEBUG': True,
        'SECRET_KEY': 'some-secret-key'
    })
    app.run(port=8000)
