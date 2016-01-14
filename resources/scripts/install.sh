
#
# WARNING:  Do not use this script directly.  Think of it as an installation guide.
#


#INSTALL GIT
sudo yum install -y git-core


#INSTALL PYTHON27
sudo yum -y install python27

rm -fr /home/ec2-user/temp
mkdir  /home/ec2-user/temp
cd /home/ec2-user/temp
wget https://bootstrap.pypa.io/get-pip.py
sudo python27 get-pip.py
sudo ln -s /usr/local/bin/pip /usr/bin/pip


cd ~
git clone https://github.com/klahnakoski/MoDataSubmission.git
cd /home/ec2-user/MoDataSubmission
sudo pip install -r requirements.txt
