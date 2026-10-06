import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.100', username='boss', password='Sshtelnet27032004!')

cmd = sys.argv[1] if len(sys.argv) > 1 else 'id'
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8', 'replace')
err = stderr.read().decode('utf-8', 'replace')

if out:
    print(out)
if err:
    print('STDERR:', err)

ssh.close()
