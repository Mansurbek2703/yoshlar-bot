import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.100', username='boss', password='Sshtelnet27032004!')

cmd = """
for i in $(seq 2 254); do
    ip="192.168.1.$i"
    # quick check if port 22 is open
    nc -z -w 1 $ip 22 2>/dev/null || continue
    h=$(sshpass -p 'Sshtelnet27032004!' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=1 boss@$ip "hostname" 2>/dev/null)
    if [ -n "$h" ]; then
        echo "FOUND: $ip -> $h"
    else
        echo "PORT 22 OPEN BUT AUTH FAILED: $ip"
    fi
done
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', 'replace'))
ssh.close()
