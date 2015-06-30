from __future__ import unicode_literals

import json
import os
from flask import Flask, request, send_from_directory, url_for
import requests
from requests.auth import HTTPBasicAuth
from cloning import merge_diff

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['GITHUB_TOKEN'] = os.getenv('GITHUB_TOKEN')
app.config['GITHUB_USERNAME'] = os.getenv('GITHUB_USERNAME')
app.config['LINK_TEMPLATE'] = os.getenv('LINK_TEMPLATE')

@app.route('/payload', methods=['POST'])
def webhook():
    payload = request.get_json()
    if payload['action'] not in ('opened', 'synchronize'):
        return '', 204
    compare = payload['pull_request']['head']['ref']
    base = payload['pull_request']['base']['ref']
    repo = payload['pull_request']['base']['repo']['name']
    full_repo = payload['pull_request']['base']['repo']['full_name']
    pr_id = payload['pull_request']['id']
    bg_task = 'python cloning.py {} {} {} {} &'.format(
        repo, base, compare, pr_id)
    print bg_task
    os.system(bg_task)
    comment_endpoint = 'https://api.github.com/repos/{repo}/issues/{pr_number}/comments'.format(
        repo=full_repo, pr_number=payload['number'])
    data = json.dumps(dict(body='<a href="{}">More accurate diff</a>'.format(
        app.config['LINK_TEMPLATE'].format(pr_id))))
    r = requests.post(
        comment_endpoint,
        data=data,
        auth=HTTPBasicAuth(app.config['GITHUB_USERNAME'], app.config['GITHUB_TOKEN']))
    print 'hit', comment_endpoint, 'with data',
    r.raise_for_status()

    return '', 204

@app.route('/diff/<pr_id>')
def retrieve_diff(pr_id):
    return send_from_directory('diff', '{}.html'.format(pr_id))

@app.route('/diff_style.css')
def root():
    return app.send_static_file('diff_style.css')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
