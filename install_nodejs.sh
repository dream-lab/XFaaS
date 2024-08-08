NODEJS_DIR=$1

export N_PREFIX=$NODEJS_DIR
curl -fsSL https://raw.githubusercontent.com/tj/n/master/bin/n | bash -s 14.20.0
