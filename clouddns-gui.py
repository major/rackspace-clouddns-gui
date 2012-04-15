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
import clouddns.consts
from flask import Flask, render_template, g, request, flash, redirect
import json
import re

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
    _authurl = clouddns.consts.us_authurl
    if "auth_url" in creds:
        if str(creds["auth_url"]).lower() == "uk":
            _authurl = clouddns.consts.uk_authurl

    g.raxdns = connection.Connection(
        creds['username'], creds['apikey'], authurl=_authurl)

@app.route("/")
@app.route("/domains")
@app.route("/domains/<accountId>/<domainname>")
@app.route("/domains/<accountId>")
def index(accountId=None, domainname=None):
    """All of the HTML for the entire app flows through here"""

    # Determine Account
    if accountId is None:
        return redirect("/domains/%s" % getAccount())
    
    # Pick up a list of domains from the API
    setAccount(accountId)
    domainlist = g.raxdns.get_domains()

    # If no domainname was specified in the URI, we need to pick up the records
    if domainname:
        domain = g.raxdns.get_domain(name=domainname)
        records = domain.get_records()
    else:
        domain = None
        records = None

    #### TODO: Implement an API limits display
    # limits_resp = g.raxdns.make_request('GET', ['limits'])
    # limits = json.loads(limits_resp.read())

    return render_template('index.html', domainobj=domain, domainname=domainname,
        domainlist=domainlist, records=records, accountId=accountId)


@app.route("/account", methods=['POST'])
def change_accountId():
    """Handles setting the accountId from the Nav Bar"""

    accountId = request.form['accountId']
	### TODO: VALIDATE!!
    if accountId:
        try:
            g.raxdns.set_account(accountId)
        except AttributeError:
            app.logger.warning('Unable to set_account(), perhaps the python-clouddns library is outdated?')
            flash("Application Error: unable to set_account(), update python-clouddns library")
            return redirect("/domains/%s" % getAccount())
        return redirect("/domains/%s" % accountId)
    else: # If its blank, return without the trailing /
        return redirect("/domains")

# No Application route, this is an internal function
def getAccount():
    """Internal Function to get the accountId (wrapper to python-clouddns function)"""
    ## Try the wrapper script, fail (more) gracefully if not support
    try: 
        accountId = g.raxdns.get_accountId()
    except AttributeError:
        ## work around for missing get_accountId()
        (baseUri, sep , accountId) = g.raxdns.uri.rstrip('/').rpartition('/')
        app.logger.warning('Unable to get_account(), perhaps the python-clouddns library is outdated? (%s)' % accountId)
	pass
    return accountId

# No Application route, this is an internal function
def setAccount(accountId=None):
    """Internal Function to set the accountId (wrapper to python-clouddns function)"""
    ## Try the wrapper script, fail (more) gracefully if not support
    try:
        g.raxdns.set_account(accountId)
    except AttributeError:
        app.logger.warning('Unable to set_account(), perhaps the python-clouddns library is outdated? (%s)' % accountId)
        #flash("Application Error: unable to set_account(), update python-clouddns library")
        pass

 
@app.route("/domains/<accountId>/add", methods=['POST'])
def add_domain(accountId=None):
    """Handles adding domains"""

    # Find out the name of the domain we're adding
    domainname = request.form['domain']

    # Issue a domain creation request to the API and flash a message
    setAccount(accountId)
    g.raxdns.create_domain(
        name=domainname,
        ttl=3600,
        emailAddress="admin@%s" % domainname)
    flash("Domain added: %s" % domainname)

    return redirect("/domains/%s/%s" % (accountId, domainname))

@app.route("/domains/<accountId>/duplicate", methods=['POST'])
def duplicate_domain(accountId=None):
    """Adds a new domain and adds records from an existing domain"""

    # Dig up the old domain and records
    setAccount(accountId)
    olddomain = g.raxdns.get_domain(name=request.form['olddomain'])
    oldrecords = olddomain.get_records()

    # Create the new domain
    newdomain = g.raxdns.create_domain(
        name=request.form['newdomain'],
        ttl=3600,
        emailAddress="admin@%s" % request.form['newdomain'])

    # Add records
    records_to_create = []
    for oldrecord in oldrecords:

        # Skip these since the new domain should have them anyway
        if oldrecord.type == 'NS' and str(oldrecord.data).endswith(
            'stabletransit.com'):
            continue

        # Change the names on the new records to reflect the new domain
        oldrecord.name = oldrecord.name.replace(
            request.form['olddomain'], request.form['newdomain'])

        # We'll have a priority field for MX/SRV records
        if oldrecord.type in ['MX', 'SRV']:
            records_to_create.append([
                oldrecord.name,
                oldrecord.data,
                oldrecord.type,
                int(oldrecord.ttl),
                oldrecord.priority])

        # Submit without priority for anything else
        else:
            records_to_create.append([
                oldrecord.name,
                oldrecord.data,
                oldrecord.type,
                int(oldrecord.ttl)])

    # Create the DNS records
    newdomain.create_records(records_to_create)

    # return str("/domains/%s" % request.form['newdomain'])
    #return redirect("/domains/%s" % request.form['newdomain'])
    return redirect("/domains/%s/%s" % (accountId, request.form['newdomain']))


@app.route("/domains/<accountId>/add_zone", methods=['POST'])
def add_domain_bind(accountId=None):
    """Handles adding domains via a BIND zone file"""

    # Get the BIND zone file from the user
    zone_file = request.form['zone_file']

    # Issue a domain import request to the API and flash a message
    setAccount(accountId)
    reply = g.raxdns.import_domain(zone_file, accountId)
    flash("Domain import done")

    return redirect("/domains/%s" % accountId)
    #return redirect("/domains/%s/%s" % (accountId, domainname))


@app.route("/domains/<accountId>/delete", methods=['POST'])
def delete_domain(accountId=None):
    """Handles deleting domains"""

    # Pick up the form fields
    confirmation = request.form['confirmation']
    domain_name = request.form['domain']

    # Did the user submit the confirmation text properly?
    if not confirmation or confirmation != 'REALLYDELETE':
        flash("Domain deletion canceled. Please type the confirmation string.")
        return redirect("/domains/%s/%s" % (accountId, domain_name))

    # Retrieve the domain from the API and delete it
    domain_name = request.form['domain']
    setAccount(accountId)
    domain = g.raxdns.get_domain(name=domain_name)
    g.raxdns.delete_domain(domain.id)

    # Flash a friendly message
    flash("Domain deleted: %s" % domain_name)

    return redirect("/domains/%s" % accountId)

@app.route("/domains/<accountId>/<domainname>/ttl_adjust", methods=['POST'])
def adjust_ttl(accountId=None,domainname=None):
    """Changes TTL values on all records"""

    # Get the domain from the API
    setAccount(accountId)
    domain = g.raxdns.get_domain(name=domainname)

    # Loop through the records and adjust them
    for record in domain.get_records():

        # The API sometimes throws 400's for these updates and I haven't fully
        # nailed down the reason why.
        try:
            record.update(ttl=int(request.form['ttl']))
        except:
            pass

    return redirect("/domains/%s/%s" % (accountId, domainname))


@app.route("/domains/<accountId>/<domainname>/add_record", methods=['POST'])
def add_record(accountId=None, domainname=None):
    """Handles adding records"""

    # Get the domain from the API
    setAccount(accountId)
    domain = g.raxdns.get_domain(name=domainname)

    # Get the form data out of an immutable dict
    formvars = {x:y[0] for x, y in dict(request.form).iteritems()}

    # Does the data from the form end with the domainname? If it doesn't the
    # user probably entered a partial name rather than a FQDN. Append
    # the domain name to ensure that the API doesn't get grumpy.
    if re.match("%s$" % domainname, formvars['name']) == None:
        formvars['name'] = "%s.%s" % (formvars['name'], domainname)

    # We'll have a priority field for MX/SRV records
    if formvars['type'] in ['MX', 'SRV']:
        domain.create_record(
            formvars['name'],
            formvars['data'],
            formvars['type'],
            ttl=int(formvars['ttl']),
            priority=formvars['priority'])

    # Submit without priority for anything else
    else:
        domain.create_record(
            formvars['name'],
            formvars['data'],
            formvars['type'],
            ttl=int(formvars['ttl']))

    # Flash a friendly message
    flash("Record added")

    return redirect("/domains/%s/%s" % (accountId, domainname))


@app.route("/domains/<accountId>/<domainname>/<recordid>/update", methods=['POST'])
def update_record(accountId=None, domainname=None, recordid=None):
    """Handles record updates"""

    # Get the domain and record from the API
    setAccount(accountId)
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

    return redirect("/domains/%s/%s" % (accountId, domainname))


@app.route("/domains/<accountId>/<domainname>/<recordid>/delete")
def delete_record(accountId=None, domainname=None, recordid=None):
    """Handles record deletions"""

    # Get the domain and delete the record
    setAccount(accountId)
    domain = g.raxdns.get_domain(name=domainname)
    domain.delete_record(recordid)

    # Flash a friendly message
    flash("Record deleted")

    return redirect("/domains/%s/%s" % (accountId, domainname))

if __name__ == "__main__":
    # Only for running this app via python directly.  This is ignored if you
    # run it through mod_wsgi.
    #app.run(host='127.0.0.1')
    app.run(host='0.0.0.0')

#vim:set ai sw=4 ts=4 tw=0 expandtab:
