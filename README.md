MoDataSubmission
================

A service that accepts HTTP POST requests of JSON, stores them in S3, and 
returns a link to its location.  Requests are authenticated using 
[Hawk](https://github.com/hueniverse/hawk).


Requirements
------------

* Python27, including Pip
* Server with write access to Amazon S3

 
Installation
------------

There is an installation script in [resources/scripts/install.sh](https://github.com/klahnakoski/MoDataSubmission/blob/dev/resources/scripts/install.sh) 
which can be used as a guide for installing the server.

Setup
-----

The server requires a configuration file.  An example configuration file is at 
[tests/resources/config/server.json](https://github.com/klahnakoski/MoDataSubmission/blob/dev/tests/resources/config/server.json)

```javascript
	{
		"flask": {
			"host": "0.0.0.0",
			"port": 5000,
			"debug": true,
			"threaded": true,
			"processes": 1
		},
		"aws": {
	        "aws_access_key_id": "sometring",
	        "aws_secret_access_key" : "somebase64",
	        "region": "us-west-2"
	    },
		"users": [
			{
				"hawk": {
					"id": "kyle@example.com",
					"key": "secret",
					"algorithm": "sha256"
				},
				"resources": [
					"testing"
				]
			}
		],
		"debug": {
			"trace": true,
			"log": [
				{
					"log_type": "console"
				}
			]
		}
	}
```

###Setup Properties

* *`flask`* - properties delivered to the `Flask.run()` method.  Be sure you have `debug=false` in production!
* *`aws`* - your AWS permissions.  These should NOT be in this configuration file, but rather in a separate key file.  See the `server.json`file for an example  
* *`users`* - An array of users and permissions.  The hawk credentials are used to identify the POST requests.  And `resources` is a list of bucket names that user is allowed to POST to.
* *`debug`* - [Logging configuration](https://github.com/klahnakoski/pyLibrary/tree/dev/pyLibrary/debugs#configuration), which lacks good documentation.

Running
-------

The [run script](https://github.com/klahnakoski/MoDataSubmission/blob/dev/resources/scripts/run.sh) details the steps to run the server.   Do not use the `sudo -i` step if you are not listening on port 80.

Testing
-------

There is a simple client in the [test code](https://github.com/klahnakoski/MoDataSubmission/blob/dev/tests/test_production.py#L27) to save some JSON in S3.   The only important line is the one that sends the data; here is that same line, expanded with parameters matching the server configuration above:

```python
	link, id = Client(
		url = "http://example.com:80/testing",
		hawk_credentials = {
			"id": "kyle@example.com",
			"key": "secret",
			"algorithm": "sha256"
		}
	).send(data)
```
