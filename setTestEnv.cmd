@echo off

REM main starts here
SET /A ARGS_COUNT=0
FOR %%A in (%*) DO SET /A ARGS_COUNT+=1

IF %ARGS_COUNT% GTR 0 goto :usage

SET IS_DOWNLOAD=""
SET unzip="C:\Program Files\7-Zip\7z.exe"

call:set_environment_variables
call:refresh_test_libraries

REM clearing out python path, but saving existing path in a different env variable
SET OLD_PYTHONPATH=%PYTHONPATH%
echo OLD_PYTHONPATH==%OLD_PYTHONPATH%

echo "%PATH%" |find "Python" > nul
IF %ERRORLEVEL% NEQ 1 (
    doskey python=python
) ELSE IF EXIST  "C:\Python27\python.exe" (
    doskey python=C:\Python27\python.exe
) ELSE IF EXIST "C:\Python26\python.exe" (
    doskey python=C:\Python26\python.exe
) ELSE (
    echo "Python is not available in the PATH environment variable. Also, tried C:\Python27 & C:\Python26 but not found."
    echo "Install python & set it in the PATH"
    goto:eof
)

REM setting the python path for test libs
set PYTHONPATH=%TEST_LIB%;%TEST_LIB%\pytest\plugin;%TEST_LIB%\httplib2-0.9.2\python2

doskey pytest=python %TEST_DIR%\bin\pytest\pytest.py $*

echo PYTHONPATH when running 'pytest': %PYTHONPATH%

REM set test artifacts directory and create if not existing
IF "%TEST_ARTIFACTS%" EQU "" (
    SET TEST_ARTIFACTS=%TEST_DIR%\test_artifacts
    )

if NOT EXIST "%TEST_ARTIFACTS%" (
   mkdir %TEST_ARTIFACTS%
   )
goto:eof

:usage

  echo  "USAGE 1: source setTestEnv"
  echo  "Source it from the absolute location of setTestEnv"
  goto:eof

REM make sure bash environment
:set_environment_variables
  SET TEST_DIR=%CD%
  SET TEST_LIB=%TEST_DIR%\lib
  echo "TEST_DIR=%TEST_DIR%"
  goto:eof

REM unzip contrib files to test/bin directory
:refresh_test_libraries
echo [INFO] unpack pytest to .\bin ......

%unzip% x %TEST_DIR%\contrib\pytest-2.3.3.zip *.* -o%TEST_DIR%\bin -r -y > nul
rmdir /s /q %TEST_DIR%\bin\pytest
ren %TEST_DIR%\bin\pytest-2.3.3 pytest
xcopy /s /q /y %TEST_DIR%\bin\pytest\* %TEST_LIB%

echo [INFO] unpack py to .\lib ......
%unzip% x %TEST_DIR%\contrib\py-1.4.7.zip -o%TEST_DIR%\contrib -r -y > nul
echo removing %TEST_LIB%\py
rmdir /s /q %TEST_LIB%\py
echo creating %TEST_LIB%\py
mkdir %TEST_LIB%\py
echo [INFO] copying files to %TEST_LIB%\py
xcopy /s /q /y %TEST_DIR%\contrib\py-1.4.7\py %TEST_LIB%\py\

echo [INFO] unpack execnet to .\lib .....
%unzip% x %TEST_DIR%\contrib\execnet-1.1.zip -o%TEST_DIR%\contrib -r -y > nul
rmdir /s /q %TEST_LIB%\execnet
mkdir %TEST_LIB%\execnet
xcopy /s /q /y %TEST_DIR%\contrib\execnet-1.1\execnet %TEST_LIB%\execnet

echo [INFO] unpack pytest-xdist to .\lib .....
%unzip% x %TEST_DIR%\contrib\pytest-xdist-1.8.zip -o%TEST_DIR%\contrib -r -y > nul
rmdir /s /q %TEST_LIB%\xdist
mkdir %TEST_LIB%\xdist
xcopy /s /q %TEST_DIR%\contrib\pytest-xdist-1.8\xdist %TEST_LIB%\xdist

echo [INFO] unpack httplib2 .\lib .....
%unzip% x %TEST_DIR%\contrib\httplib2-0.9.2.zip -o%TEST_DIR%\contrib -r -y > nul
rmdir /s /q %TEST_LIB%\httplib2-0.9.2
mkdir %TEST_LIB%\httplib2-0.9.2
xcopy /s /q %TEST_DIR%\contrib\httplib2-0.9.2 %TEST_LIB%\httplib2-0.9.2
goto:eof

:eof
