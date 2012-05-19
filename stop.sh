#! /bin/bash
###########################################################################
#    Copyright (C) 2004 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

if [ -n "$debug" ]; then
  set -vx;
fi;

[ $# -eq 1 ] || exit 1;

# read config
source config.sh;
export PYTHONPATH=.

# stop storages
k=1;
while [ $k -le $1 ]; do
  echo "Storage: Stoping sm `printf %02d $k`";
  set -x;
  ./utils/terminate.py --connect-to "vice://localhost:$((20000+$k*100))/";
  set +x;
  k=$(($k + 1));
done;
# stop metadata
for server in $servers; do
  echo "Ring: Stoping mm @ $server";
  set -x;
  ./utils/terminate.py --connect-to "umbie://$server:5647/";
  set +x;
done;
