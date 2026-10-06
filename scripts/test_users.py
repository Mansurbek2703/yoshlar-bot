import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.100', username='boss', password='Sshtelnet27032004!')

cmd = """
for u in boss root mansurbek akhu admin ubuntu student user developer; do
    echo -n "$u: "
    sshpass -p 'Sshtelnet27032004!' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 $u@192.168.1.3 "id" 2>&1
done
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', 'replace'))
ssh.close()
