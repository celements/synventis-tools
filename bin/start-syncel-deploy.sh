#!/bin/bash
set -eo pipefail

version="${1:-$version}"
[ -z "$version" ] && echo "version missing" && exit 1
fesHostArr=("fes1" "fes2")
allDeployHosts="cel1 cel2 cel3"

for deployHost in $allDeployHosts;
do
    echo "deploy $version on Host $deployHost"
    for fesHost in "${fesHostArr[@]}";
    do
        echo '-----------------------------'
        echo "remove $deployHost from $fesHost loadbalancing"
        echo '-----------------------------'
        ssh -t $fesHost "sudo /opt/server-tools/bin/tomcat/fes-set-workers.sh ${allDeployHosts/$deployHost/}"
    done
    /opt/server-tools/bin/tomcat/deploy-syncel.sh "$deployHost" "$version"
done

for fesHost in "${fesHostArr[@]}";
do
    echo "--------------------------------------------"
    echo "readd all nodes to $fesHost loadbalancing"
    echo "--------------------------------------------"
    ssh -t $fesHost "sudo /opt/server-tools/bin/tomcat/fes-set-workers.sh ${allDeployHosts}"
done
