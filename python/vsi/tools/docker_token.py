#!/usr/bin/env python3
import argparse
import getpass
import base64
import urllib.request
import json

def get_parser():
  # Looks like an arg parser. Maybe I should comment this? Nah. Oops
  parser = argparse.ArgumentParser()
  parser.add_argument('--user', '-u', default=None)
  parser.add_argument('--auth', '-a', default='https://auth.docker.io')
  parser.add_argument('--service', default='registry.docker.io')
  parser.add_argument('--scope',
      help="Repository name for scope of token. E.g. "
           '"repository:samalba/my-app:pull,push"')
  return parser


def main(args=None):
  parser = get_parser()
  args = parser.parse_args(args)

  if args.user:
    user = args.user
  else:
    user = input("Docker username: ")

  password = getpass.getpass("Docker password: ")

  auth = base64.b64encode('{}:{}'.format(user, password).encode())

  url = '{}/token?service={}&scope={}'.format(args.auth, args.service,
                                              args.scope)

  request = urllib.request.Request(url)
  request.add_header(b'Authorization', b'Basic ' + auth)

  with urllib.request.urlopen(request) as f:
    response = json.loads(f.read())

  if 'token' in response:
    print(response['token'])
  else:
    print(response['access_token'])


if __name__ == "__main__":
  main()