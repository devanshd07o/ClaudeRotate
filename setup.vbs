Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
scriptPath = fso.BuildPath(currentDir, "internal\installer_gui.py")
shell.Run "pythonw """ & scriptPath & """", 0, False
