@FOR %%I IN ("%CD%") DO @SET PROJECTFOLDER=%%~nxI
@SET PROJECTNAME=%PROJECTFOLDER%
@SET DEST_FOLDER=Python

@SET ARCHIVE=%PROJECTNAME%.zip

@if exist %MyDocFolder% goto Backup
@rem goto ErrMyDocFolder
@SET MyDocFolder=e:\!MyDoc

:Backup
@SET ARCHIVEFOLDER=%MyDocFolder%\FLOPPI\%DEST_FOLDER%\%PROJECTNAME%
@if not exist %ARCHIVEFOLDER% mkdir %ARCHIVEFOLDER%
@SET SERVERFOLDER=P:\!MyDoc\floppi\%DEST_FOLDER%\%PROJECTNAME%
@if not exist %SERVERFOLDER% mkdir %SERVERFOLDER%
@SET ZIP="%ProgramFiles%/7-Zip/7z.exe"
@if not exist %ZIP% goto ErrZip
@cd ..
%ZIP%  -xr@%PROJECTFOLDER%\excludezip.txt a %ARCHIVE% .\%PROJECTFOLDER%
@move /Y %ARCHIVE% %ARCHIVEFOLDER%
@autoname /pattern:YYMMDDhhmmss %ARCHIVEFOLDER%\%ARCHIVE%
@xcopy /A /M /Y %ARCHIVEFOLDER%\*.* "%SERVERFOLDER%\"
@cd %PROJECTFOLDER%
@goto exit

:ErrMyDocFolder
@echo MyDocFolder env variable not found!..
@pause
@goto exit

:ErrZip
@echo %ZIP% not found!..
@pause
@goto exit

:exit
