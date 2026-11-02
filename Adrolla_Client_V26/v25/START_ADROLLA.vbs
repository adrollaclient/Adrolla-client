Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = folder
' Use the diagnostic batch launcher instead of pyw.exe/pythonw.exe.
' This makes missing Python installations and startup errors visible.
sh.Run Chr(34) & folder & "\START_ADROLLA.bat" & Chr(34), 1, False
