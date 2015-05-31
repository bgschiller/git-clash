import os
from flask import Flask, request, send_from_directory
import requests
from requests.auth import HTTPBasicAuth
from cloning import merge_diff

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['GITHUB_TOKEN'] = os.getenv('GITHUB_OAUTH_TOKEN')
app.config['GITHUB_USERNAME'] = os.getenv('GITHUB_USERNAME')
app.config['LINK_TEMPLATE'] = os.getenv('LINK_TEMPLATE')

@app.route('/payload', methods=['POST'])
def webhook():
    payload = request.get_json()
    if payload['action'] not in ('opened', 'synchronized'):
        return '', 204
    compare = payload['pull_request']['head']['ref']
    base = payload['pull_request']['base']['ref']
    repo = payload['pull_request']['base']['repo']['full_name']
    out = merge_diff('https://{token}@github.com/{repo}'.format(
        token=app.config['GITHUB_TOKEN'],
        repo=repo
    ), base, compare)
    pr_id = payload['pull_request']['id']
    with open('created/{}.html'.format(pr_id), 'w') as f:
        f.write(out)
    requests.post(
        '/repos/{repo}/issues/{pr_number}/comments'.format(
            repo=repo, pr_number=payload['number']),
        data=dict(body='More accurate diff available at {}'.format(
            app.config['LINK_TEMPLATE'].format(pr_id))),
        auth=HTTPBasicAuth(app.config['GITHUB_USERNAME'], app.config['GITHUB_TOKEN']))

    return '', 204

@app.route('/diff/<pr_id>')
def retrieve_diff(pr_id):
    return send_from_directory('created', '{}.html'.format(pr_id))

@app.route('/style.css')
def root():
    return app.send_static_file('style.css')


if __name__ == '__main__':
    app.run()
