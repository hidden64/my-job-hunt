"""Notification système locale (macOS, Linux, Windows). Le canal « push » est envoyé par Claude
avec l'outil PushNotification ; ce module ne gère que le canal « system »."""
import platform
import shutil
import subprocess


def _esc_applescript(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _esc_ps(s):
    return s.replace("'", "''")


def send_system(title, message, runner=subprocess.run):
    system = platform.system()
    try:
        if system == "Darwin":
            script = 'display notification "%s" with title "%s" sound name "Glass"' % (
                _esc_applescript(message), _esc_applescript(title))
            runner(["osascript", "-e", script], check=True, capture_output=True, timeout=15)
            return {"ok": True, "via": "osascript"}
        if system == "Linux":
            if shutil.which("notify-send"):
                runner(["notify-send", "-a", "Job Hunter", title, message], check=True, capture_output=True, timeout=15)
                return {"ok": True, "via": "notify-send"}
            return {"ok": False, "via": None, "message": "notify-send introuvable (paquet libnotify-bin)"}
        if system == "Windows" or shutil.which("powershell.exe") or shutil.which("powershell"):
            ps = ("Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; "
                  "$n = New-Object System.Windows.Forms.NotifyIcon; "
                  "$n.Icon = [System.Drawing.SystemIcons]::Information; $n.Visible = $true; "
                  "$n.ShowBalloonTip(10000, '%s', '%s', [System.Windows.Forms.ToolTipIcon]::Info); "
                  "Start-Sleep -Seconds 6; $n.Dispose()") % (_esc_ps(title), _esc_ps(message))
            exe = shutil.which("powershell.exe") or shutil.which("powershell") or "powershell"
            runner([exe, "-NoProfile", "-Command", ps], check=True, capture_output=True, timeout=30)
            return {"ok": True, "via": "powershell"}
    except Exception as e:  # la notification ne doit jamais faire échouer un passage
        return {"ok": False, "via": None, "message": "notification refusée : %s" % e}
    return {"ok": False, "via": None, "message": "système %s non pris en charge" % system}
