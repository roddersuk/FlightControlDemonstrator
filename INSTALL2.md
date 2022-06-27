# Instructions for creating the SD card for the FCD - No RTC or AP
The operating system for the Raspberry Pi is Raspberry Pi OS Lite downloadable using the Raspberry Pi Imager.

## Install the O/S
* First flash the O/S onto the SD card using the Rapberry Pi Imageer on a PC
	+ Select Raspberry Pi OS Lite.
	+ Select the SD card to write to.
	+ Click Settings icon or type Ctrl-Shift-x to get Advanced Options
		- Set Hostname to THM-FCD
		- Enable SSH and set the username to bell and password to He!1c0pter
		- Configure WiFi for a local network with internet access to download additional software
		- Save
	+ Select write
* Put the SD card into the Pi and boot up.
* Log in using SSH as pi using the password of ‘He!1c0pter’ 

## Apply updates
* `sudo apt update`
* `sudo apt upgrade`

## Configure the O/S
Run the configuration utility as root:
	`sudo raspi-config`
	* Select Interface Options then:
		* Enable SPI for the application
	* Select Localisation Options then Locale and add:
		* `de_DE.UTF8`
		* `en_GB.UTF8`
		* `es_ES.UTF8`
		* `fr_FR.UTF8`
		* `it_IT.UTF8`
		* `ru_RU.UTF8`
		* `zh_CN.UTF8`
	* Select OK and choose en_GB as the default locale
	* Select OK to finish (may take a while to generate the locales)
	* Select Finish

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
	* `sudo unzip xxxSC.zip -d /usr/local/share/fonts/OTF`
	* `sudo unzip xxx.zip -d /usr/local/share/fonts/TTF`

## Configure shutdown
* `sudo vi /boot/config.txt` and add this line at the end:
	`dtoverlay=gpio-shutdown,gpio_pin=17`
		
## Tidy up
* `mkdir Downloads`
* `mv *.zip Dowloads`
* `sudo apt autoremove` (to clean up)

## Install the application
* Rename any previous FlightControlDemonstrator to FlightControlDemonstrator.timestamp
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