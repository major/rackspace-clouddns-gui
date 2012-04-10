# Rackspace Cloud DNS GUI
## A web front-end to Rackspace's Cloud DNS service

**Disclaimers**:
This application is not affiliated with or endorsed by Rackspace.  It's still very, very rough.  It may manage your domains perfectly or it may cause your phone to catch fire.

#### Screenshots

![1](http://lolcdn.mhtx.net/clouddns-gui-updated-20120409-223514.jpg)

#### Requirements

* Python 2.6+
* [Flask](http://flask.pocoo.org/)
* [python-clouddns](https://github.com/rackspace/python-clouddns)

#### Configuration

Place a JSON file in the base directory of the application which contains the username and API key for your Rackspace Cloud account.  It should look something like this:

    {
        "username": "jsmith",
        "apikey":   "very_long_api_key"
    }

#### Bugs & Requests

Pull requests and issues in GitHub are more than welcome.
