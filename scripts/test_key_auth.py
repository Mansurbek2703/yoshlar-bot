import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.100', username='boss', password='Sshtelnet27032004!')

cmd = """
sshpass -p 'Sshtelnet27032004!' ssh -o StrictHostKeyChecking=no boss@192.168.1.113 'ssh -o StrictHostKeyChecking=no -o BatchMode=yes boss@192.168.1.3 id' 2>&1
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', 'replace'))
ssh.close()
