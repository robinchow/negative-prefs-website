from flask import jsonify, render_template, request
from app import app, mongo, config, sg
from sendgrid.helpers.mail import *
import codecs, json, os.path, random

person = config['General']['Person']

prefs = None
prefs_file = '%s-prefs.json' % (person,)

if not os.path.isfile(prefs_file):
    with codecs.open(prefs_file, 'w', 'utf-8') as f:
        json.dump(prefs, f, indent=2)
else:
    with codecs.open(prefs_file, 'r', 'utf-8') as f:
        prefs = json.load(f)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', person=person)

@app.route('/check', methods=['GET'])
def check():
    global player, prefs

    thing = request.args.get('thing', '').lower()

    if not thing:
        return render_template('empty_input.html')

    mongo.db.searches.insert_one({
        "ip": request.remote_addr,
        "url": request.url,
        "thing": thing
    })
    
    rand = random.random()

    hates = False
    likes = False
    if thing in prefs['hates']:
        hates = True
    elif thing in prefs['likes']:
        likes = True
    else:
        try:
            email_person("Unknown search", 'Someone asked if you hate %s' % (thing,))
        except Exception as inst:
            print(type(inst))
            print(inst)

    return render_template('response.html', person=person, hates=hates, likes=likes, thing=thing, rand=rand)
    
@app.route('/update', methods=['GET'])
def update_view():
    global person
    return render_template('update.html', person=person)

@app.route('/update', methods=["POST"])
def update():
    global person, prefs

    data = request.get_json()
    pref = data.get('pref', None)
    action = data.get('action', None)
    thing = data.get('thing', None)

    if pref is None or action is None or thing is None:
        return json_error('One or more required fields (pref, action, thing) is missing')

    if pref not in prefs.keys():
        return json_error('Unknown preference: %s' % (pref,))

    if action not in ['add', 'remove']:
        return json_error('Unknown action: %s' % (action,))

    thing = thing.lower()

    updated = False
    if action == 'remove':
        try:
            prefs[pref].remove(thing)
            updated = True
        except ValueError:
            pass
    elif action == 'add':
        for other_pref in (x for x in prefs.keys() if x != pref):
            try:
                prefs[other_pref].remove(thing)
                updated = True
            except ValueError:
                pass
        if thing not in prefs[pref]:
            prefs[pref].append(thing)
            updated = True

    if updated:
        with codecs.open(prefs_file, 'w', 'utf-8') as f:
            json.dump(prefs, f, indent=2)
        return jsonify(status='updated')
            
    return jsonify(status='ok')

@app.route('/get_db', methods=['GET'])
def get_db_json():
    global prefs
    return json.dumps(prefs, indent=2)
    
@app.route('/list', methods=['GET'])
def list_view():
    global person, prefs
    return render_template('list.html', person=person, hates=prefs['hates'], likes=prefs['likes'])

@app.route('/list_searches', methods=['GET'])
def list_searches():
    from bson.json_util import dumps
    from bson.son import SON

    coll = mongo.db.searches
    
    pipeline = [
        {"$group": {"_id": "$thing", "count": {"$sum": 1}}},
        {"$sort": SON([("count", -1), ("_id", -1)])}
    ]

    return jsonify(count=coll.count(), search_results=list(coll.aggregate(pipeline)))

def json_error(msg=None):
    return jsonify(status='error', msg=msg)

def email_person(subject, text_content, html_content=None):
    global config, person

    send_email = config['Sendgrid']['SendAs']
    send_name = config['General']['EmailSendName']
    mail = Mail()
    mail.from_email = Email(send_email, send_name)
    mail.subject = subject

    personalization = Personalization()
    for email in (y for (_, y) in config.items('Emails') if y):
        personalization.add_to(Email(email, email))
    mail.add_personalization(personalization)

    mail.add_content(Content("text/plain", text_content))
    if html_content:
        mail.add_content(Content("text/html", html_content))

    response = sg.client.mail.send.post(request_body=mail.get())
