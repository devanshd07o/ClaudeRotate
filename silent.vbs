Dim sFolder
sFolder = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
CreateObject("WScript.Shell").Run """" & sFolder & "\Claude.bat""", 0, False