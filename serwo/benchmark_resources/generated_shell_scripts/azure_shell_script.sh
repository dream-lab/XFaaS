#!/bin/sh
apache-jmeter-5.4.3/bin/jmeter -n -t /home/azureuser/bigdata-jmx-files//azure-graph-small-static-1-120-session-0.jmx  -l /home/azureuser/bigdata-jmx-files//azure-graph-small-static-1-120-session-0.jmx.jtl
sleep 20
apache-jmeter-5.4.3/bin/jmeter -n -t /home/azureuser/bigdata-jmx-files//azure-graph-small-static-2-120-session-1.jmx  -l /home/azureuser/bigdata-jmx-files//azure-graph-small-static-2-120-session-1.jmx.jtl
sleep 20
