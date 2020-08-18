#!/usr/bin/env bash


function create_ns() {
echo "Creating the namespace $1"
ip netns add $1
}

function create_ovs_bridge() {
echo "Creating the OVS bridge $1"
ovs-vsctl add-br $1

}


function attach_ns_to_ovs() {
echo "Attaching the namespace $1 to the OVS $2"
ip link add $3 type veth peer name $4
ip link set $3 netns $1
ovs-vsctl add-port $2 $4 -- set Interface $4 ofport_request=$5
ip netns exec $1 ip addr add $6/24 dev $3
ip netns exec $1 ip link set dev $3 up
ip link set $4 up
}


function attach_ovs_to_ovs() {
echo "Attaching the OVS $1 to the OVS $2"
ip link add name $3 type veth peer name $4
ip link set $3 up
ip link set $4 up
ovs-vsctl add-port $1 $3 -- set Interface $3 ofport_request=$5
ovs-vsctl add-port $2 $4 -- set Interface $4 ofport_request=$5
}

function attach_ovs_to_sdn() {
echo "Attaching the OVS bridge to the ONOS controller"
ovs-vsctl set-controller $1 tcp:$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker ps -q  --filter ancestor=onosproject/onos)):6653
}


create_ns red
create_ns blue
create_ns green
create_ns black
create_ns yellow


create_ovs_bridge br-1
create_ovs_bridge br-2
create_ovs_bridge br-3
create_ovs_bridge br-4
create_ovs_bridge br-5
create_ovs_bridge br-6


attach_ovs_to_ovs br-1 br-2 br-ovs12 br-ovs21 1
attach_ovs_to_ovs br-1 br-3 br-ovs13 br-ovs31 2
attach_ovs_to_ovs br-1 br-4 br-ovs14 br-ovs41 3
attach_ovs_to_ovs br-2 br-6 br-ovs26 br-ovs62 2
attach_ovs_to_ovs br-3 br-5 br-ovs35 br-ovs53 1
attach_ovs_to_ovs br-4 br-6 br-ovs46 br-ovs64 1
attach_ovs_to_ovs br-5 br-6 br-ovs56 br-ovs65 3





attach_ns_to_ovs red br-1 veth-red veth-red-br 4 10.0.0.2
attach_ns_to_ovs blue br-3 veth-blue veth-blue-br 3 10.0.0.3
attach_ns_to_ovs green br-4 veth-green veth-green-br 2 10.0.0.4
attach_ns_to_ovs black br-6 veth-black veth-black-br 4 10.0.0.5
attach_ns_to_ovs yellow br-6 veth-yellow veth-yellow-br 5 10.0.0.6


attach_ovs_to_sdn br-1
attach_ovs_to_sdn br-2
attach_ovs_to_sdn br-3
attach_ovs_to_sdn br-4
attach_ovs_to_sdn br-5
attach_ovs_to_sdn br-6