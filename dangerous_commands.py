dangerous_commands = {
    "shut down": {
        "description": "shut down your PC",
        "command": "shutdown /s /t 0"
    },
    "restart": {
        "description": "restart your PC",
        "command": "shutdown /r /t 0"
    },
    "sleep": {
        "description": "put your PC to sleep",
        "command": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"
    }
}