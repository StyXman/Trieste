#! /bin/bash
###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

if [ -n "$debug" ]; then
  set -vx;
fi;

if [ "$1" == "-q" ]; then
  quiet="1";
  shift;
fi;

if ! [ $# -eq 1 ]; then
  echo "usage: $0 [-q] <number_of_vices>";
  exit 1;
fi;

# read config
source config.sh;
export PYTHONPATH=.

launchRing () {
  i=0
  for server in $servers; do
    [ -n "$quiet" ] || echo "Ring: Launching mm @ $server";
    (
	# ssh $server "cd $runDir; ./mm.py --broadcast-to $net -l m-${server}.log > m_${server}.log 2>&1" &
        set -x;
	./mm.py --broadcast-to $net -l m-${server}.log > m_${server}.log 2>&1 &
        set +x;
    )
    r=`./utils/random.py 3`;
    [ -n "$quiet" ] || echo "Ring: Delay of $r seconds";
    i=$(($i + 1));
    sleep $r;
  done;
}

launchStorage () {
  # hack ugly as old man's butt
  i=0
  for server in $servers; do
    i=$(($i + 1));
  done;

  k=1;
  while [ $k -le $1 ]; do
    number=`printf %02d $k`;
    [ -n "$quiet" ] || echo "Storage: Launching sm $number";
    s=`./utils/random.py 3`;
    (
        set -x;
	./sm.py --port $((20000+$k*100)) --data-dir data/$k --space $space --broadcast-to $net -l s-${number}.log > s_${number}.log 2>&1 &
        set +x;
    )
    [ -n "$quiet" ] || echo "Storage: Delay of $s seconds";
    sleep $s;
    k=$(($k + 1));
  done;
}

finish () {
  # killall /usr/bin/python2.2;
  echo "terminating $1";
  ./stop.sh $1 > /dev/null;
  # netstat -tapou;
}

# delete old logs
rm -f {s0,m-}*.log;

# and now...!
launchRing &
# interesting enough, when calling (ba)sh functions as background processes,
# bash spawns other bash'es. that's good, because we can wait for them
# and kill them given proper user input (i.e., CTRL+C)
ringPid=$!;
launchStorage $1 &
storagePid=$!;

# echo "CTRL+C will kill $ringPid $storagePid";
# trap "killall -9 /usr/bin/python; kill -9 $ringPid $storagePid; exit 1" INT;
# trap "finish $1; exit" USR1;
trap "finish $1; exit" INT;
# wait so watch doesn't gets its display garbled.
wait $ringPid $storagePid;

if [ -z "$quiet" ]; then
  echo "progress...";
  while true; do
    sleep 10;
  done;
  # watch -n 1 ls -lS *.log;
else
  while true; do
    sleep 10;
  done;
fi;

finish $1;
