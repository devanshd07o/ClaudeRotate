Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
scriptPath = fso.BuildPath(currentDir, "internal\installer_gui.py")

localAppData = shell.ExpandEnvironmentStrings("%LocalAppData%")

pyCmd = "pythonw"

If fso.FileExists(localAppData & "\Programs\Python\Python311\pythonw.exe") Then
    pyCmd = """" & localAppData & "\Programs\Python\Python311\pythonw.exe"""
ElseIf fso.FileExists(localAppData & "\Programs\Python\Python314\pythonw.exe") Then
    pyCmd = """" & localAppData & "\Programs\Python\Python314\pythonw.exe"""
ElseIf fso.FileExists(localAppData & "\Programs\Python\Python312\pythonw.exe") Then
    pyCmd = """" & localAppData & "\Programs\Python\Python312\pythonw.exe"""
ElseIf fso.FileExists(localAppData & "\Programs\Python\Python310\pythonw.exe") Then
    pyCmd = """" & localAppData & "\Programs\Python\Python310\pythonw.exe"""
ElseIf fso.FileExists("C:\Python312\pythonw.exe") Then
    pyCmd = """C:\Python312\pythonw.exe"""
End If

shell.Run pyCmd & " """ & scriptPath & """", 0, False
