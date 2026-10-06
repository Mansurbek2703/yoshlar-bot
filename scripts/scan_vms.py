import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.100', username='boss', password='Sshtelnet27032004!')

cmd = """
for ip in 192.168.1.88 192.168.1.113 192.168.1.112 192.168.1.64 192.168.1.7 192.168.1.3; do
    echo -n "$ip: "
    sshpass -p 'Sshtelnet27032004!' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 boss@$ip "hostname; id" 2>&1
done
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', 'replace'))
ssh.close()
