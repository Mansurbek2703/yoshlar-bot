import paramiko
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.3', username='boss', password='Sshtelnet27032004!')

print("1. Uploading setup_server.sh to /tmp/setup_server.sh ...")
sftp = ssh.open_sftp()
with open('scripts/setup_server.sh', 'rb') as f_local:
    data = f_local.read().replace(b'\r\n', b'\n')
    with sftp.file('/tmp/setup_server.sh', 'wb') as f_remote:
        f_remote.write(data)
sftp.close()
print("   Uploaded successfully.")

print("2. Executing setup_server.sh with sudo privileges...")
cmd = "echo Sshtelnet27032004! | sudo -S bash /tmp/setup_server.sh"
stdin, stdout, stderr = ssh.exec_command(cmd)

for line in iter(stdout.readline, ""):
    print(line, end="")

err = stderr.read().decode('utf-8', 'replace')
if err:
    filtered = [l for l in err.splitlines() if "[sudo] password for boss:" not in l and "NEEDRESTART" not in l]
    if filtered:
        print("\nSTDERR:", "\n".join(filtered))

print("\n3. Testing service health endpoint on port 8000...")
time.sleep(2)
stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1:8000/health || curl -s http://127.0.0.1:8000/")
print("Health response:", stdout.read().decode('utf-8', 'replace'))

ssh.close()
print("\n=== DEPLOYMENT FINISHED ===")
