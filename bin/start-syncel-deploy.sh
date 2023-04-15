#!/bin/bash
set -euo pipefail

version="${1:-$version}"
fesHostArr=("fes1" "fes2")
allDeployHosts="cel1 cel2 cel3"
IFS=' '
read -a allDeployHostArr <<< "${allDeployHosts}"

for deployHost in "${allDeployHostArr[@]}";
do
    printf "deploy $version on Host $deployHost\n"
    for fesHost in "${fesHostArr[@]}";
    do
        printf -- '-----------------------------\n'
        printf "remove $deployHost from $fesHost loadbalancing\n"
        printf -- '-----------------------------\n'
        ssh -t $fesHost "sudo /opt/server-tools/bin/tomcat/fes-set-workers.sh ${allDeployHosts/$deployHost/}"
    done
    /opt/server-tools/bin/tomcat/deploy-syncel.sh $deployHost $version
done

for fesHost in "${fesHostArr[@]}";
do
    printf -- "--------------------------------------------\n"
    printf "readd all nodes to $fesHost loadbalancing\n"
    printf -- "--------------------------------------------\n"
    ssh -t $fesHost "sudo /opt/server-tools/bin/tomcat/fes-set-workers.sh ${allDeployHosts}"
done
