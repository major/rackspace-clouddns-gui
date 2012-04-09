# Rackspace Cloud DNS GUI
## A web front-end to Rackspace's Cloud DNS service

**Disclaimers**:
This application is not affiliated with or endorsed by Rackspace.  It's still very, very rough.  It may manage your domains perfectly or it may cause your phone to catch fire.

#### Screenshots

![1](http://lolcdn.mhtx.net/clouddns-gui-1-20120409-020912.jpg)
![2](http://lolcdn.mhtx.net/clouddns-gui-2-20120409-020946.jpg)
![3](http://lolcdn.mhtx.net/clouddns-gui-3-20120409-021023.jpg)

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
