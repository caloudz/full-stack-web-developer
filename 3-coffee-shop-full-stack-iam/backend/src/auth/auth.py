import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen

# --------------------------------------------------------------
# Auth0 Config
# --------------------------------------------------------------

AUTH0_DOMAIN = 'fswd-coffee.eu.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'https://127.0.0.1:5000'

# --------------------------------------------------------------
# AuthError Exception
# --------------------------------------------------------------

class AuthError(Exception):
    '''
    A standardized way to communicate auth failure modes
    '''
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

# --------------------------------------------------------------
# Auth Methods
# https://github.com/udacity/FSND/blob/master/BasicFlaskAuth/app.py
# --------------------------------------------------------------

def get_token_auth_header():
    '''
    Retrieves access token from authorization header.
    Attempts to get header from request. Attemps to split bearer and token.
    Raises Error if no header is present or if header is malformed
    Returns:
        Token part of header
    '''
    auth = request.headers.get('Authorization', None)
    if not auth:
        # raise error if header is missing
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)
    parts = auth.split()
    if parts[0].lower() != 'bearer':
        # raise error if header does not start with "Bearer"
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)

    elif len(parts) == 1:
        # check if the Token is available
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)

    elif len(parts) > 2:
        # check if the Token is bearer
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    # if no issues, retrieve and return token (second part of header)
    token = parts[1]
    return token

def check_permissions(permission, payload):
    '''
    Check if permissions are included in payload, provided that RBAC settings are correctly set in Auth0.
    Input:
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload
    Returns:
        True if
            - permissions are included in payload
            - requested permission string is in payload permissions array
    '''
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Permissions not included in JWT.'
        }, 400)

    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Not authorized to perform this action.'
        }, 403)
    return True

'''
    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
def verify_decode_jwt(token):
    '''
    Decodes payload from token and validate the claims.
    Input:
        token: JSON web token (str)
    Return:
        Decoded payload
    '''
    # verify token using Auth0 /.well-known/jwks.json
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    
    # checks that is is an Auth0 token with key id (kid)
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    rsa_key = {}
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms = ALGORITHMS,
                audience = API_AUDIENCE,
                issuer = f'https://{AUTH0_DOMAIN}/'
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)
        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
        'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
    }, 400)

def requires_auth(permission=''):
    '''
    Authentication wrapper.
    Use get_token_auth_header method to get the token.
    Use verify_decode_jwt method to decode the jwt.
    Use check_permissions method validate claims and check the requested permission.
    Input:
        permission: string permission (i.e. 'post:drink')
    Returns:
        decorator which passes the decoded payload to the decorated method
    '''
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator