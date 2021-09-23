# Instructions for creating the SD card for the FCD
The operating system  for the Raspberry Pi is Raspberry Pi OS Lite downloadable using the Raspberry Pi Imager.
## Configure the O/S
* First flash the O/S onto the SD card using a PC
* Put the SD card into the Pi and boot up.
* Log in as pi using the default password of ‘raspberry’ and run the configuration utility as root:
	`sudo raspi-config`
	* Select Change User Password and set it to '`He!1c0pter`'
	* Select Network Options then Hostname and set it to `THM-FCD`
	* Select Interfacting Options then:
		* Enable SPI for the application
		* Enable SSH to allow remote access
		* Enable I2C for the RTC
	* Select WiFi and configure for a local network with internet access to download additional software
	* Select Locales and add:
		* `de_DE.UTF8`
		* `es_ES.UTF8`
		* `fr_FR.UTF8`
		* `it_IT.UTF8`
	* Select Finish and reboot
	
## Install software to support WiFi Direct
* `sudo apt update`
* `sudo apt upgrade`
* `sudo apt install i2c-tools` (for RTC)
* `sudo apt install hostapd` (for WifiDirect)
* `sudo apt install dnsmasq` (for WifiDirect)
* `sudo apt autoremove` (to clean up)

## Install software to support the application
* `sudo apt install python3-pygame`
* `sudo apt install python3-gpiozero`
* `sudo apt install fontconfig`
* `sudo apt install ttf-mscorefonts-installer`
* Download DancingScript font 
	`wget https://www.wfonts.com/font/dancing-script`
* copy to /usr/share/fonts/truetype

## Configure shutdown
* `sudo vi /boot/config.txt` and add this line at the end:
	`dtoverlay=gpio-shutdown,gpio_pin=17`
	
## Configure the RTC
	[http://learn.adafruit.com/adding-a-real-time-clock-to-raspberry-pi/set-rtc-time]
* `sudo vi /boot/config.txt` and add this line at the end:
	`dtoverlay=i2c-rtc,ds3231`
* Reboot
* Check that device 0x68 is present using:
	`sudo i2cdetect -y 1`
* Disable the fake hwclock as follows:
	* `sudo apt-get -y remove fake-hwclock`
	* `sudo update-rc.d -f fake-hwclock remove`
	* `sudo systemctl disable fake-hwclock`
	* `sudo vi /lib/udev/hwclock-set`
	* Comment out these lines:
		`# if [ -e /run/systemd/system ] ; then`
		`#  exit 0`
		`# fi`
		and these:
		`# /sbin/hwclock --rtc=$dev --systz --badyear`
		`# /sbin/hwclock --rtc=$dev –systz`
	* Check using
		* `sudo hwclock -r`
		* `date`
		
## Configure WifiDirect 
	[https://www.raspberryconnect.com/projects/65-raspberrypi-hotspot-accesspoints/158-raspberry-pi-auto-wifi-hotspot-switch-direct-connection]
* Check wifi device
	* `iw dev`
* Setup services
	* `sudo systemctl unmask hostapd`
	* `sudo systemctl disable hostapd`
	* `sudo systemctl disable dnsmasq`
	
### Configure hostapd
* Download the hostapd config
	`wget https://www.raspberryconnect.com/images/Autohotspot/autohotspot-95-4/hostapd.txt` 
* `sudo vi /etc/hostapd/hostapd.conf`
	Copy content from hostapd.txt and set `ssid=THM-FCD-HS, channel=8` and `wpa_passphrase=He!1c0pter`
* `sudo vi /etc/default/hostapd`
	* Change:
		`#DAEMON_CONF=””`
	to
		`DAEMON_CONF=”/etc/hostapd/hostapd.conf”`
	* Check `DAEMON_OPTS` is commented out
	
### Configure dnsmasq
* Download the dnsmasq config
	`wget https://www.raspberryconnect.com/images/Autohotspot/autohotspot-95-4/dnsmasq.txt`
	* `sudo vi /etc/dnsmasq.conf`
		* Copy content from dnsmasq.txt and add to the end of the file
		* Check /etc/network/interfaces has only the standard 5 lines
		
### Configure DHCPCD
* `sudo vi /etc/dhcpcd.conf`
	Add this to the end of the file:
	`nohook wpa_supplicant`
	
### Configure autohotspot
* Download the autohotspot script
	`wget https://www.raspberryconnect.com/images/Autohotspot/autohotspot-95-4/autohotspot.txt`
	* `sudo vi /etc/systemd/system/autohotspot.service`
		Copy content from autohotspot.txt, change wifidev to wifi device if required
	* `sudo systemctl enable autohotspot.service`
	* `sudo vi /usr/bin/autohotspot`
	* `sudo chmod +x /usr/bin/autohotsppot`
	
### Test autohotspot
* `sudo vi /etc/wpa_supplicant/wpa_supplicant.conf`
	* Add ‘off’ to SSID making it invalid
	* Reboot
	* Search for networks to find THM-FCD-HS or use ssh pi@10.0.0.5
	* Reset wpa_supplicant ssid
	
## Install the application
* `cd /home/pi/.local/bin`
* Rename previous FlightControlDemonstrator to FlightControlDemonstrator.timestamp
* Download the application
	`git clone http://github.com/roddersuk/FlightControlDemonstrator`
* `sudo vi /etc/rc.local` and add the following line just before exit 0
	`sudo /home/pi/.local/bin/FlightControlDemonstrator/src/scripts/startup&`
	
## Set up CRON job to do shutdown
* TBD

## Make a backup copy of the SD card
* TBD