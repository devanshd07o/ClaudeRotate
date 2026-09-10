Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
batPath = fso.BuildPath(currentDir, "run_switcher.bat")

shell.Run "cmd.exe /c """ & batPath & """", 0, False
