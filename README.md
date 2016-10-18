===How To Run===

Before running test, do the following on "slack-coding-assignment" git dir:

Linux & OSX: 
source ./setTestEnv

Run tests:
cd tests/slack_api
pytest -v --test_token='your_slack_test_token' test_files.py

===Notes===

This is potentially runnable on Windows, the setup difference is:

Windows: setTestEnv.cmd

Also, if you want to use urllib2.urlopen to download build through the URL, Microsoft Visual C++ 2015 Redistributable (X64) needs to be installed. This can be installed as part of curl installation (curl-7.46.0-win64.exe).
