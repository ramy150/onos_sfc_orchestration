import lxc_driver
import os
import time
import docker


def create_ovs(ovs_name):
    print("Creating the OVS bridge {}".format(ovs_name))
    basic_cmd = 'sudo ovs-vsctl add-br {}'.format(ovs_name)
    os.system(basic_cmd)


def create_sff(container_name, ovs_name, ip_address_1, port_1, ip_address_2, port_2):
    basic_cmd = 'lxc-copy -n lxc-ovs -N {}'.format(container_name)
    os.system(basic_cmd)
    time.sleep(2)
    if lxc_driver.create_container(container_name):
        lxc_driver.modify_configuration_bridge(container_name, '2')
        lxc_driver.container_bridge_ovs(container_name, str(ovs_name), str(port_1))
        lxc_driver.container_bridge_ovs(container_name, str(ovs_name), str(port_2), '2')
        time.sleep(5)
        if not lxc_driver.start_container(container_name):
            return False
        time.sleep(2)
        lxc_driver.container_attach(container_name, ["ip", "addr", "add", "{}/24".format(ip_address_1), "dev", "eth0"])
        lxc_driver.container_attach(container_name, ["ip", "link", "set", "dev", "eth0", "up"])
        lxc_driver.container_attach(container_name, ["ip", "addr", "add", "{}/24".format(ip_address_2), "dev", "eth1"])
        lxc_driver.container_attach(container_name, ["ip", "link", "set", "dev", "eth1", "up"])

        while len(lxc_driver.get_ip_container(container_name)) < 2:
            print("current_ip: {}".format(lxc_driver.get_ip_container(container_name)))
            print("envisaged_ip_1: {}".format(ip_address_1))
            print("envisaged_ip_2: {}".format(ip_address_2))
            time.sleep(1)
        response = 0
        while response != 256:
            response = lxc_driver.container_attach(container_name, ["ping", "-I", "eth0", "-c", "1", "10.0.0.90"])

        response = 0
        while response != 256:
            response = lxc_driver.container_attach(container_name, ["ping", "-I", "eth1", "-c", "1", "10.0.0.90"])

        lxc_driver.container_attach(container_name, ["ip", "link", "add", "name", "br0", "type", "bridge"])
        lxc_driver.container_attach(container_name, ["ip", "link", "set", "dev", "br0", "up"])
        lxc_driver.container_attach(container_name, ["ip", "link", "set", "dev", "eth0", "master", "br0"])
        lxc_driver.container_attach(container_name, ["ip", "link", "set", "dev", "eth1", "master", "br0"])

        return True


def create_link_ovs(ovs_name_1, ovs_name_2, ovs_interface_1, ovs_interface_2, ovs_port):
    print("Attaching the OVS {} to the OVS {}".format(ovs_name_1, ovs_name_2))

    basic_cmd = 'sudo ip link add name {} type veth peer name {}'.format(ovs_interface_1, ovs_interface_2)
    os.system(basic_cmd)

    basic_cmd = "ip link set {} up".format(ovs_interface_1)
    os.system(basic_cmd)

    basic_cmd = "ip link set {} up".format(ovs_interface_2)
    os.system(basic_cmd)

    basic_cmd = "sudo ovs-vsctl add-port {0} {1} -- set Interface {1} ofport_request={2}"\
        .format(ovs_name_1, ovs_interface_1, ovs_port)
    os.system(basic_cmd)

    basic_cmd = "sudo ovs-vsctl add-port {0} {1} -- set Interface {1} ofport_request={2}"\
        .format(ovs_name_2, ovs_interface_2, ovs_port)
    os.system(basic_cmd)


def attach_ovs_to_sdn(ovs_name):
    print("Attaching the OVS bridge to the ONOS controller")
    client = docker.DockerClient()
    container = client.containers.get("onos")
    ip_add = container.attrs['NetworkSettings']['IPAddress']
    basic_cmd = "ovs-vsctl set-controller {} tcp:{}:6653".format(ovs_name, ip_add)
    os.system(basic_cmd)


def create_lxc_container(container_name, ovs_name, ovs_port, ip_address):
    print("Creating the container: {}".format(container_name))
    if lxc_driver.create_container(container_name):
        lxc_driver.modify_configuration_bridge(container_name)
        lxc_driver.container_bridge_ovs(container_name, ovs_name, ovs_port)
        time.sleep(5)
        if not lxc_driver.start_container(container_name):
            return False
        time.sleep(2)
        lxc_driver.container_attach(container_name, ["ip", "addr", "add", "{}/24".format(ip_address), "dev", "eth0"])
        lxc_driver.container_attach(container_name, ["ip", "link", "set", "dev", "eth0", "up"])
        while len(lxc_driver.get_ip_container(container_name)) != 1:
            time.sleep(1)
        response = 0
        while response != 256:
            response = lxc_driver.container_attach(container_name, ["ping", "-c", "1", "10.0.0.90"])
        return True


if __name__ == '__main__':
    create_ovs("ovs-1")
    create_ovs("ovs-2")
    create_ovs("ovs-3")
    create_link_ovs("ovs-1", "ovs-2", "int-ovs12", "int-ovs21", 1)
    create_link_ovs("ovs-2", "ovs-3", "int-ovs23", "int-ovs32", 2)
    attach_ovs_to_sdn("ovs-1")
    attach_ovs_to_sdn("ovs-2")
    attach_ovs_to_sdn("ovs-3")
    create_lxc_container("red", "ovs-1", 3, "10.0.0.100")
    create_sff("blue", "ovs-2", "10.0.0.111", 3, "10.0.0.112", 4)
    create_lxc_container("green", "ovs-3", 3, "10.0.0.113")


