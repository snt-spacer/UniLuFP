# UniLuFP

## Pixhawk setup

TODO: Currently using default instead of space
Install QGC (default) from [here](https://docs.qgroundcontrol.com/master/en/qgc-user-guide/releases/daily_builds.html).

> FIXME: I could not change pixhawk network setting by the following steps. ([Reference](https://docs.px4.io/main/en/advanced_config/ethernet_setup.html))
>
> ```MAVLink Console (QGC > Analyze Tools)
> echo DEVICE=enP8p1s0 > /fs/microsd/net.cfg
> echo BOOTPROTO=fallback > /fs/microsd/net.cfg
> echo IPADDR=10.41.10.2 > /fs/microsd/net.cfg
> echo NETMASK=255.255.255.0 > /fs/microsd/net.cfg
> echo ROUTER=10.41.10.254 > /fs/microsd/net.cfg
> echo DNS=10.41.10.254 > /fs/microsd/net.cfg
> ```

## Jetson setup

Currently, using personal Android as a wi-fi rooter. TODO: Need to update ssh to use in ZeoG.

```host PC
ssh spacer@192.168.236.210
```

Change Ethernet name from enP8p1s0 to eth0 (not permanent. Edit rules later.)

```bash
sudo ip link set enP8p1s0 down
sudo ip link set enP8p1s0 name eth0
sudo ip link set eth0 up
```
