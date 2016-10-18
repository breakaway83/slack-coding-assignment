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


===Execution Result===

Execution result is something lokks like this:

pytest -v --pdb --test_token='my_test_token' test_files.py
=========================================================================================== test session starts ============================================================================================

platform darwin -- Python 2.7.12 -- pytest-2.3.3 -- /usr/local/opt/python/bin/python2.7

collected 5 items

test_files.py:25: TestFiles.test_files_upload_list[upload PNG file] PASSED

test_files.py:79: TestFiles.test_files_content_upload_list[upload content] PASSED

test_files.py:113: TestFiles.test_files_delete[delete PNG file] PASSED

test_files.py:113: TestFiles.test_files_delete[delete file uploaded through Content] PASSED

test_files.py:113: TestFiles.test_files_delete[delete nonexistent file] PASSED

======================================================================================== 5 passed in 33.26 seconds =========================================================================================
