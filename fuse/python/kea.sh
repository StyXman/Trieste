#! /bin/bash

ps auxw | awk '/python2.2/ { print $2 }' | xargs kill -9;
