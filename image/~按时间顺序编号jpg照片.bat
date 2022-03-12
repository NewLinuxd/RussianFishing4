echo off&setlocal enabledelayedexpansion

cls

set suffix="jpg"

set count=0

for /f "delims=" %%i in ('dir /od /b *.%suffix%') do (

set /a count+=1
if !count! gtr 9 (ren "%%i" "false-!count!.%suffix%") else (ren "%%i" "false-0!count!.%suffix%")

)

::del *.bat

::echo Success! Press any button to exit...

pause>nul