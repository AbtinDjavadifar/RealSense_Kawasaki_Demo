import subprocess


process  = subprocess.Popen('plink -telnet 192.168.0.2',bufsize = -1, shell=True,stdout = subprocess.PIPE,stdin = subprocess.PIPE,stderr=subprocess.PIPE)

log = ''
out = process.stdout.read(1).decode('utf-8')

while out != '' and process.poll() == None:
	log += out
	if(': ' in log):
		break
	process.stdout.flush()
	out =  process.stdout.read(1).decode('utf-8')
process.stdout.flush()

if ("login" in log):
	process.stdin.write('as\n\n'.encode()) #should i include login: ?
	print('robot is connected')

command = "EXECUTE WRINKLER\n"

process.stdin.write(command.encode())
process.stdin.flush()

