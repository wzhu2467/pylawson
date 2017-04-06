import logging
import sys
from pylawson.client import ms_samlpr, sec_api

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
ios = ms_samlpr.SamlSession(json_file='c:/users/sacarey/personal/google drive/dev/pylawson.json')

print('bool:', ios.__bool__())

print('is authenticated:', ios.is_authenticated)

print('profile:', ios.profile)

ios.close()

ios = sec_api.SecApiSession()

print('bool:', ios.__bool__())

print('is authenticated:', ios.is_authenticated)

print('profile:', ios.profile)

ios.close()
