# Instructions for creating the SD card for the FCD
The operating system  for the Raspberry Pi is Raspberry Pi OS Lite downloadable using the Raspberry Pi Imager.

## Configure the O/S
* First flash the O/S onto the SD card using the Rapberry Pi Imageer on a PC
	* Select Raspberry Pi OS Lite
	* Select the SD card to write to
	* Type Ctrl-Shift-x to get Advanced Options
		* Set Hostname to THM-FCD
		* Enable SSH and set the password to He!1c0pter
		* Configure WiFi for a local network with internet access to download additional software
	* Select write
* Put the SD card into the Pi and boot up.
* Log in using SSH as pi using the password of ‘He!1c0pter’ and run the configuration utility as root:
	`sudo raspi-config`
	~~* Select Change User Password and set it to '`He!1c0pter`'~~
	~~* Select Network Options then Hostname and set it to `THM-FCD`~~
	* Select Interfacting Options then:
		* Enable SPI for the application
		~~* Enable SSH to allow remote access~~
		* Enable I2C for the RTC
	~~* Select WiFi and configure for a local network with internet access to download additional software~~
	* Select Locales and add:
		* `de_DE.UTF8`
		* `es_ES.UTF8`
		* `fr_FR.UTF8`
		* `it_IT.UTF8`
		* `ru_RU.UTF8`
		* `zh_CN.UTF8`
	* Select OK and choose en_GB as the locale
	## Install software to support WiFi Direct
* `sudo apt update`
* `sudo apt upgrade`
* `sudo apt install i2c-tools` (for RTC)
* `sudo apt install hostapd` (for WifiDirect)
* `sudo apt install dnsmasq` (for WifiDirect)
* `sudo apt autoremove` (to clean up)

## Install software to support the application
* `sudo apt install git`
* `sudo apt install python3-pygame`
* `sudo apt install python3-gpiozero`
* `sudo apt install fontconfig`
* `sudo apt install ttf-mscorefonts-installer`
* `sudo apt install fonts-dancingscript`
* Get Google fonts for Chinese and Russian
	* `wget -O NotoSansSC.zip https://fonts.google.com/download?family=Noto+Sans+SC`
	* `wget -O NotoSerifSC.zip https://fonts.google.com/download?family=Noto+Serif+SC`
	* `wget -O NotoSans.zip https://fonts.google.com/download?family=Noto+Sans`
	* `wget -O NotoSerif.zip https://fonts.google.com/download?family=Noto+Serif`
	* `wget -O LongCang.zip https://fonts.google.com/download?family=Long+Cang`
	* `wget -O Caveat.zip https://fonts.google.com/download?family=Caveat`
	* Unpack zip files into /usr/local/share/fonts
	* `sudo unzip xxx.zip -d /usr/local/share/fonts/TTF` or OTF
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

## Configure shutdown
* `sudo vi /boot/config.txt` and add this line at the end:
	`dtoverlay=gpio-shutdown,gpio_pin=17`
* `sudo crontab -e`
	Add `30 16 * * * shutdown -h +1 FCD Shutting down for the day...`
		
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
* `sudo vi hostapd.txt`
	* Set `ssid=THM-FCD-HS, channel=8`
	* Set `wpa_passphrase=He!1c0pter`
* `sudo vi /etc/hostapd/ hostapd.conf`
	* Insert contents of hostapd.txt
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
	* Go to the bottom and insert the contents of dnsmasq.txt
* Check /etc/network/interfaces has only the standard line 'source-directory /etc/network/interfaces.d '
		
### Configure DHCPCD
* `sudo vi /etc/dhcpcd.conf`
	* Add this to the end of the file:
	`nohook wpa_supplicant`
	
### Configure autohotspot service
* Download the autohotspot service
	`wget https://www.raspberryconnect.com/images/Autohotspot/autohotspot-95-4/autohotspot-service.txt`
* `sudo vi autohotspot-service.txt`
	* Change wifidev to <wifi device> if required
* `sudo vi /etc/systemd/system/autohotspot.service`
	* Insert contents of autohotspot-service.txt
* `sudo systemctl enable autohotspot.service`
	
### Configure autohotspot script
* Download the autohotspot script
	`wget https://www.raspberryconnect.com/images/Autohotspot/autohotspot-95-4/autohotspot.txt`
* `sudo vi /usr/bin/autohotspot`
	* Insert contents of autohotspot.txt
* `sudo chmod +x /usr/bin/autohotspot`

### Test autohotspot
* `sudo vi /etc/wpa_supplicant/wpa_supplicant.conf`
	* Add ‘off’ to SSID making it invalid
	* Reboot
	* Search for networks to find THM-FCD-HS or use ssh pi@10.0.0.5
	* Reset wpa_supplicant ssid
	* Reboot
	
## Tidy up
* `mkdir Downloads`
* `mv *.zip Dowloads`
* `mv *.txt Downloads`
	
## Install the application
* Rename previous FlightControlDemonstrator to FlightControlDemonstrator.timestamp
* Download the application
	`git clone http://github.com/roddersuk/FlightControlDemonstrator`
* `sudo vi /etc/rc.local` and add the following line just before exit 0
	`sudo /home/pi/FlightControlDemonstrator/src/scripts/startup&`
	
## Make a backup copy of the SD card
* Shut down the Pi and put the SD card in your Linux machine
* Get PiShrink
	* `wget https://raw.githubusercontent.com/Drewsif/PiShrink/master/pishrink.sh`
	* `chmod +x pishrink.sh`
	* `sudo mv pishrink.sh /usr/local/bin`
* Make acopy of the image
	* `sudo fdisk -l` to find the SD card device name
	* `sudo dd if=/dev/mmcblk0 of=FCD.img bs=4M` to get an image file (use the right device name
	* `sudo pishrink.sh -aZ FCD.img`