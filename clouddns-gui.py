#!/usr/bin/python
#
# Copyright 2012 Major Hayden
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
from clouddns import connection
from flask import Flask, render_template, g, request, flash, redirect
import json

app = Flask(__name__)

# This should obviously be changed
app.secret_key = 'reallysecret'

# Flip this to false if you share a running app with anyone else
app.debug = True

@app.before_request
def connect_clouddns():
    """Connect to Rackspace auth and share the connection handler globally"""

    # Get the API credentials
    with open('apicredentials.json', 'r') as f:
        creds = json.load(f)

    # Connect to Rackspace auth
    g.raxdns = connection.Connection(
        creds['username'],creds['apikey'])

@app.route("/")
@app.route("/domains")
@app.route("/domains/<domainname>")
def index(domainname=None):
    """All of the HTML for the entire app flows through here"""
    
    # Pick up a list of domains from the API
    domainlist = g.raxdns.get_domains()

    # If no domainname was specified in the URI, we need to pick up the records
    if domainname != None:
        domain = g.raxdns.get_domain(name=domainname)
        records = domain.get_records()
    else:
        records = None

    #### TODO: Implement an API limits display
    # limits_resp = g.raxdns.make_request('GET', ['limits'])
    # limits = json.loads(limits_resp.read())

    return render_template('index.html', domainname=domainname,
        domainlist=domainlist, records=records)

@app.route("/domains/add", methods=['POST'])
def add_domain():
    """Handles adding domains"""

    # Find out the name of the domain we're adding
    domain = request.form['domain']

    # Issue a domain creation request to the API and flash a message
    g.raxdns.create_domain(
        name=request.form['domain'],
        ttl=3600,
        emailAddress="admin@%s" % domain)
    flash("Domain added: %s" % domain)

    return redirect("/domains/%s" % domain)

@app.route("/domains/delete", methods=['POST'])
def delete_domain():
    """Handles deleting domains"""

    # Pick up the form fields
    confirmation = request.form['confirmation']
    domain_name = request.form['domain']

    # Did the user submit the confirmation text properly?
    if confirmation == None or confirmation != 'REALLYDELETE':
        flash("Domain deletion canceled. Please type the confirmation string.")
        return redirect("/domains/%s" % domain_name)

    # Retrieve the domain from the API and delete it
    domain_name = request.form['domain']
    domain = g.raxdns.get_domain(name=domain_name)
    g.raxdns.delete_domain(domain.id)

    # Flash a friendly message
    flash("Domain deleted: %s" % domain_name)

    return redirect("/domains")

@app.route("/domains/<domainname>/add_record", methods=['POST'])
def add_record(domainname=None):
    """Handles adding records"""

    # Get the domain from the API
    domain = g.raxdns.get_domain(name=domainname)

    # We'll have a priority field for MX/SRV records
    if request.form['type'] in ['MX', 'SRV']:
        domain.create_record(
            request.form['name'],
            request.form['data'],
            request.form['type'],
            ttl=request.form['ttl'],
            priority=request.form['priority'])

    # Submit without priority for anything else
    else:
        domain.create_record(
            request.form['name'],
            request.form['data'],
            request.form['type'],
            ttl=request.form['ttl'])

    # Flash a friendly message
    flash("Record added")

    return redirect("/domains/%s" % domainname)

@app.route("/domains/<domainname>/<recordid>/update", methods=['POST'])
def update_record(domainname=None, recordid=None):
    """Handles record updates"""

    # Get the domain and record from the API
    domain = g.raxdns.get_domain(name=domainname)
    record = domain.get_record(id=recordid)

    # Submit our updates
    # Only data/TTL updates are allowed during updates.
    # See 4.2.7. Modify Domain(s) in the Cloud DNS Developer Guide.
    record.update(
        data=request.form['data'],
        ttl=request.form['ttl'])

    # Flash a friendly message
    flash("Record updated")

    return redirect("/domains/%s" % domainname)

@app.route("/domains/<domainname>/<recordid>/delete")
def delete_record(domainname=None, recordid=None):
    """Handles record deletions"""

    # Get the domain and delete the record
    domain = g.raxdns.get_domain(name=domainname)
    domain.delete_record(recordid)

    # Flash a friendly message
    flash("Record deleted")

    return redirect("/domains/%s" % domainname)

if __name__ == "__main__":
    # Only for running this app via python directly.  This is ignored if you
    # run it through mod_wsgi.
    app.run(host='0.0.0.0')
