#!/bin/sh
apache-jmeter-5.4.3/bin/jmeter -n -t /home/azureuser/bigdata-jmx-files//azure-graph-small-static-1-600-session-0.jmx  -l /home/azureuser/bigdata-jmx-files//azure-graph-small-static-1-600-session-0.jmx.jtl
sleep 20
