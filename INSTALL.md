# Installation instructions

This documents is step by step instruction how to setup development and poduction environment. As long as project in development stage production part subject to change. 

## Requirements

You need to have installed:

- python 2.7.x 
- virtualenv http://www.virtualenv.org/en/latest/
- make 
- C-code compiler
- libevent

If you are OSX user then prefereable way is use [brew](http://mxcl.github.io/homebrew/) project. Follow brew installation instructions and after:

	$ brew install python sqlite libevent 
	...
	$ which easy_install-2.7 
	/usr/local/share/python/easy_install-2.7
	$

	$ sudo easy_install-2.7 -U pip;
	$ sudo easy_install-2.7 -U virtualenv;

	$ echo export PIP_DOWNLOAD_CACHE=$HOME/.pip_download_cache >>~/.profile;
	$ mkdir ~/.pip_download_cache;


Now your system should be ready.

## Installation

Install your local environment is very easy. Project require some system programms installed, but do not install its own dependencies into system. All packages installs into folder `venv`.

Clone code from github into new folder:

	$ git clone https://github.com/xen/bakery.git bakery

Then run setup:

	$ cd bakery
	$ sudo make setup

Wait some time. 

**Optional step**: Make your own `local.cfg` based on `local.example.cfg`. Or use this as example:

	$ cat local.cfg
	GITHUB_CONSUMER_KEY = '4a1a8295dacab483f1b5'
	GITHUB_CONSUMER_SECRET = 'ec494ff274b5a5c7b0cb7563870e4a32874d93a6'
	SQLALCHEMY_ECHO = True

Github application info is for demo use only. You can [make your own](https://github.com/settings/applications/new). Default values for URL `http://localhost:5000/`, callback URL `http://localhost:5000/auth/callback`. 

Init database tables:

	$ make init

And run project:

	$ make run

Open [http://localhost:5000/](http://localhost:5000/) in your browser

## Development notes

### Login failing?

Sometimes it is possible that some cookies stay in a browser from old runs, or even different applications, since localhost is commonly used in web development. If you try to login but fail, then visit [http://localhost:5000/auth/logout](http://localhost:5000/auth/logout) and try to log in again.

### Production Mode 

Production mode has additional requirements:

* PostgreSQL, a high performance database for production systems

By default project will start in development mode, but it is possible to run in production making changes in `local.cfg`. More instructions will follow.
